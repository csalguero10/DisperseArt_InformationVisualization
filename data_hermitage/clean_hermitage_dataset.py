"""
HERMITAGE DATASET CLEANING SCRIPT
Comprehensive data cleaning for Ukrainian objects from the Hermitage collection

Tasks:
1. Remove unnecessary quotes and trailing commas from object_name
2. Replace periods between words with spaces (e.g., "Coin.Panticapaeum" -> "Coin Panticapaeum")
3. Split material_technique into material and technique columns
4. Normalize dating column and create date_normalized
5. Assign historical period_category based on dates
"""

import pandas as pd
import numpy as np
import re

# Historical periods (same as stolen objects dataset)
HISTORICAL_PERIODS = [
    {'name': 'Paleolithic Period', 'start': -1400000, 'end': -10000, 
     'label': 'Paleolithic Period (c. 1.4 million years ago - 10,000 BC)'},
    {'name': 'Neolithic Period', 'start': -5050, 'end': -2950, 
     'label': 'Neolithic Period (c. 5050 - 2950 BC)'},
    {'name': 'Bronze Age', 'start': -4500, 'end': -1950, 
     'label': 'Bronze Age (c. 4500 - 1950 BC)'},
    {'name': 'Scythian-Sarmatian Era', 'start': -700, 'end': -250, 
     'label': 'Scythian-Sarmatian Era (c. 700 BC - 250 BC)'},
    {'name': 'Greek and Roman Period', 'start': -250, 'end': 375, 
     'label': 'Greek and Roman Period (250 BC - 375 AD)'},
    {'name': 'Migration Period', 'start': 370, 'end': 700, 
     'label': 'Migration Period (370s - 7th century AD)'},
    {'name': 'Early Medieval Period - Bulgar and Khazar Era', 'start': 600, 'end': 900, 
     'label': 'Early Medieval Period - Bulgar and Khazar Era (7th - 9th centuries)'},
    {'name': 'Kievan Rus\' Period', 'start': 839, 'end': 1240, 
     'label': 'Kievan Rus\' Period (839 - 1240)'},
    {'name': 'Mongol Invasion and Domination', 'start': 1239, 'end': 1400, 
     'label': 'Mongol Invasion and Domination (1239 - 14th century)'},
    {'name': 'Kingdom of Galicia-Volhynia/Ruthenia', 'start': 1197, 'end': 1340, 
     'label': 'Kingdom of Galicia-Volhynia/Ruthenia (1197 - 1340)'},
    {'name': 'Lithuanian and Polish Period', 'start': 1340, 'end': 1648, 
     'label': 'Lithuanian and Polish Period (1340 - 1648)'},
    {'name': 'Cossack Hetmanate Period', 'start': 1648, 'end': 1764, 
     'label': 'Cossack Hetmanate Period (1648 - 1764)'},
    {'name': 'Ukraine under the Russian Empire', 'start': 1764, 'end': 1917, 
     'label': 'Ukraine under the Russian Empire (1764 - 1917)'},
    {'name': 'Ukraine\'s First Independence', 'start': 1917, 'end': 1921, 
     'label': 'Ukraine\'s First Independence (1917 - 1921)'},
    {'name': 'Soviet Period', 'start': 1921, 'end': 1991, 
     'label': 'Soviet Period (1921 - 1991)'},
    {'name': 'Independence Period', 'start': 1991, 'end': 2030, 
     'label': 'Independence Period (1991 - present)'}
]

# Roman numeral conversion
ROMAN_TO_INT = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 
    'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
    'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20
}

def clean_object_name(name):
    """Remove unnecessary quotes and trailing commas/periods"""
    if pd.isna(name) or name == '':
        return name
    
    name = str(name).strip()
    
    # Remove outer quotes if they exist
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    
    # Remove trailing comma or period
    name = name.rstrip('.,')
    
    # Replace period between words with space (e.g., "Coin.Panticapaeum" -> "Coin Panticapaeum")
    # But preserve periods at the end of abbreviations
    name = re.sub(r'\.(?=[A-Z])', ' ', name)  # Period before capital letter
    name = re.sub(r'\.(?=[a-z])', ' ', name)  # Period before lowercase letter
    
    return name.strip()

