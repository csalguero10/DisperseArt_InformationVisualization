import pandas as pd
from geopy.distance import geodesic
import re

# --- CONFIGURAZIONE PERCORSI ---
PATH_PROTETTI = 'DisperseArt_InformationVisualization/csv/2_ukraine_list_qid_coord.csv'
PATH_DANNEGGIATI = 'DisperseArt_InformationVisualization/raw_data/unesco_damage_sites.csv' 

def parse_coords(val):
    """Estrae (Lat, Lon) numerici da stringhe."""
    if pd.isna(val) or str(val).strip() == "": return None
    try:
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
        if len(nums) >= 2: return (float(nums[0]), float(nums[1]))
    except:
        return None

def find_spatial_intersection():
    print("Caricamento dataset UNESCO...")
    
    # Caricamento file
    df_p = pd.read_csv(PATH_PROTETTI, sep=';')
    df_d = pd.read_csv(PATH_DANNEGGIATI, sep=',')

    # Pulizia coordinate
    df_p['p_coords'] = df_p['coordinates'].apply(parse_coords)
    # Assumiamo che la colonna nel dataset danneggiati si chiami 'Geo location'
    df_d['d_coords'] = df_d['Geo location'].apply(parse_coords)

    intersections = []
    
    # Rimuoviamo righe senza coordinate per il confronto
    df_p = df_p.dropna(subset=['p_coords'])
    df_d = df_d.dropna(subset=['d_coords'])

    print(f"Confronto spaziale: {len(df_p)} protetti vs {len(df_d)} danneggiati...")

    for _, p in df_p.iterrows():
        for _, d in df_d.iterrows():
            # Calcolo distanza
            dist_m = geodesic(p['p_coords'], d['d_coords']).meters
            
            # Se la distanza è minima, i siti coincidono
            if dist_m <= 100:
                intersections.append({
                    'Status': 'MATCH (Same Site)',
                    'UNESCO_Protected_Name': p['name'],
                    'UNESCO_Damaged_Name': d['Title of the damage site in English'],
                    'Distance_m': round(dist_m, 1),
                    'Category': p['category']
                })
            # Se la distanza è entro 1km, è un pericolo di prossimità
            elif dist_m <= 1000:
                intersections.append({
                    'Status': 'PROXIMAL (Risk)',
                    'UNESCO_Protected_Name': p['name'],
                    'UNESCO_Damaged_Name': d['Title of the damage site in English'],
                    'Distance_m': round(dist_m, 1),
                    'Category': p['category']
                })

    # Creazione Report
    report_df = pd.DataFrame(intersections)
    if not report_df.empty:
        report_df.to_csv('DisperseArt_InformationVisualization/csv/incrocio_spaziale_liste_unesco.csv', index=False, sep=';', encoding='utf-8-sig')
        print(f"\nAnalisi completata. Trovati {len(report_df)} punti di contatto geografico.")
        print(report_df.head())
    else:
        print("\nNessuna sovrapposizione trovata tra le liste.")

if __name__ == "__main__":
    find_spatial_intersection()