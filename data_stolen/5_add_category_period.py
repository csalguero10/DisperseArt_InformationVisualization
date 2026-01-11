"""
ASSIGN HISTORICAL PERIODS TO UKRAINIAN STOLEN OBJECTS
Assigns each object to a historical period based on its date information
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
        'label': 'Paleolithic Period'
    },
    {
        'name': 'Neolithic Period',
        'start': -10000,
        'end': -4500,
        'label': 'Neolithic Period'
    },
    {
        'name': 'Bronze Age',
        'start': -4500,
        'end': -1200,
        'label': 'Bronze Age'
    },
    {
        'name': 'Iron Age',
        'start': -1200,
        'end': -700,
        'label': 'Iron Age'
    },
    {
        'name': 'Scythian-Sarmatian Era',
        'start': -700,
        'end': 250,
        'label': 'Scythian-Sarmatian Era'
    },
    {
        'name': 'Greek and Roman Period',
        'start': -250,
        'end': 375,
        'label': 'Greek and Roman Period'
    },
    {
        'name': 'Migration Period',
        'start': 370,
        'end': 700,
        'label': 'Migration Period'
    },
    {
        'name': 'Early Medieval Period',
        'start': 600,
        'end': 900,
        'label': 'Early Medieval Period'
    },
    {
        'name': 'Kievan Rus\' Period',
        'start': 839,
        'end': 1240,
        'label': 'Kievan Rus Period'
    },
    {
        'name': 'Mongol Invasion and Domination',
        'start': 1239,
        'end': 1400,
        'label': 'Mongol Invasion and Domination'
    },
    {
        'name': 'Kingdom of Galicia-Volhynia',
        'start': 1197,
        'end': 1340,
        'label': 'Kingdom of Galicia-Volhynia'
    },
    {
        'name': 'Lithuanian and Polish Period',
        'start': 1340,
        'end': 1648,
        'label': 'Lithuanian and Polish Period'
    },
    {
        'name': 'Cossack Hetmanate Period',
        'start': 1648,
        'end': 1764,
        'label': 'Cossack Hetmanate Period'
    },
    {
        'name': 'Ukraine under the Russian Empire',
        'start': 1764,
        'end': 1917,
        'label': 'Ukraine under the Russian Empire'
    },
    {
        'name': 'Ukraine\'s First Independence',
        'start': 1917,
        'end': 1921,
        'label': 'Ukraine\'s First Independence'
    },
    {
        'name': 'Soviet Period',
        'start': 1921,
        'end': 1991,
        'label': 'Soviet Period'
    },
    {
        'name': 'Independence Period',
        'start': 1991,
        'end': 2030,  # Present (using 2030 as upper bound)
        'label': 'Independence Period'
    }
]

def normalize_cyrillic_to_latin(text):
    """
    Convert Cyrillic characters that look like Latin/Roman numerals to their Latin equivalents
    """
    if pd.isna(text) or text == '':
        return text
    
    # Cyrillic to Latin mapping for characters used in Roman numerals
    cyrillic_map = {
        'Х': 'X',  # Cyrillic X (U+0425) -> Latin X
        'х': 'x',  # Cyrillic x (U+0445) -> Latin x
        'І': 'I',  # Cyrillic I (U+0406) -> Latin I
        'і': 'i',  # Cyrillic i (U+0456) -> Latin i
        'В': 'B',  # Cyrillic B (U+0412) -> Latin B (not common but just in case)
        'С': 'C',  # Cyrillic C (U+0421) -> Latin C
        'М': 'M',  # Cyrillic M (U+041C) -> Latin M
        'Ð¥': 'X',  # Common encoding issue
        'Ð†': 'I',  # Common encoding issue
        'у': 'y',  # Cyrillic y in "century"
    }
    
    for cyr, lat in cyrillic_map.items():
        text = text.replace(cyr, lat)
    
    return text

def extract_year_from_date(date_str):
    """
    Extract a year value from various date formats:
    - Single years: "1900", "1964"
    - Year ranges: "1840-1850" -> midpoint
    - Centuries: "XX century", "XVII century"
    - BC dates: "VI century BC", "150-33 millennium BC"
    - Complex ranges: "VI century BC - IV century"
    - Millennia: "II millennium BC"
    - Decades: "580-560s BC"
    - Thousands: "40-12 thousand years ago"
    - Parts of centuries: "end of VII century", "second half of XIX century"
    - Quarter ranges: "XIX - first q. XX century AD"
    """
    if pd.isna(date_str) or date_str == '':
        return None
    
    date_str = str(date_str).strip()
    
    # Normalize Cyrillic characters to Latin
    date_str = normalize_cyrillic_to_latin(date_str)
    
    # Handle lone Roman numerals without "century" (e.g., "XX", "XIX - XX")
    # But only if they're clearly Roman numerals (contain only I, V, X)
    lone_roman_match = re.match(r'^([IVX]+)\s*-\s*([IVX]+)$', date_str, re.IGNORECASE)
    if lone_roman_match and len(date_str) < 10:  # Reasonable length check
        roman1 = lone_roman_match.group(1)
        roman2 = lone_roman_match.group(2)
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman1 in century_patterns and roman2 in century_patterns:
            year1 = century_patterns[roman1]
            year2 = century_patterns[roman2]
            return (year1 + year2) / 2
    
    # Handle single lone Roman numeral (e.g., "XX", "ХVІІІ")
    single_roman_match = re.match(r'^([IVX]+)$', date_str, re.IGNORECASE)
    if single_roman_match and 2 <= len(date_str) <= 5:
        roman = single_roman_match.group(1)
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman in century_patterns:
            return century_patterns[roman]
    
    # Handle years without BC/AD suffix (e.g., "81 AD", "138-161 AD", "584-602", "49-54")
    # If it's a small number (< 500) without explicit BC/AD, assume AD for ancient period
    year_only_range = re.match(r'^(\d{1,4})[-–](\d{1,4})(\s*(AD|BC))?$', date_str)
    if year_only_range:
        year1 = int(year_only_range.group(1))
        year2 = int(year_only_range.group(2))
        suffix = year_only_range.group(4)
        
        midpoint = (year1 + year2) / 2
        
        if suffix and 'BC' in suffix.upper():
            return -midpoint
        else:
            # If years are < 500, assume AD (ancient Roman period)
            return midpoint
    
    # Handle single year without suffix (e.g., "81", "49")
    year_only = re.match(r'^(\d{1,3})(\s*(AD|BC))?$', date_str)
    if year_only:
        year = int(year_only.group(1))
        suffix = year_only.group(3)
        
        if suffix and 'BC' in suffix.upper():
            return -year
        elif year < 500:  # Assume ancient period AD
            return year
    
    # Handle "end of X-Y centuries BC" or "end of the X-Y centuries"
    end_range_match = re.search(
        r'end\s+of\s+the\s+([IVX]+)[-–]([IVX]+)\s*centuries?\s*(BC)?',
        date_str, re.IGNORECASE
    )
    if end_range_match:
        roman1 = end_range_match.group(1)
        roman2 = end_range_match.group(2)
        is_bc = bool(end_range_match.group(3))
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman2 in century_patterns:  # Use the later century
            year = century_patterns[roman2] + 38  # End of century
            return -year if is_bc else year
    
    # Handle century ranges with typos (e.g., "VI - second quarter V centuries BC")
    quarter_century_match = re.search(
        r'([IVX]+)\s*[-–]\s*(second|first|third|fourth)\s*quarter\s*([IVX]+)\s*centuries?\s*(BC)?',
        date_str, re.IGNORECASE
    )
    if quarter_century_match:
        roman1 = quarter_century_match.group(1)
        quarter = quarter_century_match.group(2).lower()
        roman2 = quarter_century_match.group(3)
        is_bc = bool(quarter_century_match.group(4))
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman1 in century_patterns and roman2 in century_patterns:
            year1 = century_patterns[roman1]
            year2 = century_patterns[roman2]
            
            # Adjust year2 for quarter
            if 'first' in quarter:
                year2 -= 38
            elif 'second' in quarter:
                year2 -= 12
            elif 'third' in quarter:
                year2 += 12
            elif 'fourth' in quarter:
                year2 += 38
            
            midpoint = (year1 + year2) / 2
            return -midpoint if is_bc else midpoint
    
    # Handle obviously wrong formats like "1900 century AD" -> treat as 1900
    wrong_format = re.match(r'^(\d{4})\s*century', date_str, re.IGNORECASE)
    if wrong_format:
        return int(wrong_format.group(1))
    
    # Handle century ranges without dashes (e.g., "XIII XVII centuries", "II I centuries BC")
    century_space_range = re.search(
        r'\b([IVX]+)\s*[-–]?\s*([IVX]+)\s*centuries?\s*(BC)?',
        date_str, re.IGNORECASE
    )
    if century_space_range:
        roman1 = century_space_range.group(1)
        roman2 = century_space_range.group(2)
        is_bc = bool(century_space_range.group(3))
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman1 in century_patterns and roman2 in century_patterns:
            year1 = century_patterns[roman1]
            year2 = century_patterns[roman2]
            midpoint = (year1 + year2) / 2
            return -midpoint if is_bc else midpoint
    
    # Handle "early XIXth century" style
    early_th_match = re.search(
        r'(early|late|end)\s+([IVX]+)th\s*century',
        date_str, re.IGNORECASE
    )
    if early_th_match:
        part = early_th_match.group(1).lower()
        roman = early_th_match.group(2)
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman in century_patterns:
            base_year = century_patterns[roman]
            if 'late' in part or 'end' in part:
                return base_year + 38
            elif 'early' in part:
                return base_year - 38
            else:
                return base_year
    
    # Handle "early 20th cent." style with Arabic numerals
    early_arabic_cent = re.search(
        r'(early|late|end|beginning)\s+(\d{1,2})(st|nd|rd|th)\s*cent',
        date_str, re.IGNORECASE
    )
    if early_arabic_cent:
        part = early_arabic_cent.group(1).lower()
        century_num = int(early_arabic_cent.group(2))
        
        # Convert century number to year (20th century = 1950)
        base_year = (century_num - 1) * 100 + 50
        
        if 'late' in part or 'end' in part:
            return base_year + 38
        elif 'early' in part or 'beginning' in part:
            return base_year - 38
        else:
            return base_year
    
    # Handle year ranges with slashes (e.g., "584‒602", "666/668", "686/687", "318/319‒341/342")
    # Note: uses various dash types (‒, –, -)
    slash_range = re.match(r'^(\d{1,4})[/‒–-](\d{1,4})(\s*г\.?)?(\s*(BC|AD|ВС))?$', date_str)
    if slash_range:
        year1 = int(slash_range.group(1))
        year2 = int(slash_range.group(2))
        suffix = slash_range.group(5)
        
        midpoint = (year1 + year2) / 2
        
        if suffix and ('BC' in suffix.upper() or 'ВС' in suffix):
            return -midpoint
        else:
            return midpoint
    
    # Handle complex slash ranges (e.g., "131/132–153/154", "15/14–9/8 BC")
    complex_slash = re.match(r'^(\d{1,4})/(\d{1,4})[-–](\d{1,4})/(\d{1,4})(\s*(BC|AD|ВС))?$', date_str)
    if complex_slash:
        year1_a = int(complex_slash.group(1))
        year1_b = int(complex_slash.group(2))
        year2_a = int(complex_slash.group(3))
        year2_b = int(complex_slash.group(4))
        suffix = complex_slash.group(6)
        
        # Use average of all years
        avg = (year1_a + year1_b + year2_a + year2_b) / 4
        
        if suffix and ('BC' in suffix.upper() or 'ВС' in suffix):
            return -avg
        else:
            return avg
    
    # Handle "or" alternatives (e.g., "596/597 or 598/599")
    or_alternative = re.search(r'(\d{1,4})/(\d{1,4})\s+or\s+(\d{1,4})/(\d{1,4})', date_str, re.IGNORECASE)
    if or_alternative:
        year1 = int(or_alternative.group(1))
        year2 = int(or_alternative.group(2))
        year3 = int(or_alternative.group(3))
        year4 = int(or_alternative.group(4))
        
        # Average all possibilities
        return (year1 + year2 + year3 + year4) / 4
    
    # Handle year with "г." suffix (Russian: год = year, e.g., "973 г.")
    year_g = re.match(r'^(\d{1,4})\s*г\.?(\s*(BC|AD|ВС))?$', date_str, re.IGNORECASE)
    if year_g:
        year = int(year_g.group(1))
        suffix = year_g.group(3)
        
        if suffix and ('BC' in suffix.upper() or 'ВС' in suffix):
            return -year
        else:
            return year
    
    # Handle "beginning/last quarter of I st – beginning of IInd century" style
    ordinal_range = re.search(
        r'(beginning|last|first|second|third|fourth)\s+quarter\s+of\s+the\s+([IVX]+)\s*(st|nd|rd|th)?\s*[-–]\s*(beginning|last|first|second|third|fourth)?\s*of\s+the\s+([IVX]+)\s*(st|nd|rd|th)?\s*century',
        date_str, re.IGNORECASE
    )
    if ordinal_range:
        quarter1 = ordinal_range.group(1).lower()
        roman1 = ordinal_range.group(2)
        quarter2 = ordinal_range.group(4).lower() if ordinal_range.group(4) else 'beginning'
        roman2 = ordinal_range.group(5)
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman1 in century_patterns and roman2 in century_patterns:
            year1 = century_patterns[roman1]
            year2 = century_patterns[roman2]
            
            # Adjust for quarters
            if 'last' in quarter1 or 'fourth' in quarter1:
                year1 += 38
            elif 'first' in quarter1 or 'beginning' in quarter1:
                year1 -= 38
            
            if 'beginning' in quarter2 or 'first' in quarter2:
                year2 -= 38
            
            return (year1 + year2) / 2
    
    # Handle "beginning of IIId century" ordinal style
    beginning_ordinal = re.search(
        r'(beginning|start|early)\s+of\s+the\s+([IVX]+)(st|nd|rd|th|d)\s*century',
        date_str, re.IGNORECASE
    )
    if beginning_ordinal:
        roman = beginning_ordinal.group(2)
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman in century_patterns:
            return century_patterns[roman] - 38
    
    # Handle "second half 2nd - first half 3rd century AD" with ordinals
    half_ordinal = re.search(
        r'(second|first)\s+half\s+(\d{1,2})(st|nd|rd|th)\s*[-–]\s*(first|second|last)\s+half\s+(\d{1,2})(st|nd|rd|th)\s*century',
        date_str, re.IGNORECASE
    )
    if half_ordinal:
        half1 = half_ordinal.group(1).lower()
        century1 = int(half_ordinal.group(2))
        half2 = half_ordinal.group(4).lower()
        century2 = int(half_ordinal.group(5))
        
        # Convert century number to year
        year1 = (century1 - 1) * 100 + 50
        year2 = (century2 - 1) * 100 + 50
        
        # Adjust for halves
        if 'second' in half1:
            year1 += 12
        elif 'first' in half1:
            year1 -= 12
        
        if 'first' in half2:
            year2 -= 12
        elif 'second' in half2:
            year2 += 12
        
        return (year1 + year2) / 2
    
    
    
    
    # Handle "X thousand years ago" format (e.g., "40-12 thousand years ago")
    thousand_range_match = re.search(r'(\d+)-(\d+)\s*thousand\s*years?\s*ago', date_str, re.IGNORECASE)
    if thousand_range_match:
        thou1 = int(thousand_range_match.group(1))
        thou2 = int(thousand_range_match.group(2))
        # Return midpoint in negative years
        return -((thou1 + thou2) / 2 * 1000)
    
    # Handle single "X thousand years ago"
    thousand_match = re.search(r'(\d+)\s*thousand\s*years?\s*ago', date_str, re.IGNORECASE)
    if thousand_match:
        thou = int(thousand_match.group(1))
        return -(thou * 1000)
    
    # Handle millennium BC/AD (e.g., "II millennium BC")
    millennium_single_match = re.search(r'\b([IVX]+)\s*millennium\s*(BC|AD)?\b', date_str, re.IGNORECASE)
    if millennium_single_match:
        roman_num = millennium_single_match.group(1)
        is_bc = millennium_single_match.group(2) and 'BC' in millennium_single_match.group(2).upper()
        
        # Convert Roman to Arabic for millennium
        millennium_map = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
            'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
        }
        
        if roman_num in millennium_map:
            mill_num = millennium_map[roman_num]
            # Millennium midpoint: II millennium BC = 2000-1000 BC -> midpoint 1500 BC
            if is_bc:
                return -((mill_num * 1000) - 500)  # e.g., II mill BC = -1500
            else:
                return (mill_num - 1) * 1000 + 500  # e.g., II mill AD = 1500
    
    # Handle millennium BC range (e.g., "150-33 millennium BC")
    millennium_match = re.search(r'(\d+)-(\d+)\s*millennium\s*BC', date_str, re.IGNORECASE)
    if millennium_match:
        mill1 = int(millennium_match.group(1))
        mill2 = int(millennium_match.group(2))
        # Convert millennium to years (150 million to 33 million years ago)
        # Using midpoint approximation
        return -(mill1 * 1000 + mill2 * 1000) / 2
    
    # Handle decades with 's' (e.g., "580-560s BC", "1920s")
    decade_range_match = re.search(r'(\d+)[-–](\d+)s\s*(BC)?', date_str, re.IGNORECASE)
    if decade_range_match:
        year1 = int(decade_range_match.group(1))
        year2 = int(decade_range_match.group(2))
        is_bc = bool(decade_range_match.group(3))
        midpoint = (year1 + year2) / 2
        return -midpoint if is_bc else midpoint
    
    # Handle single decade (e.g., "1920s", "580s BC")
    decade_match = re.search(r'(\d+)s\s*(BC)?', date_str, re.IGNORECASE)
    if decade_match:
        year = int(decade_match.group(1))
        is_bc = bool(decade_match.group(2))
        # Use middle of decade
        midpoint = year + 5
        return -midpoint if is_bc else midpoint
    
    # Handle "part of century" formats
    # "end of the VII century" -> last quarter (year 688)
    # "second half of the XIX century" -> third quarter (year 1862)
    # "first half of the XIX century" -> first quarter (year 1812)
    # "beginning of XX century" -> first quarter (year 1912)
    
    part_of_century_match = re.search(
        r'(end|ending|late|second half|first half|beginning|start|early|middle|mid).*?([IVX]+)\s*century\s*(BC|AD)?',
        date_str, re.IGNORECASE
    )
    if part_of_century_match:
        part = part_of_century_match.group(1).lower()
        roman = part_of_century_match.group(2)
        is_bc = part_of_century_match.group(3) and 'BC' in part_of_century_match.group(3).upper()
        
        # Get base century year
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman in century_patterns:
            base_year = century_patterns[roman]
            
            # Adjust based on part of century
            if 'end' in part or 'late' in part or 'ending' in part:
                # Last quarter: e.g., VII century (601-700) -> 688 (midpoint of 676-700)
                year = base_year + 38  # +38 to get to 88
            elif 'second half' in part:
                # Third quarter: e.g., XIX century (1801-1900) -> 1862 (midpoint of 1851-1875)
                year = base_year + 12  # +12 to get to 62
            elif 'first half' in part or 'early' in part or 'beginning' in part or 'start' in part:
                # First quarter: e.g., XIX century (1801-1900) -> 1812 (midpoint of 1801-1825)
                year = base_year - 38  # -38 to get to 12
            elif 'middle' in part or 'mid' in part:
                # Keep midpoint
                year = base_year
            else:
                year = base_year
            
            return -year if is_bc else year
    
    # Handle quarter ranges between centuries (e.g., "XIX - first q. XX century AD")
    quarter_range_match = re.search(
        r'([IVX]+)\s*-\s*(first|second|third|fourth|last)\s*q\.?\s*([IVX]+)\s*century\s*(BC|AD)?',
        date_str, re.IGNORECASE
    )
    if quarter_range_match:
        roman1 = quarter_range_match.group(1)
        quarter = quarter_range_match.group(2).lower()
        roman2 = quarter_range_match.group(3)
        is_bc = quarter_range_match.group(4) and 'BC' in quarter_range_match.group(4).upper()
        
        century_patterns = {
            'XX': 1950, 'XIX': 1850, 'XVIII': 1750, 'XVII': 1650, 'XVI': 1550,
            'XV': 1450, 'XIV': 1350, 'XIII': 1250, 'XII': 1150, 'XI': 1050,
            'X': 950, 'IX': 850, 'VIII': 750, 'VII': 650, 'VI': 550,
            'V': 450, 'IV': 350, 'III': 250, 'II': 150, 'I': 50,
        }
        
        if roman1 in century_patterns and roman2 in century_patterns:
            year1 = century_patterns[roman1]
            year2 = century_patterns[roman2]
            
            # Adjust year2 based on quarter
            if 'first' in quarter:
                year2 = year2 - 38  # First quarter
            elif 'second' in quarter:
                year2 = year2 - 12  # Second quarter
            elif 'third' in quarter:
                year2 = year2 + 12  # Third quarter
            elif 'fourth' in quarter or 'last' in quarter:
                year2 = year2 + 38  # Fourth quarter
            
            midpoint = (year1 + year2) / 2
            return -midpoint if is_bc else midpoint
    
    
    # Handle Roman numeral centuries
    century_patterns = {
        'XX': 1950,   # 20th century (1901-2000)
        'XIX': 1850,  # 19th century (1801-1900)
        'XVIII': 1750, # 18th century (1701-1800)
        'XVII': 1650,  # 17th century (1601-1700)
        'XVI': 1550,   # 16th century (1501-1600)
        'XV': 1450,    # 15th century (1401-1500)
        'XIV': 1350,   # 14th century (1301-1400)
        'XIII': 1250,  # 13th century (1201-1300)
        'XII': 1150,   # 12th century (1101-1200)
        'XI': 1050,    # 11th century (1001-1100)
        'X': 950,      # 10th century (901-1000)
        'IX': 850,     # 9th century (801-900)
        'VIII': 750,   # 8th century (701-800)
        'VII': 650,    # 7th century (601-700)
        'VI': 550,     # 6th century (501-600)
        'V': 450,      # 5th century (401-500)
        'IV': 350,     # 4th century (301-400)
        'III': 250,    # 3rd century (201-300)
        'II': 150,     # 2nd century (101-200)
        'I': 50,       # 1st century (1-100)
    }
    
    # Check for century BC
    for numeral, year in century_patterns.items():
        pattern = rf'\b{numeral}\b\s*century\s*BC'
        if re.search(pattern, date_str, re.IGNORECASE):
            # BC centuries need to be negative
            if numeral == 'I':
                return -50
            elif numeral == 'II':
                return -150
            elif numeral == 'III':
                return -250
            elif numeral == 'IV':
                return -350
            elif numeral == 'V':
                return -450
            elif numeral == 'VI':
                return -550
            elif numeral == 'VII':
                return -650
            elif numeral == 'VIII':
                return -750
    
    # Check for century AD or just century
    for numeral, year in century_patterns.items():
        pattern = rf'\b{numeral}\b\s*century'
        if re.search(pattern, date_str, re.IGNORECASE):
            return year
    
    # Handle century ranges like "V-VI century AD"
    range_match = re.search(r'([IVX]+)-([IVX]+)\s*century', date_str, re.IGNORECASE)
    if range_match:
        num1 = range_match.group(1)
        num2 = range_match.group(2)
        if num1 in century_patterns and num2 in century_patterns:
            year1 = century_patterns[num1]
            year2 = century_patterns[num2]
            # Check if BC
            if 'BC' in date_str:
                return -(year1 + year2) / 2
            else:
                return (year1 + year2) / 2
    
    # Handle complex ranges like "VI century BC - IV century"
    complex_match = re.search(r'([IVX]+)\s*century\s*BC\s*-\s*([IVX]+)\s*century(?!\s*BC)', date_str, re.IGNORECASE)
    if complex_match:
        bc_num = complex_match.group(1)
        ad_num = complex_match.group(2)
        if bc_num in century_patterns and ad_num in century_patterns:
            bc_year = -century_patterns[bc_num]
            ad_year = century_patterns[ad_num]
            return (bc_year + ad_year) / 2
    
    # Handle simple year ranges (e.g., "1840-1850")
    year_range_match = re.match(r'^(\d{4})-(\d{4})$', date_str)
    if year_range_match:
        year1 = int(year_range_match.group(1))
        year2 = int(year_range_match.group(2))
        return (year1 + year2) / 2
    
    # Handle single year (e.g., "1900")
    year_match = re.match(r'^(\d{4})$', date_str)
    if year_match:
        return int(year_match.group(1))
    
    return None

def create_date_normalized(row):
    """
    Create normalized date string based on extracted year
    Returns format like "1500 BC", "1850 AD", "24000 BC" for display
    """
    year = None
    
    # Try year_for_timeline first
    if pd.notna(row.get('year_for_timeline')):
        timeline_val = row['year_for_timeline']
        if isinstance(timeline_val, str):
            year_match = re.match(r'^(\d{4})', timeline_val)
            if year_match:
                year = int(year_match.group(1))
        else:
            year = float(timeline_val)
    
    # If no year_for_timeline, try to extract from 'date' column
    if year is None and pd.notna(row.get('date')):
        year = extract_year_from_date(row['date'])
    
    # If still no year, try existing date_normalized
    if year is None and pd.notna(row.get('date_normalized')):
        date_norm = row['date_normalized']
        if isinstance(date_norm, str) and date_norm != '':
            if re.match(r'^\d{4}-\d{4}$', date_norm):
                parts = date_norm.split('-')
                year = (int(parts[0]) + int(parts[1])) / 2
            elif re.match(r'^\d{4}$', date_norm):
                year = int(date_norm)
    
    if year is None:
        return ''
    
    # Format the normalized date
    if year < 0:
        return f"{int(abs(year))} BC"
    else:
        return f"{int(year)} AD"

def assign_period_category(row):
    """
    Assigns a historical period based on the year
    Priority: year_for_timeline > date column
    """
    year = None
    
    # Try year_for_timeline first (if it's already a timestamp, extract year)
    if pd.notna(row.get('year_for_timeline')):
        timeline_val = row['year_for_timeline']
        if isinstance(timeline_val, str):
            # If it's a date string like "1900-01-01"
            year_match = re.match(r'^(\d{4})', timeline_val)
            if year_match:
                year = int(year_match.group(1))
        else:
            year = float(timeline_val)
    
    # If no year_for_timeline, try to extract from 'date' column
    if year is None and pd.notna(row.get('date')):
        year = extract_year_from_date(row['date'])
    
    # If still no year, try date_normalized
    if year is None and pd.notna(row.get('date_normalized')):
        date_norm = row['date_normalized']
        if isinstance(date_norm, str) and date_norm != '':
            # Check if it's a year range like "1601-1700"
            if re.match(r'^\d{4}-\d{4}$', date_norm):
                parts = date_norm.split('-')
                year = (int(parts[0]) + int(parts[1])) / 2
            # Check if it's a single year
            elif re.match(r'^\d{4}$', date_norm):
                year = int(date_norm)
    
    if year is None:
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
    
    # Handle overlapping periods with priority rules
    if len(matching_periods) == 1:
        return matching_periods[0]['label']
    
    period_names = [p['name'] for p in matching_periods]
    
    # Priority rules for overlaps
    # Mongol period vs Galicia-Volhynia
    if 'Mongol Invasion and Domination' in period_names and 'Kingdom of Galicia-Volhynia' in period_names:
        if year < 1300:
            return next(p['label'] for p in matching_periods if p['name'] == 'Mongol Invasion and Domination')
        else:
            return next(p['label'] for p in matching_periods if p['name'] == 'Kingdom of Galicia-Volhynia')
    
    # Kievan Rus' takes precedence over Galicia-Volhynia
    if 'Kievan Rus\' Period' in period_names and 'Kingdom of Galicia-Volhynia' in period_names:
        return next(p['label'] for p in matching_periods if p['name'] == 'Kievan Rus\' Period')
    
    # Scythian-Sarmatian vs Greek-Roman overlap
    if 'Scythian-Sarmatian Era' in period_names and 'Greek and Roman Period' in period_names:
        # Prefer Greek-Roman for later dates
        if year > 0:
            return next(p['label'] for p in matching_periods if p['name'] == 'Greek and Roman Period')
        else:
            return next(p['label'] for p in matching_periods if p['name'] == 'Scythian-Sarmatian Era')
    
    # Migration Period vs Early Medieval
    if 'Migration Period' in period_names and 'Early Medieval Period' in period_names:
        if year < 650:
            return next(p['label'] for p in matching_periods if p['name'] == 'Migration Period')
        else:
            return next(p['label'] for p in matching_periods if p['name'] == 'Early Medieval Period')
    
    # Default: return first match
    return matching_periods[0]['label']

def main(input_file, output_file):
    """Main function to add period categories"""
    
    print("\n" + "="*70)
    print("ADDING HISTORICAL PERIOD CATEGORIES TO UKRAINIAN STOLEN OBJECTS")
    print("="*70 + "\n")
    
    # Read CSV
    print(f"📖 Reading file: {input_file}")
    df = pd.read_csv(input_file)
    print(f"✓ {len(df)} objects loaded\n")
    
    # Show available date columns
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'year' in col.lower()]
    print(f"📅 Available date columns: {', '.join(date_cols)}\n")
    
    
    # Update date_normalized column (overwrite with normalized year format)
    print("📅 Updating date_normalized column...")
    df['date_normalized'] = df.apply(create_date_normalized, axis=1)
    
    # Add period category
    print("🔧 Assigning historical periods...")
    print("   → Priority: year_for_timeline > date > date_normalized\n")
    
    df['period_category'] = df.apply(assign_period_category, axis=1)
    
    
    # Statistics
    print("\n📊 Date normalization statistics:")
    print("="*70)
    
    has_date_norm = df['date_normalized'].notna() & (df['date_normalized'] != '')
    
    print(f"  Objects with date_normalized: {has_date_norm.sum()}")
    print(f"  Objects without date_normalized: {(~has_date_norm).sum()}")
    
    print("\n📊 Period assignment statistics:")
    print("="*70)
    
    has_period = df['period_category'] != 'Unknown Period'
    print(f"  Objects assigned to a period: {has_period.sum()} ({(has_period.sum()/len(df)*100):.1f}%)")
    print(f"  Objects remaining as 'Unknown Period': {(~has_period).sum()} ({((~has_period).sum()/len(df)*100):.1f}%)")
    
    print("\n📊 Period distribution:")
    print("="*70)
    
    period_counts = df['period_category'].value_counts().sort_index()
    for period, count in period_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {period}: {count} ({percentage:.1f}%)")
    
    # Show examples for each period
    print("\n📋 Examples by period (showing 2 per period):")
    print("="*70)
    
    for period in sorted(df['period_category'].unique()):
        if period != 'Unknown Period' and pd.notna(period):
            period_objects = df[df['period_category'] == period][['name', 'date', 'date_normalized', 'year_for_timeline']].head(2)
            
            if len(period_objects) > 0:
                print(f"\n{period}:")
                for idx, row in period_objects.iterrows():
                    print(f"  • {row['name']}")
                    if pd.notna(row['date']):
                        print(f"    Original: {row['date']}", end='')
                    if pd.notna(row['date_normalized']) and row['date_normalized'] != '':
                        print(f" | Normalized: {row['date_normalized']}", end='')
                    if pd.notna(row['year_for_timeline']):
                        print(f" | Timeline: {row['year_for_timeline']}", end='')
                    print()
    
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
    print(f"📊 Objects with periods: {has_period.sum()}")
    print(f"📊 Unique periods: {df['period_category'].nunique()}")
    
    print("\n" + "="*70 + "\n")
    
    return df

# Execute
if __name__ == "__main__":
    input_file = 'data_stolen/stolen_objects_ukraine_timestamp.csv'
    output_file = 'data_stolen/1_stolen_objects_periods.csv'
    
    try:
        df_with_periods = main(input_file, output_file)
        
        # Show preview
        print("\n🔍 Preview of data with periods:")
        print("="*70)
        preview_cols = ['name', 'date', 'date_normalized', 'period_category']
        print(df_with_periods[preview_cols].head(10).to_string())
        print("\n")
        
    except FileNotFoundError:
        print(f"\n✗ ERROR: File not found '{input_file}'")
        print("   Make sure the file is in the current directory!")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()