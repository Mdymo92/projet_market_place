# Justification des choix d'architecture

Ce document explique pourquoi chaque brique de la plateforme Market a été choisie, quelles alternatives ont été écartées et quels compromis cela implique. Le schéma correspondant est dans `architecture.png`. Les décisions les plus structurantes sont détaillées dans les ADR (`docs/adr/`).

## Principes directeurs

1. **Chaque service possède ses données.** Aucun service ne lit les tables d'un autre ; il passe par son API ou par un événement Kafka.
2. **Le contrat avant le code.** Les API REST (OpenAPI), le schéma GraphQL et le format des événements sont écrits et relus avant toute implémentation.
3. **Cohérence forte là où il y a de l'argent et du stock, cohérence finale ailleurs.**
4. **Tout est observable et tout se lance en une commande.**
5. **Une seule famille de langages côté serveur (Python)** pour les services et les traitements Spark, afin de limiter ce que deux personnes doivent maîtriser en huit semaines.

## 1. Accès

### Application web : React + Vite

- **Rôle :** les cinq onglets de la maquette (Vue d'ensemble, Commandes, Catalogue, Logistique, Observabilité) et l'écran de connexion.
- **Pourquoi :** écosystème le plus répandu pour reproduire fidèlement une maquette, démarrage instantané avec Vite, composants de graphiques disponibles. L'interface s'adapte au rôle de l'utilisateur et n'affiche aucun chiffre écrit en dur : tout vient des API.
- **Écarté :** Angular, plus structurant mais trop lourd pour cinq onglets ; une page HTML statique, qui ne permettrait pas la gestion des rôles et du token.

### Grafana

- **Rôle :** tableaux de bord techniques et métier, un par rôle décrit dans le sujet.
- **Pourquoi :** il lit à la fois Prometheus (métriques), Loki (logs) et Jaeger (traces). Un seul outil suffit donc pour comprendre un incident.

## 2. Passerelle : Kong

- **Rôle :** point d'entrée unique (port 8000) devant tous les services.
- **Pourquoi :**
  - vérification du JWT par un plugin natif : une requête sans token ou avec un token expiré est refusée (401) avant d'atteindre un service ;
  - limitation du nombre d'appels (rate limiting), plus stricte sur la route de connexion pour freiner les tentatives de mot de passe ;
  - configuration déclarative (mode sans base de données) versionnée dans Git, donc reproductible et relisible en revue de code.
- **Écarté :** Traefik, très bon routeur mais sans vérification JWT complète en natif ; NGINX, où tout serait à écrire à la main.
- **Compromis :** Kong vérifie *qui* appelle, pas *ce qu'il a le droit de faire*. Ce second contrôle est fait dans chaque service (voir RBAC).

## 3. Services

### FastAPI (Python)

- **Rôle :** les six services : Auth, Orders, Inventory, Payment, Catalog, Dashboard API.
- **Pourquoi :** même langage que les traitements Spark ; génération OpenAPI et validation des entrées (Pydantic) intégrées ; fonctionnement asynchrone, utile pour les timeouts et pour limiter les appels simultanés (bulkhead).
- **Écarté :** Spring Boot, robuste mais qui ajouterait un deuxième langage à maîtriser.

### Authentification : JWT de 15 minutes et refresh token

- **Pourquoi :** le JWT est sans état : Kong et chaque service le vérifient avec la même clé, sans appeler le service Auth à chaque requête. La durée courte limite l'impact d'un vol ; le refresh token est à usage unique et stocké haché en base. Les mots de passe sont hachés avec bcrypt.
- **Comptes de service :** le service Orders obtient son propre token (rôle `service_account`) pour appeler Inventory et Payment.
- **Écarté :** des sessions côté serveur, qu'il faudrait partager entre tous les services.

### Contrôle des rôles (RBAC) dans chaque service

- **Pourquoi :** cinq rôles (admin, catalog_manager, analyst, logistics, service_account) et une matrice unique (`services/common/market_common/rbac.py`, `docs/rbac.md`). Un rôle non autorisé reçoit un 403, et le refus est enregistré (qui, quoi, quand).
- **Écarté :** tout contrôler dans Kong, ce qui est impossible au niveau d'un champ GraphQL ou d'une règle métier.

### Catalogue en GraphQL, schéma d'abord (Ariadne)

- **Pourquoi :** le sujet impose l'approche « contrat d'abord » ; avec Ariadne, le fichier `schema.graphql` est le contrat et le code s'y conforme. GraphQL convient au catalogue car les attributs varient selon la catégorie : l'interface demande seulement les champs qu'elle affiche.
- **Écarté :** Strawberry, où le schéma est déduit du code (l'inverse de ce qui est demandé).

### Saga orchestrée par le service Orders

- **Pourquoi :** une commande touche trois services qui ont chacun leur base. Une transaction unique est impossible ; la Saga enchaîne les étapes (réserver le stock, payer, confirmer) et compense en cas d'échec (paiement refusé au-delà de 200 €, stock libéré). Chaque étape est tracée dans `orders.saga_log`.
- **Orchestration plutôt que chorégraphie :** le déroulé est lisible à un seul endroit, plus simple à tester et à expliquer.
- **Écarté :** la transaction distribuée en deux phases (2PC), lente et fragile si un participant tombe.

### Idempotence

- **Pourquoi :** un retry réseau ne doit pas créer deux commandes ni réserver deux fois le stock. Chaque POST qui modifie l'état exige un en-tête `Idempotency-Key`, stocké avec une contrainte d'unicité.

### Résilience des appels entre services

- **Timeout** (2 s) : un appel ne reste jamais bloqué.
- **Retry** (3 tentatives, attente croissante) : uniquement sur erreur réseau ou 502/503/504.
- **Circuit breaker** : après 5 échecs consécutifs, les appels échouent immédiatement pendant 30 s ; l'API répond 503 au lieu de faire attendre l'utilisateur.
- **Bulkhead** : nombre maximal d'appels simultanés vers une dépendance, pour qu'un service lent n'épuise pas les ressources de l'appelant.
- **Outils :** httpx, tenacity, pybreaker, regroupés dans `ResilientClient`.

## 4. Données

### PostgreSQL : commandes, stock, paiements, utilisateurs

- **Pourquoi :**
  - transactions ACID : une commande et ses lignes sont enregistrées ensemble ou pas du tout ;
  - clés étrangères et contraintes CHECK (le stock ne peut jamais devenir négatif) ;
  - verrou de ligne (`SELECT ... FOR UPDATE`) : le dernier article n'est vendu qu'une fois ;
  - partitionnement natif de la table des commandes par mois, pour garder des requêtes rapides quand le volume grossit.
- **Théorème CAP :** pour l'argent et le stock, on privilégie la cohérence. Afficher un stock faux reviendrait à vendre ce qu'on n'a pas.
- **Isolation :** un schéma et un rôle par service. Le rôle `orders_svc` ne peut pas lire `inventory` (vérifié par la CI). Un rôle `analytics_reader` en lecture seule sert au tableau de bord et à l'extraction vers le lake (ADR-003).
- **Écarté :** MongoDB et Cassandra, en cohérence finale, où l'intégrité serait laissée au code.

### MongoDB : catalogue produits

- **Pourquoi :** chaque catégorie a ses propres attributs (pointure, autonomie, longueur de câble). Un document les porte naturellement ; les champs obligatoires restent validés par `$jsonSchema`, et un index texte sert la recherche. Le catalogue est surtout lu : un prix affiché avec quelques secondes de retard est acceptable (BASE), car le service Orders relit le prix au moment de la commande.
- **Écarté :** une colonne JSONB dans PostgreSQL, possible mais moins pratique pour interroger et valider des attributs libres.
- **Compromis :** pas de clé étrangère entre MongoDB et PostgreSQL ; le lien `product_id` est vérifié par le code.

### Kafka (mode KRaft)

- **Rôle :** transport de tous les événements : navigation, commandes, paiements, mouvements de stock, expéditions, alertes.
- **Pourquoi :**
  - journal durable que l'on peut relire, utile pour rejouer un traitement après un incident ;
  - partitions : le parallélisme augmente avec le volume (Black Friday) ;
  - plusieurs lecteurs indépendants (Spark, tableau de bord) sur les mêmes données ;
  - le mode KRaft supprime Zookeeper, soit un conteneur de moins.
- **Clés de partition :** `warehouse_id` pour le stock et les expéditions, `order_id` pour les commandes, ce qui garantit l'ordre des événements d'un même entrepôt ou d'une même commande.
- **Écarté :** RabbitMQ, où un message lu est consommé et ne peut pas être relu.

### Spark Structured Streaming

- **Rôle :** indicateurs en continu (commandes, chiffre d'affaires, panier moyen, ruptures) et détection d'alertes (stock bas, échecs de paiement, pic de commandes, panier abandonné, entrepôt saturé).
- **Pourquoi :** fenêtres glissantes, watermark pour les événements en retard, état, checkpoint pour reprendre après un arrêt. Combiné à Delta Lake, chaque événement est écrit une seule fois (exactly-once). Le même moteur sert aussi au batch.
- **Écarté :** Apache Flink, plus faible latence mais un second moteur à maîtriser.

### Data Lake : MinIO + Delta Lake

- **MinIO :** stockage objet compatible S3, en local et gratuit ; le même code fonctionnerait sur AWS S3.
- **Delta Lake :** ajoute aux fichiers Parquet des transactions ACID, le time travel (revenir à une version passée d'une table) et le MERGE.
- **Quatre zones :**
  - **raw :** données telles que reçues, jamais modifiées, ce qui permet de tout rejouer ;
  - **staging :** typage, dédoublonnage sur `event_id`, contrôles qualité, lignes rejetées mises en quarantaine, email client haché ;
  - **curated :** tables métier jointes (commandes avec lignes et produits, historique de stock) ;
  - **consumption :** agrégats prêts pour le tableau de bord.
- **Catalogue de données :** chaque jeu de données décrit sa source, son propriétaire et sa dernière mise à jour.
- **Écarté :** Parquet seul (pas de transactions, risque de fichiers partiels) ; Apache Iceberg, équivalent fonctionnel mais moins intégré à Spark dans notre configuration.

### Spark batch

- **Rôle :** extraction périodique de PostgreSQL vers la zone raw (JDBC, rôle en lecture seule), puis promotion de zone en zone.
- **Pourquoi :** même moteur et même code que le streaming.

## 5. Observabilité

| Brique | Rôle | Pourquoi | Écarté |
| --- | --- | --- | --- |
| Prometheus | Métriques de chaque service, de Kong, Kafka, Spark, MinIO | Standard du marché, règles d'alerte (service arrêté, taux d'erreur, latence, retard des consommateurs Kafka) | |
| OpenTelemetry + Jaeger | Traces distribuées | Suivre une requête de Kong à Orders, Inventory et Payment ; standard ouvert, indépendant de l'outil d'affichage | Zipkin, moins complet |
| Loki | Logs | Logs JSON consultables dans Grafana, léger | Elasticsearch, gourmand en mémoire |

## 6. Déploiement : Docker Compose

- **Pourquoi :** le sujet exige un démarrage en une commande. Trois profils (core, data, obs) permettent de lancer une partie seulement sur un ordinateur limité en mémoire.
- **Écarté :** Kubernetes, adapté à la production mais disproportionné pour une démonstration sur un ordinateur portable.

## 7. Limites assumées

- **Un seul nœud** pour chaque composant (PostgreSQL, Kafka, MinIO) : pas de haute disponibilité, acceptable pour une démonstration et mentionné comme évolution.
- **Paiement simulé** : la règle des 200 € remplace un vrai prestataire.
- **Lecture directe des tables par le rôle analytique** au lieu d'une capture de changements (CDC, par exemple Debezium) : plus simple, au prix d'une dépendance au format des tables (ADR-003).
- **Clé JWT partagée (HS256)** : simple à mettre en place ; une version suivante utiliserait une paire de clés (RS256) pour que seul le service Auth puisse signer.
