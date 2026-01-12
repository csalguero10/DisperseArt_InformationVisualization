import pandas as pd
from geopy.distance import geodesic
import re

# --- CONFIGURAZIONE PERCORSI ---
PATH_UNESCO_PROTETTI = 'DisperseArt_InformationVisualization/csv/2_ukraine_list_qid_coord.csv'
PATH_NUOVI_DANNI = 'DisperseArt_InformationVisualization/raw_data/unesco_damage_sites.csv' 
PATH_ACLED = 'DisperseArt_InformationVisualization/processed_data/acled_clean.csv'

def parse_coords(val):
    """Estrae (Lat, Lon) numerici."""
    if pd.isna(val) or str(val).strip() == "": return None
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
    if len(nums) >= 2: return (float(nums[0]), float(nums[1]))
    return None

def run_flexible_analysis():
    print("Caricamento dataset...")
    df_u = pd.read_csv(PATH_UNESCO_PROTETTI, sep=';')
    df_d = pd.read_csv(PATH_NUOVI_DANNI, sep=',') 
    df_a = pd.read_csv(PATH_ACLED, sep=';', low_memory=False)

    # Filtraggio ACLED: Includiamo Precisione 1 (esatta) e 2 (località)
    col_precision = 'geo_precision' if 'geo_precision' in df_a.columns else 'ACLED_GeoPrecision'
    df_a_filtered = df_a[df_a[col_precision].isin([1, 2])].copy()
    
    print(f"Eventi ACLED filtrati (Precision 1 & 2): {len(df_a_filtered)}")

    # Pulizia coordinate
    df_u['u_coords'] = df_u['coordinates'].apply(parse_coords)
    df_d['d_coords'] = df_d['Geo location'].apply(parse_coords)
    df_a_filtered['a_coords'] = list(zip(df_a_filtered['ACLED_Lat'], df_a_filtered['ACLED_Lon']))

    results = []

    for _, dam in df_d.dropna(subset=['d_coords']).iterrows():
        damage_date = str(dam['Date of damage (first reported)']).strip()
        
        for _, une in df_u.dropna(subset=['u_coords']).iterrows():
            dist_u_d = geodesic(dam['d_coords'], une['u_coords']).meters
            
            # Se il danno è avvenuto entro 2km da un sito UNESCO
            if dist_u_d <= 2000:
                # Cerchiamo attacchi ACLED nella stessa data
                daily_attacks = df_a_filtered[df_a_filtered['ACLED_Date'] == damage_date]
                
                for _, att in daily_attacks.iterrows():
                    # Distanza tra attacco ACLED e sito UNESCO
                    dist_attack_unesco = geodesic(att['a_coords'], une['u_coords']).meters
                    
                    if dist_attack_unesco <= 3000: # Raggio leggermente più ampio per precisione 2
                        results.append({
                            'UNESCO_Site': une['name'],
                            'Damaged_Site_Nearby': dam['Title of the damage site in English'],
                            'Event_Date': damage_date,
                            'ACLED_Event_Type': att['ACLED_SubEvent'],
                            'Dist_UNESCO_to_Damage_m': round(dist_u_d, 1),
                            'Geo_Precision': att[col_precision],
                            'ACLED_Notes': att['ACLED_Notes']
                        })
                        break

    report_df = pd.DataFrame(results)
    if not report_df.empty:
        output_file = 'analisi_forense_flessibile.csv'
        report_df.to_csv(output_file, sep=';', index=False, encoding='utf-8-sig')
        print(f"\nMatch trovati! Report salvato in: {output_file}")
        print(report_df[['UNESCO_Site', 'Event_Date', 'Dist_UNESCO_to_Damage_m']].head())
    else:
        print("\nNessun match trovato nemmeno con precisione 2. Verifica il formato delle date nei CSV.")

if __name__ == "__main__":
    run_flexible_analysis()