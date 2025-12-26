"""
WIKIART UKRAINIAN ARTISTS - WORKING SCRAPER
Based on actual Wikiart HTML structure

REQUIREMENTS:
pip install requests beautifulsoup4 pandas lxml

USAGE:
python wikiart_working.py

OUTPUT:
wikiart_ukrainian_artists_detailed.csv
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

print("="*60)
print("WIKIART UKRAINIAN ARTISTS SCRAPER")
print("="*60)

# Configuration
base_url = "https://www.wikiart.org"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Step 1: Get artist list from search/filter
# We'll use the advanced search to get Ukrainian artists
print("\n[STEP 1/3] Getting Ukrainian artists...")

# Try the artists by nation page
nation_url = f"{base_url}/en/artists-by-nation/ukrainian#!#resultType:masonry"
print(f"URL: {nation_url}")

response = requests.get(nation_url, headers=headers)
if response.status_code != 200:
    print(f"✗ Error: Status code {response.status_code}")
    exit(1)

soup = BeautifulSoup(response.content, 'html.parser')

# Based on your screenshot, artist names appear as plain text in breadcrumbs
# or in the page structure. Let's look for artist links in the content.

# Method: Look for links that go to artist pages
# Artist page URLs are like: /en/victor-palmov (lowercase, hyphenated)
artist_links = []
seen_slugs = set()

for link in soup.find_all('a', href=True):
    href = link['href']
    
    # Artist pages match pattern: /en/artist-name
    # Exclude known non-artist patterns
    if href.startswith('/en/') and href.count('/') == 2:
        slug = href.split('/')[-1]
        
        # Exclude non-artist pages
        excluded = [
            'artists-by-nation', 'artists-by-century', 'artists-by-genre',
            'artists-by-painting-school', 'artists-by-art-movement',
            'paintings', 'albums', 'artistadvancedsearch', 'popular-paintings',
            'actionhistory', 'terms-of-use', 'privacy-policy', 'store',
            'account', 'profile', 'app', 'api'
        ]
        
        # Artist slugs are typically lowercase with hyphens, no numbers at start
        is_artist = (
            slug not in excluded and
            slug and
            not slug[0].isdigit() and
            re.match(r'^[a-z0-9-]+$', slug) and
            slug not in seen_slugs
        )
        
        if is_artist:
            artist_url = f"{base_url}{href}"
            artist_links.append(artist_url)
            seen_slugs.add(slug)

print(f"✓ Found {len(artist_links)} potential artist URLs")

if len(artist_links) == 0:
    print("\n✗ No artists found. Trying alternative method...")
    # Alternative: manually construct URLs from known Ukrainian artists
    # This is a fallback if scraping the list page fails
    known_ukrainian_artists = [
        'kazimir-malevich', 'alexandra-exter', 'ivan-aivazovsky',
        'victor-palmov', 'alexander-bogomazov', 'vadym-meller',
        'david-burliuk', 'oleksandr-archipenko', 'sonia-delaunay-terk'
    ]
    for slug in known_ukrainian_artists:
        artist_links.append(f"{base_url}/en/{slug}")
    print(f"Using {len(artist_links)} known Ukrainian artists as fallback")

# Show sample
print("\nFirst 10 artist URLs:")
for url in artist_links[:10]:
    print(f"  - {url}")

# Step 2: Scrape each artist page
print(f"\n[STEP 2/3] Scraping artist details...")
print("This will take several minutes...\n")

artists_data = []

for i, artist_url in enumerate(artist_links, 1):
    try:
        slug = artist_url.split('/')[-1]
        print(f"  [{i:3d}/{len(artist_links)}] {slug:35s}", end='', flush=True)
        
        response = requests.get(artist_url, headers=headers)
        time.sleep(1)  # Rate limiting
        
        if response.status_code != 200:
            print(f" ✗ HTTP {response.status_code}")
            continue
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Verify this is an artist page
        # Based on your screenshot: <div class="wiki-layout-artist-info" itemprop="artist">
        artist_info = soup.find('div', class_='wiki-layout-artist-info')
        
        if not artist_info:
            print(f" ✗ Not artist page")
            continue
        
        artist_data = {
            'url': artist_url,
            'slug': slug
        }
        
        # Name from <h1>
        h1 = soup.find('h1')
        if h1:
            artist_data['name'] = h1.get_text(strip=True)
        
        # Original name from <h2 itemprop="additionalName">
        h2_original = soup.find('h2', itemprop='additionalName')
        if h2_original:
            artist_data['name_original'] = h2_original.get_text(strip=True)
        
        # Wikipedia link from meta tag
        wiki_meta = soup.find('meta', itemprop='sameAs')
        if wiki_meta:
            artist_data['wikipedia'] = wiki_meta.get('content', '')
        
        # Now extract info from the <article> section
        # Based on screenshot: <article> contains <ul> with all the metadata
        article = soup.find('article')
        if article:
            # Find the <ul> inside article
            ul = article.find('ul')
            if ul:
                for li in ul.find_all('li', recursive=False):
                    text = li.get_text(separator=' ', strip=True)
                    
                    # Parse "Label: Value" format
                    if ':' not in text:
                        continue
                    
                    # Split on first colon
                    parts = text.split(':', 1)
                    if len(parts) != 2:
                        continue
                    
                    label = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    # Map labels to columns
                    if 'born' in label:
                        artist_data['born'] = value
                        # Extract year
                        year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', value)
                        if year_match:
                            artist_data['birth_year'] = year_match.group(1)
                        # Extract place (after semicolon or year)
                        place_match = re.search(r'(?:\d{4};\s*|;\s*)(.+)$', value)
                        if place_match:
                            artist_data['birth_place'] = place_match.group(1).strip()
                    
                    elif 'died' in label:
                        artist_data['died'] = value
                        year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', value)
                        if year_match:
                            artist_data['death_year'] = year_match.group(1)
                        place_match = re.search(r'(?:\d{4};\s*|;\s*)(.+)$', value)
                        if place_match:
                            artist_data['death_place'] = place_match.group(1).strip()
                    
                    elif 'nationalit' in label:  # nationality or nationalities
                        artist_data['nationality'] = value
                    
                    elif 'art movement' in label:
                        artist_data['art_movement'] = value
                    
                    elif 'painting school' in label or label == 'school':
                        artist_data['painting_school'] = value
                    
                    elif 'field' in label:
                        artist_data['field'] = value
                    
                    elif 'influenced by' in label:
                        artist_data['influenced_by'] = value
                    
                    elif 'art institution' in label or label == 'institution':
                        artist_data['art_institution'] = value
                    
                    elif 'friend' in label or 'co-worker' in label:
                        artist_data['friends_coworkers'] = value
                    
                    elif 'teacher' in label:
                        artist_data['teachers'] = value
                    
                    elif 'pupil' in label or 'student' in label:
                        artist_data['pupils'] = value
        
        # Count artworks
        # Look for text like "123 artworks"
        for text in soup.stripped_strings:
            if 'artwork' in text.lower():
                match = re.search(r'(\d+)\s+artworks?', text, re.IGNORECASE)
                if match:
                    artist_data['artworks_count'] = match.group(1)
                    break
        
        artists_data.append(artist_data)
        print(" ✓")
        
    except Exception as e:
        print(f" ✗ {str(e)[:30]}")
        continue

print(f"\n✓ Successfully scraped {len(artists_data)} artists")

if len(artists_data) == 0:
    print("\n✗ No artist data collected. Check if the page structure has changed.")
    exit(1)

# Step 3: Create CSV
print(f"\n[STEP 3/3] Creating CSV...")

df = pd.DataFrame(artists_data)

# Reorder columns
column_order = [
    'name', 'name_original', 'slug', 'url',
    'born', 'birth_year', 'birth_place',
    'died', 'death_year', 'death_place',
    'nationality', 'art_movement', 'painting_school',
    'field', 'influenced_by', 'art_institution',
    'teachers', 'pupils', 'friends_coworkers',
    'artworks_count', 'wikipedia'
]

columns = [col for col in column_order if col in df.columns]
df = df[columns]

# Sort by name
if 'name' in df.columns:
    df = df.sort_values('name')

# Save
output_file = 'wikiart_ukrainian_artists_detailed.csv'
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"\n✓ Saved: {output_file}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

print(f"\nTotal artists: {len(df)}")

# Stats
stats = {}
for col in df.columns:
    filled = df[col].notna().sum()
    stats[col] = (filled, filled/len(df)*100)

print("\nColumn completion rates:")
for col, (count, pct) in stats.items():
    print(f"  {col:25s}: {count:3d}/{len(df)} ({pct:5.1f}%)")

# Preview
print("\n" + "="*60)
print("SAMPLE (first 5 artists)")
print("="*60)
preview_cols = [c for c in ['name', 'birth_year', 'death_year', 'art_movement'] if c in df.columns]
if preview_cols:
    print(df[preview_cols].head(5).to_string(index=False))

print("\n✓ Complete!")
print(f"\nOutput file: {output_file}")