"""
# 1.2 DATA CLEANING
Cleaning and preprocessing the Ukrainian Stolen Objects dataset
"""

import pandas as pd
import numpy as np
import re

# ============================================================================
# LOAD DATA
# ============================================================================

# Load the dataset
df = pd.read_csv('raw_data/stolen_objects_ukraine.csv')

print("="*70)
print("ORIGINAL DATASET")
print("="*70)
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"\nFirst row sample:")
print(df.iloc[0])

# ============================================================================
# 1. REMOVE PIPE CHARACTERS (|) FROM ALL TEXT FIELDS
# ============================================================================

print("\n" + "="*70)
print("1. CLEANING PIPE CHARACTERS")
print("="*70)

def remove_pipes(text):
    """Remove leading/trailing pipe characters and clean whitespace"""
    if pd.isna(text):
        return text
    text = str(text)
    # Remove leading/trailing pipes
    text = text.strip('|').strip()
    # Remove multiple pipes
    text = re.sub(r'\|+', ' ', text)
    # Clean extra whitespace
    text = ' '.join(text.split())
    return text if text else np.nan

# Apply to all text columns
text_columns = df.select_dtypes(include=['object']).columns

for col in text_columns:
    df[col] = df[col].apply(remove_pipes)
    
print(f"✓ Cleaned {len(text_columns)} text columns")

# ============================================================================
# 2. STANDARDIZE COLUMN NAMES
# ============================================================================

print("\n" + "="*70)
print("2. STANDARDIZING COLUMN NAMES")
print("="*70)

# Convert to lowercase and replace spaces with underscores
df.columns = df.columns.str.lower().str.replace(' ', '_')
print(f"✓ Standardized column names: {list(df.columns)}")

# ============================================================================
# 3. HANDLE MISSING VALUES
# ============================================================================

print("\n" + "="*70)
print("3. ANALYZING MISSING VALUES")
print("="*70)

missing_stats = pd.DataFrame({
    'Column': df.columns,
    'Missing_Count': df.isnull().sum(),
    'Missing_Percentage': (df.isnull().sum() / len(df) * 100).round(2)
})
missing_stats = missing_stats[missing_stats['Missing_Count'] > 0].sort_values('Missing_Percentage', ascending=False)

print("\nMissing values by column:")
print(missing_stats.to_string(index=False))

# Replace empty strings with NaN
df.replace(['', 'nan', 'None', 'N/A', 'n/a'], np.nan, inplace=True)

# ============================================================================
# 4. CLEAN AND STANDARDIZE YEAR FIELD
# ============================================================================

print("\n" + "="*70)
print("4. CLEANING YEAR FIELD")
print("="*70)

def extract_year(year_value):
    """Extract 4-digit year from various formats"""
    if pd.isna(year_value):
        return np.nan
    
    year_str = str(year_value).strip()
    
    # Search for 4-digit year (1900-2099)
    match = re.search(r'(19\d{2}|20\d{2})', year_str)
    if match:
        year = int(match.group(1))
        # Validate reasonable range
        if 2000 <= year <= 2025:
            return year
    
    return np.nan

if 'year_incident' in df.columns:
    df['year_clean'] = df['year_incident'].apply(extract_year)
    valid_years = df['year_clean'].notna().sum()
    print(f"✓ Extracted {valid_years} valid years ({valid_years/len(df)*100:.1f}%)")
    print(f"  Year range: {df['year_clean'].min():.0f} - {df['year_clean'].max():.0f}")
else:
    print("⚠ 'year_incident' column not found")

# ============================================================================
# 5. EXTRACT AND VALIDATE COORDINATES
# ============================================================================

print("\n" + "="*70)
print("5. CLEANING GEOGRAPHIC COORDINATES")
print("="*70)

def validate_coordinates(lat, lon):
    """Validate coordinates are within Ukraine's bounds"""
    if pd.isna(lat) or pd.isna(lon):
        return False
    
    # Ukraine's approximate bounds
    # Latitude: 44° to 52° N
    # Longitude: 22° to 40° E
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        
        if 44 <= lat_f <= 52 and 22 <= lon_f <= 40:
            return True
    except:
        pass
    
    return False

if 'latitude' in df.columns and 'longitude' in df.columns:
    # Convert to numeric
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Validate
    valid_coords = df.apply(lambda row: validate_coordinates(row['latitude'], row['longitude']), axis=1)
    df.loc[~valid_coords, ['latitude', 'longitude']] = np.nan
    
    coords_count = df['latitude'].notna().sum()
    print(f"✓ Valid coordinates: {coords_count} ({coords_count/len(df)*100:.1f}%)")
else:
    print("⚠ Coordinate columns not found")

# ============================================================================
# 6. STANDARDIZE CATEGORY NAMES
# ============================================================================

print("\n" + "="*70)
print("6. STANDARDIZING CATEGORIES")
print("="*70)

