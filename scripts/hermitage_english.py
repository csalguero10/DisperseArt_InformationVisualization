"""
HERMITAGE UKRAINE DATASET TRANSLATION SCRIPT
Translates Russian text columns to English

"""

import pandas as pd
from googletrans import Translator
import time

print("="*60)
print("HERMITAGE UKRAINE DATASET TRANSLATION")
print("="*60)

# Load data
print("\n[1/3] Loading dataset...")
df = pd.read_csv('hermitage_ukraine_all.csv')
print(f"✓ Loaded {len(df):,} objects")

# Initialize translator
print("\n[2/3] Initializing translator...")
translator = Translator()

def translate_unique_values(df, column_name, label):
    """
    Translate a column by translating unique values first (more efficient)
    """
    print(f"\n  Translating: {label} ({column_name})")
    
    # Get unique values to translate
    unique_vals = df[column_name].dropna().unique()
    print(f"    {len(unique_vals)} unique values to translate...")
    
    # Create translation dictionary
    trans_dict = {}
    failed = 0
    
    for i, val in enumerate(unique_vals):
        # Progress indicator
        if i > 0 and i % 20 == 0:
            print(f"    Progress: {i}/{len(unique_vals)} ({i/len(unique_vals)*100:.1f}%)")
        
        # Skip empty values
        if pd.isna(val) or str(val).strip() == '':
            trans_dict[val] = val
            continue
        
        # Translate with retry logic
        for attempt in range(3):
            try:
                result = translator.translate(str(val), src='ru', dest='en')
                trans_dict[val] = result.text
                time.sleep(0.5)  # Rate limiting (important!)
                break
            except Exception as e:
                if attempt < 2:
                    print(f"    Retry {attempt+1} for: {str(val)[:50]}...")
                    time.sleep(2)
                else:
                    # After 3 attempts, keep original
                    trans_dict[val] = val
                    failed += 1
    
    # Apply translations to dataframe
    df[f'{column_name}_en'] = df[column_name].map(trans_dict)
    
    if failed > 0:
        print(f"    ⚠ {failed} values kept in Russian (translation failed)")
    print(f"    ✓ Completed!")
    
    return df

# Columns to translate
columns = {
    'object_name': 'Object Name',
    'find_location': 'Find Location',
    'creation_place_school': 'Creation Place/School',
    'material_technique': 'Material & Technique',
    'dating': 'Dating',
    'category': 'Category',
    'department_sector': 'Department',
    'collection': 'Collection',
    'archaeological_site': 'Archaeological Site',
    'region_category': 'Region Category'
}

# Translate each column
print("\n[3/3] Starting translation...")
print("This will take 15-30 minutes. Please be patient!\n")

for col_name, col_label in columns.items():
    if col_name in df.columns:
        df = translate_unique_values(df, col_name, col_label)
    else:
        print(f"  ⚠ Column '{col_name}' not found, skipping...")

# Save English-only version
print("\n" + "="*60)
print("SAVING FILE")
print("="*60)

# English-only clean version
english_cols = [
    'id',
    'object_name_en',
    'find_location_en',
    'longitude',
    'latitude',
    'creation_place_school_en',
    'dating_en',
    'material_technique_en',
    'size',
    'acquisition_year',
    'inventory_number',
    'category_en',
    'department_sector_en',
    'region_category_en',
    'image_url'
]

# Filter to existing columns
available_cols = [col for col in english_cols if col in df.columns]
df_english = df[available_cols].copy()

# Remove _en suffix from column names
df_english.columns = [col.replace('_en', '') for col in df_english.columns]

output_english = 'hermitage_ukraine_english.csv'
df_english.to_csv(output_english, index=False, encoding='utf-8')
print(f"\n✓ Saved: {output_english}")
print(f"  - {len(df_english):,} objects")
print(f"  - {len(df_english.columns)} columns (English only)")

# Show sample translations
print("\n" + "="*60)
print("SAMPLE TRANSLATIONS")
print("="*60)

samples = ['object_name', 'find_location', 'dating']
for col in samples:
    if col in df.columns and f'{col}_en' in df.columns:
        print(f"\n{col.upper()}:")
        sample = df[[col, f'{col}_en']].dropna().head(3)
        for idx, row in sample.iterrows():
            print(f"  RU: {row[col]}")
            print(f"  EN: {row[f'{col}_en']}")
            print()

print("="*60)
print("✓ TRANSLATION COMPLETE!")
print("="*60)
print(f"\nFile created: {output_english}")
print(f"Total objects translated: {len(df_english):,}")
print(f"Columns: {len(df_english.columns)}")
print("\nYou can now use this file for your research!")