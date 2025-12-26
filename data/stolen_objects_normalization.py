"""
DATA CLEANING SCRIPT - Stolen Objects Ukraine Dataset
Performs the following transformations:
1. Remove double quotes ("") from text fields
2. Split name into 'name' and 'original_name' (English / Ukrainian)
3. Convert year_incident to proper data type
4. Normalize dates (including Roman numerals) to YYYY or YYYY-YYYY format
"""

import pandas as pd
import re
import numpy as np

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
    # Replace "" with "
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
    - Roman numerals: "XVIII century" -> "1700-1799"
    - Century notations: "18th century" -> "1700-1799"
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
    
    # Pattern 5: Roman numeral century (e.g., "XVIII century", "XVIII – XVI century BC")
    # Handle ranges first
    roman_range = re.search(r'([IVX]+)\s*[–—-]\s*([IVX]+)\s*century', date_str, re.IGNORECASE)
    if roman_range:
        century1 = roman_to_arabic(roman_range.group(1))
        century2 = roman_to_arabic(roman_range.group(2))
        if century1 and century2:
            # Handle BC
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
    
    # Pattern 6: Numeric century (e.g., "18th century", "18-19th century")
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

def get_year_for_timeline(date_normalized):
    """
    Extracts a single year value for timeline visualization
    - For single years: returns that year
    - For ranges: returns the midpoint
    - For BC dates: returns negative number
    """
    if pd.isna(date_normalized) or date_normalized == '':
        return np.nan
    
    date_str = str(date_normalized)
    
    # Handle BC dates
    is_bc = 'BC' in date_str
    date_str = date_str.replace(' BC', '')
    
    # Single year
    if re.match(r'^-?\d{4}$', date_str):
        return int(date_str)
    
    # Year range
    range_match = re.match(r'^(-?\d{4})-(-?\d{4})$', date_str)
    if range_match:
        year1 = int(range_match.group(1))
        year2 = int(range_match.group(2))
        # Return midpoint
        return (year1 + year2) // 2
    
    return np.nan

def clean_stolen_objects_dataset(input_file, output_file):
    """Main cleaning function"""
    
    print("\n" + "="*70)
    print("DATA CLEANING - Stolen Objects Ukraine Dataset")
    print("="*70 + "\n")
    
    # Read CSV
    print(f"📖 Reading file: {input_file}")
    df = pd.read_csv(input_file)
    print(f"✓ {len(df)} rows loaded")
    print(f"✓ Columns: {', '.join(df.columns)}\n")
    
    # ========================================
    # STEP 1: Remove double quotes
    # ========================================
    print("🔧 STEP 1: Removing double quotes from text fields...")
    text_columns = ['name', 'author', 'type', 'date', 'circumstances']
    
    for col in text_columns:
        if col in df.columns:
            original_sample = df[col].iloc[0] if len(df) > 0 and pd.notna(df[col].iloc[0]) else ''
            df[col] = df[col].apply(remove_double_quotes)
            cleaned_sample = df[col].iloc[0] if len(df) > 0 and pd.notna(df[col].iloc[0]) else ''
            if original_sample != cleaned_sample:
                print(f"  ✓ {col}: Fixed quotes")
                print(f"    Before: {original_sample[:60]}...")
                print(f"    After:  {cleaned_sample[:60]}...")
    
    print()
    
    # ========================================
    # STEP 2: Split name into name and original_name
    # ========================================
    print("🔧 STEP 2: Splitting name into English and Ukrainian...")
    
    if 'name' in df.columns:
        df[['name', 'original_name']] = df['name'].apply(
            lambda x: pd.Series(split_name_original(x))
        )
        
        # Show statistics
        has_original = df['original_name'].notna() & (df['original_name'] != '')
        print(f"  ✓ {has_original.sum()} objects have Ukrainian names")
        print(f"  ✓ {(~has_original).sum()} objects have only English names")
        
        # Show examples
        if has_original.sum() > 0:
            print("\n  Examples of split names:")
            for idx, row in df[has_original].head(3).iterrows():
                print(f"    • English: {row['name']}")
                print(f"      Ukrainian: {row['original_name']}")
    
    print()
    
    # ========================================
    # STEP 3: Convert year_incident to proper type
    # ========================================
    print("🔧 STEP 3: Converting year_incident to integer...")
    
    if 'year_incident' in df.columns:
        # Show before
        print(f"  Before: dtype = {df['year_incident'].dtype}")
        
        # Convert to integer (coerce errors to NaN)
        df['year_incident'] = pd.to_numeric(df['year_incident'], errors='coerce').astype('Int64')
        
        # Show after
        print(f"  After:  dtype = {df['year_incident'].dtype}")
        print(f"  ✓ Range: {df['year_incident'].min()} - {df['year_incident'].max()}")
        print(f"  ✓ Missing values: {df['year_incident'].isna().sum()}")
    
    print()
    
    # ========================================
    # STEP 4: Normalize dates
    # ========================================
    print("🔧 STEP 4: Normalizing dates (including Roman numerals)...")
    
    if 'date' in df.columns:
        # Create normalized column
        df['date_normalized'] = df['date'].apply(normalize_date)
        
        # Create year_for_timeline column
        df['year_for_timeline'] = df['date_normalized'].apply(get_year_for_timeline)
        
        # Show examples
        print("\n  Examples of date normalization:")
        date_examples = df[df['date'].notna() & (df['date'] != '')][['date', 'date_normalized', 'year_for_timeline']].drop_duplicates('date').head(10)
        
        for idx, row in date_examples.iterrows():
            print(f"    • Original: {row['date']}")
            print(f"      Normalized: {row['date_normalized']}")
            print(f"      Timeline year: {row['year_for_timeline']}")
            print()
        
        # Statistics
        print("  Statistics:")
        print(f"    ✓ {df['date_normalized'].notna().sum()} dates normalized")
        print(f"    ✓ {df['year_for_timeline'].notna().sum()} years extracted for timeline")
        print(f"    ✓ Timeline range: {df['year_for_timeline'].min():.0f} - {df['year_for_timeline'].max():.0f}")
    
    print()
    
    # ========================================
    # SAVE CLEANED DATASET
    # ========================================
    print("💾 Saving cleaned dataset...")
    df.to_csv(output_file, index=False)
    print(f"✓ Saved to: {output_file}")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "="*70)
    print("CLEANING SUMMARY")
    print("="*70)
    print(f"\n📊 Final dataset:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"\n📋 New columns created:")
    print(f"  • original_name - Ukrainian names")
    print(f"  • date_normalized - Standardized dates (YYYY or YYYY-YYYY)")
    print(f"  • year_for_timeline - Single year value for visualizations")
    
    print(f"\n✅ All transformations completed successfully!")
    print("="*70 + "\n")
    
    return df

# Execute
if __name__ == "__main__":
    input_file = 'data/stolen_objects_ukraine.csv'
    output_file = 'data/stolen_objects_ukraine_cleaned.csv'
    
    try:
        df_cleaned = clean_stolen_objects_dataset(input_file, output_file)
        
        # Show first few rows
        print("\n📝 Preview of cleaned data (first 3 rows):")
        print("="*70)
        print(df_cleaned[['name', 'original_name', 'date', 'date_normalized', 'year_for_timeline']].head(3).to_string())
        print("\n")
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found '{input_file}'")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()