def split_material_technique(mat_tech):
    """
    Split material_technique into materials and techniques
    Materials: clay, iron, bronze, silver, gold, stone, etc.
    Techniques: chipping, blowing, gilding, niello, retouching, etc.
    """
    if pd.isna(mat_tech) or mat_tech == '':
        return '', ''
    
    text = str(mat_tech).lower()
    
    # Common materials
    materials = []
    material_keywords = [
        'clay', 'iron', 'bronze', 'silver', 'gold', 'copper', 'brass',
        'stone', 'limestone', 'sandstone', 'marble', 'granite',
        'bone', 'wood', 'leather', 'fabric', 'glass', 'paste',
        'carnelian', 'amber', 'lignite', 'agate', 'chalcedony',
        'gypsum', 'kashin', 'faience', 'fired clay', 'engobe',
        'pebbles', 'flint', 'obsidian', 'ceramic', 'terracotta',
        'ivory', 'horn', 'shell', 'coral', 'pearl'
    ]
    
    # Common techniques
    techniques = []
    technique_keywords = [
        'chipping', 'blowing', 'gilding', 'niello', 'retouching',
        'glaze', 'glazing', 'stamp', 'stamping', 'watering',
        'painting', 'hand modeling', 'modeling', 'imprint',
        'engraving', 'carving', 'polishing', 'varnish',
        'thread', 'weaving', 'forging', 'casting', 'welding',
        'incision', 'relief', 'embossing', 'inlay', 'enameling'
    ]
    
    # Extract materials
    for material in material_keywords:
        if material in text:
            materials.append(material)
    
    # Extract techniques
    for technique in technique_keywords:
        if technique in text:
            techniques.append(technique)
    
    # Join with commas
    material_str = ', '.join(sorted(set(materials))) if materials else ''
    technique_str = ', '.join(sorted(set(techniques))) if techniques else ''
    
    # If nothing found, return original as material
    if not material_str and not technique_str:
        material_str = mat_tech.strip()
    
    return material_str, technique_str

def roman_to_arabic(roman):
    """Convert Roman numeral to Arabic number"""
    roman = roman.strip().upper()
    return ROMAN_TO_INT.get(roman, None)

def normalize_dating(dating_str):
    """
    Normalize dating strings to standard format
    Examples:
    - "IV centuryBC" -> "IV century BC"
    - "VI - V centuries.BC" -> "VI-V centuries BC"
    - "sec.floor.VIII-VI centuriesBC" -> "VIII-VI centuries BC"
    """
    if pd.isna(dating_str) or dating_str == '':
        return ''
    
    dating = str(dating_str).strip()
    
    # Remove "sec.floor." prefix
    dating = re.sub(r'^sec\.floor\.', '', dating, flags=re.IGNORECASE)
    
    # Normalize BC/BCE formatting
    dating = re.sub(r'BC[eE]?\.?', 'BC', dating)
    dating = re.sub(r'A\.?D\.?', 'AD', dating)
    
    # Add space before BC/AD if missing
    dating = re.sub(r'([IVXLC]+)(BC|AD)', r'\1 \2', dating)
    dating = re.sub(r'(century|centuries|millennium)(BC|AD)', r'\1 \2', dating)
    
    # Normalize "centuryBC" to "century BC"
    dating = re.sub(r'century(\s*)BC', r'century BC', dating, flags=re.IGNORECASE)
    dating = re.sub(r'centuries(\s*)BC', r'centuries BC', dating, flags=re.IGNORECASE)
    
    # Remove extra spaces around dashes
    dating = re.sub(r'\s*-\s*', '-', dating)
    dating = re.sub(r'\s+–\s+', '-', dating)
    
    # Remove trailing periods
    dating = dating.rstrip('.')
    
    # Capitalize century/centuries
    dating = re.sub(r'\bcentury\b', 'century', dating, flags=re.IGNORECASE)
    dating = re.sub(r'\bcenturies\b', 'centuries', dating, flags=re.IGNORECASE)
    
    return dating.strip()

