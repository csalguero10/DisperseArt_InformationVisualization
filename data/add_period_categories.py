"""
ADD HISTORICAL PERIOD CATEGORIES
Assigns each object to a historical period based on year_for_timeline
"""

import pandas as pd
import numpy as np
import re

# Historical periods with their date ranges
HISTORICAL_PERIODS = [
    {
        'name': 'Paleolithic Period',
        'start': -1400000,  # 1.4 million years ago
        'end': -10000,
        'label': 'Paleolithic Period (c. 1.4 million years ago - 10,000 BC)'
    },
    {
        'name': 'Neolithic Period',
        'start': -5050,
        'end': -2950,
        'label': 'Neolithic Period (c. 5050 - 2950 BC)'
    },
    {
        'name': 'Bronze Age',
        'start': -4500,
        'end': -1950,
        'label': 'Bronze Age (c. 4500 - 1950 BC)'
    },
    {
        'name': 'Scythian-Sarmatian Era',
        'start': -700,
        'end': -250,
        'label': 'Scythian-Sarmatian Era (c. 700 BC - 250 BC)'
    },
    {
        'name': 'Greek and Roman Period',
        'start': -250,
        'end': 375,
        'label': 'Greek and Roman Period (250 BC - 375 AD)'
    },
    {
        'name': 'Migration Period',
        'start': 370,
        'end': 700,
        'label': 'Migration Period (370s - 7th century AD)'
    },
    {
        'name': 'Early Medieval Period - Bulgar and Khazar Era',
        'start': 600,
        'end': 900,
        'label': 'Early Medieval Period - Bulgar and Khazar Era (7th - 9th centuries)'
    },
    {
        'name': 'Kievan Rus\' Period',
        'start': 839,
        'end': 1240,
        'label': 'Kievan Rus\' Period (839 - 1240)'
    },
    {
        'name': 'Mongol Invasion and Domination',
        'start': 1239,
        'end': 1400,
        'label': 'Mongol Invasion and Domination (1239 - 14th century)'
    },
    {
        'name': 'Kingdom of Galicia-Volhynia/Ruthenia',
        'start': 1197,
        'end': 1340,
        'label': 'Kingdom of Galicia-Volhynia/Ruthenia (1197 - 1340)'
    },
    {
        'name': 'Lithuanian and Polish Period',
        'start': 1340,
        'end': 1648,
        'label': 'Lithuanian and Polish Period (1340 - 1648)'
    },
    {
        'name': 'Cossack Hetmanate Period',
        'start': 1648,
        'end': 1764,
        'label': 'Cossack Hetmanate Period (1648 - 1764)'
    },
    {
        'name': 'Ukraine under the Russian Empire',
        'start': 1764,
        'end': 1917,
        'label': 'Ukraine under the Russian Empire (1764 - 1917)'
    },
    {
        'name': 'Ukraine\'s First Independence',
        'start': 1917,
        'end': 1921,
        'label': 'Ukraine\'s First Independence (1917 - 1921)'
    },
    {
        'name': 'Soviet Period',
        'start': 1921,
        'end': 1991,
        'label': 'Soviet Period (1921 - 1991)'
    },
    {
        'name': 'Independence Period',
        'start': 1991,
        'end': 2030,  # Present (using 2030 as upper bound)
        'label': 'Independence Period (1991 - present)'
    }
]

def assign_period_category(row):
    """
    Assigns a historical period based on the year
    First checks year_for_timeline, then falls back to date_normalized
    Handles overlapping periods by choosing the most specific/relevant one
    """
    year = row['year_for_timeline']
    date_normalized = row['date_normalized']
    
    # If year_for_timeline is available, use it
    if pd.notna(year):
        year = float(year)
    # Otherwise, try to extract from date_normalized
    elif pd.notna(date_normalized) and date_normalized != '':
        date_str = str(date_normalized).strip()
        
        # Handle cases like "XX century" or "ХХ century" (Cyrillic X)
        # Replace Cyrillic with Latin
        date_str = date_str.replace('Х', 'X').replace('І', 'I').replace('V', 'V')
        
        # Handle XX century (20th century) -> 1901-2000
        if re.search(r'\bXX\b', date_str, re.IGNORECASE):
            year = 1950  # midpoint of 20th century
        # Handle XIX century (19th century) -> 1801-1900
        elif re.search(r'\bXIX\b', date_str, re.IGNORECASE):
            year = 1850  # midpoint of 19th century
        # Handle XVIII century (18th century) -> 1701-1800
        elif re.search(r'\bXVIII\b', date_str, re.IGNORECASE):
            year = 1750
        # Handle XVII century (17th century) -> 1601-1700
        elif re.search(r'\bXVII\b', date_str, re.IGNORECASE):
            year = 1650
        # Try to extract a year from date_normalized
        elif re.match(r'^-?\d{4}$', date_str):
            year = float(date_str)
        # Year range - use midpoint
        elif re.match(r'^(-?\d{4})-(-?\d{4})( BC)?$', date_str):
            match = re.match(r'^(-?\d{4})-(-?\d{4})', date_str)
            year1 = int(match.group(1))
            year2 = int(match.group(2))
            year = (year1 + year2) / 2
        else:
            # Can't extract year
            return 'Unknown Period'
    else:
        return 'Unknown Period'
    
    # Find all matching periods
    matching_periods = []
    for period in HISTORICAL_PERIODS:
        if period['start'] <= year <= period['end']:
            matching_periods.append(period)
    
    if not matching_periods:
        # If no match, return closest period or Unknown
        if year < -10000:
            return 'Pre-Neolithic Period'
        elif year > 2030:
            return 'Contemporary Period'
        else:
            return 'Unknown Period'
    
    # If multiple matches (overlapping periods), choose based on priority
    # Priority: More specific periods > broader periods
    # For overlapping periods, we choose based on historical significance
    
    if len(matching_periods) == 1:
        return matching_periods[0]['label']
    
    # Handle specific overlaps
    period_names = [p['name'] for p in matching_periods]
    
    # Mongol period takes precedence over Galicia-Volhynia in overlap
    if 'Mongol Invasion and Domination' in period_names and 'Kingdom of Galicia-Volhynia/Ruthenia' in period_names:
        # If year is early (1239-1300s), prefer Mongol; if late (1300-1340), prefer Galicia
        if year < 1300:
            return next(p['label'] for p in matching_periods if p['name'] == 'Mongol Invasion and Domination')
        else:
            return next(p['label'] for p in matching_periods if p['name'] == 'Kingdom of Galicia-Volhynia/Ruthenia')
    
    # Kievan Rus' takes precedence over Galicia-Volhynia in their overlap
    if 'Kievan Rus\' Period' in period_names and 'Kingdom of Galicia-Volhynia/Ruthenia' in period_names:
        return next(p['label'] for p in matching_periods if p['name'] == 'Kievan Rus\' Period')
    
    # For ancient periods, Bronze Age and Neolithic might overlap slightly - prefer more specific
    if 'Bronze Age' in period_names and 'Neolithic Period' in period_names:
        return next(p['label'] for p in matching_periods if p['name'] == 'Bronze Age')
    
    # Default: return the first match (or you could return the most recent period)
    return matching_periods[0]['label']

