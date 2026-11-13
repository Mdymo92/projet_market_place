import html, sys
W = 1600
INK, GREY, ACC, EDGE, TINT, KONG = "#1d2433", "#5b6475", "#2f5bd3", "#9aa3b2", "#f3f5f9", "#e8eefc"
LH = 19
out = []
def t(x, y, s, size=13, weight=400, fill=INK, anchor="start", style=""):
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {style}>{html.escape(s)}</text>')
def rect(x, y, w, h, fill="#fff", stroke=EDGE, sw=1.2, rx=10):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
def box_h(b):
    return 34 + LH * (1 + len(b["why"]) + (1 if b.get("alt") else 0)) + 6
def box(x, y, w, b, h=None, hi=False):
    h = h or box_h(b)
    rect(x, y, w, h, fill=KONG if hi else "#fff", stroke=ACC if hi else EDGE, sw=2 if hi else 1.2)
    t(x + 16, y + 26, b["name"], 16, 700)
    yy = y + 26 + LH + 2
    t(x + 16, yy, b["tech"], 12.5, 400, GREY)
    for line in b["why"]:
        yy += LH
        out.append(f'<circle cx="{x+20}" cy="{yy-4.5}" r="3" fill="{ACC}"/>')
        t(x + 30, yy, line, 13)
    if b.get("alt"):
        yy += LH
        t(x + 16, yy, "Écarté : " + b["alt"], 12, 400, GREY, style='font-style="italic"')
    return h
