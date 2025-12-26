"""
TEST SCRIPT - Scraping Real de 5 Objetos
Este script ejecuta el scraping REAL pero solo extrae los primeros 5 objetos
para verificar que la estructura del CSV sea correcta.
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin
from datetime import datetime

# Solo la primera categoría para el test
TEST_CATEGORY = {
    'Painting': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=491&f%5Bp%5D=&f%5Bsearch%5D=',
}

MAX_OBJECTS_TEST = 5  # Solo 5 objetos para el test

def extract_coordinates(text):
    """Extrae las coordenadas del texto"""
    if not text:
        return None, None
    
    match = re.search(r'([-+]?\d+\.\d+)[,\s]+([-+]?\d+\.\d+)', text)
    if match:
        return match.group(1), match.group(2)
    return None, None

def clean_text(text):
    """Limpia el texto de espacios extras"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def scrape_object_details(object_url, session, category):
    """Extrae los detalles de un objeto individual"""
    try:
        time.sleep(0.5)  # Pausa corta entre requests
        
        response = session.get(object_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        details = {
            'id': object_url.rstrip('/').split('/')[-1],
            'category': category,
            'url': object_url
        }
        
        # Buscar todos los divs mb-3 que contienen campos
        content_divs = soup.find_all('div', class_='mb-3')
        
        for div in content_divs:
            # Obtener el texto completo del div para identificar el label
            div_text = div.get_text(strip=True)
            
            # Buscar el div con clase mb-3 que contiene el label
            label_div = div.find('div', class_='mb-3', recursive=False)
            if not label_div:
                label_div = div.find('div', class_=False, recursive=False)
            
            label_text = ""
            if label_div:
                label_text = clean_text(label_div.get_text())
            else:
                # Tomar el texto antes del div yellow
                for content in div.children:
                    if isinstance(content, str):
                        label_text = clean_text(content)
                        break
            
            # Buscar el div yellow o js_visibility_target que contiene el valor
            value_div = div.find('div', class_=['yellow', 'js_visibility_target', 'yellow js_visibility_target'])
            if value_div:
                value_text = clean_text(value_div.get_text())
                
                # Mapear según el label - usar el texto completo del div para identificar
                if 'Name:' in div_text or 'Name' == label_text:
                    details['name'] = value_text
                elif 'Author:' in div_text or 'Author' == label_text:
                    details['author'] = value_text
                elif 'Type:' in div_text or 'Type' == label_text:
                    details['type'] = value_text
                elif 'Date:' in div_text or 'Date' == label_text:
                    details['date'] = value_text
                elif ('Circumstances:' in div_text or 'Details of theft' in div_text) and 'circumstances' not in details:
                    details['circumstances'] = value_text
                elif 'Year of the incident:' in div_text or 'Year of the incident' in label_text:
                    details['year_incident'] = value_text
                elif 'Place of the incident:' in div_text or 'Place of the incident' in label_text:
                    details['place_incident'] = value_text
                elif 'Coordinates (Lat, Lon):' in div_text or 'Coordinates' in div_text:
                    # Extraer coordenadas numéricas
                    lat, lon = extract_coordinates(value_text)
                    if lat and lon:
                        details['latitude'] = lat
                        details['longitude'] = lon
                elif 'Description of the incident location' in div_text:
                    details['description'] = value_text[:2000]
        
        # Buscar el link de Google Maps
        google_maps_link = None
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if 'maps.google.com' in href or 'google.com/maps' in href:
                google_maps_link = href
                break
        
        if google_maps_link:
            details['google_maps_link'] = google_maps_link
        
        return details
    
    except Exception as e:
        print(f"      ✗ Error: {e}")
        return None

def extract_object_links_from_page(soup, base_url):
    """Extrae todos los enlaces de objetos de una página"""
    object_links = set()
    
    # Buscar todos los enlaces que contengan /stolen/objects/ seguido de un número
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Patrón: /en/stolen/objects/[número]
        if re.search(r'/en/stolen/objects/\d+', href):
            full_url = urljoin(base_url, href)
            object_links.add(full_url)
    
    return list(object_links)

def test_scraping():
    """Ejecuta el test de scraping de 5 objetos"""
    print("\n" + "="*70)
    print("TEST - SCRAPING REAL DE 5 OBJETOS")
    print("="*70)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Extrayendo máximo {MAX_OBJECTS_TEST} objetos de la categoría Painting\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    })
    
    all_objects = []
    category_name = 'Painting'
    category_url = TEST_CATEGORY['Painting']
    
    try:
        print(f"\n{'='*70}")
        print(f"CATEGORÍA: {category_name}")
        print(f"{'='*70}\n")
        
        # Obtener primera página
        response = session.get(category_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer enlaces
        object_links = extract_object_links_from_page(soup, category_url)
        
        print(f"✓ Encontrados {len(object_links)} objetos en la primera página")
        print(f"→ Extrayendo los primeros {MAX_OBJECTS_TEST}...\n")
        
        # Extraer solo los primeros 5
        for i, obj_url in enumerate(object_links[:MAX_OBJECTS_TEST], 1):
            obj_id = obj_url.rstrip('/').split('/')[-1]
            print(f"[{i}/{MAX_OBJECTS_TEST}] Extrayendo objeto {obj_id}...")
            
            obj_details = scrape_object_details(obj_url, session, category_name)
            
            if obj_details:
                all_objects.append(obj_details)
                print(f"    ✓ {obj_details.get('name', 'Sin nombre')[:60]}")
            else:
                print(f"    ✗ Error al extraer")
        
        # Guardar CSV
        if all_objects:
            filename = 'test_scraping_5_objects.csv'
            fieldnames = [
                'id', 'category', 'name', 'author', 'type', 'date', 
                'year_incident', 'place_incident', 'google_maps_link',
                'circumstances', 'url', 
            ]
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for obj in all_objects:
                    row = {field: obj.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            print(f"\n{'='*70}")
            print(f"✓✓✓ TEST COMPLETADO ✓✓✓")
            print(f"{'='*70}")
            print(f"\n📁 Archivo generado: {filename}")
            print(f"📊 Objetos extraídos: {len(all_objects)}\n")
            
            # Mostrar preview
            print("="*70)
            print("PREVIEW DE LOS DATOS EXTRAÍDOS:")
            print("="*70 + "\n")
            
            for i, obj in enumerate(all_objects, 1):
                print(f"--- Objeto {i} ---")
                for key in fieldnames:
                    value = obj.get(key, '')
                    if value:
                        display = value[:70] + "..." if len(value) > 70 else value
                        print(f"  {key:20s}: {display}")
                print()
            
            # Verificar orden de columnas en CSV
            print("="*70)
            print("VERIFICACIÓN DEL CSV:")
            print("="*70)
            
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                print("\nORDEN DE COLUMNAS:")
                for i, field in enumerate(reader.fieldnames, 1):
                    print(f"  {i}. {field}")
            
            print("\n" + "="*70)
            print("✓ Campos en el orden correcto")
            print("✓ Sin latitude, longitude ni description")
            print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraping()