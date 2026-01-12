import pandas as pd
import altair as alt
from geopy.distance import geodesic
import re
import math

URL_UNESCO_PROTETTI = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/2_ukraine_list_qid_coord.csv"
URL_UNESCO_DANNEGGIATI = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/cultural_damage_l4R_wiki_enriched.csv"
UNESCO_LOGO_URL = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/WEB_SITE/html/viz/img/UNESCO_logo.svg.png"

OUTPUT_FILE = "DisperseArt_InformationVisualization/scripts/unesco_and_icom/viz/target_tchernihiv.html"
TARGET_SITE = "Historic Centre of Tchernigov, 9th—13th centuries"

UNESCO_SITE_INFO = {
    "name": "Historic Centre of Tchernigov, 9th—13th centuries",
    "location": "Chernihiv, Ukraine",
    "category": "Cultural Heritage",
    "inscription_year": "1989",
    "criteria": "(ii), (iv)",
    "description": (
        "The historic centre of Chernihiv preserves architectural monuments from the 9th to 13th centuries, "
        "including the Transfiguration Cathedral, Boris and Gleb Cathedral, and the Pyatnytska Church, "
        "representing the architectural school of the medieval Kyivan Rus."
    ),
}

# --- FUNZIONI UTILI ---

def parse_coords(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(val))
    if len(nums) >= 2:
        return (float(nums[0]), float(nums[1]))
    return None

def circle_points(radius_m, n_points=120):
    """
    Ritorna un DataFrame di punti per disegnare un cerchio.
    L'aggiunta di 'order' evita le linee verticali di disturbo in Altair.
    """
    pts = []
    for i in range(n_points + 1):
        t = 2 * math.pi * i / n_points
        pts.append({
            "x": radius_m * math.cos(t), 
            "y": radius_m * math.sin(t), 
            "r": radius_m,
            "order": i  # Campo fondamentale per il corretto disegno della linea
        })
    return pd.DataFrame(pts)

def main():
    # Caricamento dati
    df_p = pd.read_csv(URL_UNESCO_PROTETTI, sep=";")
    df_d = pd.read_csv(URL_UNESCO_DANNEGGIATI)

    df_p["p_coords"] = df_p["coordinates"].apply(parse_coords)
    d_coord_col = df_d.columns[df_d.columns.str.contains("Geo|coord", case=False)][0]
    df_d["d_coords"] = df_d[d_coord_col].apply(parse_coords)

    df_p = df_p.dropna(subset=["p_coords"])
    df_d = df_d.dropna(subset=["d_coords"])

    # Calcolo distanze
    intersections = []
    for _, p in df_p.iterrows():
        for _, d in df_d.iterrows():
            dist = geodesic(p["p_coords"], d["d_coords"]).meters
            if dist <= 1000:
                intersections.append({
                    "UNESCO_Protected_Name": p["name"],
                    "UNESCO_Damaged_Name": d.get("name") or d.get("Title of the damage site in English"),
                    "Distance_m": round(dist, 1),
                })

    df_int = pd.DataFrame(intersections)
    df_focus = df_int[df_int["UNESCO_Protected_Name"] == TARGET_SITE].copy()

    if df_focus.empty:
        print("Nessun impatto vicino al sito selezionato.")
        return

    df_focus = df_focus.reset_index(drop=True)
    max_dist = float(df_focus["Distance_m"].max())
    min_dist = float(df_focus["Distance_m"].min())

    # Posizionamento punti impatto
    n = len(df_focus)
    df_focus["angle"] = [2 * math.pi * i / n for i in range(n)]
    df_focus["x"] = df_focus.apply(lambda r: r["Distance_m"] * math.cos(r["angle"]), axis=1)
    df_focus["y"] = df_focus.apply(lambda r: r["Distance_m"] * math.sin(r["angle"]), axis=1)

    # Definizione Anelli (Rings)
    ring_radii = [250, 500, 1000]
    rings_df = pd.concat([circle_points(r) for r in ring_radii], ignore_index=True)

    pad = 120
    domain_max = max(ring_radii) + pad

    # GRAFICO: Cerchi (Corretto con order="order:Q")
    rings = (
        alt.Chart(rings_df)
        .mark_line(stroke="lightgray", strokeDash=[4, 4], strokeWidth=1)
        .encode(
            x=alt.X("x:Q", scale=alt.Scale(domain=[-domain_max, domain_max]), axis=None),
            y=alt.Y("y:Q", scale=alt.Scale(domain=[-domain_max, domain_max]), axis=None),
            detail="r:Q",
            order="order:Q" # <--- QUESTO ELIMINA IL DISTURBO VISIVO
        )
    )

    # Etichette cerchi
    labels_df = pd.DataFrame({
        "x": [-(r + 40) for r in ring_radii],
        "y": [0 for _ in ring_radii],
        "label": ["250 m", "500 m", "1 km"],
    })

    ring_labels = (
        alt.Chart(labels_df)
        .mark_text(align="left", baseline="middle", fontSize=12, color="#666666", fontWeight=500)
        .encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            text="label:N",
        )
    )

    # Logo Centrale
    center_df = pd.DataFrame([{
        "x": 0, "y": 0, "url": UNESCO_LOGO_URL,
        "site_name": UNESCO_SITE_INFO["name"],
        "site_location": UNESCO_SITE_INFO["location"],
        "site_category": UNESCO_SITE_INFO["category"],
        "site_inscription": UNESCO_SITE_INFO["inscription_year"],
        "site_criteria": UNESCO_SITE_INFO["criteria"],
        "site_description": UNESCO_SITE_INFO["description"],
    }])

    center_logo = (
        alt.Chart(center_df)
        .mark_image(width=85, height=85, opacity=1)
        .encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            url="url:N",
            tooltip=[
                alt.Tooltip("site_name:N", title="UNESCO site"),
                alt.Tooltip("site_location:N", title="Location"),
                alt.Tooltip("site_description:N", title="Description"),
            ],
        )
    )

    # Punti Impatto
    impacts = (
        alt.Chart(df_focus)
        .mark_circle(size=150, opacity=0.9, stroke="white", strokeWidth=1)
        .encode(
            x=alt.X("x:Q", axis=None),
            y=alt.Y("y:Q", axis=None),
            color=alt.Color(
                "Distance_m:Q",
                scale=alt.Scale(domain=[0, 1000], range=["#C0392B", "#F4D03F", "#27AE60"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("UNESCO_Damaged_Name:N", title="Damaged site"),
                alt.Tooltip("Distance_m:Q", title="Distance (m)", format=".1f"),
            ],
        )
    )

    # Composizione Finale
    final_chart = (rings + ring_labels + center_logo + impacts).properties(
        width=650,
        height=650,
        background="white",
    ).configure_view(strokeWidth=0)

    # Generazione HTML
    chart_json = final_chart.to_json()
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Tchernihiv Target Map</title>
      <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
      <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
      <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
      <style>
        body {{ margin: 0; padding: 40px 0; background: #ffffff; font-family: sans-serif; }}
        .viz-wrapper {{ max-width: 900px; margin: 0 auto; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="viz-wrapper">
        <h1 style="font-size:24px; color:#2C3E50;">Historic Centre of Tchernihiv: within the range of attacks</h1>
        <p style="color:#666; margin-bottom:20px;">
            Distance of documented damage from the UNESCO site center. Closest: {min_dist}m.
        </p>
        <div id="vis"></div>
      </div>
      <script>
        vegaEmbed('#vis', {chart_json}, {{actions: false}});
      </script>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"File salvato correttamente: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()