"""
VISUALIZACIÓN INTERACTIVA - ACLED Looting & Property Destruction en Ucrania
Mapa interactivo con filtros, timeline y análisis
"""

import pandas as pd
import folium
from folium import plugins
from datetime import datetime
import json

def create_acled_interactive_map(csv_file):
    """Crea un mapa interactivo del dataset de ACLED"""
    
    print("\n" + "="*70)
    print("CREANDO VISUALIZACIÓN INTERACTIVA - ACLED DATASET")
    print("="*70 + "\n")
    
    # Leer el CSV
    print(f"📖 Leyendo archivo: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"✓ {len(df)} eventos encontrados\n")
    
    # Filtrar eventos con coordenadas válidas
    df_coords = df.dropna(subset=['latitude', 'longitude'])
    print(f"✓ {len(df_coords)} eventos con coordenadas válidas")
    print(f"✗ {len(df) - len(df_coords)} eventos sin coordenadas\n")
    
    if len(df_coords) == 0:
        print("⚠️  No hay eventos con coordenadas para visualizar")
        return
    
    # Convertir event_date a datetime
    df_coords['event_date'] = pd.to_datetime(df_coords['event_date'])
    df_coords['year'] = df_coords['event_date'].dt.year
    
    # Estadísticas
    print("📊 ESTADÍSTICAS DEL DATASET:")
    print(f"  Período: {df_coords['event_date'].min().strftime('%Y-%m-%d')} a {df_coords['event_date'].max().strftime('%Y-%m-%d')}")
    print(f"  Años: {df_coords['year'].nunique()}")
    print(f"  Tipos de eventos: {df_coords['sub_event_type'].nunique()}")
    print(f"  Regiones afectadas: {df_coords['admin1'].nunique()}")
    print()
    
    # Centro del mapa (Ucrania)
    center_lat = df_coords['latitude'].mean()
    center_lon = df_coords['longitude'].mean()
    
    print(f"🗺️  Creando mapa centrado en: {center_lat:.4f}, {center_lon:.4f}\n")
    
    # Crear mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Agregar tiles adicionales
    folium.TileLayer('CartoDB positron', name='CartoDB Positivo').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB Oscuro').add_to(m)
    
    # Colores por tipo de evento
    event_colors = {
        'Looting/property destruction': 'red',
        'Looting': 'orange',
        'Property destruction': 'darkred'
    }
    
    # Crear grupos de marcadores por año
    print("📍 Creando capas por año...")
    years = sorted(df_coords['year'].unique())
    
    for year in years:
        df_year = df_coords[df_coords['year'] == year]
        
        # Crear grupo para este año
        year_group = folium.FeatureGroup(name=f'📅 {year} ({len(df_year)} eventos)', show=True)
        
        # Crear cluster de marcadores para este año
        marker_cluster = plugins.MarkerCluster(name=f'Cluster {year}')
        
        for idx, row in df_year.iterrows():
            # Preparar el popup con información detallada
            popup_html = f"""
            <div style="width: 400px; max-height: 400px; overflow-y: auto;">
                <h4 style="margin-bottom: 10px; color: #d62728;">
                    {row.get('event_type', 'N/A')}
                </h4>
                <hr>
                <p><strong>📅 Fecha:</strong> {row.get('event_date', 'N/A')}</p>
                <p><strong>📍 Ubicación:</strong> {row.get('location', 'N/A')}, {row.get('admin1', 'N/A')}</p>
                <p><strong>🏷️ Sub-tipo:</strong> {row.get('sub_event_type', 'N/A')}</p>
                <p><strong>👥 Actor 1:</strong> {row.get('actor1', 'N/A')}</p>
                <p><strong>👥 Actor 2:</strong> {row.get('actor2', 'N/A')}</p>
                <p><strong>💀 Fatalidades:</strong> {row.get('fatalities', 0)}</p>
                <hr>
                <p><strong>📝 Notas:</strong></p>
                <p style="font-size: 0.9em; max-height: 150px; overflow-y: auto;">
                    {row.get('notes', 'Sin notas')[:500]}...
                </p>
                <hr>
                <p style="font-size: 0.8em; color: #666;">
                    <strong>Fuente:</strong> {row.get('source', 'N/A')}<br>
                    <strong>ID:</strong> {row.get('event_id_cnty', 'N/A')}
                </p>
            </div>
            """
            
            # Determinar color según el sub_event_type
            color = event_colors.get(row.get('sub_event_type'), 'gray')
            
            # Crear marcador
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5,
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{row.get('location', 'Ubicación')}: {row.get('event_date', '')}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(marker_cluster)
        
        marker_cluster.add_to(year_group)
        year_group.add_to(m)
    
    print(f"✓ Creadas {len(years)} capas por año\n")
    
    # Crear mapa de calor
    print("🔥 Creando mapa de calor...")
    heat_data = [[row['latitude'], row['longitude']] for idx, row in df_coords.iterrows()]
    
    heat_group = folium.FeatureGroup(name='🔥 Mapa de Calor', show=False)
    plugins.HeatMap(
        heat_data,
        min_opacity=0.3,
        max_zoom=13,
        radius=15,
        blur=20,
        gradient={0.4: 'blue', 0.6: 'lime', 0.7: 'yellow', 0.8: 'orange', 1: 'red'}
    ).add_to(heat_group)
    heat_group.add_to(m)
    
    print("✓ Mapa de calor creado\n")
    
    # Agregar estadísticas por región
    print("📊 Creando capa de círculos por región...")
    region_stats = df_coords.groupby('admin1').agg({
        'event_id_cnty': 'count',
        'latitude': 'first',
        'longitude': 'first',
        'fatalities': 'sum'
    }).reset_index()
    region_stats.columns = ['region', 'events', 'lat', 'lon', 'total_fatalities']
    region_stats = region_stats.sort_values('events', ascending=False)
    
    regions_group = folium.FeatureGroup(name='📊 Eventos por Región', show=False)
    
    for idx, row in region_stats.iterrows():
        # Lista de eventos en esta región
        region_events = df_coords[df_coords['admin1'] == row['region']]
        
        popup_html = f"""
        <div style="width: 300px;">
            <h4>{row['region']}</h4>
            <hr>
            <p><strong>Total de eventos:</strong> {row['events']}</p>
            <p><strong>Total de fatalidades:</strong> {row['total_fatalities']}</p>
            <hr>
            <p><strong>Distribución por año:</strong></p>
            <ul>
        """
        
        for year in sorted(region_events['year'].unique()):
            year_count = len(region_events[region_events['year'] == year])
            popup_html += f"<li>{year}: {year_count} eventos</li>"
        
        popup_html += "</ul></div>"
        
        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=row['events'] * 300,  # Radio proporcional al número de eventos
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['region']}: {row['events']} eventos",
            color='purple',
            fill=True,
            fillColor='purple',
            fillOpacity=0.3,
            weight=2
        ).add_to(regions_group)
    
    regions_group.add_to(m)
    print("✓ Capa de regiones creada\n")
    
    # Agregar leyenda personalizada
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 250px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 15px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        <h4 style="margin-top:0; margin-bottom: 10px;">
            📊 Eventos de Saqueo y Destrucción
        </h4>
        <hr style="margin: 10px 0;">
        <p style="margin: 5px 0;">
            <span style="background-color: red; padding: 5px 10px; color: white; border-radius: 3px;">●</span>
            Saqueo/Destrucción
        </p>
        <p style="margin: 5px 0;">
            <span style="background-color: orange; padding: 5px 10px; color: white; border-radius: 3px;">●</span>
            Saqueo
        </p>
        <p style="margin: 5px 0;">
            <span style="background-color: darkred; padding: 5px 10px; color: white; border-radius: 3px;">●</span>
            Destrucción de Propiedad
        </p>
        <hr style="margin: 10px 0;">
        <p style="font-size: 12px; color: #666; margin: 5px 0;">
            <strong>Total:</strong> ''' + f"{len(df_coords):,}" + ''' eventos<br>
            <strong>Período:</strong> ''' + f"{df_coords['year'].min()}-{df_coords['year'].max()}" + '''<br>
            <strong>Fatalidades:</strong> ''' + f"{df_coords['fatalities'].sum():,}" + '''
        </p>
        <hr style="margin: 10px 0;">
        <p style="font-size: 11px; color: #999; margin-top: 10px;">
            Fuente: ACLED<br>
            <em>Usa las capas para filtrar por año</em>
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Control de capas
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Agregar búsqueda de ubicaciones
    plugins.Search(
        layer=marker_cluster,
        search_label='location',
        placeholder='Buscar ubicación...',
        collapsed=False
    ).add_to(m)
    
    # Agregar medidor de distancias
    plugins.MeasureControl(position='topleft').add_to(m)
    
    # Agregar minimapa
    minimap = plugins.MiniMap(toggle_display=True)
    m.add_child(minimap)
    
    # Agregar botón de pantalla completa
    plugins.Fullscreen(
        position='topleft',
        title='Pantalla completa',
        title_cancel='Salir de pantalla completa',
        force_separate_button=True
    ).add_to(m)
    
    # Guardar mapa
    output_file = 'mapa_acled_looting_destruction.html'
    m.save(output_file)
    
    print(f"✓ Mapa guardado: {output_file}\n")
    
    # Mostrar estadísticas finales
    print("="*70)
    print("RESUMEN DE ESTADÍSTICAS")
    print("="*70)
    print(f"\n📊 Total de eventos: {len(df_coords):,}")
    print(f"💀 Total de fatalidades: {df_coords['fatalities'].sum():,}")
    print(f"📅 Período: {df_coords['event_date'].min().strftime('%Y-%m-%d')} a {df_coords['event_date'].max().strftime('%Y-%m-%d')}")
    
    print(f"\n🏆 Top 10 Regiones más afectadas:")
    for i, row in region_stats.head(10).iterrows():
        print(f"  {i+1}. {row['region']}: {row['events']:,} eventos")
    
    print(f"\n📅 Eventos por año:")
    year_counts = df_coords['year'].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"  {year}: {count:,} eventos")
    
    print(f"\n🏷️  Tipos de sub-eventos:")
    subtype_counts = df_coords['sub_event_type'].value_counts()
    for subtype, count in subtype_counts.items():
        print(f"  {subtype}: {count:,} eventos")
    
    print("\n" + "="*70)
    print("✓ Visualización completada")
    print(f"✓ Abre '{output_file}' en tu navegador")
    print("="*70)
    print("\n🎯 CARACTERÍSTICAS DEL MAPA:")
    print("  ✓ Capas por año (activa/desactiva)")
    print("  ✓ Mapa de calor")
    print("  ✓ Círculos por región")
    print("  ✓ Clustering de marcadores")
    print("  ✓ Búsqueda de ubicaciones")
    print("  ✓ Medidor de distancias")
    print("  ✓ Minimapa")
    print("  ✓ Pantalla completa")
    print("  ✓ Popups con información detallada")
    print("="*70 + "\n")

# Ejecutar
if __name__ == "__main__":
    csv_filename = 'raw_data/ACLED Data_Looting_PropertyDestruction.csv'
    
    try:
        print("\n🗺️  GENERANDO VISUALIZACIÓN INTERACTIVA ACLED")
        print("="*70)
        
        create_acled_interactive_map(csv_filename)
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: No se encontró el archivo '{csv_filename}'")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()