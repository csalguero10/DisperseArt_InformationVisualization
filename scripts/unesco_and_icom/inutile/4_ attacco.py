"""
uso acled e lista unesco per confrontare con le coordinate che tipo ti attacco hanno fatto, ma con geo_precision di 1 o 2 massimo. creo un indice di rischio a seconda del tipo di attacco e della distanza dal sito unesco
"""

import pandas as pd
from geopy.distance import geodesic
import re

def parse_coords(val):
    """Estrae (Lat, Lon) da stringhe di vario formato."""
    if pd.isna(val): return None
    try:
        # Trova tutti i numeri decimali nella stringa
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
        if len(nums) >= 2:
            return (float(nums[0]), float(nums[1]))
    except:
        return None

# Pesi basati sul potenziale distruttivo e l'imprecisione dell'arma
ATTACK_WEIGHTS = {
    'Air/drone strike': 10,
    'Shelling/artillery/missile attack': 8,
    'Remote explosive weapon': 7,
    'Armed clash': 4,
    'Attack': 5
}

def analyze_legal_compliance(unesco_path, acled_path):
    print("Caricamento dataset...")
    # Leggiamo i file (assicurati che i separatori siano corretti)
    df_u = pd.read_csv(unesco_path, sep=';')
    df_a = pd.read_csv(acled_path, sep=';', low_memory=False)

    # Pulizia coordinate
    df_u['u_coords'] = df_u['coordinates'].apply(parse_coords)
    # ACLED solitamente ha già colonne numeriche, ma per sicurezza le ri-processiamo
    df_a['a_coords'] = df_a.apply(lambda x: parse_coords(f"{x['ACLED_Lat']} {x['ACLED_Lon']}"), axis=1)

    df_u = df_u.dropna(subset=['u_coords'])
    df_a = df_a.dropna(subset=['a_coords'])

    compliance_report = []

    print(f"Analisi di {len(df_u)} siti vs {len(df_a)} eventi ACLED...")

    for _, u in df_u.iterrows():
        for _, a in df_a.iterrows():
            # Calcolo distanza in metri
            dist_m = geodesic(u['u_coords'], a['a_coords']).meters
            
            # Soglia di analisi: 2000 metri (Raggio di potenziale danno collaterale)
            if dist_m <= 2000:
                sub_event = a['ACLED_SubEvent']
                danger_score = ATTACK_WEIGHTS.get(sub_event, 1)
                
                # Definizione del sospetto di violazione:
                # Se l'arma è imprecisa (Shelling) ed è entro 500m, il rischio è 'Critical'
                violation_risk = "Low"
                if dist_m < 500 and danger_score >= 8:
                    violation_risk = "Critical (Indiscriminate Attack)"
                elif dist_m < 1000:
                    violation_risk = "High (Negligence Risk)"
                elif dist_m < 2000:
                    violation_risk = "Moderate (Proximity Warning)"

                compliance_report.append({
                    'UNESCO_Site': u['name'],
                    'UNESCO_Category': u['category'],
                    'Event_Date': a['ACLED_Date'],
                    'Attack_Type': sub_event,
                    'Distance_m': round(dist_m, 1),
                    'Danger_Score': danger_score,
                    'Violation_Risk_Level': violation_risk,
                    'ACLED_Notes': a['ACLED_Notes']
                })

    return pd.DataFrame(compliance_report)

# --- ESECUZIONE ---
# Aggiorna i path con quelli corretti del tuo MacBook
path_unesco = 'DisperseArt_InformationVisualization/csv/ukraine_list_qid_coord.csv'
path_acled = 'DisperseArt_InformationVisualization/processed_data/acled_clean.csv'

report = analyze_legal_compliance(path_unesco, path_acled)

if not report.empty:
    output_path = 'analisi_violazioni_internazionali.csv'
    report.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
    print(f"File generato con successo: {output_path}")
    print(report[['UNESCO_Site', 'Attack_Type', 'Distance_m', 'Violation_Risk_Level']].head())
else:
    print("Nessun evento trovato entro il raggio di 2km.")

