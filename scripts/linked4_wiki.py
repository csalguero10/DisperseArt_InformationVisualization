import pandas as pd
import requests
import math
import time
import re
from urllib.parse import unquote

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {"Accept": "application/sparql-results+json"}

# Classi Wikidata più ampie per siti culturali
ALLOWED_CLASSES = {
    "Q16970", "Q23413", "Q33506", "Q4989906", "Q839954", "Q13226383", 
    "Q1664720", "Q38723", "Q2031836", "Q41176", "Q32815", "Q11424",
    "Q173782", "Q35127", "Q207694", "Q24398318", "Q4989906", "Q2365880",
    "Q11722877", "Q15621286", "Q44613", "Q174782", "Q4006", "Q123705",
    "Q16970", "Q33506", "Q43229", "Q23413", "Q41137", "Q924018"
}

def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def query_wikidata(query):
    try:
        r = requests.get(
            ENDPOINT,
            params={'query': query, 'format': 'json'},
            headers=HEADERS,
            timeout=30
        )
        if r.status_code != 200:
            print(f"  HTTP Error: {r.status_code}")
            return []
        return r.json().get("results", {}).get("bindings", [])
    except Exception as e:
        print(f"  Query error: {e}")
        return []

def clean_name(name):
    """Pulizia più aggressiva dei nomi"""
    if not isinstance(name, str):
        return ""
    
    # Rimuove parentesi, trattini, punti eccessivi
    name = re.sub(r'\([^)]*\)', '', name)  # rimuove tutto tra parentesi
    name = re.sub(r'[–—]', ' ', name)      # sostituisce trattini con spazi
    name = re.sub(r'\s+', ' ', name)       # spazi multipli a singolo
    name = re.sub(r'^\s+|\s+$', '', name)  # trim
    name = re.sub(r'[.,;]$', '', name)     # rimuove punteggiatura finale
    
    return name

def search_by_label_advanced(name, lat, lon, radius_km=5):
    """Ricerca avanzata per label con filtri geografici"""
    clean_names = [
        clean_name(name),
        clean_name(name.split('(')[0]),  # senza parentesi
        clean_name(re.sub(r'[^\w\s]', ' ', name)),  # senza punteggiatura
    ]
    
    # Prendi le prime 3 parole significative per ricerca più ampia
    words = [w for w in clean_name(name).split() if len(w) > 3][:3]
    if words:
        clean_names.append(' '.join(words))
    
    queries = []
    
    for search_name in set(clean_names):
        if len(search_name) < 3:
            continue
            
        # Query 1: Ricerca per nome esatto + coordinate
        q1 = f"""
        SELECT ?item ?itemLabel ?coord ?class ?classLabel WHERE {{
          ?item ?label "{search_name}"@uk .
          ?item wdt:P625 ?coord .
          FILTER(str(?itemLabel) = "{search_name}")
          OPTIONAL {{ ?item wdt:P31 ?class . }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "uk,en". }}
        }}
        LIMIT 10
        """
        queries.append(q1)
        
        # Query 2: Ricerca per nome parziale + filtro geografico
        q2 = f"""
        SELECT ?item ?itemLabel ?coord ?class ?classLabel WHERE {{
          SERVICE wikibase:around {{
            ?item wdt:P625 ?coord .
            bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral .
            bd:serviceParam wikibase:radius "{radius_km}" .
          }}
          ?item rdfs:label ?itemLabel .
          FILTER(CONTAINS(LCASE(?itemLabel), LCASE("{search_name}")))
          OPTIONAL {{ ?item wdt:P31 ?class . }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "uk,en". }}
        }}
        LIMIT 15
        """
        queries.append(q2)
    
    all_results = []
    for query in queries:
        results = query_wikidata(query)
        all_results.extend(results)
        time.sleep(0.5)  # Rate limiting
    
    return all_results

