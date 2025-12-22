import pandas as pd
from datetime import datetime
import os

# --- CONFIG ---
PATH_ACLED = "DisperseArt_InformationVisualization/raw_data/ACLED_Data_2025-11-19.csv"
OUT_PATH   = "DisperseArt_InformationVisualization/processed_data/acled_clean.csv"
START_DATE = datetime(2022, 2, 24)

EVENT_TYPES_INCLUDE = [
    "Explosions/Remote violence",
    "Battles",
    "Violence against civilians",
    "Strategic developments",
]

# --- LOAD ---
df_acled = pd.read_csv(
    PATH_ACLED,
    sep=";",
    encoding="utf-8",
    on_bad_lines="skip",
    engine="python"
)

# FIX minimo: nomi colonne
df_acled.columns = df_acled.columns.str.strip()

# Tipi necessari
df_acled["event_date"] = pd.to_datetime(df_acled["event_date"], errors="coerce")
df_acled["latitude"]   = pd.to_numeric(df_acled["latitude"], errors="coerce")
df_acled["longitude"]  = pd.to_numeric(df_acled["longitude"], errors="coerce")

# Filtri minimi
df_acled = df_acled[df_acled["event_date"] >= START_DATE]
df_acled = df_acled[df_acled["event_type"].isin(EVENT_TYPES_INCLUDE)]
df_acled = df_acled.dropna(subset=["event_date", "latitude", "longitude"]).copy()

# Rinomina (per uso futuro)
df_acled = df_acled.rename(columns={
    "event_date": "ACLED_Date",
    "latitude": "ACLED_Lat",
    "longitude": "ACLED_Lon",
    "event_type": "ACLED_EventType",
})

# --- OUTPUT ---
os.makedirs("processed_data", exist_ok=True)
df_acled.to_csv(OUT_PATH, index=False)

print("ACLED cleaned shape:", df_acled.shape)
print("Saved to:", OUT_PATH)

df_acled.head(3)
