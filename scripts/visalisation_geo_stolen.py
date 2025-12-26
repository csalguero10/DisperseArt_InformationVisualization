"""
VISUALIZACIÓN GEOREFERENCIADA - Objetos Robados de Ucrania
Extrae coordenadas de los links de Google Maps y crea un mapa interactivo
"""

import pandas as pd
import re
import folium
from folium import plugins

def extract_coords_from_google_maps_link(link):
    """Extrae latitud y longitud de un link de Google Maps"""
    if not link or pd.isna(link):
        return None, None
    
    # Patrón: ?q=LAT,LON o ll=LAT,LON
    # Ejemplo: https://maps.google.com/?q=46.94916210384292, 35.46606313178811&ll=46.94916210384292, 35.46606313178811&z=13&hl=en
    
    # Intentar extraer de q=
    match = re.search(r'q=([-+]?\d+\.\d+)[,\s]+([-+]?\d+\.\d+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    # Intentar extraer de ll=
    match = re.search(r'll=([-+]?\d+\.\d+)[,\s]+([-+]?\d+\.\d+)', link)
    if match:
        return float(match.group(1)), float(match.group(2))
    
    return None, None

def create_map_visualization(csv_file):
    """Crea un mapa interactivo con los objetos robados"""
    
    print("\n" + "="*70)
    print("CREANDO VISUALIZACIÓN GEOREFERENCIADA")
    print("="*70 + "\n")
    
    # Leer el CSV
    print(f"📖 Leyendo archivo: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"✓ {len(df)} objetos encontrados\n")
    
    # Extraer coordenadas de los links
    print("🗺️  Extrayendo coordenadas de los links de Google Maps...")
    df[['latitude', 'longitude']] = df['google_maps_link'].apply(
        lambda x: pd.Series(extract_coords_from_google_maps_link(x))
    )
    
    # Filtrar objetos con coordenadas válidas
    df_with_coords = df.dropna(subset=['latitude', 'longitude'])
    
    print(f"✓ {len(df_with_coords)} objetos tienen coordenadas válidas")
    print(f"✗ {len(df) - len(df_with_coords)} objetos sin coordenadas\n")
    
    if len(df_with_coords) == 0:
        print("⚠️  No hay objetos con coordenadas para visualizar")
        return
    
    # Calcular el centro del mapa (promedio de coordenadas)
    center_lat = df_with_coords['latitude'].mean()
    center_lon = df_with_coords['longitude'].mean()
    
    print(f"📍 Centro del mapa: {center_lat:.4f}, {center_lon:.4f}\n")
    
    # Crear el mapa base
    print("🗺️  Creando mapa interactivo...")
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Colores por categoría
    category_colors = {
        'Painting': 'red',
        'Sculpture': 'blue',
        'Metal products': 'green',
        'Ceramic products': 'orange',
        'Stone products': 'purple',
        'Weapon': 'darkred',
        'Bone products': 'lightgray',
        'Numismatic': 'gold',
        'Jewelry products': 'pink',
        'Architectural details': 'brown',
        'Glass objects': 'lightblue',
        'Wood products': 'beige',
        'Graphics': 'lightgreen',
        'Furniture': 'darkblue',
        'Books': 'cadetblue',
        'Icon': 'lightred',
    }
    
    # Agregar marcadores para cada objeto
    marker_cluster = plugins.MarkerCluster()
    
    for idx, row in df_with_coords.iterrows():
        # Preparar el popup con información del objeto
        popup_html = f"""
        <div style="width: 300px;">
            <h4 style="margin-bottom: 10px;">{row.get('name', 'Sin nombre')}</h4>
            <hr>
            <p><strong>Categoría:</strong> {row.get('category', 'N/A')}</p>
            <p><strong>Tipo:</strong> {row.get('type', 'N/A')}</p>
            <p><strong>Autor:</strong> {row.get('author', 'N/A')}</p>
            <p><strong>Fecha:</strong> {row.get('date', 'N/A')}</p>
            <p><strong>Año del incidente:</strong> {row.get('year_incident', 'N/A')}</p>
            <p><strong>Lugar:</strong> {row.get('place_incident', 'N/A')}</p>
            <p><strong>Circunstancias:</strong><br>{row.get('circumstances', 'N/A')[:200]}...</p>
            <p><a href="{row.get('url', '#')}" target="_blank">Ver detalles completos</a></p>
        </div>
        """
        
        # Color según categoría
        color = category_colors.get(row.get('category'), 'gray')
        
        # Crear marcador
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row.get('name', 'Sin nombre')[:50],
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(marker_cluster)
    
    marker_cluster.add_to(m)
    
    # Agregar leyenda
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: auto; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
        <h4 style="margin-top:0">Categorías</h4>
    '''
    
    categories_in_data = df_with_coords['category'].unique()
    for cat in sorted(categories_in_data):
        color = category_colors.get(cat, 'gray')
        legend_html += f'<p><i class="fa fa-map-marker" style="color:{color}"></i> {cat}</p>'
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Guardar el mapa
    output_file = 'mapa_objetos_robados_ucrania.html'
    m.save(output_file)
    
    print(f"✓ Mapa guardado: {output_file}\n")
    
    # Estadísticas
    print("="*70)
    print("ESTADÍSTICAS DE GEOREFERENCIACIÓN")
    print("="*70)
    print(f"\nObjetos por categoría (con coordenadas):")
    category_counts = df_with_coords['category'].value_counts()
    for cat, count in category_counts.items():
        print(f"  {cat}: {count}")
    
    print(f"\nObjetos por año del incidente:")
    year_counts = df_with_coords['year_incident'].value_counts()
    for year, count in year_counts.items():
        print(f"  {year}: {count}")
    
    print("\n" + "="*70)
    print("✓ Visualización completada")
    print(f"✓ Abre '{output_file}' en tu navegador para ver el mapa")
    print("="*70 + "\n")
    
    return df_with_coords

# Ejecutar
if __name__ == "__main__":
    # Asegúrate de tener instalado folium: pip install folium
    
    # Cambiar por el nombre de tu archivo CSV
    csv_filename = 'data/stolen_objects_ukraine.csv'  # o 'stolen_objects_ukraine.csv'
    
    try:
        df_coords = create_map_visualization(csv_filename)
        
        # Opcional: guardar también un CSV con las coordenadas extraídas
        if df_coords is not None and len(df_coords) > 0:
            output_csv = 'objetos_con_coordenadas.csv'
            df_coords.to_csv(output_csv, index=False)
            print(f"📁 CSV con coordenadas guardado: {output_csv}\n")
            
    except FileNotFoundError:
        print(f"\n✗ ERROR: No se encontró el archivo '{csv_filename}'")
        print("Asegúrate de haber ejecutado el scraping primero.\n")
    except ImportError:
        print("\n✗ ERROR: No se encontró la librería 'folium'")
        print("Instálala con: pip install folium\n")