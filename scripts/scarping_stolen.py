import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin
from datetime import datetime

# Definir todas las categorías
CATEGORIES = {
    'Painting': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=491&f%5Bp%5D=&f%5Bsearch%5D=',
    'Sculpture': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=492&f%5Bp%5D=&f%5Bsearch%5D=',
    'Metal products': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=1038&f%5Bp%5D=&f%5Bsearch%5D=',
    'Ceramic products': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=1055&f%5Bp%5D=&f%5Bsearch%5D=',
    'Stone products': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=739&f%5Bp%5D=&f%5Bsearch%5D=',
    'Weapon': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=536&f%5Bp%5D=&f%5Bsearch%5D=',
    'Bone products': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=1057&f%5Bp%5D=&f%5Bsearch%5D=',
    'Numismatic': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=535&f%5Bp%5D=&f%5Bsearch%5D=',
    'Jewelry products': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=534&f%5Bp%5D=&f%5Bsearch%5D=',
    'Architectural details': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=1056&f%5Bp%5D=&f%5Bsearch%5D=',
    'Ceramic products 2': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=1037&f%5Bp%5D=&f%5Bsearch%5D=',
    'Glass objects': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=635&f%5Bp%5D=&f%5Bsearch%5D=',
    'Wood products': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=741&f%5Bp%5D=&f%5Bsearch%5D=',
    'Graphics': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=632&f%5Bp%5D=&f%5Bsearch%5D=',
    'Furniture': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=496&f%5Bp%5D=&f%5Bsearch%5D=',
    'Books': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=539&f%5Bp%5D=&f%5Bsearch%5D=',
    'Icon': 'https://war-sanctions.gur.gov.ua/en/stolen/objects?f%5Bt%5D=627&f%5Bp%5D=&f%5Bsearch%5D=',
}

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
            'url': object_url,
            'category': category
        }
        
        # Extraer todos los campos del objeto
        # Buscar todos los divs que contienen información
        content_divs = soup.find_all('div', class_='mb-3')
        
        for div in content_divs:
            text = div.get_text(separator='|', strip=True)
            
            # Separar label y valor
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) == 2:
                    label = clean_text(parts[0])
                    value = clean_text(parts[1])
                    
                    # Mapear campos
                    if label == 'Name':
                        details['name'] = value
                    elif label == 'Author':
                        details['author'] = value
                    elif label == 'Type':
                        details['type'] = value
                    elif label == 'Date':
                        details['date'] = value
                    elif label == 'Original name':
                        details['original_name'] = value
                    elif 'Circumstances' in label or 'Details of theft' in label:
                        details['circumstances'] = value
                    elif 'Year of the incident' in label:
                        details['year_incident'] = value
                    elif 'Place of the incident' in label:
                        details['place_incident'] = value
                        # Intentar extraer coordenadas
                        lat, lon = extract_coordinates(value)
                        if lat and lon:
                            details['latitude'] = lat
                            details['longitude'] = lon
                    elif 'country' in label.lower():
                        details['country'] = value
                    elif 'Museum' in label or 'Gallery' in label:
                        details['museum_origin'] = value
        
        # Buscar descripción en divs con clase yellow
        yellow_divs = soup.find_all('div', class_='yellow')
        for div in yellow_divs:
            text = clean_text(div.get_text())
            if len(text) > 30 and 'description' not in details:
                details['description'] = text[:1000]
                break
        
        # Buscar enlaces
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if href.startswith('http') and 'facebook' in href or 'google' in href:
                if href not in links:
                    links.append(href)
        
        details['links'] = '; '.join(links) if links else ''
        
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

