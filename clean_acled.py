import pandas as pd
import numpy as np
from datetime import datetime
from scipy.spatial.distance import cdist
from math import radians, sin, cos, sqrt, atan2
import os

# =========================================================
# 0. CONFIGURAZIONE E CARICAMENTO DEI DATI
# =========================================================

# --- PATH E SEPARATORI CORRETTI ---
path_acled = 'raw_data/ACLED Data_2025-11-19.csv' 
path_unesco = 'raw_data/unesco.csv' 
ACLED_SEPARATOR = ';'
UNESCO_SEPARATOR = ',' 

# --- CARICAMENTO DEI FILE ---
try:
    # 1. Caricamento ACLED con il separatore PUNTO E VIRGOLA
    df_acled_grezzo = pd.read_csv(
        path_acled, 
        sep=ACLED_SEPARATOR, 
        encoding='utf-8',
        on_bad_lines='skip', 
        engine='python'      
    )
    # FIX CHIAVE: Pulisci gli spazi bianchi dai nomi delle colonne ACLED
    df_acled_grezzo.columns = df_acled_grezzo.columns.str.strip()
    print(f"Caricato ACLED: {len(df_acled_grezzo)} righe.")

    # 2. Caricamento UNESCO con il separatore VIRGOLA
    df_unesco_grezzo = pd.read_csv(
        path_unesco, 
        sep=UNESCO_SEPARATOR, 
        encoding='utf-8',
        on_bad_lines='skip', 
        engine='python'
    )
    # FIX CHIAVE: Pulisci gli spazi bianchi dai nomi delle colonne UNESCO
    df_unesco_grezzo.columns = df_unesco_grezzo.columns.str.strip()
    print(f"Caricato UNESCO: {len(df_unesco_grezzo)} righe.")

except FileNotFoundError as e:
    print(f"ERRORE: File non trovato. Controlla il path: {e}")
    exit() 
except Exception as e:
    print(f"ERRORE durante la lettura del CSV. Dettaglio: {e}")
    exit() 

# =========================================================
# 1. FUNZIONI DI PULIZIA E FILTRAGGIO (PREPARAZIONE)
# Le funzioni di pulizia sono state modificate per assumere che le colonne siano pulite.
# =========================================================

def prepara_acled(acled_df):
    """Filtra e prepara il DataFrame ACLED."""
    
    # Conversione date e coordinate
    # 'event_date' dovrebbe ora funzionare grazie allo str.strip()
    acled_df['event_date'] = pd.to_datetime(acled_df['event_date'], errors='coerce')
    acled_df['latitude'] = pd.to_numeric(acled_df['latitude'], errors='coerce')
    acled_df['longitude'] = pd.to_numeric(acled_df['longitude'], errors='coerce')
    
    # Filtro temporale (dal 24 Febbraio 2022)
    start_date = datetime(2022, 2, 24)
    acled_df_filtrato = acled_df[acled_df['event_date'] >= start_date].copy()
    
    # Filtro per EVENT TYPE (i tipi più distruttivi/rilevanti)
    event_types_da_includere = [
        'Explosions/Remote violence', 
        'Battles', 
        'Violence against civilians', 
        'Strategic developments'      
    ]
    acled_df_filtrato = acled_df_filtrato[
        acled_df_filtrato['event_type'].isin(event_types_da_includere)
    ]
    
    # Rinomina e seleziona colonne
    acled_df_filtrato.rename(columns={
        'event_date': 'ACLED_Date',
        'latitude': 'ACLED_Lat',
        'longitude': 'ACLED_Lon',
        'event_type': 'ACLED_EventType'
    }, inplace=True)
    
    return acled_df_filtrato[[
        'ACLED_Date', 'ACLED_Lat', 'ACLED_Lon', 'ACLED_EventType', 
        'sub_event_type', 'admin1', 'fatalities'
    ]].dropna(subset=['ACLED_Lat', 'ACLED_Lon'])

def prepara_unesco(unesco_df):
    """Prepara il DataFrame UNESCO (siti danneggiati)."""
    
    # Conversione data del danno
    unesco_df['Date of damage (first reported)'] = pd.to_datetime(
        unesco_df['Date of damage (first reported)'], errors='coerce'
    )
    
    # Estrazione e conversione delle coordinate dalla colonna 'Geo location'
    if 'Geo location' in unesco_df.columns:
        unesco_df[['LAT', 'LON']] = unesco_df['Geo location'].str.split(',', expand=True) # Separatore corretto
        # Pulisci gli spazi dopo lo split
        unesco_df['LAT'] = unesco_df['LAT'].str.strip() 
        unesco_df['LON'] = unesco_df['LON'].str.strip()
        
        unesco_df['LAT'] = pd.to_numeric(unesco_df['LAT'], errors='coerce')
        unesco_df['LON'] = pd.to_numeric(unesco_df['LON'], errors='coerce')
    else:
        # Se 'Geo location' non esiste, interrompi
        print("\nERRORE: La colonna 'Geo location' non è stata trovata nel CSV UNESCO.")
        return unesco_df[[]] # Ritorna un DF vuoto per evitare KeyError

    
    # Rinomina e seleziona colonne
    unesco_df_filtrato = unesco_df.rename(columns={
        'Date of damage (first reported)': 'UNESCO_Date',
        'Type of damanged site': 'Site_Type',
        'Region': 'Region'
    })
    
    return unesco_df_filtrato[[
        'Title of the damage site in English', 'UNESCO_Date', 'Site_Type', 
        'Region', 'LAT', 'LON'
    ]].dropna(subset=['LAT', 'LON', 'UNESCO_Date'])

