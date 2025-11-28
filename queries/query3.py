"""
Script: ukraine_damaged_cultural_sites.py
Descrizione: Query ottimizzata per siti culturali danneggiati in Ucraina dal 2022
"""

import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import time

# === CONFIG ===
OUTPUT_FILE = "DisperseArt_InformationVisualization/raw_data/ukraine_damaged_cultural_sites3.csv"
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

def query_damaged_cultural_sites():
    """Query specifica per siti culturali danneggiati"""
    query = """
    PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT DISTINCT ?item ?itemLabel ?itemDescription ?type ?typeLabel 
       ?location ?locationLabel ?date ?event ?eventLabel ?image ?coordinates WHERE {
  
  # Item in Ucraina
  ?item wdt:P276/wdt:P17 wd:Q212.
  
  # Tipi di patrimonio culturale
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
  
  # CERCA INDICATORI DI DANNO - approccio più selettivo
  {
    # 1. Item con data di distruzione dopo il 2022-02-24
    ?item wdt:P576 ?date.
    FILTER(?date >= "2022-02-24T00:00:00Z"^^xsd:dateTime)
  }
  UNION
  {
    # 2. Item con stato di danno specifico: danni da invasione russa
    ?item wdt:P5008 wd:Q110411718.  # Danni da invasione russa
    OPTIONAL { ?item wdt:P585 ?date. }
  }
  UNION
  {
    # 3. Item con eventi di guerra recenti (invasione russa dell'Ucraina)
    ?item wdt:P793 wd:Q110411718.  # Evento: invasione russa dell'Ucraina
    OPTIONAL { ?item wdt:P585 ?date. }
  }
  UNION
  {
    # 4. Item con eventi di guerra (più generici) dopo il 2022-02-24
    ?item wdt:P793 ?event.
    ?event wdt:P31/wdt:P279* wd:Q79913.  # Evento di guerra
    ?event wdt:P585 ?date.
    FILTER(?date >= "2022-02-24T00:00:00Z"^^xsd:dateTime)
  }
  
  # Filtra solo eventi dal 24 febbraio 2022 in poi (per le date)
  FILTER(!BOUND(?date) || ?date >= "2022-02-24T00:00:00Z"^^xsd:dateTime)
  
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
    print("=== QUERY OTTIMIZZATA PER SITI CULTURALI DANNIATI IN UCRAINA ===\n")
    
    print("Esecuzione query specifica...")
    start_time = time.time()
    
    df = query_damaged_cultural_sites()
    
    if not df.empty:
        # Filtra ulteriormente per assicurarci della rilevanza
        damage_indicators = ['destroyed', 'damaged', 'war', 'bombing', 'fire', 'shelling', 'occupation']
        
        def has_damage_indicator(row):
            desc = (row['description'] + ' ' + row['name']).lower()
            return any(indicator in desc for indicator in damage_indicators)
        
        # Applica il filtro
        df['has_damage_indicator'] = df.apply(has_damage_indicator, axis=1)
        filtered_df = df[df['has_damage_indicator'] | df['date'].notna()]
        
        # Salva
        filtered_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        end_time = time.time()
        print(f"✅ Query completata in {end_time - start_time:.2f} secondi")
        print(f"✅ Trovati {len(filtered_df)} siti culturali danneggiati")
        print(f"✅ File salvato: {OUTPUT_FILE}")
        
        # Anteprima
        print("\nPRIMI 10 SITI TROVATI:")
        print(filtered_df[['qid', 'name', 'type', 'location', 'date']].head(10).to_string(index=False))
        
    else:
        print("❌ Nessun risultato trovato")

if __name__ == "__main__":
    main()