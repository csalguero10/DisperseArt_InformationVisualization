"""
DATA CLEANING - UKRAINIAN STOLEN OBJECTS
Cleaning and preprocessing the dataset from web scraping
"""

import pandas as pd
import numpy as np
import re
from urllib.parse import urlparse, parse_qs

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Roman numeral conversion dictionary
ROMAN_TO_INT = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
    'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
    'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
    'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20,
    'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25
}

def remove_double_quotes(text):
    """
    Removes double quotes ("") from text
    Example: 'From the series ""Our Smaller Brothers""' -> 'From the series "Our Smaller Brothers"'
    """
    if pd.isna(text) or text == '':
        return text
    
    text = str(text)
    cleaned = text.replace('""', '"')
    return cleaned

def split_name_original(name):
    """
    Splits name into English and Ukrainian parts
    Example: 'Sick child / Khvora dytyna' -> ('Sick child', 'Khvora dytyna')
    """
    if pd.isna(name) or name == '':
        return name, ''
    
    name = str(name)
    
    # Check if there's a slash separator
    if ' / ' in name:
        parts = name.split(' / ', 1)  # Split only on first occurrence
        return parts[0].strip(), parts[1].strip()
    elif '/' in name:
        parts = name.split('/', 1)
        return parts[0].strip(), parts[1].strip()
    else:
        return name, ''

def roman_to_arabic(roman):
    """Converts Roman numeral to Arabic number"""
    roman = roman.strip().upper()
    if roman in ROMAN_TO_INT:
        return ROMAN_TO_INT[roman]
    return None

def normalize_date(date_str):
    """
    Normalizes dates to YYYY or YYYY-YYYY format
    Handles:
    - Single years: "1840" -> "1840"
    - Year ranges: "1840-1850" -> "1840-1850"
    - Roman numerals: "XVIII century" -> "1701-1800"
    - Century notations: "18th century" -> "1701-1800"
    - Decades: "1840s" -> "1840-1849"
    """
    if pd.isna(date_str) or date_str == '':
        return ''
    
    date_str = str(date_str).strip()
    
    # Pattern 1: Already in YYYY-YYYY format
    if re.match(r'^\d{4}-\d{4}$', date_str):
        return date_str
    
    # Pattern 2: Single year
    if re.match(r'^\d{4}$', date_str):
        return date_str
    
    # Pattern 3: Year range with dash or other separator
    range_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4})', date_str)
    if range_match:
        return f"{range_match.group(1)}-{range_match.group(2)}"
    
    # Pattern 4: Decade (e.g., "1840s")
    decade_match = re.search(r'(\d{3})0s', date_str)
    if decade_match:
        decade_start = decade_match.group(1) + '0'
        decade_end = decade_match.group(1) + '9'
        return f"{decade_start}-{decade_end}"
    
    # Pattern 5: Roman numeral century (e.g., "XVIII century")
    roman_range = re.search(r'([IVX]+)\s*[–—-]\s*([IVX]+)\s*century', date_str, re.IGNORECASE)
    if roman_range:
        century1 = roman_to_arabic(roman_range.group(1))
        century2 = roman_to_arabic(roman_range.group(2))
        if century1 and century2:
            if 'BC' in date_str.upper():
                year1_start = -(century1 * 100 - 99)
                year2_end = -(century2 * 100 - 100)
                return f"{year1_start}-{year2_end} BC"
            else:
                year1_start = (century1 - 1) * 100 + 1
                year2_end = century2 * 100
                return f"{year1_start}-{year2_end}"
    
    # Single Roman numeral century
    roman_match = re.search(r'([IVX]+)\s*century', date_str, re.IGNORECASE)
    if roman_match:
        century = roman_to_arabic(roman_match.group(1))
        if century:
            if 'BC' in date_str.upper():
                year_start = -(century * 100 - 99)
                year_end = -(century * 100 - 100)
                return f"{year_start}-{year_end} BC"
            else:
                year_start = (century - 1) * 100 + 1
                year_end = century * 100
                return f"{year_start}-{year_end}"
    
    # Pattern 6: Numeric century (e.g., "18th century")
    numeric_century_range = re.search(r'(\d+)(?:th|st|nd|rd)?\s*[-–]\s*(\d+)(?:th|st|nd|rd)?\s*centur', date_str, re.IGNORECASE)
    if numeric_century_range:
        cent1 = int(numeric_century_range.group(1))
        cent2 = int(numeric_century_range.group(2))
        year_start = (cent1 - 1) * 100 + 1
        year_end = cent2 * 100
        return f"{year_start}-{year_end}"
    
    numeric_century = re.search(r'(\d+)(?:th|st|nd|rd)?\s*centur', date_str, re.IGNORECASE)
    if numeric_century:
        century = int(numeric_century.group(1))
        year_start = (century - 1) * 100 + 1
        year_end = century * 100
        return f"{year_start}-{year_end}"
    
    # Pattern 7: Just extract any 4-digit year
    year_match = re.search(r'\b(\d{4})\b', date_str)
    if year_match:
        return year_match.group(1)
    
    # If nothing matches, return original
    return date_str