# --- APPLICAZIONE DELLE FUNZIONI DI PULIZIA ---
df_acled_pulito = prepara_acled(df_acled_grezzo.copy())
df_unesco_pulito = prepara_unesco(df_unesco_grezzo.copy())

print("\n--- Stato dei dati puliti ---")
print(f"ACLED Eventi filtrati: {len(df_acled_pulito)}")
print(f"UNESCO Siti danneggiati: {len(df_unesco_pulito)}")

# =========================================================
# 2. FUNZIONE HAVERSINE (CALCOLO PRECISO DELLA DISTANZA)
# =========================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcola la distanza Haversine tra due punti in chilometri (km)."""
    R = 6371  # Raggio terrestre in km
    
    # Converti gradi in radianti
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        np.radians, [lat1, lon1, lat2, lon2]
    )
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    return R * c

# =========================================================
# 3. ESECUZIONE DELLA QUERY B: TROVA DISTANZA E RITARDO MINIMI
# =========================================================

def esegui_query_b(df_unesco, df_acled):
    """
    Esegue lo spatial-temporal join: per ogni sito UNESCO, trova l'evento ACLED
    più vicino (minima distanza) e calcola il ritardo temporale.
    """
    
    # Controllo per DF vuoti
    if df_unesco.empty or df_acled.empty:
        print("ATTENZIONE: Uno o entrambi i DataFrames sono vuoti dopo la pulizia. Impossibile eseguire la Query B.")
        return pd.DataFrame()

    # Prepara le matrici di coordinate
    coords_unesco = df_unesco[['LAT', 'LON']].values
    coords_acled = df_acled[['ACLED_Lat', 'ACLED_Lon']].values
    
    # 1. Calcola la matrice delle distanze Euclidee (proxy veloce per trovare l'indice minimo)
    dist_matrix = cdist(coords_unesco, coords_acled, metric='euclidean')
    
    # Troviamo l'indice dell'evento ACLED più vicino per ogni sito UNESCO
    min_dist_indices = dist_matrix.argmin(axis=1)
    
    # 2. Estraiamo i dati dell'evento ACLED più vicino
    # Usiamo 'iloc' per selezionare le righe ACLED corrispondenti agli indici minimi
    closest_acled_events = df_acled.iloc[min_dist_indices].reset_index(drop=True)
    
    # 3. Uniamo i risultati
    df_risultato = pd.concat([df_unesco.reset_index(drop=True), closest_acled_events], axis=1)
    
    # 4. Calcoliamo la Distanza Haversine PRECISA (Min_Distance_KM)
    df_risultato['Min_Distance_KM'] = haversine_distance(
        df_risultato['LAT'], df_risultato['LON'], 
        df_risultato['ACLED_Lat'], df_risultato['ACLED_Lon']
    )
    
    # 5. Calcoliamo il Ritardo Temporale (Days_Delay)
    # Misura in giorni: UNESCO_Date (danno/segnalazione) - ACLED_Date (evento di conflitto)
    df_risultato['Days_Delay'] = (df_risultato['UNESCO_Date'] - df_risultato['ACLED_Date']).dt.days
    
    return df_risultato

# --- ESEGUI LA QUERY B ---
df_risultato_query = esegui_query_b(df_unesco_pulito, df_acled_pulito)


# =========================================================
# 4. OUTPUT E ANALISI INIZIALE
# =========================================================

# Controllo per DF vuoti dopo la Query B
if df_risultato_query.empty:
    print("\nImpossibile generare l'analisi statistica: Nessun dato valido dopo l'allineamento.")
    exit()

# Seleziona le colonne finali per l'analisi RQ1 e RQ2
risultato_finale = df_risultato_query[[
    'Title of the damage site in English', 'Region', 'Site_Type',
    'Min_Distance_KM', 'ACLED_EventType', 'ACLED_Date', 'UNESCO_Date', 
    'Days_Delay', 'sub_event_type'
]]

print("\n--- Risultati della Query B (Allineamento Spaziale-Temporale) ---")
print(risultato_finale.sort_values(by='Min_Distance_KM').head(10).to_markdown(index=False, floatfmt=".2f"))

# Analisi Aggiuntive per RQ1 e RQ2:

print("\n--- Analisi Statistica ---")

# RQ1: Distanza media dal conflitto
media_distanza = risultato_finale['Min_Distance_KM'].mean()
print(f"Distanza media di un sito danneggiato dall'evento ACLED più vicino: {media_distanza:.2f} km")

# RQ2: Ritardo medio nella segnalazione
media_ritardo = risultato_finale['Days_Delay'].mean()
print(f"Ritardo medio (ACLED Evento -> UNESCO Segnalazione): {media_ritardo:.2f} giorni")

# Distribuzione per Tipo di Sito (RQ1)
print("\nDistribuzione del Danno per Tipologia (Query A):")
tipi_sito_colpiti = df_risultato_query['Site_Type'].value_counts().head(5).to_markdown()
print(tipi_sito_colpiti)

# Salvataggio del risultato finale per la visualizzazione
output_path = 'risultato_allineamento_spaziale_temporale.csv'
df_risultato_query.to_csv(output_path, index=False)
print(f"\n Risultato completo salvato in: {output_path}")