def add_period_categories(input_file, output_file):
    """Main function to add period categories"""
    
    print("\n" + "="*70)
    print("ADDING HISTORICAL PERIOD CATEGORIES")
    print("="*70 + "\n")
    
    # Read CSV
    print(f"📖 Reading file: {input_file}")
    df = pd.read_csv(input_file)
    print(f"✓ {len(df)} objects loaded\n")
    
    # Check if year_for_timeline exists
    if 'year_for_timeline' not in df.columns:
        print("✗ ERROR: 'year_for_timeline' column not found!")
        print("   Please run the cleaning script first.")
        return
    
    # Add period category
    print("🔧 Assigning historical periods...")
    print("   → Checking year_for_timeline first")
    print("   → Falling back to date_normalized if year_for_timeline is empty\n")
    
    df['period_category'] = df.apply(assign_period_category, axis=1)
    
    # Statistics
    print("\n📊 Period assignment statistics:")
    print("="*70)
    
    # Count how many used year_for_timeline vs date_normalized
    has_timeline_year = df['year_for_timeline'].notna()
    has_normalized_date = df['date_normalized'].notna() & (df['date_normalized'] != '')
    has_period = df['period_category'] != 'Unknown Period'
    
    print(f"  Objects with year_for_timeline: {has_timeline_year.sum()}")
    print(f"  Objects with date_normalized: {has_normalized_date.sum()}")
    print(f"  Objects assigned to a period: {has_period.sum()}")
    print(f"  Objects remaining as 'Unknown Period': {(~has_period).sum()}")
    
    # Objects that got period from date_normalized fallback
    fallback_used = (~has_timeline_year) & has_normalized_date & has_period
    print(f"\n  ✓ Objects assigned via date_normalized fallback: {fallback_used.sum()}")
    
    print("\n📊 Period distribution:")
    print("="*70)
    
    period_counts = df['period_category'].value_counts().sort_index()
    for period, count in period_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {period}")
        print(f"    → {count} objects ({percentage:.1f}%)")
        print()
    
    # Show examples for each period
    print("\n📋 Examples by period:")
    print("="*70)
    
    for period in df['period_category'].unique():
        if period != 'Unknown Period' and pd.notna(period):
            period_objects = df[df['period_category'] == period][['name', 'year_for_timeline', 'date_normalized']].head(2)
            
            if len(period_objects) > 0:
                print(f"\n{period}:")
                for idx, row in period_objects.iterrows():
                    print(f"  • {row['name']}")
                    print(f"    Year: {row['year_for_timeline']:.0f} | Date: {row['date_normalized']}")
    
    # Save
    print("\n" + "="*70)
    print("💾 Saving dataset with period categories...")
    df.to_csv(output_file, index=False)
    print(f"✓ Saved to: {output_file}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n✅ Successfully added 'period_category' column")
    print(f"📊 Total objects: {len(df)}")
    print(f"📊 Objects with periods: {df['period_category'].notna().sum()}")
    print(f"📊 Objects with timeline years: {df['year_for_timeline'].notna().sum()}")
    print(f"📊 Unique periods: {df['period_category'].nunique()}")
    
    # Timeline range
    if df['year_for_timeline'].notna().sum() > 0:
        print(f"\n📅 Timeline range:")
        print(f"  Earliest: {df['year_for_timeline'].min():.0f}")
        print(f"  Latest: {df['year_for_timeline'].max():.0f}")
        print(f"  Span: {df['year_for_timeline'].max() - df['year_for_timeline'].min():.0f} years")
    
    print("\n" + "="*70 + "\n")
    
    return df

# Execute
if __name__ == "__main__":
    input_file = 'data/stolen_objects_ukraine_cleaned.csv'
    output_file = 'data/stolen_objects_ukraine_with_periods.csv'
    
    try:
        df_with_periods = add_period_categories(input_file, output_file)
        
        # Show preview
        print("\n📝 Preview of data with periods:")
        print("="*70)
        preview_cols = ['name', 'date_normalized', 'year_for_timeline', 'period_category']
        print(df_with_periods[preview_cols].head(5).to_string())
        print("\n")
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found '{input_file}'")
        print("   Make sure to run clean_dataset.py first!")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()