"""
Script: opere_arte_ucraina_danneggiate.py
Autrice: Santo Cielo
Descrizione:
    Interroga Wikidata per estrarre opere d'arte e beni culturali in Ucraina
    che sono stati rubati, distrutti o dispersi dal 24 febbraio 2022.
    Salva il risultato in un CSV strutturato.
Compatibilità: Python 3.10+ | Dipendenze: pandas, SPARQLWrapper
"""

import pandas as pd
import time
from SPARQLWrapper import SPARQLWrapper, JSON
from datetime import datetime

# === CONFIG ===
OUTPUT_FILE = "opere_arte_ucraina_danneggiate.csv"
BATCH_SIZE = 20                    # Batch più piccoli per query complesse
SLEEP_TIME = 30                    # Più pausa per non saturare Wikidata
START_DATE = "2022-02-24T00:00:00Z"

sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

# === DEFINIZIONE QUERY ===
def get_ukraine_cultural_heritage_batch(offset=0):
    """
    Query per patrimonio culturale ucraino con possibili danni di guerra
    """
    query = f"""
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX bd: <http://www.bigdata.com/rdf#>

    SELECT DISTINCT ?item ?itemLabel ?itemDescription ?type ?typeLabel 
           ?location ?locationLabel ?date ?eventType ?image WHERE {{
      
      # Filtro per ubicazione in Ucraina
      ?item wdt:P276/wdt:P17 wd:Q212.
      
      # Tipi di patrimonio culturale
      ?item wdt:P31/wdt:P279* ?type.
      VALUES ?type {{
        wd:Q838948    # Opera d'arte
        wd:Q23413     # Museo
        wd:Q4989906   # Monumento
        wd:Q35127     # Patrimonio culturale
        wd:Q2065736   # Monumento patrimonio
        wd:Q860861    # Luogo di interesse
        wd:Q33506     # Edificio
        wd:Q2221906   # Sito patrimonio mondiale
      }}
      
      # Cerca eventi recenti o stati negativi
      OPTIONAL {{
        ?item wdt:P585 ?date.
        FILTER(?date >= "{START_DATE}"^^xsd:dateTime)
      }}
      
      # Cerca proprietà che indicano danni
      OPTIONAL {{
        ?item wdt:P5008 ?status.
        FILTER(STRSTARTS(STR(?status), "http://www.wikidata.org/entity/"))
      }}
      
      # Determina il tipo di evento
      BIND(
        IF(BOUND(?date) && BOUND(?status), "Danneggiato/Disperso",
          IF(BOUND(?date), "Evento recente", 
            IF(BOUND(?status), "Stato negativo", "Patrimonio culturale")
          )
        ) AS ?eventType
      )
      
      # Opzionale: immagine
      OPTIONAL {{ ?item wdt:P18 ?image }}
      
      SERVICE wikibase:label {{ 
        bd:serviceParam wikibase:language "it,en,uk,ru".
        ?item rdfs:label ?itemLabel.
        ?type rdfs:label ?typeLabel.
        ?location rdfs:label ?locationLabel.
        ?item schema:description ?itemDescription.
      }}
    }}
    ORDER BY DESC(?date)
    LIMIT {BATCH_SIZE}
    OFFSET {offset}
    """
    return query

def get_damaged_heritage_detailed():
    """
    Query più specifica per danni di guerra
    """
    query = """
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX bd: <http://www.bigdata.com/rdf#>

    SELECT ?item ?itemLabel ?itemDescription ?type ?typeLabel 
           ?location ?locationLabel ?date ?event ?eventLabel ?image WHERE {
      
      # Item in Ucraina con eventi recenti
      ?item wdt:P276/wdt:P17 wd:Q212;
            wdt:P31/wdt:P279* ?type;
            wdt:P585 ?date.
      
      FILTER(?date >= "2022-02-24T00:00:00Z"^^xsd:dateTime)
      
      # Tipi di patrimonio
      VALUES ?type {
        wd:Q838948 wd:Q23413 wd:Q4989906 wd:Q35127 
        wd:Q2065736 wd:Q860861 wd:Q33506 wd:Q2221906
      }
      
      # Evento associato (se presente)
      OPTIONAL { 
        ?item wdt:P793 ?event.
        ?event wdt:P31/wdt:P279* wd:Q79913.  # Evento di guerra
      }
      
      # Opzionale: immagine
      OPTIONAL { ?item wdt:P18 ?image }
      
      SERVICE wikibase:label { 
        bd:serviceParam wikibase:language "it,en,uk".
        ?item rdfs:label ?itemLabel.
        ?type rdfs:label ?typeLabel.
        ?location rdfs:label ?locationLabel.
        ?event rdfs:label ?eventLabel.
        ?item schema:description ?itemDescription.
      }
    }
    ORDER BY DESC(?date)
    LIMIT 100
    """
    return query

