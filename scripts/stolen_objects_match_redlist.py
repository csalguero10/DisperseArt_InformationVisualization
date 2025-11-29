import pandas as pd
import numpy as np
from datetime import datetime
import re

# ============================================================================
# 1. CARGAR DATOS
# ============================================================================

def load_data():
    """Carga ambos CSVs"""
    print("="*70)
    print("CARGANDO DATOS")
    print("="*70)
    
    # Cargar Red List
    try:
        redlist = pd.read_csv('raw_data/red_list.csv')
        print(f"✓ Red List cargada: {len(redlist)} objetos")
        print(f"  Columnas: {list(redlist.columns)}")
    except FileNotFoundError:
        print("✗ Error: No se encontró 'raw_data/red_list.csv'")
        print("  Por favor guarda el CSV de Red List con ese nombre")
        return None, None
    
    # Cargar objetos robados
    try:
        stolen = pd.read_csv('raw_data/stolen_objects_ukraine.csv')
        print(f"\n✓ Objetos Robados cargados: {len(stolen)} objetos")
        print(f"  Columnas: {list(stolen.columns)}")
    except FileNotFoundError:
        print("\n✗ Error: No se encontró 'stolen_objects_ukraine.csv'")
        return None, None
    
    return redlist, stolen

# ============================================================================
# 2. FUNCIONES DE LIMPIEZA Y NORMALIZACIÓN
# ============================================================================