def scrape_category(category_name, category_url, session):
    """Scraper para una categoría específica"""
    print(f"\n{'='*70}")
    print(f"CATEGORÍA: {category_name}")
    print(f"{'='*70}")
    
    category_objects = []
    seen_ids = set()  # Para detectar objetos duplicados
    page = 1
    consecutive_duplicates = 0  # Contador de páginas con duplicados
    
    while True:
        try:
            # Construir URL con paginación correcta
            if page == 1:
                url = category_url
            else:
                # Las URLs ya tienen parámetros, agregar &page=X&per-page=10
                url = f"{category_url}&page={page}&per-page=10"
            
            print(f"\nPágina {page}: {url}")
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer enlaces de objetos
            object_links = extract_object_links_from_page(soup, category_url)
            
            if not object_links:
                if page == 1:
                    print(f"  ⚠ No se encontraron objetos en la primera página")
                else:
                    print(f"  ✓ No hay más objetos en esta categoría (total páginas: {page-1})")
                break
            
            print(f"  Encontrados {len(object_links)} objetos en esta página")
            
            # Verificar si son objetos nuevos o duplicados
            new_objects = 0
            duplicates = 0
            
            # Extraer detalles de cada objeto
            for i, obj_url in enumerate(object_links, 1):
                obj_id = obj_url.rstrip('/').split('/')[-1]
                
                # Si ya vimos este objeto, es un duplicado
                if obj_id in seen_ids:
                    duplicates += 1
                    print(f"    [{i}/{len(object_links)}] {obj_url} [DUPLICADO]")
                    continue
                
                seen_ids.add(obj_id)
                print(f"    [{i}/{len(object_links)}] {obj_url}", end=' ')
                
                obj_data = scrape_object_details(obj_url, session, category_name)
                
                if obj_data:
                    category_objects.append(obj_data)
                    new_objects += 1
                    print(f"✓")
                else:
                    print(f"✗")
            
            # Si todos los objetos son duplicados, hemos terminado
            if duplicates == len(object_links):
                consecutive_duplicates += 1
                print(f"\n  ⚠ TODOS los objetos en esta página son duplicados ({consecutive_duplicates}° página duplicada)")
                
                # Si encontramos 2 páginas consecutivas con duplicados, terminamos
                if consecutive_duplicates >= 2:
                    print(f"  ✓ Fin de categoría detectado (páginas duplicadas)")
                    break
            else:
                consecutive_duplicates = 0  # Resetear contador si hay objetos nuevos
            
            print(f"\n  Subtotal categoría: {len(category_objects)} objetos")
            print(f"  Nuevos en esta página: {new_objects} | Duplicados: {duplicates}")
            
            # Si hay menos de 10 objetos, probablemente es la última página
            if len(object_links) < 10:
                print(f"  ℹ Última página detectada (menos de 10 objetos)")
                break
            
            # Si no hay objetos nuevos, también terminamos
            if new_objects == 0:
                print(f"  ✓ No hay objetos nuevos, fin de categoría")
                break
            
            page += 1
            time.sleep(1)  # Pausa entre páginas
            
        except Exception as e:
            print(f"\n  Error en página {page}: {e}")
            break
    
    return category_objects

def scrape_all_categories(categories=CATEGORIES, test_mode=False):
    """Scraper principal que recorre todas las categorías"""
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    })
    
    all_objects = []
    
    # En modo test, solo procesar las primeras 3 categorías
    categories_to_process = dict(list(categories.items())[:3]) if test_mode else categories
    
    for category_name, category_url in categories_to_process.items():
        try:
            category_objects = scrape_category(category_name, category_url, session)
            all_objects.extend(category_objects)
            
            print(f"\n{'='*70}")
            print(f"✓ {category_name}: {len(category_objects)} objetos extraídos")
            print(f"  TOTAL ACUMULADO: {len(all_objects)} objetos")
            print(f"{'='*70}")
            
            # GUARDAR PROGRESO después de cada categoría
            if all_objects:
                save_to_csv(all_objects, 'stolen_objects_ukraine_progress.csv')
                print(f"💾 Progreso guardado automáticamente ({len(all_objects)} objetos)")
            
            time.sleep(2)  # Pausa entre categorías
            
        except KeyboardInterrupt:
            print(f"\n\n⚠ Interrupción detectada por el usuario")
            print(f"💾 Guardando progreso antes de salir...")
            if all_objects:
                save_to_csv(all_objects, 'stolen_objects_ukraine_interrupted.csv')
            raise
            
        except Exception as e:
            print(f"\n✗ Error al procesar categoría {category_name}: {e}")
            continue
    
    return all_objects

