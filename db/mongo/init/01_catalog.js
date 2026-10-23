// MongoDB catalog (volet 1). Flexible "attributes" per category; prices in cents.
// product_id is the application link with PostgreSQL (order_items, stock): no FK, checked by code.
const market = db.getSiblingDB("market");

market.createUser({
  user: "catalog_svc",
  pwd: process.env.CATALOG_DB_PASSWORD,
  roles: [{ role: "readWrite", db: "market" }],
});

market.createCollection("catalog", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["product_id", "name", "category", "price_cents", "status"],
      properties: {
        product_id: { bsonType: "int", minimum: 1 },
        name: { bsonType: "string", minLength: 1 },
        category: { bsonType: "string" },
        price_cents: { bsonType: "int", minimum: 0 },
        status: { enum: ["active", "inactive"] },
        tags: { bsonType: "array", items: { bsonType: "string" } },
        description: { bsonType: "string" },
        attributes: { bsonType: "object" },
        indexed_at: { bsonType: "date" },
      },
    },
  },
  validationLevel: "strict",
});

market.catalog.createIndex({ product_id: 1 }, { unique: true });
market.catalog.createIndex({ category: 1 });
market.catalog.createIndex({ name: "text", description: "text" });

const now = new Date();
const p = (id, name, category, price, attributes, tags, description) => ({
  product_id: NumberInt(id), name, category, price_cents: NumberInt(price), status: "active",
  tags, description, attributes, indexed_at: now,
});

market.catalog.insertMany([
  p(1, "Casque Nova ANC", "Audio", 12990, { autonomie_h: 30, couleur: ["noir", "blanc"], bluetooth: "5.3" }, ["casque", "anc"], "Casque sans fil a reduction de bruit"),
  p(2, "Ecouteurs Pulse", "Audio", 5990, { autonomie_h: 8, couleur: ["noir"], etanche: "IPX4" }, ["ecouteurs"], "Ecouteurs intra-auriculaires"),
  p(3, "Enceinte Boom Mini", "Audio", 3990, { autonomie_h: 12, puissance_w: 10 }, ["enceinte"], "Petite enceinte portable"),
  p(4, "Basket Run 2", "Chaussures", 8990, { pointure: [39, 40, 41, 42, 43, 44], couleur: ["gris", "bleu"] }, ["running"], "Chaussure de course legere"),
  p(5, "Sneaker Urban", "Chaussures", 6990, { pointure: [38, 39, 40, 41, 42], couleur: ["blanc"] }, ["ville"], "Sneaker en cuir"),
  p(6, "Bottine Trek", "Chaussures", 11990, { pointure: [40, 41, 42, 43, 44, 45], impermeable: true }, ["randonnee"], "Bottine de randonnee"),
  p(7, "Chargeur USB-C 65W", "Accessoires", 2990, { puissance_w: 65, ports: 2 }, ["chargeur"], "Chargeur rapide GaN"),
  p(8, "Cable USB-C 2m", "Accessoires", 990, { longueur_m: 2, puissance_w: 100 }, ["cable"], "Cable tresse"),
  p(9, "Coque Smartphone", "Accessoires", 1490, { compatibilite: ["Pixel 9", "iPhone 16"], couleur: ["noir", "rouge"] }, ["coque"], "Coque antichoc"),
  p(10, "Montre Fit S", "Wearables", 15990, { autonomie_h: 168, gps: true, taille_mm: 42 }, ["montre", "sport"], "Montre connectee sport"),
  p(11, "Sac a dos City 20L", "Bagagerie", 4990, { volume_l: 20, poche_laptop_pouces: 15 }, ["sac"], "Sac a dos urbain"),
  p(12, "Clavier Mecanique K1", "Informatique", 9990, { switches: "brown", disposition: "AZERTY", sans_fil: true }, ["clavier"], "Clavier mecanique compact"),
]);

print("catalog ready: " + market.catalog.countDocuments() + " products");
