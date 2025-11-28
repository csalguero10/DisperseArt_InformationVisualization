"""
Script: ukraine_war_damaged_cultural_sites_v2.py
Descrizione: Query migliorata per siti culturali danneggiati nella guerra Russia-Ucraina 2022-2024
"""

import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import time

# === CONFIG ===
OUTPUT_FILE = "DisperseArt_InformationVisualization/raw_data/ukraine_war_damaged_cultural_sites_v2.csv"
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

def query_war_damaged_sites():
    """Query migliorata per danni di guerra 2022-2024"""
    query = """
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX bd: <http://www.bigdata.com/rdf#>

    SELECT DISTINCT ?item ?itemLabel ?itemDescription ?type ?typeLabel 
           ?location ?locationLabel ?date ?event ?eventLabel ?image ?coordinates WHERE {
      {
        # Cerca item danneggiati dall'invasione russa
        ?item wdt:P5008 wd:Q110411718.
        OPTIONAL { ?item wdt:P585 ?date. }
      }
      UNION
      {
        # Cerca item con evento di invasione russa
        ?item wdt:P793 wd:Q110411718.
        OPTIONAL { ?item wdt:P585 ?date. }
      }
      UNION
      {
        # Cerca item distrutti dopo il 24 febbraio 2022
        ?item wdt:P576 ?date.
        FILTER(?date >= "2022-02-24T00:00:00Z"^^xsd:dateTime)
      }
      UNION
      {
        # Cerca item con descrizioni che menzionano la guerra
        ?item schema:description ?desc.
        FILTER(LANG(?desc) = "en" || LANG(?desc) = "uk" || LANG(?desc) = "ru")
        FILTER(CONTAINS(LCASE(?desc), "russian invasion") || 
               CONTAINS(LCASE(?desc), "2022 invasion") ||
               CONTAINS(LCASE(?desc), "war in ukraine") ||
               CONTAINS(LCASE(?desc), "destroyed in 2022") ||
               CONTAINS(LCASE(?desc), "damaged in 2022"))
        OPTIONAL { ?item wdt:P585 ?date. }
      }
      
      # Filtra che siano in Ucraina
      ?item wdt:P276/wdt:P17 wd:Q212.
      
      # Filtra per tipi di patrimonio culturale
      ?item wdt:P31/wdt:P279* ?type.
      VALUES ?type {
        wd:Q838948    # Opera d'arte
        wd:Q23413     # Museo
        wd:Q4989906   # Monumento
        wd:Q35127     # Patrimonio culturale
        wd:Q2065736   # Monumento patrimonio
        wd:Q860861    # Luogo di interesse
        wd:Q33506     # Edificio
        wd:Q2221906   # Sito patrimonio mondiale
        wd:Q41176     # Chiesa
        wd:Q16970     # Cattedrale
      }
      
      # Opzionali
      OPTIONAL { ?item wdt:P18 ?image }
      OPTIONAL { ?item wdt:P625 ?coordinates }
      OPTIONAL { 
        ?item wdt:P793 ?event.
        ?event rdfs:label ?eventLabel.
        FILTER(LANG(?eventLabel) = "en")
      }
      
      SERVICE wikibase:label { 
        bd:serviceParam wikibase:language "en,uk,ru".
        ?item rdfs:label ?itemLabel.
        ?type rdfs:label ?typeLabel.
        ?location rdfs:label ?locationLabel.
        ?item schema:description ?itemDescription.
      }
    }
    ORDER BY DESC(?date)
    LIMIT 500
    """
    
    sparql.setQuery(query)
    try:
        results = sparql.query().convert()
        data = []
        for r in results["results"]["bindings"]:
            data.append({
                "qid": r["item"]["value"].split("/")[-1],
                "name": r.get("itemLabel", {}).get("value", ""),
                "description": r.get("itemDescription", {}).get("value", ""),
                "type": r.get("typeLabel", {}).get("value", ""),
                "location": r.get("locationLabel", {}).get("value", ""),
                "date": r.get("date", {}).get("value", ""),
                "event": r.get("eventLabel", {}).get("value", ""),
                "image": r.get("image", {}).get("value", ""),
                "coordinates": r.get("coordinates", {}).get("value", "")
            })
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Errore nella query: {e}")
        return pd.DataFrame()

def main():
    print("=== QUERY MIGLIORATA PER DANNI GUERRA UCRAINA 2022-2024 ===\n")
    
    print("Esecuzione query...")
    start_time = time.time()
    
    df = query_war_damaged_sites()
    
    if not df.empty:
        # Filtra ulteriormente per assicurarci della rilevanza
        war_keywords = ['russian invasion', '2022 invasion', 'war in ukraine', 'destroyed', 'damaged']
        
        def has_war_indicator(row):
            text = (row['description'] + ' ' + row.get('event', '')).lower()
            return any(keyword in text for keyword in war_keywords)
        
        df['has_damage_indicator'] = df.apply(has_war_indicator, axis=1)
        
        # Salva
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        end_time = time.time()
        print(f"✅ Query completata in {end_time - start_time:.2f} secondi")
        print(f"✅ Trovati {len(df)} siti culturali (prima del filtro)")
        print(f"✅ Di cui con indicatori di danno: {df['has_damage_indicator'].sum()}")
        print(f"✅ File salvato: {OUTPUT_FILE}")
        
        # Anteprima
        print("\nPRIMI 10 SITI TROVATI:")
        print(df[['qid', 'name', 'type', 'date', 'has_damage_indicator']].head(10).to_string(index=False))
        
    else:
        print("❌ Nessun risultato trovato")

if __name__ == "__main__":
    main()