def normalize_text(text):
    """Normaliza texto para comparación"""
    if pd.isna(text) or text == '':
        return ''
    
    text = str(text).lower().strip()
    # Remover caracteres especiales
    text = re.sub(r'[^\w\s]', '', text)
    # Remover espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_century(date_str):
    """Extrae el siglo de una fecha"""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).lower()
    
    # Buscar patrones como "18th c.", "XIII-XV century", etc.
    century_match = re.search(r'(\d+)(?:th|st|nd|rd)?\s*c', date_str)
    if century_match:
        return int(century_match.group(1))
    
    # Buscar rangos como "XIII-XV"
    roman_match = re.search(r'([xvi]+)', date_str)
    if roman_match:
        # Convertir números romanos (simplificado)
        roman_to_int = {
            'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
            'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
            'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
            'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20
        }
        return roman_to_int.get(roman_match.group(1), None)
    
    # Buscar años específicos
    year_match = re.search(r'(\d{4})', date_str)
    if year_match:
        year = int(year_match.group(1))
        return (year // 100) + 1
    
    return None

# ============================================================================
# 3. CRUCE DE DATOS
# ============================================================================

def find_matches(redlist, stolen):
    """Encuentra coincidencias entre Red List y objetos robados"""
    
    print("\n" + "="*70)
    print("BUSCANDO COINCIDENCIAS")
    print("="*70)
    
    matches = []
    
    # Normalizar campos para comparación
    redlist['title_norm'] = redlist['title'].apply(normalize_text)
    redlist['author_norm'] = redlist['author'].apply(normalize_text)
    redlist['category_norm'] = redlist['category'].apply(normalize_text)
    
    stolen['name_norm'] = stolen['name'].apply(normalize_text)
    stolen['author_norm'] = stolen['author'].apply(normalize_text)
    stolen['type_norm'] = stolen['type'].apply(normalize_text)
    
    print("\nBuscando coincidencias...")
    print("Criterios:")
    print("  1. Coincidencia exacta de nombre/título")
    print("  2. Coincidencia de autor + categoría similar")
    print("  3. Coincidencia parcial de nombre + autor")
    
    for idx, red_obj in redlist.iterrows():
        if idx % 10 == 0:
            print(f"  Procesando objeto {idx+1}/{len(redlist)}...", end='\r')
        
        # Criterio 1: Coincidencia exacta de nombre
        exact_matches = stolen[
            (stolen['name_norm'] == red_obj['title_norm']) & 
            (stolen['name_norm'] != '')
        ]
        
        if len(exact_matches) > 0:
            for _, stolen_obj in exact_matches.iterrows():
                matches.append({
                    'redlist_id': red_obj['ID'],
                    'redlist_title': red_obj['title'],
                    'redlist_author': red_obj['author'],
                    'redlist_category': red_obj['category'],
                    'stolen_id': stolen_obj['id'],
                    'stolen_name': stolen_obj['name'],
                    'stolen_author': stolen_obj['author'],
                    'stolen_type': stolen_obj['type'],
                    'stolen_category': stolen_obj['category'],
                    'match_type': 'exact_name',
                    'confidence': 'high'
                })
            continue
        
        # Criterio 2: Autor + categoría similar
        if red_obj['author_norm'] != '':
            author_matches = stolen[
                (stolen['author_norm'] == red_obj['author_norm']) &
                (stolen['author_norm'] != '')
            ]
            
            for _, stolen_obj in author_matches.iterrows():
                matches.append({
                    'redlist_id': red_obj['ID'],
                    'redlist_title': red_obj['title'],
                    'redlist_author': red_obj['author'],
                    'redlist_category': red_obj['category'],
                    'stolen_id': stolen_obj['id'],
                    'stolen_name': stolen_obj['name'],
                    'stolen_author': stolen_obj['author'],
                    'stolen_type': stolen_obj['type'],
                    'stolen_category': stolen_obj['category'],
                    'match_type': 'author_match',
                    'confidence': 'medium'
                })
        
        # Criterio 3: Coincidencia parcial de nombre (al menos 3 palabras en común)
        if red_obj['title_norm'] != '':
            red_words = set(red_obj['title_norm'].split())
            if len(red_words) >= 3:
                for _, stolen_obj in stolen.iterrows():
                    if stolen_obj['name_norm'] == '':
                        continue
                    
                    stolen_words = set(stolen_obj['name_norm'].split())
                    common_words = red_words & stolen_words
                    
                    if len(common_words) >= 3:
                        matches.append({
                            'redlist_id': red_obj['ID'],
                            'redlist_title': red_obj['title'],
                            'redlist_author': red_obj['author'],
                            'redlist_category': red_obj['category'],
                            'stolen_id': stolen_obj['id'],
                            'stolen_name': stolen_obj['name'],
                            'stolen_author': stolen_obj['author'],
                            'stolen_type': stolen_obj['type'],
                            'stolen_category': stolen_obj['category'],
                            'match_type': 'partial_name',
                            'confidence': 'low',
                            'common_words': len(common_words)
                        })
    
    print(f"\n✓ Búsqueda completada")
    
    return pd.DataFrame(matches)

# ============================================================================
# 4. ANÁLISIS Y ESTADÍSTICAS
# ============================================================================

def analyze_data(redlist, stolen, matches):
    """Genera estadísticas y análisis"""
    
    print("\n" + "="*70)
    print("ESTADÍSTICAS GENERALES")
    print("="*70)
    
    print(f"\nRed List:")
    print(f"  Total objetos: {len(redlist)}")
    print(f"  Categorías: {redlist['category'].nunique()}")
    print(f"  Con autor: {redlist['author'].notna().sum()}")
    
    print(f"\nObjetos Robados:")
    print(f"  Total objetos: {len(stolen)}")
    print(f"  Categorías: {stolen['category'].nunique()}")
    print(f"  Con autor: {stolen['author'].notna().sum()}")
    print(f"  Con coordenadas: {stolen['latitude'].notna().sum()}")
    
    print(f"\nCoincidencias encontradas:")
    print(f"  Total matches: {len(matches)}")
    if len(matches) > 0:
        print(f"  Alta confianza: {len(matches[matches['confidence'] == 'high'])}")
        print(f"  Media confianza: {len(matches[matches['confidence'] == 'medium'])}")
        print(f"  Baja confianza: {len(matches[matches['confidence'] == 'low'])}")
    
    # Análisis por categoría
    print("\n" + "="*70)
    print("ANÁLISIS POR CATEGORÍA")
    print("="*70)
    
    print("\nRed List - Top 10 categorías:")
    category_counts = redlist['category'].value_counts().head(10)
    for cat, count in category_counts.items():
        print(f"  {cat}: {count}")
    
    print("\nObjetos Robados - Top 10 categorías:")
    stolen_category_counts = stolen['category'].value_counts().head(10)
    for cat, count in stolen_category_counts.items():
        print(f"  {cat}: {count}")
    
    # Análisis temporal
    print("\n" + "="*70)
    print("ANÁLISIS TEMPORAL")
    print("="*70)
    
    stolen['year_int'] = pd.to_numeric(stolen['year_incident'], errors='coerce')
    year_distribution = stolen['year_int'].value_counts().sort_index()
    
    print("\nAños con más robos:")
    for year, count in year_distribution.head(10).items():
        print(f"  {int(year)}: {count} objetos")
    
    # Análisis geográfico
    print("\n" + "="*70)
    print("ANÁLISIS GEOGRÁFICO")
    print("="*70)
    
    with_coords = stolen[stolen['latitude'].notna()]
    print(f"\nObjetos con ubicación: {len(with_coords)}")
    
    if len(with_coords) > 0:
        print(f"\nLugares con más robos:")
        place_counts = stolen['place_incident'].value_counts().head(10)
        for place, count in place_counts.items():
            if pd.notna(place):
                print(f"  {place[:60]}: {count}")

# ============================================================================
# 5. EXPORTAR RESULTADOS
# ============================================================================

def export_results(matches, redlist, stolen):
    """Exporta resultados a CSVs"""
    
    print("\n" + "="*70)
    print("EXPORTANDO RESULTADOS")
    print("="*70)
    
    # Guardar coincidencias
    if len(matches) > 0:
        matches.to_csv('matches_redlist_stolen.csv', index=False, encoding='utf-8')
        print(f"✓ Coincidencias guardadas en: matches_redlist_stolen.csv")
    
    # Objetos de Red List que fueron robados (alta confianza)
    if len(matches) > 0:
        high_confidence = matches[matches['confidence'] == 'high']
        if len(high_confidence) > 0:
            high_confidence.to_csv('redlist_confirmed_stolen.csv', index=False, encoding='utf-8')
            print(f"✓ Red List robados (alta confianza): redlist_confirmed_stolen.csv")
    
    # Estadísticas por categoría
    category_stats = pd.DataFrame({
        'redlist_count': redlist['category'].value_counts(),
        'stolen_count': stolen.groupby('category').size()
    }).fillna(0)
    category_stats.to_csv('category_comparison.csv', encoding='utf-8')
    print(f"✓ Comparación por categoría: category_comparison.csv")
    
    # Datos para visualización geográfica
    geo_data = stolen[stolen['latitude'].notna()][
        ['id', 'name', 'category', 'latitude', 'longitude', 
         'place_incident', 'year_incident']
    ]
    geo_data.to_csv('stolen_objects_geo.csv', index=False, encoding='utf-8')
    print(f"✓ Datos geográficos: stolen_objects_geo.csv")
    
    # Timeline de robos
    timeline = stolen.groupby('year_incident').size().reset_index()
    timeline.columns = ['year', 'count']
    timeline = timeline.sort_values('year')
    timeline.to_csv('theft_timeline.csv', index=False, encoding='utf-8')
    print(f"✓ Timeline de robos: theft_timeline.csv")

# ============================================================================
# 6. EJECUTAR ANÁLISIS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ANÁLISIS DE OBJETOS CULTURALES UCRANIANOS")
    print("Red List vs Objetos Robados")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Cargar datos
    redlist, stolen = load_data()
    
    if redlist is None or stolen is None:
        print("\n✗ No se pudieron cargar los datos. Verifica los archivos.")
        exit(1)
    
    # Buscar coincidencias
    matches = find_matches(redlist, stolen)
    
    # Análisis
    analyze_data(redlist, stolen, matches)
    
    # Exportar
    export_results(matches, redlist, stolen)
    
    print("\n" + "="*70)
    print("✓✓✓ ANÁLISIS COMPLETADO ✓✓✓")
    print("="*70)
    print("\nArchivos generados:")
    print("  1. matches_redlist_stolen.csv - Todas las coincidencias")
    print("  2. redlist_confirmed_stolen.csv - Red List confirmados robados")
    print("  3. category_comparison.csv - Comparación por categoría")
    print("  4. stolen_objects_geo.csv - Datos para mapa")
    print("  5. theft_timeline.csv - Timeline de robos")
    print("\n" + "="*70 + "\n")