def extract_year_from_dating(dating_normalized):
    """Extract a single year value for timeline from normalized dating"""
    if pd.isna(dating_normalized) or dating_normalized == '':
        return np.nan
    
    text = str(dating_normalized).strip()
    
    # Handle specific year (e.g., "1850", "1920-1930")
    year_match = re.search(r'\b(\d{4})\b', text)
    if year_match:
        return int(year_match.group(1))
    
    # Handle year range (e.g., "1920-1930")
    range_match = re.search(r'(\d{4})-(\d{4})', text)
    if range_match:
        year1 = int(range_match.group(1))
        year2 = int(range_match.group(2))
        return (year1 + year2) // 2
    
    # Handle Roman numeral centuries
    # Single century (e.g., "XIV century", "XIV century BC")
    single_century = re.search(r'\b([IVX]+)\s+century', text, re.IGNORECASE)
    if single_century:
        century_num = roman_to_arabic(single_century.group(1))
        if century_num:
            is_bc = 'BC' in text.upper()
            if is_bc:
                year = -(century_num * 100 - 50)  # Midpoint of BC century
            else:
                year = (century_num - 1) * 100 + 50  # Midpoint of AD century
            return year
    
    # Century range (e.g., "VI-V centuries BC", "XIV-XV centuries")
    century_range = re.search(r'\b([IVX]+)-([IVX]+)\s+centuries', text, re.IGNORECASE)
    if century_range:
        cent1 = roman_to_arabic(century_range.group(1))
        cent2 = roman_to_arabic(century_range.group(2))
        if cent1 and cent2:
            is_bc = 'BC' in text.upper()
            if is_bc:
                year1 = -(cent1 * 100 - 50)
                year2 = -(cent2 * 100 - 50)
            else:
                year1 = (cent1 - 1) * 100 + 50
                year2 = (cent2 - 1) * 100 + 50
            return (year1 + year2) // 2
    
    # Handle millennium (e.g., "V-IV millennium BC")
    millennium_match = re.search(r'([IVX]+)-([IVX]+)\s+millennium', text, re.IGNORECASE)
    if millennium_match:
        mill1 = roman_to_arabic(millennium_match.group(1))
        mill2 = roman_to_arabic(millennium_match.group(2))
        if mill1 and mill2:
            is_bc = 'BC' in text.upper()
            if is_bc:
                year1 = -(mill1 * 1000 - 500)
                year2 = -(mill2 * 1000 - 500)
            else:
                year1 = (mill1 - 1) * 1000 + 500
                year2 = (mill2 - 1) * 1000 + 500
            return (year1 + year2) // 2
    
    return np.nan

def assign_period_category(year):
    """Assign historical period based on year"""
    if pd.isna(year):
        return 'Unknown Period'
    
    year = float(year)
    
    # Find matching periods
    matching_periods = [p for p in HISTORICAL_PERIODS if p['start'] <= year <= p['end']]
    
    if not matching_periods:
        if year < -10000:
            return 'Pre-Neolithic Period'
        elif year > 2030:
            return 'Contemporary Period'
        else:
            return 'Unknown Period'
    
    # Handle overlapping periods
    if len(matching_periods) == 1:
        return matching_periods[0]['label']
    
    period_names = [p['name'] for p in matching_periods]
    
    # Priority rules for overlapping periods
    if 'Mongol Invasion and Domination' in period_names and 'Kingdom of Galicia-Volhynia/Ruthenia' in period_names:
        if year < 1300:
            return next(p['label'] for p in matching_periods if p['name'] == 'Mongol Invasion and Domination')
        else:
            return next(p['label'] for p in matching_periods if p['name'] == 'Kingdom of Galicia-Volhynia/Ruthenia')
    
    if 'Kievan Rus\' Period' in period_names and 'Kingdom of Galicia-Volhynia/Ruthenia' in period_names:
        return next(p['label'] for p in matching_periods if p['name'] == 'Kievan Rus\' Period')
    
    if 'Bronze Age' in period_names and 'Neolithic Period' in period_names:
        return next(p['label'] for p in matching_periods if p['name'] == 'Bronze Age')
    
    return matching_periods[0]['label']

