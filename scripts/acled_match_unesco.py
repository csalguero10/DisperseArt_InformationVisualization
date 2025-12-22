import pandas as pd
import numpy as np
from datetime import datetime
import os

# =========================================================
# CONFIG
# =========================================================
PATH_ACLED  = "DisperseArt_InformationVisualization/raw_data/ACLED_Data_2025-11-19.csv"
PATH_UNESCO = "DisperseArt_InformationVisualization/raw_data/unesco_damage_sites.csv"

ACLED_SEP  = ";"
UNESCO_SEP = ","

START_DATE = datetime(2022, 2, 24)

# Finestra temporale: considera solo eventi ACLED entro +/- N giorni dalla data UNESCO
# Se vuoi SOLO match spaziale, metti: TIME_WINDOW_DAYS = None
TIME_WINDOW_DAYS = 30

# Se True: limita agli eventi ACLED con data <= UNESCO_Date (più restrittivo)
ONLY_ACLED_BEFORE_UNESCO = True

# Chunk per ridurre RAM (numero siti UNESCO per batch)
CHUNK_SIZE = 200  # 500 può essere pesante con ACLED grande; 200 è più safe

OUTPUT_CSV = "DisperseArt_InformationVisualization/processed_data/aligned_acled_unesco.csv"

# =========================================================
# UTILS
# =========================================================
def safe_read_csv(path, sep, encoding="utf-8"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File non trovato: {path}")
    df = pd.read_csv(
        path,
        sep=sep,
        encoding=encoding,
        on_bad_lines="skip",
        engine="python"
    )
    df.columns = df.columns.str.strip()
    return df

def clean_str_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().replace({"nan": np.nan, "None": np.nan})

def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorized Haversine in km (broadcasting supported)."""
    R = 6371.0
    lat1 = np.radians(lat1); lon1 = np.radians(lon1)
    lat2 = np.radians(lat2); lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * (np.sin(dlon / 2.0) ** 2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

# =========================================================
# PREP ACLED
# =========================================================
def prepara_acled(df: pd.DataFrame) -> pd.DataFrame:
    required = {"event_date", "latitude", "longitude", "event_type"}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(f"ACLED: colonne mancanti: {missing}")

    df = df.copy()
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df["latitude"]   = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"]  = pd.to_numeric(df["longitude"], errors="coerce")

    df = df.dropna(subset=["event_date", "latitude", "longitude"]).copy()
    df = df[df["event_date"] >= START_DATE].copy()

    event_types = [
        "Explosions/Remote violence",
        "Battles",
        "Violence against civilians",
        "Strategic developments"
    ]
    df = df[df["event_type"].isin(event_types)].copy()

    df = df.rename(columns={
        "event_date": "ACLED_Date",
        "latitude": "ACLED_Lat",
        "longitude": "ACLED_Lon",
        "event_type": "ACLED_EventType",
    })

    for col in ["sub_event_type", "admin1", "fatalities"]:
        if col not in df.columns:
            df[col] = np.nan

    df = df[[
        "ACLED_Date", "ACLED_Lat", "ACLED_Lon", "ACLED_EventType",
        "sub_event_type", "admin1", "fatalities"
    ]].copy()

    return df

# =========================================================
# PREP UNESCO
# =========================================================
def prepara_unesco(df: pd.DataFrame) -> pd.DataFrame:
    col_date   = "Date of damage (first reported)"
    col_geo    = "Geo location"
    col_title  = "Title of the damage site in English"
    col_type   = "Type of damanged site"
    col_region = "Region"

    missing = {col_date, col_geo, col_title} - set(df.columns)
    if missing:
        raise KeyError(f"UNESCO: colonne mancanti: {missing}")

    df = df.copy()

    # rimuove righe "di sezione" tipo "22 sites in the Chernihiv Region"
    first_col = df.columns[0]
    df["_id_num"] = pd.to_numeric(df[first_col], errors="coerce")
    df = df[df["_id_num"].notna()].copy()
    df = df.drop(columns=["_id_num"])

    df[col_geo]  = clean_str_series(df[col_geo])
    df[col_date] = clean_str_series(df[col_date]).str.replace(r",$", "", regex=True)

    df["UNESCO_Date"] = pd.to_datetime(df[col_date], errors="coerce")

    geo_split = df[col_geo].str.split(",", n=1, expand=True)
    if geo_split.shape[1] < 2:
        df["LAT"] = np.nan
        df["LON"] = np.nan
    else:
        df["LAT"] = pd.to_numeric(geo_split[0].str.strip(), errors="coerce")
        df["LON"] = pd.to_numeric(geo_split[1].str.strip(), errors="coerce")

    if col_type not in df.columns:
        df[col_type] = np.nan
    if col_region not in df.columns:
        df[col_region] = np.nan

    df = df.rename(columns={
        col_title: "Site_Title_EN",
        col_type:  "Site_Type",
        col_region:"Region",
    })

    df = df[[
        "Site_Title_EN", "UNESCO_Date", "Site_Type", "Region", "LAT", "LON"
    ]].dropna(subset=["Site_Title_EN", "UNESCO_Date", "LAT", "LON"]).copy()

    return df

# =========================================================
# SPATIO-TEMPORAL MATCH (Nearest ACLED per UNESCO)
# =========================================================
def match_nearest_acled(df_unesco, df_acled):
    if df_unesco.empty or df_acled.empty:
        return pd.DataFrame()

    acled_lat  = df_acled["ACLED_Lat"].to_numpy()
    acled_lon  = df_acled["ACLED_Lon"].to_numpy()
    acled_date = df_acled["ACLED_Date"].to_numpy(dtype="datetime64[ns]")

    results = []

    for start in range(0, len(df_unesco), CHUNK_SIZE):
        chunk = df_unesco.iloc[start:start+CHUNK_SIZE].copy().reset_index(drop=True)

        u_lat  = chunk["LAT"].to_numpy()
        u_lon  = chunk["LON"].to_numpy()
        u_date = chunk["UNESCO_Date"].to_numpy(dtype="datetime64[ns]")

        # mask temporale
        if TIME_WINDOW_DAYS is not None:
            window = np.timedelta64(TIME_WINDOW_DAYS, "D")
            time_diff = np.abs(acled_date[None, :] - u_date[:, None])
            time_ok = time_diff <= window
        else:
            time_ok = np.ones((len(chunk), len(df_acled)), dtype=bool)

        if ONLY_ACLED_BEFORE_UNESCO:
            time_ok = time_ok & (acled_date[None, :] <= u_date[:, None])

        # quante opzioni ACLED restano per ogni sito UNESCO
        candidate_count = time_ok.sum(axis=1)

        # distanze
        dist_km = haversine_km(
            u_lat[:, None], u_lon[:, None],
            acled_lat[None, :], acled_lon[None, :]
        )

        # blocca fuori finestra temporale
        dist_km = np.where(time_ok, dist_km, np.inf)

        idx_min = np.argmin(dist_km, axis=1)
        min_dist = dist_km[np.arange(len(chunk)), idx_min]

        matched_acled = df_acled.iloc[idx_min].reset_index(drop=True)
        out = pd.concat([chunk, matched_acled], axis=1)

        out["Min_Distance_KM"] = min_dist
        out["Candidate_Count"] = candidate_count
        out["Has_Match"] = np.isfinite(out["Min_Distance_KM"])

        # delay (solo se match valido)
        out["Days_Delay"] = (out["UNESCO_Date"] - out["ACLED_Date"]).dt.days
        out.loc[~out["Has_Match"], "Days_Delay"] = np.nan

        # se non c’è match valido, pulisci i campi ACLED e la distanza
        cols_acled = ["ACLED_Date","ACLED_Lat","ACLED_Lon","ACLED_EventType","sub_event_type","admin1","fatalities"]
        out.loc[~out["Has_Match"], cols_acled] = np.nan
        out.loc[~out["Has_Match"], "Min_Distance_KM"] = np.nan

        results.append(out)

    return pd.concat(results, ignore_index=True)

# =========================================================
# MAIN
# =========================================================
def main():
    df_acled_raw  = safe_read_csv(PATH_ACLED, ACLED_SEP)
    df_unesco_raw = safe_read_csv(PATH_UNESCO, UNESCO_SEP)

    print(f"Caricato ACLED grezzo:  {len(df_acled_raw)} righe")
    print(f"Caricato UNESCO grezzo: {len(df_unesco_raw)} righe")

    df_acled  = prepara_acled(df_acled_raw)
    df_unesco = prepara_unesco(df_unesco_raw)

    print("\n--- Stato dati puliti ---")
    print(f"ACLED pulito:  {len(df_acled)} righe")
    print(f"UNESCO pulito: {len(df_unesco)} righe")

    df_match = match_nearest_acled(df_unesco, df_acled)

    if df_match.empty:
        print("\nATTENZIONE: Nessun match prodotto (DF vuoti o filtri troppo restrittivi).")
        return

    valid = df_match[df_match["Has_Match"]].copy()

    print("\n--- Statistiche ---")
    print(f"Match validi: {len(valid)} / {len(df_match)}")
    if len(valid) > 0:
        print(f"Distanza media (km): {valid['Min_Distance_KM'].mean():.2f}")
        print(f"Ritardo medio (giorni): {valid['Days_Delay'].mean():.2f}")
        print("\nTop 5 Site_Type (solo match validi):")
        print(valid["Site_Type"].value_counts().head(5).to_markdown())

        preview = valid.sort_values("Min_Distance_KM").head(10)
        cols_preview = [
            "Site_Title_EN","Region","Site_Type",
            "Min_Distance_KM","ACLED_EventType","ACLED_Date","UNESCO_Date","Days_Delay","sub_event_type","Candidate_Count"
        ]
        print("\n--- Top 10 match (distanza minima) ---")
        print(preview[cols_preview].to_markdown(index=False, floatfmt=".2f"))

    # salva
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df_match.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSalvato: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
