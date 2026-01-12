import pandas as pd
import altair as alt
from geopy.distance import geodesic
import re
import os

# --- CONFIGURAZIONE ---
URL_UNESCO_PROTETTI = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/2_ukraine_list_qid_coord.csv"
URL_UNESCO_DANNEGGIATI = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/cultural_damage_l4R_wiki_enriched.csv"

# Percorso di output per la visualizzazione HTML
OUTPUT_FILE = "DisperseArt_InformationVisualization/scripts/unesco_and_icom/viz/unesco_spatial_intersection.html"

# -----------------------------
# Helpers
# -----------------------------
def parse_coords(val):
    if pd.isna(val) or str(val).strip() == "" or str(val).lower() == "nan":
        return None
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
    if len(nums) >= 2:
        return (float(nums[0]), float(nums[1]))
    return None

def categorize_distance(dist_m):
    if dist_m <= 100: return "0 - 100m"
    elif dist_m <= 500: return "100 - 500m"
    return "500 - 1000m"

def main():
    # --- CARICAMENTO DATI ---
    print("Caricamento dati...")
    df_p = pd.read_csv(URL_UNESCO_PROTETTI, sep=";")
    df_d = pd.read_csv(URL_UNESCO_DANNEGGIATI)

    # Pulizia coordinate protetti
    df_p["p_coords"] = df_p["coordinates"].apply(parse_coords)
    df_p = df_p.dropna(subset=["p_coords"]).reset_index(drop=True)

    # Pulizia coordinate danneggiati
    df_d['latitude'] = pd.to_numeric(df_d['latitude'], errors='coerce')
    df_d['longitude'] = pd.to_numeric(df_d['longitude'], errors='coerce')
    df_d = df_d.dropna(subset=['latitude', 'longitude']).reset_index(drop=True)
    df_d["d_coords"] = list(zip(df_d["latitude"], df_d["longitude"]))

    # --- CALCOLO INTERSEZIONI (Logica Originale) ---
    intersections = []
    print(f"Calcolo intersezioni spaziali per {len(df_p)} siti protetti...")

    for _, p in df_p.iterrows():
        for _, d in df_d.iterrows():
            try:
                dist_m = geodesic(p['p_coords'], d['d_coords']).meters
                if dist_m <= 1000:
                    intersections.append({
                        'UNESCO_Protected_Name': p['name'],
                        'UNESCO_Damaged_Name': d.get('name', d.get('Title of the damage site in English')),
                        'Distance_m': round(dist_m, 1),
                        'Category': p.get('category', 'N/A'),
                        'Damage_Date': d.get('Date of damage (first reported)', '2022-2023')
                    })
            except:
                continue

    report_df = pd.DataFrame(intersections)

    if report_df.empty:
        print("Nessuna intersezione trovata.")
        return

    report_df['Fascia_Distanza'] = report_df['Distance_m'].apply(categorize_distance)

    # --- COSTRUZIONE GRAFICO ALTAIR ---
    chart = alt.Chart(report_df).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        size=50
    ).encode(
        x=alt.X('count():Q', title="Numero di Siti Danneggiati"),
        y=alt.Y('Fascia_Distanza:N', 
                sort=["0 - 100m", 
                      "100 - 500m", 
                      "500 - 1000m"],
                title=None),
        color=alt.Color('Fascia_Distanza:N', scale=alt.Scale(
            domain=["0 - 100m", "100 - 500m", "500 - 1000m"],
            range=['#7b241c', '#c0392b', '#e67e22']
        ), legend=None),
        tooltip=[
            alt.Tooltip('UNESCO_Protected_Name:N', title="Sito Protetto"),
            alt.Tooltip('UNESCO_Damaged_Name:N', title="Sito Danneggiato"),
            alt.Tooltip('Distance_m:Q', title="Distanza (m)"),
            alt.Tooltip('Damage_Date:N', title="Data Segnalazione")
        ]
    ).properties(
        width=700,
        height=350,
        background="white"
    ).configure_view(strokeWidth=0).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    )

    # --- ESPORTAZIONE HTML STILIZZATO ---
    spec_json = chart.to_json(indent=None)

    # Creazione cartella se non esiste
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Spatial Intersection: UNESCO vs Damages</title>
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    body {{
      margin: 0;
      padding: 40px 0;
      background: #ffffff;
      font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    }}
    .viz-wrapper {{
      max-width: 900px;
      margin: 0 auto;
      text-align: center;
    }}
    h1 {{
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 8px;
      color: #222;
    }}
    p.subtitle {{
      font-size: 14px;
      margin-top: 0;
      margin-bottom: 22px;
      color: #555;
      max-width: 820px;
      margin-left: auto;
      margin-right: auto;
      line-height: 1.45;
    }}
    .highlight-red {{ color: #c0392b; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="viz-wrapper">
    <h1>
Spatial Intersection: UNESCO Sites Under Threat    </h1>
    <p class="subtitle">
      Analysis of verified damage reports occurring within a 1 km radius of UNESCO sites (World Heritage and Tentative Lists). Extreme proximity highlights cases where damage occurred directly within or in the immediate vicinity of the protected area.
    </p>

    <div id="vis"></div>
  </div>

  <script>
    vegaEmbed("#vis", {spec_json}, {{ actions: false }});
  </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ HTML salvato con successo in: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()