def clean_hermitage_dataset(input_file, output_file):
    """Main cleaning function"""
    
    print("\n" + "="*70)
    print("HERMITAGE DATASET CLEANING")
    print("="*70 + "\n")
    
    # Read CSV
    print(f"📖 Reading file: {input_file}")
    df = pd.read_csv(input_file)
    print(f"✓ {len(df)} objects loaded")
    print(f"✓ Columns: {', '.join(df.columns[:8])}...\n")
    
    # ========================================
    # STEP 1: Clean object_name
    # ========================================
    print("🔧 STEP 1: Cleaning object names...")
    df['object_name'] = df['object_name'].apply(clean_object_name)
    print("  ✓ Removed quotes and trailing punctuation")
    print("  ✓ Replaced periods between words with spaces\n")
    
    # ========================================
    # STEP 2: Split material_technique
    # ========================================
    print("🔧 STEP 2: Splitting material_technique into material and technique...")
    df[['material', 'technique']] = df['material_technique'].apply(
        lambda x: pd.Series(split_material_technique(x))
    )
    
    has_material = df['material'].notna() & (df['material'] != '')
    has_technique = df['technique'].notna() & (df['technique'] != '')
    print(f"  ✓ {has_material.sum()} objects with identified materials")
    print(f"  ✓ {has_technique.sum()} objects with identified techniques\n")
    
    # ========================================
    # STEP 3: Normalize dating
    # ========================================
    print("🔧 STEP 3: Normalizing dating...")
    df['date_normalized'] = df['dating'].apply(normalize_dating)
    
    # Show examples
    print("\n  Examples of normalization:")
    examples = df[df['dating'].notna()][['dating', 'date_normalized']].drop_duplicates('dating').head(5)
    for idx, row in examples.iterrows():
        print(f"    • {row['dating'][:50]}")
        print(f"      → {row['date_normalized']}")
    print()
    
    # ========================================
    # STEP 4: Extract year for timeline
    # ========================================
    print("🔧 STEP 4: Extracting years for timeline...")
    df['year_for_timeline'] = df['date_normalized'].apply(extract_year_from_dating)
    
    has_year = df['year_for_timeline'].notna()
    print(f"  ✓ {has_year.sum()} objects with extracted years")
    if has_year.sum() > 0:
        print(f"  ✓ Timeline range: {df['year_for_timeline'].min():.0f} to {df['year_for_timeline'].max():.0f}\n")
    
    # ========================================
    # STEP 5: Assign period categories
    # ========================================
    print("🔧 STEP 5: Assigning historical periods...")
    df['period_category'] = df['year_for_timeline'].apply(assign_period_category)
    
    period_counts = df['period_category'].value_counts()
    print(f"\n  Period distribution (top 10):")
    for period, count in period_counts.head(10).items():
        print(f"    • {period}: {count} objects")
    print()
    
    # ========================================
    # SAVE
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
    print(f"  • material - Extracted materials")
    print(f"  • technique - Extracted techniques")
    print(f"  • date_normalized - Standardized dates")
    print(f"  • year_for_timeline - Numeric year values")
    print(f"  • period_category - Historical periods")
    
    print(f"\n✅ All transformations completed!")
    print("="*70 + "\n")
    
    return df

# Execute
if __name__ == "__main__":
    input_file = 'data_hermitage/hermitage_ukraine_english.csv'
    output_file = 'data_hermitage/hermitage_ukraine_cleaned.csv'
    
    try:
        df_cleaned = clean_hermitage_dataset(input_file, output_file)
        
        # Preview
        print("\n📝 Preview (first 3 rows, selected columns):")
        print("="*70)
        cols = ['object_name', 'material', 'technique', 'date_normalized', 'period_category']
        print(df_cleaned[cols].head(3).to_string())
        print("\n")
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found '{input_file}'")
        print("   Place the file in the same directory as this script!")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()