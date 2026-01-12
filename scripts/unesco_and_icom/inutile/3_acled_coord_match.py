"""
uso acled e lista unesco per confrontare coordinate se hanno attaccato in zona ma con raggio di 200 m è troppo poco, uso 5km che è troppo
"""
import pandas as pd
from geopy.distance import geodesic
import re

def clean_coords(lat, lon):
    """Converte e pulisce le coordinate in float."""
    try:
        return (float(lat), float(lon))
    except (ValueError, TypeError):
        return None

def analyze_unesco_acled(unesco_path, acled_path, radius_km=5.0):
    # 1. Caricamento Dataset
    # UNESCO: sep=';' (basato sui tuoi messaggi precedenti)
    df_u = pd.read_csv(unesco_path, sep=';')
    
    # ACLED: sep=';' (basato sulla struttura che hai incollato)
    df_a = pd.read_csv(acled_path, sep=';', low_memory=False)

    # 2. Pulizia Coordinate UNESCO
    # Estraiamo i numeri dal campo 'coordinates' (es: "50.45, 30.51")
    def parse_unesco_coords(val):
        if pd.isna(val): return None
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
        if len(nums) >= 2: return (float(nums[0]), float(nums[1]))
        return None

    df_u['u_coords'] = df_u['coordinates'].apply(parse_unesco_coords)
    
    # 3. Pulizia Coordinate ACLED
    df_a['a_coords'] = df_a.apply(lambda x: clean_coords(x['ACLED_Lat'], x['ACLED_Lon']), axis=1)

    # Rimuoviamo righe senza coordinate valide
    df_u = df_u.dropna(subset=['u_coords'])
    df_a = df_a.dropna(subset=['a_coords'])

    matches = []

    print(f"Inizio analisi: {len(df_u)} siti UNESCO vs {len(df_a)} eventi ACLED...")

    # 4. Loop di confronto (ottimizzato: controlla prima la regione admin1 per velocità)
    for _, u in df_u.iterrows():
        # Opzionale: filtra ACLED per admin1 se i nomi coincidono (es. "Donetsk")
        # Per ora facciamo un controllo spaziale globale per sicurezza
        
        for _, a in df_a.iterrows():
            # Calcolo distanza geodesica
            dist = geodesic(u['u_coords'], a['a_coords']).km
            
            if dist <= radius_km:
                matches.append({
                    'unesco_id': u['id'],
                    'unesco_site': u['name'],
                    'acled_event_id': a['event_id_cnty'],
                    'date': a['ACLED_Date'],
                    'event_type': a['ACLED_EventType'],
                    'sub_event': a['ACLED_SubEvent'],
                    'distance_km': round(dist, 2),
                    'fatalities': a['fatalities'],
                    'notes': a['ACLED_Notes'],
                    'location_acled': a['location']
                })

    # 5. Risultato
    df_results = pd.DataFrame(matches)
    return df_results

# --- ESECUZIONE ---
# Assicurati che i nomi dei file siano corretti
output_matches = analyze_unesco_acled('DisperseArt_InformationVisualization/csv/ukraine_list_qid_coord.csv', 'DisperseArt_InformationVisualization/processed_data/acled_clean.csv', radius_km=5)

if not output_matches.empty:
    # Salvataggio in Excel o CSV per analisi facilitata
    output_matches.to_csv('unesco_acled_proximity_report.csv', index=False, sep=';')
    print(f"Match trovati: {len(output_matches)}")
    print(output_matches[['unesco_site', 'date', 'distance_km', 'event_type']].head(10))
else:
    print("Nessun match trovato. Suggerimento: aumenta il raggio (radius_km) o verifica il formato delle coordinate nel file UNESCO.")