def arrow(x1, y1, x2, y2, label=None, lx=None, ly=None, anchor="start"):
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{EDGE}" stroke-width="1.6" marker-end="url(#ar)"/>')
    if label:
        t(lx if lx is not None else x1 + 8, ly if ly is not None else (y1 + y2) / 2 + 4, label, 12.5, 500, GREY, anchor)
def layer(y, h, num, name):
    t(28, y + 24, num, 26, 700, ACC)
    t(28, y + 46, name, 13, 600, GREY)
    out.append(f'<line x1="28" y1="{y+56}" x2="140" y2="{y+56}" stroke="{ACC}" stroke-width="2"/>')

X0, X1 = 170, W - 40
CW = X1 - X0
y = 100
# ---- 1 access
web = dict(name="Application web Market", tech="React + Vite · login + 5 onglets", why=["Fidèle à la maquette, l'interface s'adapte au rôle", "Aucun chiffre en dur : tout vient des API"], alt="Angular, trop lourd pour 5 onglets")
graf = dict(name="Grafana", tech="un tableau de bord par rôle", why=["Un seul outil pour métriques, traces et logs", "Alertes visibles en quelques secondes"])
wl = (CW - 24) * 0.58
h1 = max(box_h(web), box_h(graf))
layer(y, h1, "1", "Accès")
box(X0, y, wl, web, h1); box(X0 + wl + 24, y, CW - wl - 24, graf, h1)
web_bottom = y + h1; graf_y = y; graf_x2 = X1
y += h1 + 46
arrow(X0 + wl / 2, web_bottom, X0 + wl / 2, y - 2, "appels HTTPS + JWT")
# ---- 2 gateway
kong = dict(name="Kong · API gateway", tech="point d'entrée unique :8000 · configuration déclarative versionnée dans Git",
            why=["Vérifie le JWT sans écrire de code : pas de token ou token expiré = 401 à l'entrée", "Limite le nombre d'appels (rate limiting), route /v1/* et /graphql vers le bon service"],
            alt="Traefik (pas de vérification JWT complète en natif), NGINX (tout à coder)")
layer(y, 0, "2", "Passerelle")
hk = box(X0, y, CW, kong, hi=True)
y += hk + 46
arrow(X0 + CW / 2, y - 46, X0 + CW / 2, y - 2, "requête authentifiée")
# ---- 3 services
svc = [
 dict(name="Auth", tech="JWT 15 min + refresh à usage unique", why=["Sans état : Kong et les services vérifient la même clé", "Mots de passe bcrypt, comptes de service"]),
 dict(name="Orders", tech="orchestrateur de la Saga", why=["3 bases séparées : pas de transaction commune possible", "Paiement refusé = stock libéré (compensation)", "Idempotency-Key : un retry ne crée pas 2 commandes"]),
 dict(name="Catalog", tech="GraphQL, schéma d'abord (Ariadne)", why=["Le sujet impose le contrat avant le code", "Attributs variables : le client choisit ses champs"]),
 dict(name="Inventory", tech="stocks, entrepôts, réservations", why=["Verrou de ligne : le dernier article n'est vendu qu'une fois", "Réservation idempotente"]),
 dict(name="Payment", tech="paiement simulé", why=["Refuse au-delà de 200 €", "Déclenche la compensation de la Saga"]),
 dict(name="Dashboard API", tech="données des onglets 1, 4 et 5", why=["Lecture seule : Delta, PostgreSQL, Prometheus", "Alertes en direct (Server-Sent Events)"]),
]
bw = (CW - 32 - 2 * 16) / 3
rh = max(box_h(b) for b in svc)
head = 70
foot = 58
ch = head + 2 * rh + 16 + foot
layer(y, ch, "3", "Services")
rect(X0, y, CW, ch, fill=TINT)
t(X0 + 16, y + 28, "Microservices FastAPI · chacun possède ses données", 16, 700)
t(X0 + 16, y + 50, "FastAPI : même langage que Spark, OpenAPI et validation intégrés, asynchrone · écarté : Spring Boot (2e langage)", 12.5, 400, GREY)
for i, b in enumerate(svc):
    r, c = divmod(i, 3)
    box(X0 + 16 + c * (bw + 16), y + head + r * (rh + 16), bw, b, rh)
fy = y + head + 2 * rh + 16 + 24
out.append(f'<circle cx="{X0+20}" cy="{fy-4.5}" r="3" fill="{ACC}"/>')
t(X0 + 30, fy, "Chaque appel sortant : timeout, retry, circuit breaker, bulkhead · un service en panne = échec rapide (503) au lieu de bloquer", 13)
out.append(f'<circle cx="{X0+20}" cy="{fy+LH-4.5}" r="3" fill="{ACC}"/>')
t(X0 + 30, fy + LH, "Contrôle du rôle dans chaque service : rôle non autorisé = 403, refus enregistré (qui, quoi, quand)", 13)
svc_bottom = y + ch
y += ch + 50
half = (CW - 40) / 2
LX, RX = X0, X0 + half + 40
arrow(LX + half / 2, svc_bottom, LX + half / 2, y - 2, "lit et écrit uniquement son schéma", LX + half / 2 + 8)
arrow(RX + half / 2, svc_bottom, RX + half / 2, y - 2, "publie des événements", RX + half / 2 + 8)
# ---- 4 data
pg = dict(name="PostgreSQL", tech="commandes · stock · paiements · utilisateurs", why=["ACID, clés étrangères, CHECK (stock jamais négatif)", "Partitionnement des commandes par mois", "CAP : cohérence d'abord pour l'argent et le stock", "Un schéma + un rôle par service (vérifié en CI)"], alt="MongoDB, Cassandra (cohérence finale)")
mg = dict(name="MongoDB", tech="catalogue produits", why=["Attributs différents par catégorie (pointure, autonomie)", "Validation $jsonSchema + recherche texte", "Prix en retard de quelques secondes acceptable (BASE)"], alt="JSONB PostgreSQL, peu pratique ici")
sb = dict(name="Spark batch", tech="extraction JDBC vers la zone raw", why=["Même moteur que le streaming", "Rôle analytics_reader en lecture seule"])
kf = dict(name="Kafka (KRaft)", tech="7 topics : clicks, orders, payments, inventory…", why=["Journal durable qu'on peut relire, partitionné", "Plusieurs lecteurs indépendants · sans Zookeeper"], alt="RabbitMQ (un message lu disparaît)")
ss = dict(name="Spark Structured Streaming", tech="KPIs et alertes en continu", why=["Fenêtres, watermark, état, checkpoint", "Exactly-once vers Delta, alertes vers le topic alerts"], alt="Flink (un 2e moteur à maîtriser)")
lk = dict(name="Data Lake · MinIO + Delta Lake", tech="raw → staging → curated → consumption", why=["MinIO : S3 compatible, en local, gratuit", "Delta : transactions ACID et time travel sur fichiers", "Raw jamais modifié, qualité + quarantaine, email haché"], alt="Parquet seul (pas ACID), Iceberg (moins intégré)")
lh_ = sum(box_h(b) for b in (pg, mg, sb)) + 2 * 22
rh_ = sum(box_h(b) for b in (kf, ss, lk)) + 2 * 22
dh = 50 + max(lh_, rh_) + 16
layer(y, dh, "4", "Données")
rect(LX, y, half, dh, fill=TINT); rect(RX, y, half, dh, fill=TINT)
t(LX + 16, y + 30, "Stockage opérationnel", 16, 700); t(RX + 16, y + 30, "Temps réel et Data Lake", 16, 700)
yy = y + 50
ys = {}
for k, b in (("pg", pg), ("mg", mg), ("sb", sb)):
    h = box(LX + 16, yy, half - 32, b); ys[k] = (yy, h); yy += h + 22
yy = y + 50
for k, b in (("kf", kf), ("ss", ss), ("lk", lk)):
    h = box(RX + 16, yy, half - 32, b); ys[k] = (yy, h); yy += h + 22
cx = RX + half / 2
arrow(cx, ys["kf"][0] + ys["kf"][1], cx, ys["ss"][0] - 2)
arrow(cx, ys["ss"][0] + ys["ss"][1], cx, ys["lk"][0] - 2)
cl = LX + half / 2
arrow(cl, ys["mg"][0] + ys["mg"][1], cl, ys["sb"][0] - 2)
by = ys["sb"][0] + ys["sb"][1] / 2
arrow(LX + half - 16, by, RX + 14, by, "raw", (LX + half + RX) / 2, by - 8, "middle")
data_bottom = y + dh
y += dh + 46
# ---- 5 observability
ob = [dict(name="Prometheus", tech="métriques de chaque service, Kong, Kafka, Spark", why=["Standard des métriques, alertes en 5 à 10 s"]),
      dict(name="OpenTelemetry → Jaeger", tech="traces distribuées", why=["Suit une requête Kong → orders → payment", "Standard ouvert, indépendant de l'outil"], alt="Zipkin"),
      dict(name="Loki", tech="logs JSON", why=["Consultables dans le même Grafana, léger"], alt="Elasticsearch (gourmand en RAM)")]
ow = (CW - 2 * 16) / 3
oh = max(box_h(b) for b in ob)
layer(y, oh, "5", "Observabilité")
for i, b in enumerate(ob):
    box(X0 + i * (ow + 16), y, ow, b, oh)
# link obs -> grafana along the right edge
gx = X1 + 18
out.append(f'<path d="M{X1} {y + oh/2} H{gx} V{graf_y + 40} H{X1 + 2}" fill="none" stroke="{EDGE}" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#ar)"/>')
y += oh + 40
t(X0, y, "Docker Compose : toute la plateforme se lance en une commande (profils core, data, obs) · écarté : Kubernetes, trop lourd pour une démo sur laptop", 13, 500, GREY)
H = y + 30
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Inter, 'DejaVu Sans', Arial, sans-serif">
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{EDGE}"/></marker></defs>
<rect width="{W}" height="{H}" fill="#ffffff"/>
<text x="28" y="44" font-size="26" font-weight="700" fill="{INK}">Architecture de la plateforme Market</text>
<text x="28" y="72" font-size="14" fill="{GREY}">Chaque brique, son rôle et pourquoi elle a été choisie · les points bleus donnent la justification</text>
{"".join(out)}
</svg>'''
open(sys.argv[1], "w").write(svg)
print(W, H)
