import requests
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
import time

# ============================================================================
# CONSULTAS SPARQL A WIKIDATA
# ============================================================================

def query_wikidata(sparql_query):
    """Ejecuta una consulta SPARQL en Wikidata"""
    
    endpoint = "https://query.wikidata.org/sparql"
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(60)  # Timeout de 60 segundos
    
    # User agent requerido por Wikidata
    sparql.addCustomHttpHeader("User-Agent", "UkraineCulturalHeritageBot/1.0")
    
    try:
        print("  Ejecutando consulta...", end=' ')
        results = sparql.query().convert()
        print("✓")
        return results
    except Exception as e:
        print(f"✗")
        print(f"  Error detallado: {type(e).__name__}: {e}")
        return None

# ============================================================================
# QUERY 1: Obras de arte ucranianas en Wikidata
# ============================================================================

def get_ukrainian_artworks():
    """Obtiene obras de arte ucranianas de Wikidata"""
    
    # Consulta simplificada para evitar timeout
    query = """
    SELECT DISTINCT ?item ?itemLabel ?creatorLabel ?typeLabel ?inception
    WHERE {
      # Obras de arte de Ucrania
      ?item wdt:P31/wdt:P279* wd:Q838948 .  # instancia de obra de arte
      ?item wdt:P17 wd:Q212 .                # país: Ucrania
      
      OPTIONAL { ?item wdt:P170 ?creator . }    # creador
      OPTIONAL { ?item wdt:P31 ?type . }        # tipo
      OPTIONAL { ?item wdt:P571 ?inception . }  # fecha de creación
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk". }
    }
    LIMIT 500
    """
    
    print("\n1. Consultando obras de arte ucranianas en Wikidata...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            df = pd.json_normalize(bindings)
            print(f"  ✓ Encontradas {len(df)} obras de arte")
            return df
        else:
            print("  ⚠ La consulta no devolvió resultados")
            return pd.DataFrame()
    else:
        print("  ✗ Error en la respuesta de Wikidata")
        return pd.DataFrame()

# ============================================================================
# QUERY 2: Museos ucranianos y sus colecciones
# ============================================================================

def get_ukrainian_museums():
    """Obtiene museos ucranianos y sus coordenadas"""
    
    query = """
    SELECT DISTINCT ?museum ?museumLabel ?coord ?locationLabel
    WHERE {
      ?museum wdt:P31/wdt:P279* wd:Q33506 .    # instancia de museo
      ?museum wdt:P17 wd:Q212 .                 # país: Ucrania
      
      OPTIONAL { ?museum wdt:P625 ?coord . }    # coordenadas
      OPTIONAL { ?museum wdt:P131 ?location . } # ubicación administrativa
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk". }
    }
    LIMIT 500
    """
    
    print("\n2. Consultando museos ucranianos en Wikidata...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            df = pd.json_normalize(bindings)
            print(f"  ✓ Encontrados {len(df)} museos")
            return df
        else:
            print("  ⚠ La consulta no devolvió resultados")
            return pd.DataFrame()
    else:
        print("  ✗ Error en la respuesta de Wikidata")
        return pd.DataFrame()

# ============================================================================
# QUERY MEJORADA: Patrimonio cultural ucraniano (para cruzar con robados)
# ============================================================================

def get_all_ukrainian_cultural_objects():
    """Obtiene TODOS los objetos culturales ucranianos de Wikidata"""
    
    query = """
    SELECT DISTINCT ?item ?itemLabel ?typeLabel ?creatorLabel ?locationLabel ?collectionLabel ?image
    WHERE {
      # Diferentes tipos de patrimonio cultural
      VALUES ?culturalType {
        wd:Q3305213   # pintura
        wd:Q860861    # escultura
        wd:Q4989906   # monumento
        wd:Q220659    # ícono religioso
        wd:Q8192      # libro
        wd:Q11424     # película
        wd:Q838948    # obra de arte (general)
      }
      
      ?item wdt:P31/wdt:P279* ?culturalType .  # es un tipo de objeto cultural
      ?item wdt:P17 wd:Q212 .                   # país: Ucrania
      
      OPTIONAL { ?item wdt:P31 ?type . }
      OPTIONAL { ?item wdt:P170 ?creator . }
      OPTIONAL { ?item wdt:P276 ?location . }
      OPTIONAL { ?item wdt:P195 ?collection . }
      OPTIONAL { ?item wdt:P18 ?image . }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru". }
    }
    LIMIT 1000
    """
    
    print("\n📚 Consultando TODO el patrimonio cultural ucraniano en Wikidata...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            df = pd.json_normalize(bindings)
            print(f"  ✓ Encontrados {len(df)} objetos culturales")
            return df
        else:
            print("  ⚠ La consulta no devolvió resultados")
            return pd.DataFrame()
    else:
        print("  ✗ Error en la respuesta de Wikidata")
        return pd.DataFrame()

# ============================================================================
# QUERY ESPECÍFICA: Obras de artistas ucranianos conocidos
# ============================================================================

def get_works_by_ukrainian_artists():
    """Obtiene obras de artistas ucranianos (más probable que estén robadas)"""
    
    query = """
    SELECT DISTINCT ?item ?itemLabel ?artistLabel ?artistQID ?inception ?collectionLabel ?image
    WHERE {
      # Artista ucraniano
      ?artist wdt:P27 wd:Q212 .        # nacionalidad: Ucrania
      ?artist wdt:P106/wdt:P279* wd:Q483501 .  # ocupación: artista
      
      # Obra del artista
      ?item wdt:P170 ?artist .
      ?item wdt:P31/wdt:P279* wd:Q838948 .  # es obra de arte
      
      OPTIONAL { ?item wdt:P571 ?inception . }
      OPTIONAL { ?item wdt:P195 ?collection . }
      OPTIONAL { ?item wdt:P18 ?image . }
      
      BIND(STRAFTER(STR(?artist), "http://www.wikidata.org/entity/") AS ?artistQID)
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru". }
    }
    LIMIT 1000
    """
    
    print("\n🎨 Consultando obras de artistas ucranianos en Wikidata...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            df = pd.json_normalize(bindings)
            print(f"  ✓ Encontradas {len(df)} obras de artistas ucranianos")
            return df
        else:
            print("  ⚠ La consulta no devolvió resultados")
            return pd.DataFrame()
    else:
        print("  ✗ Error en la respuesta de Wikidata")
        return pd.DataFrame()

# ============================================================================
# QUERY: Colecciones de museos ucranianos
# ============================================================================

def get_museum_collections():
    """Obtiene objetos que estaban en museos ucranianos"""
    
    query = """
    SELECT DISTINCT ?item ?itemLabel ?museumLabel ?typeLabel
    WHERE {
      # Museo ucraniano
      ?museum wdt:P31/wdt:P279* wd:Q33506 .  # es un museo
      ?museum wdt:P17 wd:Q212 .               # en Ucrania
      
      # Objeto en la colección del museo
      ?item wdt:P195 ?museum .
      
      OPTIONAL { ?item wdt:P31 ?type . }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk,ru". }
    }
    LIMIT 1000
    """
    
    print("\n🏛️ Consultando colecciones de museos ucranianos en Wikidata...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            df = pd.json_normalize(bindings)
            print(f"  ✓ Encontrados {len(df)} objetos en museos")
            return df
        else:
            print("  ⚠ La consulta no devolvió resultados")
            return pd.DataFrame()
    else:
        print("  ✗ Error en la respuesta de Wikidata")
        return pd.DataFrame()

# ============================================================================
# QUERY 4: Pinturas específicas de artistas ucranianos famosos
# ============================================================================

def get_ukrainian_artists_works():
    """Obtiene obras de artistas ucranianos específicos"""
    
    query = """
    SELECT DISTINCT ?item ?itemLabel ?artistLabel ?collectionLabel
    WHERE {
      # Artistas ucranianos famosos
      VALUES ?artist {
        wd:Q234496   # Maria Prymachenko
        wd:Q2066793  # Mykola Pymonenko
        wd:Q234661   # Oleksandra Ekster
        wd:Q4095345  # Oleksandr Bohomazov
      }
      
      ?item wdt:P170 ?artist .          # creado por el artista
      
      OPTIONAL { ?item wdt:P195 ?collection . }
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk". }
    }
    LIMIT 500
    """
    
    print("\n4. Consultando obras de artistas ucranianos famosos en Wikidata...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            df = pd.json_normalize(bindings)
            print(f"  ✓ Encontradas {len(df)} obras")
            return df
        else:
            print("  ⚠ La consulta no devolvió resultados")
            return pd.DataFrame()
    else:
        print("  ✗ Error en la respuesta de Wikidata")
        return pd.DataFrame()

# ============================================================================
# CRUZAR CON DATOS LOCALES
# ============================================================================

def cross_reference_with_local_data(wikidata_df, local_csv='raw_data/stolen_objects_ukraine.csv'):
    """Cruza datos de Wikidata con el CSV local de objetos robados - MEJORADO"""
    
    print("\n" + "="*70)
    print("🔍 CRUZANDO WIKIDATA CON OBJETOS ROBADOS")
    print("="*70)
    
    try:
        local_df = pd.read_csv(local_csv)
        print(f"✓ CSV local cargado: {len(local_df)} objetos robados")
    except:
        print("✗ No se pudo cargar el CSV local")
        return pd.DataFrame()
    
    # Limpiar y normalizar nombres
    def normalize_name(text):
        if pd.isna(text):
            return ''
        text = str(text).lower().strip()
        # Remover caracteres especiales pero mantener espacios
        import re
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    # Preparar Wikidata
    if 'itemLabel.value' in wikidata_df.columns:
        wikidata_df['name_norm'] = wikidata_df['itemLabel.value'].apply(normalize_name)
    else:
        print("⚠ No se encontró columna itemLabel en Wikidata")
        return pd.DataFrame()
    
    # Preparar datos locales
    if 'name' in local_df.columns:
        local_df['name_norm'] = local_df['name'].apply(normalize_name)
    
    if 'author' in local_df.columns:
        local_df['author_norm'] = local_df['author'].apply(normalize_name)
    
    # Preparar autor de Wikidata
    if 'creatorLabel.value' in wikidata_df.columns:
        wikidata_df['creator_norm'] = wikidata_df['creatorLabel.value'].apply(normalize_name)
    elif 'artistLabel.value' in wikidata_df.columns:
        wikidata_df['creator_norm'] = wikidata_df['artistLabel.value'].apply(normalize_name)
    
    print(f"\nBuscando coincidencias...")
    matches = []
    
    # Estrategia 1: Coincidencia exacta de nombre
    for idx, wiki_row in wikidata_df.iterrows():
        if pd.isna(wiki_row['name_norm']) or wiki_row['name_norm'] == '':
            continue
        
        # Buscar por nombre exacto
        exact_matches = local_df[local_df['name_norm'] == wiki_row['name_norm']]
        
        if len(exact_matches) > 0:
            for _, local_row in exact_matches.iterrows():
                matches.append({
                    'match_type': 'exact_name',
                    'confidence': 'HIGH',
                    'wikidata_item': wiki_row.get('item.value', ''),
                    'wikidata_name': wiki_row.get('itemLabel.value', ''),
                    'wikidata_creator': wiki_row.get('creatorLabel.value', '') or wiki_row.get('artistLabel.value', ''),
                    'stolen_id': local_row.get('id', ''),
                    'stolen_name': local_row.get('name', ''),
                    'stolen_author': local_row.get('author', ''),
                    'stolen_category': local_row.get('category', ''),
                    'stolen_year': local_row.get('year_incident', ''),
                })
        
        # Estrategia 2: Coincidencia por autor si existe
        if 'creator_norm' in wiki_row and 'author_norm' in local_df.columns:
            if pd.notna(wiki_row['creator_norm']) and wiki_row['creator_norm'] != '':
                author_matches = local_df[
                    (local_df['author_norm'] == wiki_row['creator_norm']) &
                    (local_df['author_norm'] != '')
                ]
                
                for _, local_row in author_matches.iterrows():
                    # Evitar duplicados
                    already_matched = any(
                        m['wikidata_item'] == wiki_row.get('item.value', '') and 
                        m['stolen_id'] == local_row.get('id', '')
                        for m in matches
                    )
                    
                    if not already_matched:
                        matches.append({
                            'match_type': 'same_author',
                            'confidence': 'MEDIUM',
                            'wikidata_item': wiki_row.get('item.value', ''),
                            'wikidata_name': wiki_row.get('itemLabel.value', ''),
                            'wikidata_creator': wiki_row.get('creatorLabel.value', '') or wiki_row.get('artistLabel.value', ''),
                            'stolen_id': local_row.get('id', ''),
                            'stolen_name': local_row.get('name', ''),
                            'stolen_author': local_row.get('author', ''),
                            'stolen_category': local_row.get('category', ''),
                            'stolen_year': local_row.get('year_incident', ''),
                        })
    
    matches_df = pd.DataFrame(matches)
    
    print(f"\n{'='*70}")
    print(f"✓ RESULTADOS DEL CRUCE")
    print(f"{'='*70}")
    print(f"Total de coincidencias: {len(matches_df)}")
    
    if len(matches_df) > 0:
        print(f"\nPor tipo de coincidencia:")
        print(matches_df['match_type'].value_counts())
        
        print(f"\nPor nivel de confianza:")
        print(matches_df['confidence'].value_counts())
        
        print(f"\nPrimeras 5 coincidencias:")
        for idx, match in matches_df.head(5).iterrows():
            print(f"\n  {idx+1}. {match['wikidata_name']}")
            print(f"     → Robado: {match['stolen_name']}")
            print(f"     → Confianza: {match['confidence']}")
    
    return matches_df

# ============================================================================
# GUARDAR RESULTADOS
# ============================================================================

def save_wikidata_results(artworks, museums, looted, artists_works, matches):
    """Guarda todos los resultados en CSVs"""
    
    print("\n" + "="*70)
    print("GUARDANDO RESULTADOS DE WIKIDATA")
    print("="*70)
    
    files_created = []
    
    if not artworks.empty:
        artworks.to_csv('wikidata_ukrainian_artworks.csv', index=False, encoding='utf-8')
        print("✓ wikidata_ukrainian_artworks.csv ({} obras)".format(len(artworks)))
        files_created.append('wikidata_ukrainian_artworks.csv')
    else:
        print("⚠ No hay obras de arte para guardar")
    
    if not museums.empty:
        museums.to_csv('wikidata_ukrainian_museums.csv', index=False, encoding='utf-8')
        print("✓ wikidata_ukrainian_museums.csv ({} museos)".format(len(museums)))
        files_created.append('wikidata_ukrainian_museums.csv')
    else:
        print("⚠ No hay museos para guardar")
    
    if not looted.empty:
        looted.to_csv('wikidata_looted_items.csv', index=False, encoding='utf-8')
        print("✓ wikidata_looted_items.csv ({} objetos)".format(len(looted)))
        files_created.append('wikidata_looted_items.csv')
    else:
        print("⚠ No hay objetos robados para guardar")
    
    if not artists_works.empty:
        artists_works.to_csv('wikidata_artists_works.csv', index=False, encoding='utf-8')
        print("✓ wikidata_artists_works.csv ({} obras)".format(len(artists_works)))
        files_created.append('wikidata_artists_works.csv')
    else:
        print("⚠ No hay obras de artistas para guardar")
    
    if not matches.empty:
        matches.to_csv('wikidata_local_matches.csv', index=False, encoding='utf-8')
        print("✓ wikidata_local_matches.csv ({} coincidencias)".format(len(matches)))
        files_created.append('wikidata_local_matches.csv')
    else:
        print("⚠ No hay coincidencias para guardar")
    
    return files_created

# ============================================================================
# EJECUTAR
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🇺🇦 WIKIDATA: PATRIMONIO CULTURAL UCRANIANO")
    print("="*70)
    print("\nEste script obtiene datos de Wikidata y los cruza con")
    print("los objetos robados para identificar coincidencias.\n")
    
    # Consultas principales
    cultural_objects = get_all_ukrainian_cultural_objects()
    time.sleep(3)
    
    artists_works = get_works_by_ukrainian_artists()
    time.sleep(3)
    
    museum_items = get_museum_collections()
    time.sleep(3)
    
    museums = get_ukrainian_museums()
    time.sleep(3)
    
    # Combinar todos los objetos culturales
    all_objects = pd.DataFrame()
    
    if not cultural_objects.empty:
        all_objects = pd.concat([all_objects, cultural_objects], ignore_index=True)
    
    if not artists_works.empty:
        all_objects = pd.concat([all_objects, artists_works], ignore_index=True)
    
    if not museum_items.empty:
        all_objects = pd.concat([all_objects, museum_items], ignore_index=True)
    
    # Eliminar duplicados
    if not all_objects.empty and 'item.value' in all_objects.columns:
        before = len(all_objects)
        all_objects = all_objects.drop_duplicates(subset=['item.value'])
        after = len(all_objects)
        print(f"\n📊 Total objetos culturales únicos en Wikidata: {after}")
        print(f"   (se eliminaron {before - after} duplicados)")
    
    # Cruzar con datos locales
    matches = pd.DataFrame()
    if not all_objects.empty:
        try:
            matches = cross_reference_with_local_data(all_objects)
        except FileNotFoundError:
            print("\n⚠ No se encontró stolen_objects_ukraine.csv")
            print("  Coloca el archivo en la misma carpeta y ejecuta de nuevo")
    
    # Guardar resultados
    print("\n" + "="*70)
    print("💾 GUARDANDO RESULTADOS")
    print("="*70)
    
    files_created = []
    
    if not all_objects.empty:
        all_objects.to_csv('wikidata_ukrainian_cultural_heritage.csv', index=False, encoding='utf-8')
        print(f"✓ wikidata_ukrainian_cultural_heritage.csv ({len(all_objects)} objetos)")
        files_created.append('wikidata_ukrainian_cultural_heritage.csv')
    
    if not museums.empty:
        museums.to_csv('wikidata_ukrainian_museums.csv', index=False, encoding='utf-8')
        print(f"✓ wikidata_ukrainian_museums.csv ({len(museums)} museos)")
        files_created.append('wikidata_ukrainian_museums.csv')
    
    if not matches.empty:
        matches.to_csv('wikidata_stolen_matches.csv', index=False, encoding='utf-8')
        print(f"✓ wikidata_stolen_matches.csv ({len(matches)} coincidencias) ⭐ IMPORTANTE")
        files_created.append('wikidata_stolen_matches.csv')
    
    print("\n" + "="*70)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*70)
    
    if matches.empty:
        print("\n❌ No se encontraron coincidencias entre Wikidata y objetos robados")
        print("\nPosibles razones:")
        print("  1. Los nombres en Wikidata y en tu CSV son muy diferentes")
        print("  2. Los objetos robados no están documentados en Wikidata")
        print("  3. Wikidata usa nombres en otros idiomas (ucraniano/ruso)")
        print("\n💡 Sugerencia: Revisa manualmente algunos nombres en ambos archivos")
    else:
        print(f"\n✅ Se encontraron {len(matches)} coincidencias!")
        print("\n📊 Esto significa que:")
        print(f"  - {len(matches)} objetos robados YA estaban en Wikidata")
        print(f"  - Estos objetos tienen documentación internacional")
        print(f"  - Puedes enriquecer tus datos con info de Wikidata")
    
    if files_created:
        print(f"\n📁 Archivos creados ({len(files_created)}):")
        for f in files_created:
            print(f"  - {f}")
    
    print("\n" + "="*70 + "\n")