"""
WIKIDATA SPARQL QUERY: Ukrainian Artists and Their Works
Query artworks by Ukrainian artists from Wikidata
"""

from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import time

# ============================================================================
# SPARQL ENDPOINT CONFIGURATION
# ============================================================================

def query_wikidata(sparql_query):
    """
    Execute a SPARQL query against Wikidata endpoint
    
    Parameters:
    -----------
    sparql_query : str
        SPARQL query string
    
    Returns:
    --------
    dict or None
        JSON results from Wikidata or None if error
    """
    endpoint = "https://query.wikidata.org/sparql"
    sparql = SPARQLWrapper(endpoint)
    
    # Set query and format
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    
    # Add required User-Agent header
    sparql.addCustomHttpHeader("User-Agent", "UkrainianCulturalHeritageResearch/1.0")
    
    # Set timeout (60 seconds)
    sparql.setTimeout(60)
    
    try:
        print("  Executing query...", end=' ')
        results = sparql.query().convert()
        print("✓")
        return results
    except Exception as e:
        print(f"✗")
        print(f"  Error: {type(e).__name__}: {e}")
        return None

# ============================================================================
# QUERY 1: FAMOUS UKRAINIAN ARTISTS
# ============================================================================

def get_famous_ukrainian_artists():
    """
    Query for famous Ukrainian artists from Wikidata
    
    Returns artists who are:
    - Ukrainian nationals (P27 = Q212)
    - Have occupation of artist/painter (P106)
    """
    
    query = """
    SELECT DISTINCT ?artist ?artistLabel ?birthDate ?deathDate ?description
    WHERE {
      # Artist is Ukrainian
      ?artist wdt:P27 wd:Q212 .
      
      # Artist's occupation is painter/artist
      {
        ?artist wdt:P106 wd:Q1028181 .  # painter
      }
      UNION
      {
        ?artist wdt:P106 wd:Q483501 .   # artist
      }
      
      # Optional: birth and death dates
      OPTIONAL { ?artist wdt:P569 ?birthDate . }
      OPTIONAL { ?artist wdt:P570 ?deathDate . }
      
      # Get labels in English and Ukrainian
      SERVICE wikibase:label { 
        bd:serviceParam wikibase:language "en,uk,ru" .
        ?artist rdfs:label ?artistLabel .
        ?artist schema:description ?description .
      }
    }
    """
    
    print("\n1️⃣ Querying ALL Ukrainian Artists (no limit)...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            # Convert to DataFrame
            data = []
            for item in bindings:
                data.append({
                    'artist_id': item.get('artist', {}).get('value', '').split('/')[-1],
                    'name': item.get('artistLabel', {}).get('value', ''),
                    'birth_date': item.get('birthDate', {}).get('value', ''),
                    'death_date': item.get('deathDate', {}).get('value', ''),
                    'description': item.get('description', {}).get('value', '')
                })
            
            df = pd.DataFrame(data)
            print(f"  ✓ Found {len(df)} Ukrainian artists")
            return df
        else:
            print("  ⚠ Query returned no results")
            return pd.DataFrame()
    else:
        print("  ✗ Error in Wikidata response")
        return pd.DataFrame()

# ============================================================================
# QUERY 2: ARTWORKS BY UKRAINIAN ARTISTS
# ============================================================================

def get_ukrainian_artworks():
    """
    Query for artworks created by Ukrainian artists
    
    Returns artworks with:
    - Creator (artist) information
    - Creation date
    - Current location/collection
    - Image (if available)
    """
    
    query = """
    SELECT DISTINCT ?artwork ?artworkLabel ?artistLabel ?inception ?collectionLabel ?image
    WHERE {
      # Artwork created by Ukrainian artist
      ?artwork wdt:P170 ?artist .
      ?artist wdt:P27 wd:Q212 .        # Artist is Ukrainian
      
      # Artwork is a painting or artwork
      {
        ?artwork wdt:P31 wd:Q3305213 . # painting
      }
      UNION
      {
        ?artwork wdt:P31 wd:Q838948 .  # work of art
      }
      
      # Optional fields
      OPTIONAL { ?artwork wdt:P571 ?inception . }     # inception date
      OPTIONAL { ?artwork wdt:P195 ?collection . }    # collection
      OPTIONAL { ?artwork wdt:P18 ?image . }          # image
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk". }
    }
    """
    
    print("\n2️⃣ Querying ALL Artworks by Ukrainian Artists (no limit)...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            # Convert to DataFrame
            data = []
            for item in bindings:
                data.append({
                    'artwork_id': item.get('artwork', {}).get('value', '').split('/')[-1],
                    'artwork_name': item.get('artworkLabel', {}).get('value', ''),
                    'artist': item.get('artistLabel', {}).get('value', ''),
                    'year': item.get('inception', {}).get('value', ''),
                    'collection': item.get('collectionLabel', {}).get('value', ''),
                    'image_url': item.get('image', {}).get('value', '')
                })
            
            df = pd.DataFrame(data)
            print(f"  ✓ Found {len(df)} artworks")
            return df
        else:
            print("  ⚠ Query returned no results")
            return pd.DataFrame()
    else:
        print("  ✗ Error in Wikidata response")
        return pd.DataFrame()

# ============================================================================
# QUERY 3: SPECIFIC FAMOUS ARTISTS' WORKS
# ============================================================================

def get_works_by_famous_artists():
    """
    Query works by specific famous Ukrainian artists:
    - Maria Prymachenko (Q234496)
    - Mykola Pymonenko (Q2066793)
    - Oleksandra Ekster (Q234661)
    - Oleksandr Bohomazov (Q4095345)
    """
    
    query = """
    SELECT DISTINCT ?artwork ?artworkLabel ?artistLabel ?artistQID ?inception ?collectionLabel
    WHERE {
      # Specific famous Ukrainian artists
      VALUES ?artist {
        wd:Q234496   # Maria Prymachenko
        wd:Q2066793  # Mykola Pymonenko
        wd:Q234661   # Oleksandra Ekster
        wd:Q4095345  # Oleksandr Bohomazov
      }
      
      # Artworks by these artists
      ?artwork wdt:P170 ?artist .
      
      # Optional information
      OPTIONAL { ?artwork wdt:P571 ?inception . }
      OPTIONAL { ?artwork wdt:P195 ?collection . }
      
      # Get artist Wikidata ID
      BIND(STRAFTER(STR(?artist), "http://www.wikidata.org/entity/") AS ?artistQID)
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en,uk". }
    }
    """
    
    print("\n3️⃣ Querying ALL Works by Famous Ukrainian Artists (no limit)...")
    results = query_wikidata(query)
    
    if results and 'results' in results and 'bindings' in results['results']:
        bindings = results['results']['bindings']
        if bindings:
            # Convert to DataFrame
            data = []
            for item in bindings:
                data.append({
                    'artwork_id': item.get('artwork', {}).get('value', '').split('/')[-1],
                    'artwork_name': item.get('artworkLabel', {}).get('value', ''),
                    'artist': item.get('artistLabel', {}).get('value', ''),
                    'artist_qid': item.get('artistQID', {}).get('value', ''),
                    'year': item.get('inception', {}).get('value', ''),
                    'collection': item.get('collectionLabel', {}).get('value', '')
                })
            
            df = pd.DataFrame(data)
            print(f"  ✓ Found {len(df)} artworks by famous artists")
            return df
        else:
            print("  ⚠ Query returned no results")
            return pd.DataFrame()
    else:
        print("  ✗ Error in Wikidata response")
        return pd.DataFrame()

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("WIKIDATA SPARQL: UKRAINIAN ARTISTS AND ARTWORKS")
    print("="*70)
    
    # Query 1: Ukrainian Artists
    artists_df = get_famous_ukrainian_artists()
    time.sleep(2)  # Respect Wikidata rate limits
    
    if not artists_df.empty:
        print("\n📊 Sample Artists:")
        print(artists_df[['name', 'birth_date', 'description']].head(10))
        
        # Save to CSV
        artists_df.to_csv('wikidata_ukrainian_artists.csv', index=False, encoding='utf-8')
        print("\n✓ Saved: wikidata_ukrainian_artists.csv")
    
    # Query 2: All artworks by Ukrainian artists
    artworks_df = get_ukrainian_artworks()
    time.sleep(2)
    
    if not artworks_df.empty:
        print("\n📊 Sample Artworks:")
        print(artworks_df[['artwork_name', 'artist', 'year']].head(10))
        
        # Save to CSV
        artworks_df.to_csv('wikidata_ukrainian_artworks.csv', index=False, encoding='utf-8')
        print("\n✓ Saved: wikidata_ukrainian_artworks.csv")
    
    # Query 3: Famous artists' works
    famous_works_df = get_works_by_famous_artists()
    time.sleep(2)
    
    if not famous_works_df.empty:
        print("\n📊 Works by Famous Artists:")
        print(famous_works_df[['artwork_name', 'artist']].head(10))
        
        # Save to CSV
        famous_works_df.to_csv('wikidata_famous_artists_works.csv', index=False, encoding='utf-8')
        print("\n✓ Saved: wikidata_famous_artists_works.csv")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Ukrainian Artists Found: {len(artists_df)}")
    print(f"Artworks Found: {len(artworks_df)}")
    print(f"Famous Artists' Works: {len(famous_works_df)}")
    
    print("\n" + "="*70)
    print("✅ QUERIES COMPLETED")
    print("="*70)
    print("\nInstallation required:")
    print("  pip install SPARQLWrapper pandas")
    print("\nFiles created:")
    if not artists_df.empty:
        print("  - wikidata_ukrainian_artists.csv")
    if not artworks_df.empty:
        print("  - wikidata_ukrainian_artworks.csv")
    if not famous_works_df.empty:
        print("  - wikidata_famous_artists_works.csv")
    print("="*70)