if 'category' in df.columns:
    # Remove extra whitespace and standardize capitalization
    df['category'] = df['category'].str.strip().str.title()
    
    print(f"✓ Categories found: {df['category'].nunique()}")
    print("\nCategory distribution:")
    print(df['category'].value_counts().head(10))
else:
    print("⚠ 'category' column not found")

# ============================================================================
# 7. CLEAN TEXT FIELDS (NAME, AUTHOR, DESCRIPTION)
# ============================================================================

print("\n" + "="*70)
print("7. CLEANING TEXT FIELDS")
print("="*70)

def clean_text_field(text):
    """Deep clean text fields"""
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

text_fields = ['name', 'author', 'description', 'circumstances']

for field in text_fields:
    if field in df.columns:
        df[field] = df[field].apply(clean_text_field)
        print(f"✓ Cleaned '{field}' field")

# ============================================================================
# 8. REMOVE DUPLICATE ENTRIES
# ============================================================================

print("\n" + "="*70)
print("8. REMOVING DUPLICATES")
print("="*70)

initial_count = len(df)

# Check for duplicates based on ID
if 'id' in df.columns:
    duplicates = df.duplicated(subset=['id'], keep='first')
    df = df[~duplicates].copy()
    removed = duplicates.sum()
    print(f"✓ Removed {removed} duplicate entries based on ID")

# Check for duplicates based on name + author
if 'name' in df.columns and 'author' in df.columns:
    content_dupes = df.duplicated(subset=['name', 'author'], keep='first')
    additional_dupes = content_dupes.sum()
    if additional_dupes > 0:
        print(f"⚠ Found {additional_dupes} potential content duplicates (not removed)")

print(f"Final count: {len(df)} objects ({len(df)/initial_count*100:.1f}% retained)")

# ============================================================================
# 9. CREATE DERIVED FIELDS
# ============================================================================

print("\n" + "="*70)
print("9. CREATING DERIVED FIELDS")
print("="*70)

# Add period classification
if 'year_clean' in df.columns:
    def classify_period(year):
        if pd.isna(year):
            return 'Unknown'
        elif year < 2014:
            return 'Pre-2014'
        elif year < 2022:
            return '2014-2021 (Crimea annexation)'
        else:
            return '2022+ (Full-scale invasion)'
    
    df['period'] = df['year_clean'].apply(classify_period)
    print("✓ Added 'period' classification")
    print(df['period'].value_counts())

# Add has_coordinates flag
if 'latitude' in df.columns:
    df['has_coordinates'] = df['latitude'].notna()
    print(f"\n✓ Added 'has_coordinates' flag")

# Add has_author flag
if 'author' in df.columns:
    df['has_author'] = df['author'].notna()
    print(f"✓ Added 'has_author' flag")

# ============================================================================
# 10. DATA TYPE OPTIMIZATION
# ============================================================================

print("\n" + "="*70)
print("10. OPTIMIZING DATA TYPES")
print("="*70)

# Convert year to integer where possible
if 'year_clean' in df.columns:
    df['year_clean'] = df['year_clean'].astype('Int64')  # Nullable integer

# Convert boolean flags
bool_cols = ['has_coordinates', 'has_author']
for col in bool_cols:
    if col in df.columns:
        df[col] = df[col].astype(bool)

print("✓ Optimized data types")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*70)
print("CLEANED DATASET SUMMARY")
print("="*70)

print(f"\nShape: {df.shape}")
print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

print("\nData Quality Metrics:")
print(f"  Complete records (no missing values): {df.notna().all(axis=1).sum()} ({df.notna().all(axis=1).sum()/len(df)*100:.1f}%)")
print(f"  Records with coordinates: {df['has_coordinates'].sum() if 'has_coordinates' in df.columns else 0}")
print(f"  Records with author: {df['has_author'].sum() if 'has_author' in df.columns else 0}")
print(f"  Records with valid year: {df['year_clean'].notna().sum() if 'year_clean' in df.columns else 0}")

print("\nColumn types:")
print(df.dtypes)

# ============================================================================
# SAVE CLEANED DATA
# ============================================================================

print("\n" + "="*70)
print("SAVING CLEANED DATASET")
print("="*70)

# Save to CSV
df.to_csv('data/stolen_objects_cleaned.csv', index=False, encoding='utf-8')
print("✓ Saved to: data/stolen_objects_cleaned.csv")

# Save summary statistics
summary = pd.DataFrame({
    'Column': df.columns,
    'Non-Null Count': df.notna().sum(),
    'Null Count': df.isna().sum(),
    'Data Type': df.dtypes,
    'Unique Values': [df[col].nunique() for col in df.columns]
})
summary.to_csv('data/cleaning_summary.csv', index=False)
print("✓ Saved cleaning summary to: data/cleaning_summary.csv")

print("\n" + "="*70)
print("✅ DATA CLEANING COMPLETED")
print("="*70)

# Display cleaned data sample
print("\nCleaned data preview:")
df.head()