# === FUNZIONI QUERY ===
def query_ukraine_heritage(offset=0):
    """Esegue query per patrimonio ucraino"""
    query = get_ukraine_cultural_heritage_batch(offset)
    sparql.setQuery(query)
    
    try:
        results = sparql.query().convert()
        data = []
        
        for r in results["results"]["bindings"]:
            record = {
                "item_qid": r.get("item", {}).get("value", "").split("/")[-1],
                "itemLabel": r.get("itemLabel", {}).get("value", ""),
                "itemDescription": r.get("itemDescription", {}).get("value", ""),
                "type_qid": r.get("type", {}).get("value", "").split("/")[-1] if "type" in r else "",
                "typeLabel": r.get("typeLabel", {}).get("value", ""),
                "location_qid": r.get("location", {}).get("value", "").split("/")[-1] if "location" in r else "",
                "locationLabel": r.get("locationLabel", {}).get("value", ""),
                "date": r.get("date", {}).get("value", ""),
                "eventType": r.get("eventType", {}).get("value", ""),
                "image": r.get("image", {}).get("value", "")
            }
            data.append(record)
        
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"Errore nella query: {e}")
        return pd.DataFrame()

def query_damaged_heritage():
    """Query specifica per danni di guerra"""
    query = get_damaged_heritage_detailed()
    sparql.setQuery(query)
    
    try:
        results = sparql.query().convert()
        data = []
        
        for r in results["results"]["bindings"]:
            record = {
                "item_qid": r.get("item", {}).get("value", "").split("/")[-1],
                "itemLabel": r.get("itemLabel", {}).get("value", ""),
                "itemDescription": r.get("itemDescription", {}).get("value", ""),
                "type_qid": r.get("type", {}).get("value", "").split("/")[-1] if "type" in r else "",
                "typeLabel": r.get("typeLabel", {}).get("value", ""),
                "location_qid": r.get("location", {}).get("value", "").split("/")[-1] if "location" in r else "",
                "locationLabel": r.get("locationLabel", {}).get("value", ""),
                "date": r.get("date", {}).get("value", ""),
                "event_qid": r.get("event", {}).get("value", "").split("/")[-1] if "event" in r else "",
                "eventLabel": r.get("eventLabel", {}).get("value", ""),
                "image": r.get("image", {}).get("value", "")
            }
            data.append(record)
        
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"Errore nella query danni: {e}")
        return pd.DataFrame()

# === ESECUZIONE IN BATCH ===
def batch_query_all_heritage():
    """Esegue query batch per tutto il patrimonio"""
    print("Avvio query batch per patrimonio culturale ucraino...")
    all_results = pd.DataFrame()
    offset = 0
    batch_count = 0
    
    while True:
        batch_count += 1
        print(f"Batch {batch_count} - Offset {offset}")
        
        try:
            df_batch = query_ukraine_heritage(offset)
            
            if df_batch.empty:
                print("Nessun altro risultato trovato.")
                break
                
            all_results = pd.concat([all_results, df_batch], ignore_index=True)
            print(f"Recuperati {len(df_batch)} record in questo batch")
            
            # Se abbiamo meno risultati del batch size, siamo alla fine
            if len(df_batch) < BATCH_SIZE:
                break
                
            offset += BATCH_SIZE
            time.sleep(SLEEP_TIME)
            
        except Exception as e:
            print(f"Errore nel batch {batch_count}: {e}")
            time.sleep(SLEEP_TIME * 2)
    
    return all_results

