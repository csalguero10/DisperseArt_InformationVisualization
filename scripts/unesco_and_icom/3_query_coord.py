"""
aggiungo coordinate ai siti di unesco list
"""

import pandas as pd
import requests
import time
import os

def get_wikidata_coordinates(qids):
    """Interroga Wikidata per ottenere le coordinate di una lista di QID (P625)."""
    endpoint_url = "https://query.wikidata.org/sparql"
    
    # Pulizia e formattazione QID (rimuove eventuali spazi o nan)
    valid_qids = [q for q in qids if isinstance(q, str) and q.startswith('Q')]
    if not valid_qids:
        return {}

    qid_formatted = " ".join([f"wd:{q}" for q in valid_qids])
    
    query = f"""
    SELECT ?item ?coords WHERE {{
      VALUES ?item {{ {qid_formatted} }}
      ?item wdt:P625 ?coords.
    }}
    """
    
    headers = {
        'User-Agent': 'UNESCO-Bot/1.0 (https://example.org/; user@example.com)',
        'Accept': 'application/sparql-results+json'
    }
    
    try:
        response = requests.get(endpoint_url, params={'query': query, 'format': 'json'}, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = {}
        for row in data['results']['bindings']:
            qid = row['item']['value'].split('/')[-1]
            # Formato Wikidata: Point(long lat)
            raw_coords = row['coords']['value'].replace('Point(', '').replace(')', '')
            lon, lat = raw_coords.split(' ')
            # Formattazione standard: Lat, Lon
            results[qid] = f"{lat}, {lon}"
        return results
    except Exception as e:
        print(f"Errore durante l'interrogazione SPARQL: {e}")
        return {}

def process_unesco_csv(input_path, output_path):
    # 1. Caricamento del file
    if not os.path.exists(input_path):
        print(f"Errore: Il file {input_path} non esiste.")
        return

    print(f"Caricamento file: {input_path}...")
    df = pd.read_csv(input_path, sep=';')

    # 2. Identificazione QID univoci per minimizzare le chiamate API
    unique_qids = df['QID'].dropna().unique().tolist()
    
    print(f"Recupero coordinate per {len(unique_qids)} QID da Wikidata...")
    coords_map = get_wikidata_coordinates(unique_qids)

    # 3. Funzione di aggiornamento
    def update_coords(row):
        # Aggiorna solo se la colonna è vuota o NaN
        if pd.isna(row['coordinates']) or str(row['coordinates']).strip() == "":
            return coords_map.get(row['QID'], "")
        return row['coordinates']

    # 4. Applicazione dell'aggiornamento
    df['coordinates'] = df.apply(update_coords, axis=1)

    # 5. Salvataggio
    df.to_csv(output_path, sep=';', index=False, encoding='utf-8')
    print(f"Successo! File aggiornato salvato in: {output_path}")

# --- CONFIGURAZIONE ---
input_csv = "DisperseArt_InformationVisualization/processed_data/unesco_ukraine_lists_qid.csv"
output_csv = "DisperseArt_InformationVisualization/processed_data/2_ukraine_list_qid_coord.csv"

if __name__ == "__main__":
    process_unesco_csv(input_csv, output_csv)