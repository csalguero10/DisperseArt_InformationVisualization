"""
GENERATE ALL HTML VISUALIZATIONS
Creates standalone HTML files for all Plotly visualizations
Ready for web deployment
Author: Cata
Date: January 2026
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

print("="*70)
print("GENERATING HTML VISUALIZATIONS FOR WEB")
print("="*70)

# Create output directory
os.makedirs('html_visualizations', exist_ok=True)

# =============================================================================
# HERMITAGE MUSEUM VISUALIZATIONS
# =============================================================================

print("\n📊 HERMITAGE MUSEUM VISUALIZATIONS")
print("-"*70)

# Load Hermitage data
df_hermitage = pd.read_csv('data_hermitage/5_FINAL_hermitage_ukraine.csv')
print(f"✓ Loaded {len(df_hermitage):,} Hermitage objects")

# Extract acquisition year
def extract_year_from_acquisition(value):
    if pd.isna(value):
        return np.nan
    try:
        return int(float(value))
    except:
        pass
    try:
        import re
        match = re.search(r'(\d{4})', str(value))
        if match:
            return int(match.group(1))
    except:
        pass
    return np.nan

df_hermitage['acquisition_year_only'] = df_hermitage['acquisition_year'].apply(extract_year_from_acquisition)

# --- 1. Material Categories Bar Chart ---
print("\n1. Material Categories Bar Chart...")
material_counts = df_hermitage['category'].value_counts().head(12)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=material_counts.index,
    x=material_counts.values,
    orientation='h',
    marker=dict(color=material_counts.values, colorscale='YlOrBr',
                line=dict(color='#4A2511', width=1.5)),
    text=material_counts.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Ukrainian Objects by Material Category',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=600,
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/hermitage_material_categories.html')
print("   ✓ hermitage_material_categories.html")

# --- 2. Material Categories Treemap ---
print("2. Material Categories Treemap...")
material_df = df_hermitage['category'].value_counts().reset_index()
material_df.columns = ['Category', 'Count']
material_df = material_df[material_df['Category'].notna()]

fig = px.treemap(
    material_df,
    path=['Category'],
    values='Count',
    title='Material Categories - Hierarchical View',
    color='Count',
    color_continuous_scale='YlOrBr',
    height=600
)

fig.update_traces(textinfo='label+value+percent parent', textfont=dict(size=14, color='white'),
                  marker=dict(line=dict(color='#4A2511', width=2)))
fig.update_layout(title_font=dict(size=20, color='#5C3317', family='Arial Black'),
                  plot_bgcolor='#FFF8F0', paper_bgcolor='#FFF8F0')

fig.write_html('html_visualizations/hermitage_material_treemap.html')
print("   ✓ hermitage_material_treemap.html")

# --- 3. Historical Periods Bar Chart ---
print("3. Historical Periods Bar Chart...")
period_counts = df_hermitage[df_hermitage['period_category'] != 'Unknown Period']['period_category'].value_counts().head(15)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=period_counts.index,
    x=period_counts.values,
    orientation='h',
    marker=dict(color=period_counts.values, colorscale='Reds',
                line=dict(color='#4A2511', width=1.5)),
    text=period_counts.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Ukrainian Objects by Historical Period (Top 15)',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=700,
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/hermitage_periods.html')
print("   ✓ hermitage_periods.html")

# --- 4. Timeline Scatter Plot ---
print("4. Timeline Scatter Plot...")
df_timeline = df_hermitage[df_hermitage['year_for_timeline'].notna()].copy()
df_timeline = df_timeline.sample(min(3000, len(df_timeline)))

fig = px.scatter(
    df_timeline,
    x='year_for_timeline',
    y=np.random.randn(len(df_timeline)),
    color='period_category',
    hover_data=['object_name', 'find_location', 'material'],
    title='Timeline: Ukrainian Objects Through History (40,000 BC - Present)',
    labels={'year_for_timeline': 'Year'},
    height=600,
    color_discrete_sequence=px.colors.sequential.Reds
)

fig.update_traces(marker=dict(size=8, opacity=0.6, line=dict(width=0.5, color='#4A2511')))
fig.update_layout(
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0',
    yaxis=dict(showticklabels=False, title='')
)

fig.write_html('html_visualizations/hermitage_timeline_scatter.html')
print("   ✓ hermitage_timeline_scatter.html")

# --- 5. Geographic Map ---
print("5. Geographic Map (Scatter Mapbox)...")
df_geo = df_hermitage[df_hermitage['latitude'].notna() & df_hermitage['longitude'].notna()].copy()
df_map = df_geo.sample(min(5000, len(df_geo)))

fig = px.scatter_mapbox(
    df_map,
    lat='latitude',
    lon='longitude',
    hover_name='object_name',
    hover_data={'find_location': True, 'category': True, 'period_category': True,
                'latitude': False, 'longitude': False},
    color='category',
    zoom=5.5,
    title='Geographic Distribution of Ukrainian Archaeological Objects',
    height=700,
    color_discrete_sequence=px.colors.sequential.Reds
)

fig.update_layout(
    mapbox_style='open-street-map',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    margin={"r":0,"t":50,"l":0,"b":0}
)

fig.write_html('html_visualizations/hermitage_map.html')
print("   ✓ hermitage_map.html")

# --- 6. Top Archaeological Sites ---
print("6. Top 20 Archaeological Sites...")
location_counts = df_geo['find_location'].value_counts().head(20)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=location_counts.index,
    x=location_counts.values,
    orientation='h',
    marker=dict(color=location_counts.values, colorscale='YlOrBr',
                line=dict(color='#4A2511', width=1.5)),
    text=location_counts.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Top 20 Archaeological Sites by Object Count',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=700,
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/hermitage_sites.html')
print("   ✓ hermitage_sites.html")

# --- 7. Acquisition Timeline ---
print("7. Acquisition Timeline...")
df_acq = df_hermitage[df_hermitage['acquisition_year_only'].notna()].copy()
yearly_acq = df_acq.groupby('acquisition_year_only').size().reset_index(name='count')

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=yearly_acq['acquisition_year_only'],
    y=yearly_acq['count'],
    mode='lines',
    fill='tozeroy',
    line=dict(color='#8B4513', width=3),
    fillcolor='rgba(139, 69, 19, 0.3)',
    hovertemplate='Year: %{x}<br>Objects: %{y:,}<extra></extra>'
))

period_markers = [
    (1764, 'Russian Empire', '#8B4513'),
    (1917, 'First Independence', '#CD5C5C'),
    (1922, 'Soviet Period', '#DC143C'),
    (1991, 'Independence', '#D2691E')
]

for year, label, color in period_markers:
    fig.add_vline(x=year, line_dash="dash", line_color=color, line_width=2, opacity=0.7)
    fig.add_annotation(x=year, y=yearly_acq['count'].max(), text=label,
                      showarrow=False, textangle=-90, yshift=10,
                      font=dict(size=10, color=color))

fig.update_layout(
    title='Timeline: Acquisition of Ukrainian Objects by the Hermitage Museum',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Year',
    yaxis_title='Number of Objects Acquired',
    height=600,
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/hermitage_acquisition_timeline.html')
print("   ✓ hermitage_acquisition_timeline.html")

# --- 8. Acquisition by Period ---
print("8. Acquisition by Period...")
def classify_acquisition_period(year):
    if pd.isna(year):
        return 'Unknown'
    elif 1764 <= year <= 1917:
        return 'Russian Empire (1764-1917)'
    elif 1917 < year <= 1921:
        return 'First Independence (1917-1921)'
    elif 1922 <= year <= 1991:
        return 'Soviet Period (1922-1991)'
    elif 1991 < year <= 2024:
        return 'Independence (1991-present)'
    elif year < 1764:
        return 'Before Russian Empire'
    else:
        return 'Recent'

df_acq['acquisition_period'] = df_acq['acquisition_year_only'].apply(classify_acquisition_period)
period_acq = df_acq['acquisition_period'].value_counts()

period_order = ['Before Russian Empire', 'Russian Empire (1764-1917)', 'First Independence (1917-1921)',
                'Soviet Period (1922-1991)', 'Independence (1991-present)', 'Recent']
period_order = [p for p in period_order if p in period_acq.index]
period_acq = period_acq.reindex(period_order)

colors_period = ['#696969', '#8B4513', '#CD5C5C', '#DC143C', '#D2691E', '#4B0082']

fig = go.Figure()
fig.add_trace(go.Bar(
    y=period_acq.index,
    x=period_acq.values,
    orientation='h',
    marker=dict(color=colors_period[:len(period_acq)],
                line=dict(color='#4A2511', width=1.5)),
    text=period_acq.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Objects Acquired by Historical Period',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=500,
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/hermitage_acquisition_periods.html')
print("   ✓ hermitage_acquisition_periods.html")

# --- 9. Regional Distribution (Oblasts) ---
print("9. Regional Distribution (Oblasts)...")

def assign_oblast_by_coordinates(lat, lon):
    if pd.isna(lat) or pd.isna(lon):
        return 'Unknown'
    if not (22 <= lon <= 41) or not (44 <= lat <= 53):
        return 'Outside Ukraine'
    if lat < 46 and 33 <= lon <= 37:
        return 'Crimea'
    if 46 <= lat < 47.5:
        if 28 <= lon < 31:
            return 'Odesa'
        elif 31 <= lon < 33:
            return 'Mykolaiv'
        elif 33 <= lon < 36:
            return 'Kherson'
    if lat >= 47.5 and 36 <= lon <= 41:
        if lat >= 49.5:
            return 'Kharkiv'
        elif lat >= 48:
            return 'Luhansk'
        else:
            return 'Donetsk'
    if 46.5 <= lat < 48.5 and 33 <= lon < 36:
        return 'Zaporizhzhia'
    return 'Other Region'

df_geo['current_oblast'] = df_geo.apply(
    lambda row: assign_oblast_by_coordinates(row['latitude'], row['longitude']), axis=1)

oblast_counts = df_geo['current_oblast'].value_counts().head(15)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=oblast_counts.index,
    x=oblast_counts.values,
    orientation='h',
    marker=dict(color=oblast_counts.values, colorscale='Reds',
                line=dict(color='#4A2511', width=1.5)),
    text=oblast_counts.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Ukrainian Regions Most Affected by Cultural Appropriation',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=650,
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/hermitage_oblasts.html')
print("   ✓ hermitage_oblasts.html")

# --- 10. Materials × Periods Cross-Analysis ---
print("10. Materials × Periods Cross-Analysis...")
top_materials = df_hermitage['category'].value_counts().head(10).index
top_periods = df_hermitage[df_hermitage['period_category'] != 'Unknown Period']['period_category'].value_counts().head(10).index

cross_data = df_hermitage[
    df_hermitage['category'].isin(top_materials) & 
    df_hermitage['period_category'].isin(top_periods)
].groupby(['period_category', 'category']).size().reset_index(name='count')

fig = px.bar(
    cross_data,
    x='period_category',
    y='count',
    color='category',
    title='Material Categories Across Historical Periods',
    labels={'period_category': 'Historical Period', 'count': 'Number of Objects'},
    height=600,
    barmode='stack',
    color_discrete_sequence=px.colors.sequential.Reds
)

fig.update_layout(
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_tickangle=-45,
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0',
    xaxis=dict(title='')
)

fig.write_html('html_visualizations/hermitage_materials_periods.html')
print("   ✓ hermitage_materials_periods.html")

# --- 11. Oblast Clusters Interactive ---
print("11. Oblast Clusters Interactive...")

top_oblasts = df_geo['current_oblast'].value_counts().head(12)
positions = [
    (0.5, 3.5), (2, 3.5), (3.5, 3.5),
    (1.25, 2.6), (2.75, 2.6),
    (0.5, 1.7), (2, 1.7), (3.5, 1.7),
    (0.3, 0.8), (1.4, 0.8), (2.6, 0.8), (3.7, 0.8)
]
base_colors = ['#C94A38', '#E07A5F', '#D4634A', '#B8403A', '#E8927C', '#A63A2F']

fig = go.Figure()

for idx, (oblast, count) in enumerate(top_oblasts.items()):
    if idx >= len(positions):
        break
    
    x, y = positions[idx]
    oblast_data = df_geo[df_geo['current_oblast'] == oblast]
    years = oblast_data['year_for_timeline'].dropna()
    
    if len(years) > 0:
        min_year, max_year = years.min(), years.max()
        if min_year < 0 and max_year < 0:
            date_range = f"{int(abs(min_year)):,} - {int(abs(max_year)):,} BC"
        elif min_year < 0 and max_year >= 0:
            date_range = f"{int(abs(min_year)):,} BC - {int(max_year)} AD"
        else:
            date_range = f"{int(min_year)} - {int(max_year)} AD"
    else:
        date_range = "Various periods"
    
    color = base_colors[idx % len(base_colors)]
    max_count, min_count = top_oblasts.values[0], top_oblasts.values[-1]
    radius = 0.30 + (count - min_count) / (max_count - min_count) * 0.35
    
    n_points = min(int(count / 3.5), 2000)
    np.random.seed(idx)
    
    points_x, points_y = [], []
    for _ in range(n_points):
        r = min(abs(np.random.normal(0, radius/2.5)), radius)
        theta = np.random.random() * 2 * np.pi
        points_x.append(x + r * np.cos(theta))
        points_y.append(y + r * np.sin(theta))
    
    fig.add_trace(go.Scatter(
        x=points_x, y=points_y,
        mode='markers',
        marker=dict(color=color, size=np.random.uniform(2, 4, n_points),
                    opacity=np.random.uniform(0.6, 0.85, n_points), line=dict(width=0)),
        name=oblast,
        hovertemplate=f'<b>{oblast}</b><br>Total: {count:,}<br>Period: {date_range}<extra></extra>',
        showlegend=False
    ))
    
    fig.add_annotation(x=x, y=y+0.15, text=f'<b>{oblast}</b>',
                      showarrow=False, font=dict(size=13, color='#2C1810'))
    fig.add_annotation(x=x, y=y-0.05, text=f'<b>{count:,} objects</b>',
                      showarrow=False, font=dict(size=11, color='#3D2415'))
    fig.add_annotation(x=x, y=y-0.25, text=f'<i>{date_range}</i>',
                      showarrow=False, font=dict(size=10, color='#4A2511'))

fig.update_layout(
    title='<b>Ukrainian Regions - Cluster Visualization</b>',
    xaxis=dict(range=[-0.3, 4.3], showgrid=False, showticklabels=False, zeroline=False),
    yaxis=dict(range=[-0.3, 4.3], showgrid=False, showticklabels=False, zeroline=False,
               scaleanchor='x', scaleratio=1),
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0',
    height=900,
    hovermode='closest',
    title_font=dict(size=22, color='#5C3317', family='Arial Black')
)

fig.write_html('html_visualizations/hermitage_oblast_clusters.html')
print("   ✓ hermitage_oblast_clusters.html")

# =============================================================================
# STOLEN OBJECTS VISUALIZATIONS
# =============================================================================

print("\n\n📊 STOLEN OBJECTS VISUALIZATIONS")
print("-"*70)

# Load Stolen Objects data
df_stolen = pd.read_csv('data_stolen/5_stolen_objects_final.csv')
print(f"✓ Loaded {len(df_stolen):,} stolen objects")

# --- 1. Categories Bar Chart ---
print("\n1. Categories Bar Chart...")
category_counts = df_stolen['category'].value_counts().head(15)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=category_counts.index,
    x=category_counts.values,
    orientation='h',
    marker=dict(color=category_counts.values, colorscale='YlOrBr',
                line=dict(color='#4A2511', width=1.5)),
    text=category_counts.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Stolen Ukrainian Objects by Category',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=600,
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/stolen_categories.html')
print("   ✓ stolen_categories.html")

# --- 2. Geographic Map ---
print("2. Geographic Map...")
df_stolen_geo = df_stolen[df_stolen['latitude'].notna() & df_stolen['longitude'].notna()].copy()

fig = px.scatter_mapbox(
    df_stolen_geo,
    lat='latitude',
    lon='longitude',
    hover_name='name',
    hover_data={'place_incident': True, 'category': True, 'period_category': True,
                'latitude': False, 'longitude': False},
    color='category',
    zoom=5.5,
    title='Geographic Distribution of Stolen Ukrainian Objects',
    height=700,
    color_discrete_sequence=px.colors.sequential.Reds
)

fig.update_layout(
    mapbox_style='open-street-map',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    margin={"r":0,"t":50,"l":0,"b":0}
)

fig.write_html('html_visualizations/stolen_map.html')
print("   ✓ stolen_map.html")

# --- 3. Historical Periods ---
print("3. Historical Periods...")
period_counts_stolen = df_stolen[df_stolen['period_category'] != 'Unknown Period']['period_category'].value_counts()

fig = go.Figure()
fig.add_trace(go.Bar(
    y=period_counts_stolen.index,
    x=period_counts_stolen.values,
    orientation='h',
    marker=dict(color=period_counts_stolen.values, colorscale='Reds',
                line=dict(color='#4A2511', width=1.5)),
    text=period_counts_stolen.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Stolen Objects by Historical Period',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=600,
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/stolen_periods.html')
print("   ✓ stolen_periods.html")

# --- 4. Locations Bar Chart ---
print("4. Top Locations...")
location_counts_stolen = df_stolen['place_incident'].value_counts().head(15)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=location_counts_stolen.index,
    x=location_counts_stolen.values,
    orientation='h',
    marker=dict(color=location_counts_stolen.values, colorscale='YlOrBr',
                line=dict(color='#4A2511', width=1.5)),
    text=location_counts_stolen.values,
    texttemplate='%{text:,}',
    textposition='outside'
))

fig.update_layout(
    title='Top 15 Locations of Stolen Objects',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Number of Objects',
    height=600,
    yaxis={'categoryorder':'total ascending'},
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/stolen_locations.html')
print("   ✓ stolen_locations.html")

# --- 5. Timeline (Year of Incident) ---
print("5. Incident Timeline...")

def extract_year_stolen(value):
    if pd.isna(value):
        return np.nan
    try:
        return int(float(value))
    except:
        pass
    try:
        import re
        match = re.search(r'(\d{4})', str(value))
        if match:
            return int(match.group(1))
    except:
        pass
    return np.nan

df_stolen['year_only'] = df_stolen['year_incident'].apply(extract_year_stolen)
df_stolen_timeline = df_stolen[df_stolen['year_only'].notna()].copy()
incident_counts = df_stolen_timeline['year_only'].value_counts().sort_index()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=incident_counts.index,
    y=incident_counts.values,
    mode='lines',
    fill='tozeroy',
    line=dict(color='#DC143C', width=3),
    fillcolor='rgba(220, 20, 60, 0.3)',
    hovertemplate='Year: %{x}<br>Objects: %{y:,}<extra></extra>'
))

fig.update_layout(
    title='Timeline of Cultural Object Theft During Russian Invasion',
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_title='Year',
    yaxis_title='Number of Objects Stolen',
    height=600,
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0'
)

fig.write_html('html_visualizations/stolen_timeline.html')
print("   ✓ stolen_timeline.html")

# --- 6. Categories × Periods ---
print("6. Categories × Periods...")
top_categories = df_stolen['category'].value_counts().head(10).index
top_periods_stolen = df_stolen[df_stolen['period_category'] != 'Unknown Period']['period_category'].value_counts().head(8).index

cross_stolen = df_stolen[
    df_stolen['category'].isin(top_categories) & 
    df_stolen['period_category'].isin(top_periods_stolen)
].groupby(['period_category', 'category']).size().reset_index(name='count')

fig = px.bar(
    cross_stolen,
    x='period_category',
    y='count',
    color='category',
    title='Stolen Object Categories Across Historical Periods',
    height=600,
    barmode='stack',
    color_discrete_sequence=px.colors.sequential.Reds
)

fig.update_layout(
    title_font=dict(size=20, color='#5C3317', family='Arial Black'),
    xaxis_tickangle=-45,
    plot_bgcolor='#FFF8F0',
    paper_bgcolor='#FFF8F0',
    xaxis=dict(title='')
)

fig.write_html('html_visualizations/stolen_categories_periods.html')
print("   ✓ stolen_categories_periods.html")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "="*70)
print("✅ ALL HTML VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("="*70)
print(f"\n📁 Output directory: html_visualizations/")
print(f"\n📊 HERMITAGE MUSEUM ({11} files):")
print("   1. hermitage_material_categories.html")
print("   2. hermitage_material_treemap.html")
print("   3. hermitage_periods.html")
print("   4. hermitage_timeline_scatter.html")
print("   5. hermitage_map.html")
print("   6. hermitage_sites.html")
print("   7. hermitage_acquisition_timeline.html")
print("   8. hermitage_acquisition_periods.html")
print("   9. hermitage_oblasts.html")
print("   10. hermitage_materials_periods.html")
print("   11. hermitage_oblast_clusters.html")

print(f"\n📊 STOLEN OBJECTS ({6} files):")
print("   1. stolen_categories.html")
print("   2. stolen_map.html")
print("   3. stolen_periods.html")
print("   4. stolen_locations.html")
print("   5. stolen_timeline.html")
print("   6. stolen_categories_periods.html")

print(f"\n✨ Total: {17} interactive HTML files ready for web!")
print("="*70)
print("\n💡 To use on your website:")
print("   1. Upload all HTML files to your server")
print("   2. Embed using <iframe>:")
print("      <iframe src='hermitage_material_categories.html' width='100%' height='600px'></iframe>")
print("   3. Or link directly: <a href='hermitage_material_categories.html'>View Chart</a>")
print("\n🎨 All charts are:")
print("   ✓ Fully interactive (zoom, pan, hover)")
print("   ✓ Self-contained (no external dependencies)")
print("   ✓ Consistent terracotta color scheme")
print("   ✓ Responsive design")
print("   ✓ Ready for web deployment")
print("="*70)