# === FILTRO PER EVENTI RECENTI ===
def filter_recent_events(df):
    """Filtra i dataframe per eventi recenti e cerca indicatori di danno"""
    if df.empty:
        return df
    
    # Crea una copia per evitare SettingWithCopyWarning
    df_filtered = df.copy()
    
    # Filtra per date recenti
    if 'date' in df_filtered.columns:
        df_filtered['date'] = pd.to_datetime(df_filtered['date'], errors='coerce')
        has_recent_date = df_filtered['date'] >= pd.to_datetime(START_DATE)
    else:
        has_recent_date = False
    
    # Cerca indicatori di danno nelle descrizioni
    damage_keywords = ['stolen', 'damaged', 'destroyed', 'lost', 'missing', 'war', 'bombing', 'fire', 'looted', 'raid']
    
    description = df_filtered['itemDescription'].str.lower().fillna('')
    label = df_filtered['itemLabel'].str.lower().fillna('')
    
    has_damage_keyword = (
        description.str.contains('|'.join(damage_keywords)) |
        label.str.contains('|'.join(damage_keywords))
    )
    
    # Combina i filtri
    df_filtered['is_recent_damage'] = has_recent_date | has_damage_keyword
    
    return df_filtered

# === ESECUZIONE PRINCIPALE ===
def main():
    print("=== RICERCA OPERE D'ARTE E BENI CULTURALI IN UCRAINA (DAL 24/02/2022) ===\n")
    
    # Strategy 1: Query specifica per danni
    print("1. Esecuzione query specifica per danni di guerra...")
    damaged_df = query_damaged_heritage()
    print(f"Trovati {len(damaged_df)} record con danni specifici\n")
    time.sleep(SLEEP_TIME)
    
    # Strategy 2: Query batch per tutto il patrimonio
    print("2. Esecuzione query batch per patrimonio culturale ucraino...")
    heritage_df = batch_query_all_heritage()
    print(f"Trovati {len(heritage_df)} record totali di patrimonio culturale\n")
    
    # Filtra per eventi recenti/danni
    print("3. Filtraggio per eventi recenti e indicatori di danno...")
    filtered_heritage = filter_recent_events(heritage_df)
    
    recent_count = filtered_heritage['is_recent_damage'].sum() if not filtered_heritage.empty else 0
    print(f"Trovati {recent_count} record con indicatori di danno recente\n")
    
    # Combina i risultati
    if not damaged_df.empty:
        # Aggiungi source per tracciabilità
        damaged_df['source'] = 'danni_specifici'
        if not filtered_heritage.empty:
            filtered_heritage['source'] = 'patrimonio_filtrato'
            combined_df = pd.concat([damaged_df, filtered_heritage[filtered_heritage['is_recent_damage']]], 
                                  ignore_index=True)
        else:
            combined_df = damaged_df
    else:
        combined_df = filtered_heritage[filtered_heritage['is_recent_damage']] if not filtered_heritage.empty else pd.DataFrame()
        combined_df['source'] = 'patrimonio_filtrato'
    
    # Rimuovi duplicati
    if not combined_df.empty and 'item_qid' in combined_df.columns:
        combined_df = combined_df.drop_duplicates(subset=['item_qid'])
    
    # === SALVATAGGIO ===
    if not combined_df.empty:
        # Riordina le colonne per una migliore leggibilità
        column_order = ['item_qid', 'itemLabel', 'itemDescription', 'typeLabel', 
                       'locationLabel', 'date', 'eventType', 'eventLabel', 'source', 'image']
        
        # Mantieni solo le colonne presenti
        available_columns = [col for col in column_order if col in combined_df.columns]
        other_columns = [col for col in combined_df.columns if col not in column_order]
        
        combined_df = combined_df[available_columns + other_columns]
        
        combined_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"File salvato: {OUTPUT_FILE}")
        print(f"Totale record salvati: {len(combined_df)}")
        
        # Statistiche
        if 'date' in combined_df.columns:
            recent_items = combined_df[combined_df['date'] >= START_DATE]
            print(f"Di cui con data successiva al 24/02/2022: {len(recent_items)}")
            
    else:
        print("Nessun risultato trovato da salvare.")
        
    print("\n=== RICERCA COMPLETATA ===")

if __name__ == "__main__":
    main()