def save_to_csv(objects, filename='stolen_objects_ukraine.csv'):
    """Guarda los objetos en un archivo CSV"""
    
    if not objects:
        print("\n⚠ No hay objetos para guardar")
        return
    
    # Definir campos en orden específico
    fieldnames = [
        'id', 'url', 'category', 'name', 'author', 'type', 'date', 
        'original_name', 'circumstances', 'year_incident', 'place_incident', 
        'latitude', 'longitude', 'country', 'museum_origin', 'description', 'links'
    ]
    
    # Agregar cualquier campo adicional que aparezca
    all_fields = set()
    for obj in objects:
        all_fields.update(obj.keys())
    
    for field in all_fields:
        if field not in fieldnames:
            fieldnames.append(field)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for obj in objects:
            row = {field: obj.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    print(f"\n{'='*70}")
    print(f"✓✓✓ DATOS GUARDADOS EN '{filename}' ✓✓✓")
    print(f"{'='*70}")

def print_statistics(objects):
    """Muestra estadísticas de los objetos extraídos"""
    
    if not objects:
        return
    
    print(f"\n{'='*70}")
    print("ESTADÍSTICAS FINALES")
    print(f"{'='*70}")
    print(f"\nTotal de objetos extraídos: {len(objects)}")
    
    # Contar por categoría
    print("\n--- Objetos por categoría ---")
    by_category = {}
    for obj in objects:
        cat = obj.get('category', 'Sin categoría')
        by_category[cat] = by_category.get(cat, 0) + 1
    
    for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")
    
    # Contar por tipo
    print("\n--- Objetos por tipo ---")
    by_type = {}
    for obj in objects:
        obj_type = obj.get('type', 'Sin especificar')
        by_type[obj_type] = by_type.get(obj_type, 0) + 1
    
    for obj_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {obj_type}: {count}")
    
    # Ejemplo de objeto
    print(f"\n--- Ejemplo del primer objeto ---")
    first = objects[0]
    for key, value in first.items():
        if value:
            display_value = str(value)[:80] if len(str(value)) > 80 else str(value)
            print(f"  {key}: {display_value}")

# EJECUTAR
if __name__ == "__main__":
    print("\n" + "="*70)
    print("WEB SCRAPER - Objetos Robados de Ucrania")
    print("https://war-sanctions.gur.gov.ua/en/stolen/objects/")
    print("="*70)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categorías a procesar: {len(CATEGORIES)}")
    
    # MODO TEST: Solo 3 categorías (para pruebas rápidas)
    print("\n⚠ MODO TEST ACTIVADO: Solo se procesarán las primeras 3 categorías")
    print("   Cada categoría mostrará TODAS sus páginas (10 objetos por página)")
    print("   Para procesar TODO, cambia test_mode=False en la línea siguiente\n")
    
    #objects = scrape_all_categories(test_mode=True)
    
    # MODO COMPLETO: Descomentar la siguiente línea y comentar la anterior
    objects = scrape_all_categories(test_mode=False)
    
    if objects:
        save_to_csv(objects)
        print_statistics(objects)
        
        print(f"\n{'='*70}")
        print("✓✓✓ SCRAPING COMPLETADO EXITOSAMENTE ✓✓✓")
        print(f"{'='*70}")
        print(f"\n📁 Archivos generados:")
        print(f"   - stolen_objects_ukraine.csv (archivo final)")
        print(f"   - stolen_objects_ukraine_progress.csv (respaldo automático)")
        print(f"{'='*70}\n")
    else:
        print("\n⚠ No se pudieron extraer objetos")