def search_by_coords_extended(lat, lon, radius_km=2):
    """Ricerca estesa per coordinate"""
    queries = []
    
    # Prova con diversi raggi
    for radius in [0.5, 1, 2]:
        q = f"""
        SELECT ?item ?itemLabel ?coord ?class ?classLabel WHERE {{
          SERVICE wikibase:around {{
            ?item wdt:P625 ?coord .
            bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral .
            bd:serviceParam wikibase:radius "{radius}" .
          }}
          OPTIONAL {{ ?item wdt:P31 ?class . }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "uk,en". }}
        }}
        LIMIT 30
        """
        queries.append(q)
    
    all_results = []
    for query in queries:
        results = query_wikidata(query)
        all_results.extend(results)
        time.sleep(0.3)
    
    return all_results

def parse_coord(coord):
    if not coord:
        return None, None
    try:
        s = coord.replace("Point(", "").replace(")", "").strip()
        lon, lat = s.split()
        return float(lat), float(lon)
    except:
        return None, None

def extract_wikipedia_id(wiki_url):
    """Estrae il titolo Wikipedia dall'URL"""
    if not isinstance(wiki_url, str):
        return None
    
    # Cerca pattern comune negli URL Wikipedia
    patterns = [
        r'wikipedia.org/wiki/([^?#]+)',
        r'uk\.wikipedia.org/wiki/([^?#]+)',
        r'uk\.m\.wikipedia.org/wiki/([^?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, wiki_url)
        if match:
            title = unquote(match.group(1))
            return title.replace('_', ' ')
    
    return None

def search_by_wikipedia_title(title):
    """Cerca in Wikidata usando il titolo Wikipedia"""
    if not title:
        return []
    
    q = f"""
    SELECT ?item ?itemLabel ?coord ?class ?classLabel WHERE {{
      ?sitelink schema:about ?item ;
                schema:isPartOf <https://uk.wikipedia.org/> ;
                schema:name "{title}"@uk .
      OPTIONAL {{ ?item wdt:P625 ?coord . }}
      OPTIONAL {{ ?item wdt:P31 ?class . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "uk,en". }}
    }}
    LIMIT 5
    """
    return query_wikidata(q)

def score_match(candidate, original_name, original_lat, original_lon):
    """Assegna un punteggio al candidato"""
    qid, label, cls, dist, method, cls_label = candidate
    score = 0
    
    # Punteggio per distanza
    if dist <= 0.1:
        score += 100
    elif dist <= 0.5:
        score += 80
    elif dist <= 1:
        score += 60
    elif dist <= 2:
        score += 40
    
    # Punteggio per similarità del nome
    original_lower = original_name.lower()
    label_lower = label.lower()
    
    if original_lower == label_lower:
        score += 100
    elif original_lower in label_lower or label_lower in original_lower:
        score += 70
    elif any(word in label_lower for word in original_lower.split() if len(word) > 3):
        score += 40
    
    # Punteggio per classe rilevante
    if cls in ALLOWED_CLASSES:
        score += 50
    
    # Bonus per metodo di ricerca
    if method == "wikipedia":
        score += 30
    
    return score

# Carica i dati
df = pd.read_csv("DisperseArt_InformationVisualization/csv/cultural_damage_full.csv")

# Nuove colonne
df["wikidata_id"] = None
df["wikidata_label"] = None
df["instance_of"] = None
df["instance_of_label"] = None
df["distance_km"] = None
df["method"] = None
df["match_score"] = None

print("Totale righe:", len(df))
print()

for idx, row in df.iterrows():
    name = row["name"]
    lat = row.get("latitude")
    lon = row.get("longitude")
    wiki_url = row.get("wikiUA", "")

    print(f"[{idx+1}/{len(df)}] {name}")

    # Salta senza coordinate
    if pd.isna(lat) or pd.isna(lon):
        print("  → Skip: nessuna coordinata\n")
        df.at[idx, "method"] = "no_coords"
        continue

    candidates = []

    # STRATEGIA 1: Ricerca via Wikipedia (più affidabile)
    wikipedia_title = extract_wikipedia_id(wiki_url)
    if wikipedia_title:
        print(f"  Ricerca Wikipedia: {wikipedia_title}")
        wiki_results = search_by_wikipedia_title(wikipedia_title)
        for r in wiki_results:
            qid = r["item"]["value"].split("/")[-1]
            lbl = r["itemLabel"]["value"]
            cls = r.get("class", {}).get("value", "").split("/")[-1]
            cls_label = r.get("classLabel", {}).get("value", "")
            lat2, lon2 = parse_coord(r.get("coord", {}).get("value"))
            dist = distance_km(lat, lon, lat2, lon2) if lat2 else 999
            candidates.append((qid, lbl, cls, dist, "wikipedia", cls_label))

    # STRATEGIA 2: Ricerca avanzata per label
    if not candidates:
        print("  Ricerca avanzata per label...")
        label_results = search_by_label_advanced(name, lat, lon)
        for r in label_results:
            qid = r["item"]["value"].split("/")[-1]
            lbl = r["itemLabel"]["value"]
            cls = r.get("class", {}).get("value", "").split("/")[-1]
            cls_label = r.get("classLabel", {}).get("value", "")
            lat2, lon2 = parse_coord(r.get("coord", {}).get("value"))
            dist = distance_km(lat, lon, lat2, lon2) if lat2 else 999
            candidates.append((qid, lbl, cls, dist, "label", cls_label))

    # STRATEGIA 3: Ricerca estesa per coordinate
    if not candidates:
        print("  Ricerca estesa per coordinate...")
        coord_results = search_by_coords_extended(lat, lon)
        for r in coord_results:
            qid = r["item"]["value"].split("/")[-1]
            lbl = r["itemLabel"]["value"]
            cls = r.get("class", {}).get("value", "").split("/")[-1]
            cls_label = r.get("classLabel", {}).get("value", "")
            lat2, lon2 = parse_coord(r.get("coord", {}).get("value"))
            dist = distance_km(lat, lon, lat2, lon2) if lat2 else 999
            candidates.append((qid, lbl, cls, dist, "coords", cls_label))

    # Rimuovi duplicati
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c[0] not in seen:  # QID unico
            seen.add(c[0])
            unique_candidates.append(c)
    candidates = unique_candidates

    print(f"  Candidati trovati: {len(candidates)}")

    # Seleziona il miglior match
    if candidates:
        # Calcola punteggi per tutti i candidati
        scored_candidates = []
        for candidate in candidates:
            score = score_match(candidate, name, lat, lon)
            scored_candidates.append((candidate, score))
        
        # Ordina per punteggio
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_candidate, best_score = scored_candidates[0]
        
        qid, lbl, cls, dist, method, cls_label = best_candidate
        
        df.at[idx, "wikidata_id"] = qid
        df.at[idx, "wikidata_label"] = lbl
        df.at[idx, "instance_of"] = cls
        df.at[idx, "instance_of_label"] = cls_label
        df.at[idx, "distance_km"] = dist
        df.at[idx, "method"] = method
        df.at[idx, "match_score"] = best_score
        
        print(f"  → MATCH: {qid} | {lbl} | dist: {dist:.3f}km | score: {best_score} | {method}")
        
        # Mostra anche i secondi migliori per debug
        if len(scored_candidates) > 1:
            for i, (candidate, score) in enumerate(scored_candidates[1:4], 2):
                qid2, lbl2, _, dist2, method2, _ = candidate
                print(f"     {i}°: {qid2} | {lbl2} | dist: {dist2:.3f}km | score: {score}")
    else:
        print("  → Nessun match trovato")
        df.at[idx, "method"] = "none"

    print()
    time.sleep(1)  # Rate limiting tra le righe

# Salva i risultati
df.to_csv("DisperseArt_InformationVisualization/csv/cultural_damage_wikidata_enriched_improved.csv", index=False)
print("OK — creato: cultural_damage_wikidata_enriched_improved.csv")

# Statistiche
matched = df[df["wikidata_id"].notna()]
print(f"\nSTATISTICHE:")
print(f"Righe totali: {len(df)}")
print(f"Match trovati: {len(matched)} ({len(matched)/len(df)*100:.1f}%)")
print(f"Metodi di match:")
print(df["method"].value_counts())