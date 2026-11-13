"""Market architecture diagram (no justification). Usage: python build_diagram.py out.svg"""
import html, sys
INK, GREY, ACC, EDGE, TINT, HI = "#1d2433", "#5b6475", "#2f5bd3", "#8f98a8", "#f3f5f9", "#e8eefc"
o = []
def t(x, y, s, size=13, w=400, fill=INK, a="start", extra=""):
    o.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}" {extra}>{html.escape(s)}</text>')
def r(x, y, w, h, fill="#fff", stroke=EDGE, sw=1.3, rx=10, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
def box(x, y, w, h, name, tech, hi=False):
    r(x, y, w, h, HI if hi else "#fff", ACC if hi else EDGE, 2 if hi else 1.3)
    t(x + w / 2, y + h / 2 - 3, name, 15, 700, a="middle")
    t(x + w / 2, y + h / 2 + 16, tech, 12, 400, GREY, a="middle")
def chip(x, y, w, s):
    r(x, y, w, 24, TINT, EDGE, 1, 6); t(x + w / 2, y + 16, s, 12, 500, a="middle")
def path(d, label=None, lx=0, ly=0, a="start", dash=False):
    ds = ' stroke-dasharray="5 4"' if dash else ""
    o.append(f'<path d="{d}" fill="none" stroke="{EDGE}" stroke-width="1.6"{ds} marker-end="url(#ar)"/>')
    if label:
        t(lx, ly, label, 12, 500, GREY, a)

L0, L1, R0, R1 = 40, 1020, 1140, 1560
MID = (L0 + L1) / 2
GAP = (L1 + R0) / 2
RC = (R0 + R1) / 2
# row A
t(MID, 92, "CONSOMMATEURS INTERNES", 11, 700, ACC, "middle", 'letter-spacing="1"')
t(RC, 92, "CONSOMMATEURS INTERNES", 11, 700, ACC, "middle", 'letter-spacing="1"')
box(MID - 260, 100, 520, 64, "Application web Market", "React + Vite · login + 5 onglets")
box(R0, 100, R1 - R0, 64, "Grafana", "tableaux de bord et alertes")
path(f"M{MID} 164 V198", "HTTPS + JWT", MID + 8, 186)
# row B
box(L0, 200, L1 - L0, 64, "Kong · API gateway", ":8000 · vérification JWT · rate limiting · routage /v1 et /graphql", hi=True)
t(RC, 194, "SOURCES", 11, 700, ACC, "middle", 'letter-spacing="1"')
box(R0, 200, R1 - R0, 64, "Générateur d'événements", "navigation, paniers, expéditions")
path(f"M{MID} 264 V298")
# services container
r(L0, 300, L1 - L0, 244, TINT)
t(L0 + 16, 326, "Microservices FastAPI", 15, 700); t(L0 + 186, 326, "chaque service a sa propre base", 12, 400, GREY)
IN = L1 - L0 - 32
bw = (IN - 48) / 3; cx = [L0 + 16, L0 + 16 + bw + 24, L0 + 16 + 2 * (bw + 24)]
box(cx[0], 344, bw, 70, "Orders", "commandes · orchestre la Saga")
box(cx[1], 344, bw, 70, "Inventory", "stocks · entrepôts · réservations")
box(cx[2], 344, bw, 70, "Payment", "paiement simulé")
box(cx[0], 454, bw, 70, "Catalog", "GraphQL · produits et prix")
box(cx[1], 454, bw, 70, "Auth", "login · JWT · rôles")
box(cx[2], 454, bw, 70, "Dashboard API", "données des onglets 1, 4, 5")
path(f"M{cx[0]+bw} 379 H{cx[1]-2}")
t(cx[0] + bw + 12, 372, "", 11)
oc, pc = cx[0] + bw / 2, cx[2] + bw / 2
qx = cx[0] + bw * 0.25
path(f"M{qx} 414 V452", "prix", qx + 6, 440)
path(f"M{oc} 414 V430 H{pc} V416", "Saga : réserve le stock, paie, libère si échec", (oc + pc) / 2, 446, "middle")
# right column streaming
box(R0, 344, R1 - R0, 70, "Apache Kafka (KRaft)", "clicks · orders · payments · inventory · shipments · alerts")
path(f"M{L1} 379 H{R0-2}", "événements", GAP, 370, "middle")
path(f"M{RC} 264 V342")
box(R0, 454, R1 - R0, 70, "Spark Structured Streaming", "fenêtres · watermark · checkpoint · KPIs et alertes")
path(f"M{RC-60} 414 V452")
path(f"M{RC+60} 454 V416", "alertes", RC + 68, 440)
# lake
r(R0, 580, R1 - R0, 150)
t(RC, 606, "Data Lake · MinIO + Delta Lake", 15, 700, a="middle")
zw = (R1 - R0 - 32 - 3 * 18) / 4
zones = ["raw", "staging", "curated", "consumption"]
for i, z in enumerate(zones):
    zx = R0 + 16 + i * (zw + 18)
    chip(zx, 626, zw, z)
    if i < 3:
        path(f"M{zx+zw+2} 638 H{zx+zw+16}")
t(RC, 680, "qualité + quarantaine · catalogue de données", 12, 400, GREY, "middle")
t(RC, 700, "buckets S3 · tables Delta partitionnées par date", 12, 400, GREY, "middle")
path(f"M{RC} 524 V578")
# databases
r(cx[1], 600, bw, 120)
t(cx[1] + bw / 2, 626, "PostgreSQL", 15, 700, a="middle")
cw = (bw - 40) / 2
for i, s in enumerate(["schéma auth", "schéma orders", "schéma inventory", "schéma payments"]):
    chip(cx[1] + 16 + (i % 2) * (cw + 8), 642 + (i // 2) * 32, cw, s)
r(cx[0], 600, bw, 120)
t(cx[0] + bw / 2, 646, "MongoDB", 15, 700, a="middle")
t(cx[0] + bw / 2, 668, "collection catalog", 12, 400, GREY, "middle")
t(cx[0] + bw / 2, 688, "attributs libres par catégorie", 12, 400, GREY, "middle")
box(cx[2], 640, bw, 70, "Spark batch", "extraction JDBC")
path(f"M{cx[1]+bw/2} 544 V598", "un schéma et un rôle par service", cx[1] + bw / 2 + 8, 576)
path(f"M{oc} 544 V598", "catalogue", oc + 8, 576)
mc = cx[1] + bw / 2
path(f"M{mc} 720 V744 H{pc} V712", "lecture seule", (mc + pc) / 2, 760, "middle")
path(f"M{cx[2]+bw} 675 H{R0-2}", "vers raw", (cx[2] + bw + R0) / 2, 667, "middle")
# lake -> dashboard (reads consumption)
path(f"M{R0} 610 H{GAP} V489 H{cx[2]+bw+2}", "lit", GAP + 6, 560, dash=True)
# observability
oy = 800
t(L0, oy - 12, "Observabilité · métriques, traces et logs de toutes les briques", 13, 700)
ow = (L1 - L0 - 48) / 3
box(L0, oy, ow, 64, "Prometheus", "métriques + règles d'alerte")
box(L0 + ow + 24, oy, ow, 64, "OpenTelemetry → Jaeger", "traces distribuées")
box(L0 + 2 * (ow + 24), oy, ow, 64, "Loki", "logs JSON")
path(f"M{L1} {oy+32} H1580 V132 H{R1+2}", "vers Grafana", L1 + 20, oy + 26, dash=True)
t(L0, oy + 110, "Le tout lancé par Docker Compose en une commande (profils core, data, obs).", 13, 500, GREY)
W, H = 1600, oy + 135
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Inter, 'DejaVu Sans', Arial, sans-serif">
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{EDGE}"/></marker></defs>
<rect width="{W}" height="{H}" fill="#fff"/>
<text x="40" y="46" font-size="26" font-weight="700" fill="{INK}">Architecture de la plateforme Market</text>
<text x="40" y="74" font-size="14" fill="{GREY}">Flux des requêtes, des événements et des données</text>
{"".join(o)}
</svg>'''
open(sys.argv[1], "w").write(svg)
