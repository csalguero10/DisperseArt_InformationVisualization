"""
DASHBOARD INTERACTIVO - Objetos Robados de Ucrania
Visualización estilo ACLED Ukraine Conflict Monitor
Incluye mapa interactivo, gráficos, estadísticas y filtros
"""

import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

def extract_coords_from_google_maps_link(link):
    """Extrae latitud y longitud de un link de Google Maps"""
    if not link or pd.isna(link):
        return None, None
    
    match = re.search(r'q=([-+]?\d+\.\d+)[,\s]+([-+]?\d+\.\d+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    match = re.search(r'll=([-+]?\d+\.\d+)[,\s]+([-+]?\d+\.\d+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    return None, None

def create_interactive_dashboard(csv_file):
    """Crea un dashboard interactivo completo con mapa y gráficos"""
    
    print("\n" + "="*70)
    print("CREANDO DASHBOARD INTERACTIVO ESTILO ACLED")
    print("="*70 + "\n")
    
    # Leer datos
    print(f"📖 Leyendo archivo: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"✓ {len(df)} objetos encontrados\n")
    
    # Extraer coordenadas
    print("🗺️  Extrayendo coordenadas...")
    df[['latitude', 'longitude']] = df['google_maps_link'].apply(
        lambda x: pd.Series(extract_coords_from_google_maps_link(x))
    )
    
    df_coords = df.dropna(subset=['latitude', 'longitude'])
    print(f"✓ {len(df_coords)} objetos con coordenadas válidas\n")
    
    if len(df_coords) == 0:
        print("⚠️  No hay objetos con coordenadas para visualizar")
        return
    
    # Preparar datos
    df_coords['hover_text'] = df_coords.apply(
        lambda row: f"<b>{row.get('name', 'Sin nombre')}</b><br>" +
                    f"Categoría: {row.get('category', 'N/A')}<br>" +
                    f"Año: {row.get('year_incident', 'N/A')}<br>" +
                    f"Lugar: {row.get('place_incident', 'N/A')}<br>" +
                    f"<a href='{row.get('url', '#')}'>Ver detalles</a>",
        axis=1
    )
    
    print("📊 Creando visualizaciones...\n")
    
    # ==================================================================
    # 1. MAPA PRINCIPAL CON MARCADORES
    # ==================================================================
    fig_map = px.scatter_mapbox(
        df_coords,
        lat='latitude',
        lon='longitude',
        color='category',
        size_max=15,
        zoom=5,
        hover_name='name',
        hover_data={
            'category': True,
            'year_incident': True,
            'place_incident': True,
            'latitude': False,
            'longitude': False
        },
        title='Mapa de Objetos Culturales Robados en Ucrania',
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    
    fig_map.update_layout(
        mapbox_style="open-street-map",
        height=600,
        margin={"r":0,"t":50,"l":0,"b":0},
        hovermode='closest'
    )
    
    # ==================================================================
    # 2. GRÁFICO DE BARRAS - OBJETOS POR CATEGORÍA
    # ==================================================================
    category_counts = df_coords['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    
    fig_categories = px.bar(
        category_counts,
        x='category',
        y='count',
        title='Objetos Robados por Categoría',
        labels={'category': 'Categoría', 'count': 'Número de Objetos'},
        color='count',
        color_continuous_scale='Reds'
    )
    
    fig_categories.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=False
    )
    
    # ==================================================================
    # 3. GRÁFICO DE LÍNEA - EVOLUCIÓN TEMPORAL
    # ==================================================================
    df_coords['year_incident'] = pd.to_numeric(df_coords['year_incident'], errors='coerce')
    timeline_data = df_coords.dropna(subset=['year_incident'])
    timeline_counts = timeline_data['year_incident'].value_counts().sort_index().reset_index()
    timeline_counts.columns = ['year', 'count']
    
    fig_timeline = px.line(
        timeline_counts,
        x='year',
        y='count',
        title='Evolución Temporal de Robos',
        labels={'year': 'Año del Incidente', 'count': 'Número de Objetos'},
        markers=True
    )
    
    fig_timeline.update_traces(line_color='#d62728', line_width=3, marker_size=10)
    fig_timeline.update_layout(height=400)
    
    # ==================================================================
    # 4. GRÁFICO DE PASTEL - DISTRIBUCIÓN POR TIPO
    # ==================================================================
    type_counts = df_coords['type'].value_counts().head(10).reset_index()
    type_counts.columns = ['type', 'count']
    
    fig_pie = px.pie(
        type_counts,
        values='count',
        names='type',
        title='Top 10 Tipos de Objetos Robados',
        hole=0.4
    )
    
    fig_pie.update_layout(height=400)
    
    # ==================================================================
    # 5. TABLA DE LUGARES MÁS AFECTADOS
    # ==================================================================
    location_counts = df_coords['place_incident'].value_counts().head(10).reset_index()
    location_counts.columns = ['place', 'count']
    
    fig_locations = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Lugar del Incidente</b>', '<b>Objetos Robados</b>'],
            fill_color='paleturquoise',
            align='left',
            font=dict(size=12, color='black')
        ),
        cells=dict(
            values=[location_counts['place'], location_counts['count']],
            fill_color='lavender',
            align='left',
            font=dict(size=11)
        )
    )])
    
    fig_locations.update_layout(
        title='Top 10 Lugares Más Afectados',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    # ==================================================================
    # 6. MAPA DE DENSIDAD (HEATMAP)
    # ==================================================================
    fig_density = px.density_mapbox(
        df_coords,
        lat='latitude',
        lon='longitude',
        z=[1] * len(df_coords),  # Peso igual para todos
        radius=20,
        zoom=5,
        title='Mapa de Densidad de Robos',
        color_continuous_scale='YlOrRd'
    )
    
    fig_density.update_layout(
        mapbox_style="open-street-map",
        height=600,
        margin={"r":0,"t":50,"l":0,"b":0}
    )
    
    # ==================================================================
    # CREAR HTML CON TODOS LOS GRÁFICOS
    # ==================================================================
    print("📝 Generando HTML...\n")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Dashboard - Objetos Culturales Robados en Ucrania</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .header {{
                background-color: #1f77b4;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .header p {{
                margin: 5px 0 0 0;
                font-size: 1.2em;
            }}
            .stats-container {{
                display: flex;
                justify-content: space-around;
                padding: 20px;
                background-color: white;
                margin: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .stat-box {{
                text-align: center;
                padding: 20px;
            }}
            .stat-number {{
                font-size: 3em;
                font-weight: bold;
                color: #d62728;
            }}
            .stat-label {{
                font-size: 1.2em;
                color: #666;
                margin-top: 10px;
            }}
            .dashboard-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                padding: 20px;
            }}
            .dashboard-item {{
                background-color: white;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .full-width {{
                grid-column: 1 / -1;
            }}
            .footer {{
                background-color: #333;
                color: white;
                text-align: center;
                padding: 20px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏛️ Objetos Culturales Robados en Ucrania</h1>
            <p>Monitor Interactivo de Patrimonio Cultural</p>
        </div>
        
        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-number">{len(df_coords)}</div>
                <div class="stat-label">Objetos Robados</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{df_coords['category'].nunique()}</div>
                <div class="stat-label">Categorías</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{df_coords['place_incident'].nunique()}</div>
                <div class="stat-label">Lugares Afectados</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{df_coords['year_incident'].nunique()}</div>
                <div class="stat-label">Años de Incidentes</div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="dashboard-item full-width">
                <div id="map"></div>
            </div>
            
            <div class="dashboard-item">
                <div id="categories"></div>
            </div>
            
            <div class="dashboard-item">
                <div id="timeline"></div>
            </div>
            
            <div class="dashboard-item">
                <div id="pie"></div>
            </div>
            
            <div class="dashboard-item">
                <div id="locations"></div>
            </div>
            
            <div class="dashboard-item full-width">
                <div id="density"></div>
            </div>
        </div>
        
        <div class="footer">
            <p>Datos extraídos de: <a href="https://war-sanctions.gur.gov.ua/en/stolen/objects/" style="color: #4da6ff;">https://war-sanctions.gur.gov.ua/en/stolen/objects/</a></p>
            <p>Dashboard generado con Plotly | Última actualización: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <script>
            // Mapa principal
            var mapData = {fig_map.to_json()};
            Plotly.newPlot('map', mapData.data, mapData.layout);
            
            // Gráfico de categorías
            var categoriesData = {fig_categories.to_json()};
            Plotly.newPlot('categories', categoriesData.data, categoriesData.layout);
            
            // Timeline
            var timelineData = {fig_timeline.to_json()};
            Plotly.newPlot('timeline', timelineData.data, timelineData.layout);
            
            // Pie chart
            var pieData = {fig_pie.to_json()};
            Plotly.newPlot('pie', pieData.data, pieData.layout);
            
            // Tabla de lugares
            var locationsData = {fig_locations.to_json()};
            Plotly.newPlot('locations', locationsData.data, locationsData.layout);
            
            // Mapa de densidad
            var densityData = {fig_density.to_json()};
            Plotly.newPlot('density', densityData.data, densityData.layout);
        </script>
    </body>
    </html>
    """
    
    # Guardar HTML
    output_file = 'dashboard_objetos_robados_ucrania.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Dashboard guardado: {output_file}\n")
    
    # Estadísticas en consola
    print("="*70)
    print("ESTADÍSTICAS DEL DASHBOARD")
    print("="*70)
    print(f"\n📊 Total de objetos: {len(df_coords)}")
    print(f"🗂️  Categorías: {df_coords['category'].nunique()}")
    print(f"📍 Lugares afectados: {df_coords['place_incident'].nunique()}")
    print(f"📅 Años con incidentes: {df_coords['year_incident'].nunique()}")
    
    print(f"\n🏆 Top 3 categorías:")
    for i, (cat, count) in enumerate(category_counts.head(3).values, 1):
        print(f"  {i}. {cat}: {count} objetos")
    
    print(f"\n📍 Top 3 lugares más afectados:")
    for i, (place, count) in enumerate(location_counts.head(3).values, 1):
        print(f"  {i}. {place}: {count} objetos")
    
    print("\n" + "="*70)
    print("✓ Dashboard completado")
    print(f"✓ Abre '{output_file}' en tu navegador")
    print("="*70 + "\n")

# Ejecutar
if __name__ == "__main__":
    # Cambiar por el nombre de tu archivo CSV
    csv_filename = 'data/stolen_objects_ukraine.csv'  # o 'stolen_objects_ukraine.csv'
    
    try:
        print("\n🎨 GENERANDO DASHBOARD INTERACTIVO")
        print("="*70)
        print("\nAsegúrate de tener instalado: pip install plotly pandas\n")
        
        create_interactive_dashboard(csv_filename)
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: No se encontró el archivo '{csv_filename}'")
        print("Asegúrate de haber ejecutado el scraping primero.\n")
    except ImportError as e:
        print(f"\n✗ ERROR: {e}")
        print("Instala las dependencias con:")
        print("  pip install plotly pandas\n")