import pandas as pd
import os

# --- 1. CONFIGURAZIONE URL ---
URL_UNESCO_LIST = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/2_ukraine_list_qid_coord.csv"
URL_UNESCO_DAMAGED = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/unesco-damage-sites-qid.csv"
URL_L4R = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/cultural_damage_l4R_wiki_enriched.csv"

def run_matching_analysis():
    print("--- Avvio Analisi di Matching ---")
    
    try:
        df_u_list = pd.read_csv(URL_UNESCO_LIST, sep=';', on_bad_lines='skip')
        df_u_damaged = pd.read_csv(URL_UNESCO_DAMAGED, sep=None, engine='python', on_bad_lines='skip')
        df_l4r = pd.read_csv(URL_L4R, sep=None, engine='python', on_bad_lines='skip')
        print("Dati caricati correttamente.")
    except Exception as e:
        print(f"Errore nel caricamento: {e}")
        return

    def get_actual_column(df, target):
        for c in df.columns:
            if c.strip().lower() == target.lower():
                return c
        return None

    def extract_qids(df, column):
        col = get_actual_column(df, column)
        if not col: return set()
        return set(df[col].dropna().astype(str).str.strip().unique())

    # Identifichiamo le colonne QID nei tre file
    col_list = get_actual_column(df_u_list, 'QID')
    col_dmg = get_actual_column(df_u_damaged, 'qid')
    col_l4r = get_actual_column(df_l4r, 'wikidata_id')

    qids_world_heritage = extract_qids(df_u_list, 'QID')
    qids_unesco_dmg = extract_qids(df_u_damaged, 'qid')
    qids_l4r_dmg = extract_qids(df_l4r, 'wikidata_id')

    matches_unesco = qids_world_heritage.intersection(qids_unesco_dmg)
    matches_l4r = qids_world_heritage.intersection(qids_l4r_dmg)

    print(f"\nRisultati: {len(matches_unesco)} match UNESCO, {len(matches_l4r)} match L4R.")

    if matches_unesco:
        # Filtriamo il dataset dei danni per esportare solo le righe che hanno fatto match
        df_output_unesco = df_u_damaged[df_u_damaged[col_dmg].isin(matches_unesco)]
        df_output_unesco.to_csv("matches_unesco_world_heritage.csv", index=False, sep=';')
        print(f"File creato: matches_unesco_world_heritage.csv ({len(matches_unesco)} siti)")
    else:
        print(" Nessun match UNESCO trovato, nessun CSV generato.")

    if matches_l4r:
        df_output_l4r = df_l4r[df_l4r[col_l4r].isin(matches_l4r)]
        df_output_l4r.to_csv("matches_l4r_world_heritage.csv", index=False, sep=';')
        print(f"File creato: matches_l4r_world_heritage.csv ({len(matches_l4r)} siti)")
    else:
        print("Nessun match L4R trovato, nessun CSV generato.")

    print("\n--- Analisi terminata ---")

if __name__ == "__main__":
    run_matching_analysis()