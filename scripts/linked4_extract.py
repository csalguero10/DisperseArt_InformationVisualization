from rdflib import Dataset
import pandas as pd
import re

g = Dataset()
g.parse("DisperseArt_InformationVisualization/raw_data/https___linked4resilience.eu_graphs_cultural-site-damage-events.trig", format="trig")

print("Numero triple:", len(g))
print("Grafi caricati:", len(list(g.graphs())))

q_meta = """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX schema: <https://schema.org/>
PREFIX vocab: <https://linked4resilience.eu/vocab/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?site
       (SAMPLE(?name) AS ?name)
       (SAMPLE(?altName) AS ?altName)
       (SAMPLE(?address) AS ?address)
       (SAMPLE(?observationYear) AS ?observationYear)
       (SAMPLE(?comment) AS ?comment)
       (SAMPLE(?wikiUA) AS ?wikiUA)
       (SAMPLE(?newsLink) AS ?newsLink)
       (SAMPLE(?wkt) AS ?wkt)
WHERE {
  GRAPH ?g {
    ?site geo:hasGeometry ?geom .
    ?geom geo:asWKT ?wkt .
    OPTIONAL { ?site schema:name ?name . }
    OPTIONAL { ?site schema:alternateName ?altName . }
    OPTIONAL { ?site schema:address ?address . }
    OPTIONAL { ?site schema:observationTime ?observationYear . }
    OPTIONAL { ?site rdfs:comment ?comment . }
    OPTIONAL { ?site vocab:wikipediaUkrainian ?wikiUA . }
    OPTIONAL { ?site vocab:wasMentionedIn ?newsLink . }
  }
}
GROUP BY ?site

"""

# --- METADATA ---
df_meta = pd.DataFrame([
    {
        "site": str(r["site"]),
        "name": str(r["name"]) if r["name"] else None,
        "altName": str(r["altName"]) if r["altName"] else None,
        "address": str(r["address"]) if r["address"] else None,
        "observationYear": str(r["observationYear"]) if r["observationYear"] else None,
        "comment": str(r["comment"]) if r["comment"] else None,
        "wikiUA": str(r["wikiUA"]) if r["wikiUA"] else None,
        "newsLink": str(r["newsLink"]) if r["newsLink"] else None,
    }
    for r in g.query(q_meta)
])

# --- WKT ---
q_wkt = """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
SELECT ?site ?wkt
WHERE {
  GRAPH ?g {
    ?site geo:hasGeometry ?geom .
    ?geom geo:asWKT ?wkt .
  }
}
"""

df_wkt = pd.DataFrame([
    {"site": str(r["site"]), "wkt": str(r["wkt"])}
    for r in g.query(q_wkt)
])

# --- MERGE ---
full = df_meta.merge(df_wkt, on="site", how="left")

# --- DEBUG COLONNE ---
print("Colonne nel DataFrame:", list(full.columns))

# --- TROVA COLONNA WKT QUESTA è UNA COSA STUPIDISSIMA---
wkt_col = None
for col in full.columns:
    if "wkt" in col.lower():
        wkt_col = col
        break

print("Colonna WKT trovata:", wkt_col)

# --- PARSE WKT → COORDS ---
def extract_coords(wkt_str):
    if isinstance(wkt_str, str):
        m = re.search(r"POINT\s*\(\s*([-0-9\.]+)\s+([-0-9\.]+)\s*\)", wkt_str, flags=re.IGNORECASE)
        if m:
            lon = float(m.group(1))
            lat = float(m.group(2))
            return lon, lat
    return None, None

full["longitude"], full["latitude"] = zip(*full[wkt_col].apply(extract_coords))

print("Prime coordinate estratte:")
print(full[["site", wkt_col, "longitude", "latitude"]].head())

# --- EXTRACT OBLAST ---
def extract_oblast(address):
    if pd.isna(address):
        return None
    parts = [p.strip() for p in address.split(",")]
    for p in parts:
        if "oblast" in p.lower():
            return p
    return None

full["oblast"] = full["address"].map(extract_oblast)

# --- COORDINATE P625 ---
def make_p625(lat, lon):
    if lat is None or lon is None:
        return None
    return f"{lat},{lon}"

full["coordinate_p625"] = full.apply(lambda r: make_p625(r["latitude"], r["longitude"]), axis=1)

# --- SALVA ---
full.to_csv("DisperseArt_InformationVisualization/processed_data/cultural_damage_l4R.csv", index=False)
print("File generato: cultural_damage_l4R.csv")