def calculate_midpoint_year(date_normalized):
    """
    Calculate midpoint year from normalized date for timeline visualization
    Examples:
    - "1840-1850" -> 1845
    - "1900" -> 1900
    - "1701-1800" -> 1750.5
    """
    if pd.isna(date_normalized) or date_normalized == '':
        return np.nan
    
    date_str = str(date_normalized).strip()
    
    # Handle BC dates
    if 'BC' in date_str:
        # Remove BC and parse
        date_str = date_str.replace(' BC', '').strip()
        
        # Range format
        if '-' in date_str:
            parts = date_str.split('-')
            try:
                year1 = -abs(int(parts[0]))
                year2 = -abs(int(parts[1]))
                return (year1 + year2) / 2
            except ValueError:
                return np.nan
        else:
            # Single year BC
            try:
                return -abs(int(date_str))
            except ValueError:
                return np.nan
    
    # AD dates
    # Range format: "1840-1850"
    if '-' in date_str:
        parts = date_str.split('-')
        try:
            year1 = int(parts[0])
            year2 = int(parts[1])
            return (year1 + year2) / 2
        except ValueError:
            return np.nan
    
    # Single year: "1900"
    try:
        return float(date_str)
    except ValueError:
        return np.nan

def extract_coordinates_from_google_maps(url):
    """
    Extract latitude and longitude from Google Maps URL
    Supports various Google Maps URL formats
    """
    if pd.isna(url) or url == '':
        return (np.nan, np.nan)
    
    url = str(url)
    
    try:
        # Method 1: Parse query parameters (?q=lat,lon or ?ll=lat,lon)
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Try 'q' parameter
        if 'q' in params:
            coords = params['q'][0].split(',')
            if len(coords) == 2:
                try:
                    lat = float(coords[0].strip())
                    lon = float(coords[1].strip())
                    return (lat, lon)
                except ValueError:
                    pass
        
        # Try 'll' parameter
        if 'll' in params:
            coords = params['ll'][0].split(',')
            if len(coords) == 2:
                try:
                    lat = float(coords[0].strip())
                    lon = float(coords[1].strip())
                    return (lat, lon)
                except ValueError:
                    pass
        
        # Method 2: Extract from URL path (/@lat,lon format)
        at_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if at_match:
            lat = float(at_match.group(1))
            lon = float(at_match.group(2))
            return (lat, lon)
        
        # Method 3: Extract any lat,lon pattern
        coord_match = re.search(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)', url)
        if coord_match:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            return (lat, lon)
        
    except Exception:
        pass
    
    return (np.nan, np.nan)

def clean_text_field(text):
    """Clean text fields by removing extra whitespace and HTML"""
    if pd.isna(text):
        return np.nan
    
    text = str(text)
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove leading/trailing punctuation
    text = text.strip('.,;:!?-_')
    
    # Replace multiple dots/dashes
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'-{2,}', '-', text)
    
    return text if text else np.nan

# ============================================================================
# MAIN CLEANING FUNCTION
# ============================================================================

