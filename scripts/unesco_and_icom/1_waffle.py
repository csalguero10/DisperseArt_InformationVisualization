import pandas as pd
import altair as alt
import json

URL_UNESCO_PROTETTI = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/2_ukraine_list_qid_coord.csv"
URL_UNESCO_DANNEGGIATI = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/processed_data/cultural_damage_l4R_wiki_enriched.csv"

GRID_COLUMNS = 21
OUTPUT_FILE = "DisperseArt_InformationVisualization/scripts/unesco_and_icom/viz/waffle.html"

MACRO_COLORS = {
    "UNESCO protection": "#F1C40F",        # Giallo
    "Unprotected damaged sites": "#2471A3" # Blu
}
MACRO_ORDER = list(MACRO_COLORS.keys())

DAMAGE_CATEGORY_LABELS = [
    "Religious Heritage",
    "Museums & Arts",
    "Libraries & Archives",
    "Other Historic Sites",
]


def map_damage_category(row):
    text = f"{str(row.get('name', ''))} {str(row.get('instance_of_label', ''))} {str(row.get('Title of the damage site in English', ''))}".lower()
    if any(k in text for k in ["religious", "church", "cathedral", "monastery", "собор"]):
        return "Religious Heritage"
    if any(k in text for k in ["museum", "музей", "gallery"]):
        return "Museums & Arts"
    if any(k in text for k in ["library", "archive"]):
        return "Libraries & Archives"
    return "Other Historic Sites"

def main():
    print("Building the Protection Gap Grid...")

    df_p = pd.read_csv(URL_UNESCO_PROTETTI, sep=';')
    df_p["category"] = df_p["category"].str.strip()
    df_d = pd.read_csv(URL_UNESCO_DANNEGGIATI)

    waffle_elements = []

    # a. unesco protected -whlist + tentative
    wh_sites = df_p[df_p["category"] == "World Heritage List"]
    tent_sites = df_p[df_p["category"] == "Tentative List"]

    for _, row in wh_sites.iterrows():
        waffle_elements.append({
            "name": row["name"],
            "macro": "UNESCO protection",
            "damage_cat": "",
            "status": "Protected",
        })

    for _, row in tent_sites.iterrows():
        waffle_elements.append({
            "name": row["name"],
            "macro": "UNESCO protection",
            "damage_cat": "",
            "status": "Protected (Tentative)",
        })

    # b. unprotected damaged sites
    df_d["mapped_cat"] = df_d.apply(map_damage_category, axis=1)
    for _, row in df_d.iterrows():
        name = row.get("name") or row.get("Title of the damage site in English") or "Unnamed Site"
        waffle_elements.append({
            "name": name,
            "macro": "Unprotected damaged sites",
            "damage_cat": row["mapped_cat"],
            "status": "Damaged",
        })

    df_w = pd.DataFrame(waffle_elements)

    # gialli in alto
    df_w["macro"] = pd.Categorical(df_w["macro"], categories=MACRO_ORDER, ordered=True)
    df_w["damage_cat"] = pd.Categorical(df_w["damage_cat"], categories=DAMAGE_CATEGORY_LABELS, ordered=True)

    df_w = df_w.sort_values(["macro", "damage_cat"]).reset_index(drop=True)

    # Grid mapping (fisso, top-->bottom)
    df_w["idx"] = range(len(df_w))
    df_w["x"] = df_w["idx"] % GRID_COLUMNS
    df_w["y"] = df_w["idx"] // GRID_COLUMNS
    # niente inversione: prima riga in alto, ultima in basso

    # --- ALTAIR CHART ---

    chart_width = 550
    num_rows = df_w["y"].max() + 1
    chart_height = (chart_width / GRID_COLUMNS) * num_rows

    # Parametro per evidenziare un tipo di bene danneggiato !!! <-- 
    damage_filter = alt.param(
        name="damage_filter",
        bind=alt.binding_radio(
            options=["None"] + DAMAGE_CATEGORY_LABELS,
            name="Highlight damaged type: "
        ),
        value="None"
    )

    base = (
        alt.Chart(df_w)
        .add_params(damage_filter)
        .transform_calculate(
            opacity_expr=(
                "datum.status == 'Padding' ? 0 : "
                "(damage_filter == 'None' || datum.status != 'Damaged' || datum.damage_cat == damage_filter "
                "? 1 : 0.25)"
            )
        )
    )

    common_encodings = dict(
        x=alt.X("x:O", axis=None),
        y=alt.Y("y:O", axis=None),
        opacity=alt.Opacity("opacity_expr:Q", scale=None),
        color=alt.condition(
            "datum.status == 'Padding'",
            alt.value("white"),
            alt.Color(
                "macro:N",
                scale=alt.Scale(
                    domain=MACRO_ORDER,
                    range=list(MACRO_COLORS.values())
                ),
                legend=None
            )
        ),
        stroke=alt.condition(
            "(damage_filter != 'None') && (datum.damage_cat == damage_filter) && (datum.status == 'Damaged')",
            alt.value("black"),
            alt.value(None)
        ),
        strokeWidth=alt.condition(
            "(damage_filter != 'None') && (datum.damage_cat == damage_filter) && (datum.status == 'Damaged')",
            alt.value(1),
            alt.value(0)
        ),
    )

    damaged_layer = (
        base
        .transform_filter("datum.status == 'Damaged'")
        .mark_square(size=380, stroke=None)
        .encode(
            **common_encodings,
            tooltip=[
                alt.Tooltip("name:N", title="Site Name"),
                alt.Tooltip("macro:N", title="Protection"),
                alt.Tooltip("damage_cat:N", title="Type of damaged site"),
                alt.Tooltip("status:N", title="Detail"),
            ]
        )
    )

    protected_layer = (
        base
        .transform_filter("(datum.status != 'Damaged') && (datum.status != 'Padding')")
        .mark_square(size=380, stroke=None)
        .encode(
            **common_encodings,
            tooltip=[
                alt.Tooltip("name:N", title="Site Name"),
                alt.Tooltip("macro:N", title="Protection"),
                alt.Tooltip("status:N", title="Detail"),
            ]
        )
    )

    chart = alt.layer(damaged_layer, protected_layer).properties(
        width=chart_width,
        height=chart_height,
        background="white",
    ).configure_view(
        strokeWidth=0
    )

    spec_json = chart.to_json(indent=None)

    html_template = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>The Protection Gap</title>
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
    .vega-bindings {{
      font-size: 12px;
      margin-top: 16px;
      display: inline-block;
    }}
    .vega-bindings label {{
      font-weight: 600;
      margin-right: 6px;
    }}
    .vega-bindings input {{
      margin-left: 8px;
      margin-right: 2px;
    }}
  </style>
</head>

<body>
  <div class="viz-wrapper">

    <h1 style="font-size:26px; font-weight:700; margin-bottom:8px;">
      What UNESCO Lists in <span style="color:#F1C40F;">Yellow</span>, 
      What the War Hits in <span style="color:#2471A3;">Blue</span>
    </h1>

    <p style="font-size:15px; margin-top:0; margin-bottom:25px; color:#444;">
      Each square represents one cultural site. Yellow = UNESCO-listed, Blue = damaged and not protected.
    </p>

    <div id="vis"></div>

  </div>

  <script type="text/javascript">
    var spec = {spec_json};
    vegaEmbed("#vis", spec, {{
      actions: false
    }});
  </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)

    print("✓ Static grid saved with UNESCO on top and filters capitalized as:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
