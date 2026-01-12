"""
UPDATE COLOR PALETTE - RED SQUIRREL THEME
Updates all HTML visualizations with new Adobe Color palette
Author: Cata
Date: January 2026

New Palette (Red Squirrel):
#752520 - Dark reddish brown
#F7948D - Light salmon pink  
#F54D41 - Bright coral red
#754643 - Medium reddish brown
#C23E34 - Terracotta red
"""

import os
import glob

print("="*70)
print("UPDATING COLOR PALETTE - RED SQUIRREL THEME")
print("="*70)

# New color palette
NEW_PALETTE = {
    'dark_brown': '#752520',
    'light_salmon': '#F7948D', 
    'coral_red': '#F54D41',
    'medium_brown': '#754643',
    'terracotta': '#C23E34'
}

# Color array for sequential scales
color_array = ['#752520', '#754643', '#C23E34', '#F54D41', '#F7948D']
color_array_reverse = ['#F7948D', '#F54D41', '#C23E34', '#754643', '#752520']

print("\n🎨 New Color Palette:")
for name, color in NEW_PALETTE.items():
    print(f"   {name:20} → {color}")

# Find all HTML files
html_files = glob.glob('html_visualizations/*.html')

if not html_files:
    print("\n❌ No HTML files found in html_visualizations/")
    print("   Run generate_all_html_visualizations.py first!")
    exit()

print(f"\n📁 Found {len(html_files)} HTML files to update")

# Old colors to replace
old_colors = {
    # Old terracotta/brown colors
    '#D2691E': '#C23E34',
    '#CD853F': '#F7948D',
    '#B8860B': '#F54D41',
    '#8B4513': '#752520',
    '#4A2511': '#752520',
    '#5C3317': '#752520',
    '#2C1810': '#752520',
    '#3D2415': '#754643',
    
    # Old reds
    '#DC143C': '#C23E34',
    '#CD5C5C': '#F54D41',
    
    # Cluster colors
    '#C94A38': '#C23E34',
    '#E07A5F': '#F7948D',
    '#D4634A': '#F54D41',
    '#B8403A': '#752520',
    '#E8927C': '#F7948D',
    '#A63A2F': '#754643',
}

# Update each file
updated_count = 0
for html_file in html_files:
    filename = os.path.basename(html_file)
    print(f"\n📝 Processing: {filename}")
    
    # Read file
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Replace individual colors
    for old_color, new_color in old_colors.items():
        if old_color.lower() in content.lower():
            count = content.count(old_color) + content.count(old_color.lower())
            content = content.replace(old_color, new_color)
            content = content.replace(old_color.lower(), new_color.lower())
            if count > 0:
                changes_made.append(f"{old_color} → {new_color} ({count}x)")
    
    # Replace Plotly color scales with custom arrays
    # YlOrBr scale
    if '"colorscale":"YlOrBr"' in content or "'colorscale':'YlOrBr'" in content:
        # Create custom colorscale
        custom_scale = str(color_array_reverse)
        content = content.replace('"colorscale":"YlOrBr"', f'"colorscale":{custom_scale}')
        content = content.replace("'colorscale':'YlOrBr'", f"'colorscale':{custom_scale}")
        changes_made.append("YlOrBr → Custom Red Squirrel scale")
    
    # Reds scale
    if '"colorscale":"Reds"' in content or "'colorscale':'Reds'" in content:
        custom_scale = str(color_array)
        content = content.replace('"colorscale":"Reds"', f'"colorscale":{custom_scale}')
        content = content.replace("'colorscale':'Reds'", f"'colorscale':{custom_scale}")
        changes_made.append("Reds → Custom Red Squirrel scale")
    
    # Replace px.colors.sequential.Reds with custom array
    if 'px.colors.sequential.Reds' in content:
        # This is trickier - need to find the actual usage
        # For now, add a note that manual update may be needed
        changes_made.append("⚠️  Contains px.colors.sequential.Reds - may need manual update")
    
    # Write back if changes were made
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ Updated - {len(changes_made)} changes")
        for change in changes_made[:5]:  # Show first 5 changes
            print(f"      • {change}")
        if len(changes_made) > 5:
            print(f"      • ... and {len(changes_made) - 5} more")
        updated_count += 1
    else:
        print(f"   ℹ️  No changes needed")

print("\n" + "="*70)
print(f"✅ PALETTE UPDATE COMPLETE!")
print("="*70)
print(f"\n📊 Updated {updated_count} out of {len(html_files)} files")
print(f"\n🎨 New Red Squirrel palette applied:")
print(f"   Dark Brown:  {NEW_PALETTE['dark_brown']}")
print(f"   Med Brown:   {NEW_PALETTE['medium_brown']}")
print(f"   Terracotta:  {NEW_PALETTE['terracotta']}")
print(f"   Coral Red:   {NEW_PALETTE['coral_red']}")
print(f"   Light Salmon: {NEW_PALETTE['light_salmon']}")
print("="*70)