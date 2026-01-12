import pandas as pd
import altair as alt
import re

URL_RED_LIST = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/raw_data/red_list.csv"
URL_STOLEN = "https://raw.githubusercontent.com/csalguero10/DisperseArt_InformationVisualization/refs/heads/main/data_stolen/5_stolen_objects_final.csv"

OUTPUT_FILE = "DisperseArt_InformationVisualization/scripts/unesco_and_icom/viz/redlist_vs_stolen.html"

# Optional support signal for archaeology ONLY when paired with weak material cues
# (ICOM archaeology is contextual; this is a proxy under data constraints)
ARCHAEOLOGY_DATE_THRESHOLD = 1500  # try 1400 / 1500 / 1600 (lower = stricter)


# -----------------------------
# Helpers
# -----------------------------
def safe_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x).strip()


def text_blob(row, cols) -> str:
    parts = []
    for c in cols:
        if c in row.index and pd.notna(row[c]):
            parts.append(str(row[c]))
    return " ".join(parts).lower()


def extract_year(val):
    """Extract first 3–4 digit year from date_normalized/date fields (supports strings/ranges)."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        try:
            return int(val)
        except Exception:
            return None
    s = str(val)
    m = re.search(r"\b(\d{3,4})\b", s)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


# -----------------------------
# ICOM categories (target)
# -----------------------------
ICOM_CATEGORIES = [
    "PAINTINGS",
    "ARCHAEOLOGY",
    "ICONS",
    "BOOKS / MANUSCRIPTS",
    "RELIGIOUS OBJECTS",
]

# -----------------------------
# Keyword sets (tuned on your counts)
# - ICONS: include EN variants + UA/RU spellings
# - BOOKS: broaden beyond "book/manuscript" to documents/registers/archives etc.
# - RELIGIOUS: liturgical/church cues, including UA/RU stems
# - ARCHAEOLOGY: split STRONG vs WEAK cues to reduce false positives
# -----------------------------
ICON_KW = [
    " icon ", " icons ", "icon,", "icon.", "icon:", "iconostasis",
    "ikon", "ikona", "икона", "ікона", "ікони", "иконы"
]

BOOKS_KW = [
    "manuscript", "manuscripts", "codex",
    "book", "books", "rare book", "old print", "incunable", "incunabula",
    "archive", "archival", "document", "documents", "inventory", "register",
    "bible", "gospel", "psalter", "evangeliary", "liturgical book",
    "map", "atlas", "sheet music", "score",
    # UA/RU stems (very common in descriptions)
    "книга", "книг", "рукопис", "рукоп", "манускрип", "архів", "архив",
    "документ", "реєстр", "реестр"
]

RELIGIOUS_KW = [
    # liturgical objects & church furnishing (EN)
    "chalice", "ciborium", "patena", "paten", "reliquary", "reliquia", "relic",
    "censer", "thurible", "incense", "cross", "crucifix", "processional",
    "altar", "liturgical", "liturgy", "monstrance", "tabernacle",
    "church", "cathedral", "monastery", "abbey", "chapel", "parish",
    "priest", "bishop", "saint", "sacred", "devotional",
    # UA/RU stems (keep them short on purpose to catch inflections)
    "церк", "храм", "собор", "каплиц", "каплич", "монаст", "лавр",
    "крест", "хрест", "розп'ят", "распят",
    "свят", "бог", "євангел", "евангел", "літург", "литург",
    "іконостас", "иконостас"  # note: icons handled earlier; still OK here (excluded by priority)
]

PAINTING_KW = [
    "painting", "paintings", "oil on", "canvas", "panel", "watercolor", "watercolour",
    "икона на доске", "полотно", "живопис"  # optional: can overlap; icons handled first
]

ARCH_CONTEXT_KW = [
    "excavation", "excavated", "archaeological", "archaeology", "findspot",
    "site", "settlement", "burial", "tumulus", "kurgan", "hoard", "stratum",
    # UA/RU stems
    "розкоп", "раскоп", "археолог", "похован", "знахід", "находк", "скарб"
]

ARCH_OBJECT_STRONG = [
    "coin", "coins", "amphora", "fibula", "arrowhead", "spearhead",
    "stela", "stele", "inscription", "seal", "mosaic", "hoard"
]

ARCH_OBJECT_WEAK = [
    "pottery", "ceramic", "vessel", "figurine",
    "bronze", "iron", "stone", "ancient", "antiquity", "artifact", "artefact"
]


def normalize_redlist(cat: str) -> str:
    """Red List → our 5 bins."""
    cat_l = safe_str(cat).lower()

    if "painting" in cat_l:
        return "PAINTINGS"
    if "archaeolog" in cat_l:
        return "ARCHAEOLOGY"
    if "icon" in cat_l:
        return "ICONS"
    if "manuscript" in cat_l or "book" in cat_l:
        return "BOOKS / MANUSCRIPTS"
    if "religious" in cat_l:
        return "RELIGIOUS OBJECTS"

    return "OTHER / MISC"


def map_stolen_to_icom(row) -> str:
    """
    Map stolen objects → ICOM categories using proxies.
    Priority:
      1) ICONS
      2) BOOKS / MANUSCRIPTS
      3) ARCHAEOLOGY (context/material + optional early date support)
      4) RELIGIOUS OBJECTS (liturgical/church cues; excluding icons/books already)
      5) PAINTINGS
      6) OTHER / MISC
    """

    # columns we try to read if present
    cols_for_text = []
    for c in [
        "category", "title", "name", "description",
        "object_type", "type", "materials", "technique", "notes"
    ]:
        if c in row.index:
            cols_for_text.append(c)

    blob = text_blob(row, cols_for_text)
    cat_raw = safe_str(row.get("category", "")).lower()

    # --- 1) ICONS ---
    # use blob + category hint
    if ("icon" in cat_raw) or any(k in blob for k in ICON_KW):
        return "ICONS"

    # --- 2) BOOKS / MANUSCRIPTS ---
    if ("manuscript" in cat_raw) or ("book" in cat_raw) or any(k in blob for k in BOOKS_KW):
        return "BOOKS / MANUSCRIPTS"

    # --- 3) ARCHAEOLOGY (ICOM proxy) ---
    context_hit = any(k in blob for k in ARCH_CONTEXT_KW)
    strong_hit = any(k in blob for k in ARCH_OBJECT_STRONG)
    weak_hit = any(k in blob for k in ARCH_OBJECT_WEAK)

    # Optional date support (only helps when weak_hit is true)
    year = None
    if "date_normalized" in row.index:
        year = extract_year(row.get("date_normalized"))
    elif "date" in row.index:
        year = extract_year(row.get("date"))

    early_date_hit = (year is not None and year <= ARCHAEOLOGY_DATE_THRESHOLD)

    # archaeology if:
    # - strong contextual cue
    # - OR strong object cue
    # - OR weak object cue + early date support
    if context_hit or strong_hit or (weak_hit and early_date_hit):
        return "ARCHAEOLOGY"

    # --- 4) RELIGIOUS OBJECTS (liturgical/church cues, excluding icons/books already handled) ---
    if ("religious" in cat_raw) or any(k in blob for k in RELIGIOUS_KW):
        return "RELIGIOUS OBJECTS"

    # --- 5) PAINTINGS ---
    if ("painting" in cat_raw) or any(k in blob for k in PAINTING_KW):
        return "PAINTINGS"

    return "OTHER / MISC"


def generate_chart():
    # --- LOAD ---
    df_r = pd.read_csv(URL_RED_LIST)
    df_s = pd.read_csv(URL_STOLEN)

    # --- MAP / NORMALIZE ---
    df_r["cat_clean"] = df_r["category"].apply(normalize_redlist)
    df_s["cat_clean"] = df_s.apply(map_stolen_to_icom, axis=1)

    # --- COUNTS / SHARES ---
    red_counts = df_r["cat_clean"].value_counts().to_dict()
    stolen_counts = df_s["cat_clean"].value_counts().to_dict()

    red_total = sum(red_counts.values()) or 1
    stolen_total = sum(stolen_counts.values()) or 1

    rows = []
    for cat in ICOM_CATEGORIES:
        r_share = red_counts.get(cat, 0) / red_total
        s_share = stolen_counts.get(cat, 0) / stolen_total

        rows.append({
            "Category": cat,
            "Share": r_share,
            "Share_Label": f"{r_share:.1%}",
            "Source": "Red List (ICOM risk categories)",
        })
        rows.append({
            "Category": cat,
            "Share": s_share,
            "Share_Label": f"{s_share:.1%}",
            "Source": "Stolen objects (mapped to ICOM)",
        })

    df_final = pd.DataFrame(rows)

    # --- CHART ---
    base = alt.Chart(df_final).encode(
        x=alt.X(
            "Category:N",
            title=None,
            sort=ICOM_CATEGORIES,
            axis=alt.Axis(labelAngle=0, labelPadding=10, labelColor="#333"),
        ),
        xOffset="Source:N",
        color=alt.Color(
            "Source:N",
            scale=alt.Scale(
                domain=["Red List (ICOM risk categories)", "Stolen objects (mapped to ICOM)"],
                range=["#C0392B", "#7F8C8D"],
            ),
            legend=alt.Legend(
                orient="top-right", direction="vertical", title=None, labelFontSize=12
            ),
        ),
    )

    max_share = float(df_final["Share"].max()) if not df_final.empty else 0.5

    bars = base.mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        size=40,
    ).encode(
        y=alt.Y(
            "Share:Q",
            title=None,
            axis=None,
            scale=alt.Scale(domain=[0, max_share * 1.15]),
        ),
        tooltip=[
            alt.Tooltip("Category:N", title="Category"),
            alt.Tooltip("Source:N", title="Source"),
            alt.Tooltip("Share_Label:N", title="Share"),
        ],
    )

    labels = base.mark_text(
        align="center",
        baseline="middle",
        color="white",
        fontWeight="bold",
        fontSize=14,
        dy=-10,
    ).encode(
        y=alt.Y("Share:Q"),
        text=alt.Text("Share_Label:N"),
    )

    chart = (bars + labels).properties(
        width=800,
        height=450,
        background="white",
    ).configure_view(strokeWidth=0)

    # --- EXPORT HTML ---
    spec_json = chart.to_json(indent=None)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Red List vs Stolen – mapped to ICOM categories</title>
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
      line-height: 1.35;
    }}
  </style>
</head>
<body>
  <div class="viz-wrapper">
    <h1>
      What the <span style="color:#C0392B;">Red List</span> anticipates vs what is actually <span style="color:#7F8C8D;">stolen</span>
    </h1>
    <p class="subtitle">
      Stolen objects are mapped to ICOM-style categories using operational rules based on object type and descriptive cues
      (icons, manuscripts/books, liturgical objects, and archaeological-context proxies). Archaeology uses an optional date support
      threshold of ≤ {ARCHAEOLOGY_DATE_THRESHOLD} only when paired with weak material cues.
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

    print("✓ HTML saved:", OUTPUT_FILE)
    print("\nQuick check (counts):")
    print("Red List:", df_r["cat_clean"].value_counts().to_dict())
    print("Stolen (mapped):", df_s["cat_clean"].value_counts().to_dict())

if __name__ == "__main__":
    generate_chart()
