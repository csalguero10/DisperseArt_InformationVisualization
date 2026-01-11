"""
ADD JITTER TO OVERLAPPING COORDINATES
Adds small random offset to duplicate coordinates so all points are visible in Kepler.gl
"""

import pandas as pd
import numpy as np

def add_jitter_to_duplicates(input_file, output_file, jitter_amount=0.001):
    """
    Add small random offset (jitter) to duplicate coordinates
    
    Args:
        input_file: Input CSV file
        output_file: Output CSV file with jittered coordinates
        jitter_amount: Maximum offset in degrees (default 0.001 ≈ 111 meters)
    """
    
    print("\n" + "="*70)
    print("ADDING JITTER TO OVERLAPPING COORDINATES")
    print("="*70 + "\n")
    
    # Read CSV
    print(f"📖 Reading file: {input_file}")
    df = pd.read_csv(input_file)
    print(f"✓ {len(df)} objects loaded\n")
    
    # Check for latitude/longitude columns
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        print("✗ ERROR: 'latitude' and 'longitude' columns not found!")
        return None
    
    # Count objects with coordinates
    with_coords = df['latitude'].notna().sum()
    print(f"📍 Objects with coordinates: {with_coords}")
    
    # Find duplicates
    df_coords = df[df['latitude'].notna()].copy()
    duplicates = df_coords.groupby(['latitude', 'longitude']).size()
    duplicate_locations = duplicates[duplicates > 1]
    
    print(f"🔍 Found {len(duplicate_locations)} locations with overlapping coordinates")
    print(f"   Total overlapping objects: {duplicate_locations.sum()}\n")
    
    if len(duplicate_locations) > 0:
        print("Top 5 locations with most objects:")
        print("-" * 70)
        top_duplicates = duplicate_locations.sort_values(ascending=False).head(5)
        for (lat, lon), count in top_duplicates.items():
            # Find place name
            place = df[(df['latitude'] == lat) & (df['longitude'] == lon)]['place_incident'].iloc[0]
            print(f"  {place}")
            print(f"    {count} objects at ({lat:.6f}, {lon:.6f})")
    
    # Add jitter to duplicates
    print(f"\n🎲 Adding random jitter (max ±{jitter_amount}° ≈ {jitter_amount * 111:.0f} meters)...")
    
    # Group by coordinates and add jitter
    jitter_applied = 0
    for (lat, lon), count in duplicate_locations.items():
        if count > 1:
            # Find all rows with these coordinates
            mask = (df['latitude'] == lat) & (df['longitude'] == lon)
            indices = df[mask].index
            
            # Add jitter to all except the first one
            for i, idx in enumerate(indices):
                if i > 0:  # Keep first one at original position
                    # Random offset in range [-jitter_amount, +jitter_amount]
                    df.at[idx, 'latitude'] = lat + np.random.uniform(-jitter_amount, jitter_amount)
                    df.at[idx, 'longitude'] = lon + np.random.uniform(-jitter_amount, jitter_amount)
                    jitter_applied += 1
    
    print(f"✓ Applied jitter to {jitter_applied} objects")
    print(f"✓ Original coordinates preserved for {len(duplicate_locations)} reference points")
    
    # Verify no duplicates remain
    df_coords_new = df[df['latitude'].notna()].copy()
    duplicates_after = df_coords_new.groupby(['latitude', 'longitude']).size()
    duplicate_locations_after = duplicates_after[duplicates_after > 1]
    
    print(f"\n📊 After jitter:")
    print(f"   Locations with duplicates: {len(duplicate_locations_after)}")
    
    # Save
    print(f"\n💾 Saving dataset with jittered coordinates...")
    df.to_csv(output_file, index=False)
    print(f"✓ Saved to: {output_file}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total objects: {len(df)}")
    print(f"Objects with coordinates: {with_coords}")
    print(f"Jitter applied to: {jitter_applied} objects")
    print(f"Jitter amount: ±{jitter_amount}° (≈{jitter_amount * 111:.0f} meters)")
    print("="*70 + "\n")
    
    print("✅ SUCCESS! All points will now be visible in Kepler.gl")
    print("   Points from the same location are slightly spread out")
    print("   but still appear in the correct area.\n")
    
    return df

# Execute
if __name__ == "__main__":
    # INPUT: Your CSV file with coordinates
    input_file = 'data_stolen/stolen_objects_ukraine_with_coords.csv'
    
    # OUTPUT: Same file with jittered coordinates
    output_file = 'data_stolen/stolen_objects_ukraine_jittered.csv'
    
    # Jitter amount (0.001 degrees ≈ 111 meters)
    # Adjust if needed: 0.0001 = 11m, 0.001 = 111m, 0.01 = 1.1km
    jitter_amount = 0.0005  # ~55 meters
    
    try:
        df_jittered = add_jitter_to_duplicates(input_file, output_file, jitter_amount)
        
        if df_jittered is not None:
            print("🗺️  Now load this CSV in Kepler.gl:")
            print(f"   {output_file}")
            print("\n   All objects will be visible as separate points!")
            print("   Objects from the same museum will appear in a small cluster.\n")
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found '{input_file}'")
        print("   Make sure the file is in the same directory as this script!")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()