def clean_stolen_objects(input_file, output_file):
    """
    Main function to clean the stolen objects dataset
    """
    
    print("\n" + "="*70)
    print("DATA CLEANING - UKRAINIAN STOLEN OBJECTS")
    print("="*70 + "\n")
    
    # ========================================================================
    # 1. LOAD DATA
    # ========================================================================
    
    print("📖 Loading dataset...")
    df = pd.read_csv(input_file)
    print(f"✓ {len(df)} objects loaded")
    print(f"✓ Columns: {list(df.columns)}\n")
    
    # Show sample
    print("📋 First 5 rows:")
    print("-"*70)
    print(df[['id', 'name', 'author', 'date']].head(5).to_string(index=False))
    print()
    
    # ========================================================================
    # 2. STANDARDIZE COLUMN NAMES
    # ========================================================================
    
    print("\n" + "="*70)
    print("STANDARDIZING COLUMN NAMES")
    print("="*70 + "\n")
    
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    print(f"✓ Standardized: {list(df.columns)}\n")
    
    # ========================================================================
    # 3. HANDLE MISSING VALUES
    # ========================================================================
    
    print("\n" + "="*70)
    print("ANALYZING MISSING VALUES")
    print("="*70 + "\n")
    
    missing_stats = pd.DataFrame({
        'Column': df.columns,
        'Missing': df.isnull().sum(),
        'Percentage': (df.isnull().sum() / len(df) * 100).round(1)
    })
    missing_stats = missing_stats[missing_stats['Missing'] > 0].sort_values('Percentage', ascending=False)
    
    print("Missing values by column:")
    print(missing_stats.to_string(index=False))
    print()
    
    # Replace empty strings with NaN
    df.replace(['', 'nan', 'None', 'N/A', 'n/a'], np.nan, inplace=True)
    
    # ========================================================================
    # 4. CLEAN TEXT FIELDS
    # ========================================================================
    
    print("\n" + "="*70)
    print("CLEANING TEXT FIELDS")
    print("="*70 + "\n")
    
    # Remove double quotes from name field
    if 'name' in df.columns:
        print("Removing double quotes from names...")
        df['name'] = df['name'].apply(remove_double_quotes)
        print("✓ Double quotes removed\n")
    
    # Split bilingual names (English / Ukrainian)
    if 'name' in df.columns:
        print("Separating English and Ukrainian names...")
        name_parts = df['name'].apply(split_name_original)
        df['name'] = name_parts.apply(lambda x: x[0])
        df['original_name'] = name_parts.apply(lambda x: x[1] if x[1] != '' else np.nan)
        
        has_translation = df['original_name'].notna().sum()
        print(f"✓ {has_translation} objects have Ukrainian translations")
        
        print("\nExamples of name separation:")
        print("-"*70)
        examples = df[df['original_name'].notna()][['name', 'original_name']].head(5)
        for idx, row in examples.iterrows():
            print(f"  English: {row['name']}")
            print(f"  Ukrainian: {row['original_name']}")
            print()
    
    # Clean other text fields
    text_fields = ['author', 'circumstances']
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].apply(clean_text_field)
            print(f"✓ Cleaned '{field}' field")
    
    # ========================================================================
    # 5. NORMALIZE DATES
    # ========================================================================
    
    print("\n" + "="*70)
    print("NORMALIZING DATES")
    print("="*70 + "\n")
    
    if 'date' in df.columns:
        print("Converting various date formats to YYYY or YYYY-YYYY...")
        df['date_normalized'] = df['date'].apply(normalize_date)
        
        has_date = df['date_normalized'].notna() & (df['date_normalized'] != '')
        print(f"✓ {has_date.sum()} dates normalized ({has_date.sum()/len(df)*100:.1f}%)\n")
        
        print("Examples of date normalization:")
        print("-"*70)
        examples = df[has_date][['date', 'date_normalized']].head(5)
        for idx, row in examples.iterrows():
            print(f"  Original: {row['date']}")
            print(f"  Normalized: {row['date_normalized']}")
            print()
        
        # Calculate midpoint for timeline
        print("Calculating midpoint years for timeline visualization...")
        df['year_for_timeline'] = df['date_normalized'].apply(calculate_midpoint_year)
        
        has_timeline = df['year_for_timeline'].notna().sum()
        print(f"✓ {has_timeline} timeline years calculated\n")
        
        print("Timeline year examples:")
        print("-"*70)
        timeline_examples = df[df['year_for_timeline'].notna()][['date', 'date_normalized', 'year_for_timeline']].head(5)
        for idx, row in timeline_examples.iterrows():
            print(f"  Original: {row['date']}")
            print(f"  Normalized: {row['date_normalized']}")
            print(f"  Timeline year: {row['year_for_timeline']}")
            print()
    
    # ========================================================================
    # 6. EXTRACT COORDINATES
    # ========================================================================
    
    print("\n" + "="*70)
    print("EXTRACTING COORDINATES FROM GOOGLE MAPS LINKS")
    print("="*70 + "\n")
    
    if 'google_maps_link' in df.columns:
        url_count = df['google_maps_link'].notna().sum()
        print(f"📍 Found {url_count} Google Maps links\n")
        
        print("Extracting coordinates...")
        coordinates = df['google_maps_link'].apply(extract_coordinates_from_google_maps)
        
        df['latitude'] = coordinates.apply(lambda x: x[0])
        df['longitude'] = coordinates.apply(lambda x: x[1])
        
        success_count = df['latitude'].notna().sum()
        print(f"✓ Successfully extracted {success_count} coordinate pairs")
        print(f"✗ Failed: {url_count - success_count}\n")
        
        if success_count > 0:
            print("Coordinate statistics:")
            print(f"  Latitude range: {df['latitude'].min():.6f} to {df['latitude'].max():.6f}")
            print(f"  Longitude range: {df['longitude'].min():.6f} to {df['longitude'].max():.6f}\n")
            
            print("Sample coordinates:")
            print("-"*70)
            sample = df[df['latitude'].notna()][['place_incident', 'latitude', 'longitude']].head(5)
            for idx, row in sample.iterrows():
                print(f"  {row['place_incident']}")
                print(f"    Coordinates: {row['latitude']:.6f}, {row['longitude']:.6f}")
                print()
    
    # ========================================================================
    # 7. REMOVE DUPLICATES
    # ========================================================================
    
    print("\n" + "="*70)
    print("CHECKING FOR DUPLICATES")
    print("="*70 + "\n")
    
    initial_count = len(df)
    
    if 'id' in df.columns:
        duplicates = df.duplicated(subset=['id'], keep='first')
        df = df[~duplicates].copy()
        removed = duplicates.sum()
        print(f"✓ Removed {removed} duplicate IDs")
    
    print(f"✓ Final count: {len(df)} objects ({len(df)/initial_count*100:.1f}% retained)\n")
    
    # ========================================================================
    # 8. SAVE CLEANED DATA
    # ========================================================================
    
    print("\n" + "="*70)
    print("SAVING CLEANED DATASET")
    print("="*70 + "\n")
    
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✓ Saved to: {output_file}")
    
    # ========================================================================
    # 9. FINAL SUMMARY
    # ========================================================================
    
    print("\n" + "="*70)
    print("CLEANING SUMMARY")
    print("="*70 + "\n")
    
    print(f"Total objects: {len(df)}")
    print(f"Objects with Ukrainian translations: {df['original_name'].notna().sum()}")
    print(f"Objects with normalized dates: {df['date_normalized'].notna().sum()}")
    print(f"Objects with timeline years: {df['year_for_timeline'].notna().sum()}")
    print(f"Objects with coordinates: {df['latitude'].notna().sum()}")
    
    print("\nNew columns added:")
    print("  • original_name (Ukrainian titles)")
    print("  • date_normalized (standardized dates)")
    print("  • year_for_timeline (numeric years)")
    print("  • latitude, longitude (coordinates)")
    
    print("\n" + "="*70)
    print("✅ DATA CLEANING COMPLETED!")
    print("="*70 + "\n")
    
    return df

# ============================================================================
# EXECUTE
# ============================================================================

if __name__ == "__main__":
    # File paths - ADJUST THESE TO YOUR DIRECTORY STRUCTURE
    input_file = '1_stolen_objects_ukraine.csv'
    output_file = '2_stolen_objects_cleaned.csv'
    
    try:
        df_cleaned = clean_stolen_objects(input_file, output_file)
        
        print("🔍 Preview of cleaned data:")
        print("="*70)
        display_cols = ['name', 'author', 'date', 'date_normalized', 'latitude', 'longitude']
        available_cols = [col for col in display_cols if col in df_cleaned.columns]
        print(df_cleaned[available_cols].head(5).to_string(index=False))
        print("\n")
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found '{input_file}'")
        print("   Make sure the file is in the correct directory!")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()