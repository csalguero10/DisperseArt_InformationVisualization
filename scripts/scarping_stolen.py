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
                elif ('Coordinates (Lat, Lon):' in div_text or 'Coordinates:' in div_text) and 'coordinates_found' not in details:
                    # Marcar que encontramos coordenadas pero no las guardamos
                    details['coordinates_found'] = True
        
        # Buscar el link de Google Maps
        google_maps_link = None
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            if 'maps.google.com' in href or 'google.com/maps' in href:
                google_maps_link = href
                break
        
        if google_maps_link:
            details['google_maps_link'] = google_maps_link
        
        # Limpiar campo temporal
        if 'coordinates_found' in details:
            del details['coordinates_found']
        
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
                print(f"   ⚠ No se encontraron más objetos en esta página")
                break
            
            print(f"   → Encontrados {len(object_links)} objetos en esta página")
            
            # Contar cuántos objetos son nuevos
            new_objects_count = 0
            duplicates_count = 0
            
            for obj_url in object_links:
                obj_id = obj_url.rstrip('/').split('/')[-1]
                
                if obj_id in seen_ids:
                    duplicates_count += 1
                    continue
                
                seen_ids.add(obj_id)
                new_objects_count += 1
                
                print(f"   [{len(category_objects)+1}] Extrayendo: {obj_id}")
                
                # Extraer detalles
                obj_details = scrape_object_details(obj_url, session, category_name)
                
                if obj_details:
                    category_objects.append(obj_details)
                    print(f"      ✓ Extraído: {obj_details.get('name', 'Sin nombre')[:50]}")
                else:
                    print(f"      ✗ No se pudieron extraer detalles")
            
            print(f"\n   📊 Resumen de página {page}:")
            print(f"      Objetos nuevos: {new_objects_count}")
            print(f"      Duplicados: {duplicates_count}")
            
            # Si todos los objetos eran duplicados, incrementar contador
            if new_objects_count == 0:
                consecutive_duplicates += 1
                print(f"   ⚠ Página completamente duplicada ({consecutive_duplicates} consecutivas)")
                
                # Si hay 2 páginas consecutivas con solo duplicados, asumir que terminamos
                if consecutive_duplicates >= 2:
                    print(f"   → Detectadas {consecutive_duplicates} páginas consecutivas duplicadas")
                    print(f"   → Asumiendo fin de categoría")
                    break
            else:
                consecutive_duplicates = 0
            
            # Verificar si hay botón "Next" o paginación
            pagination = soup.find('ul', class_='pagination')
            has_next = False
            
            if pagination:
                next_link = pagination.find('a', {'rel': 'next'})
                has_next = next_link is not None
            
            if not has_next and new_objects_count == 0:
                print(f"   → No hay más páginas disponibles")
                break
            
            page += 1
            time.sleep(1)  # Pausa entre páginas
            
        except requests.exceptions.RequestException as e:
            print(f"\n✗ Error de red en página {page}: {e}")
            break
        except Exception as e:
            print(f"\n✗ Error inesperado en página {page}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    return category_objects

def scrape_all_categories(test_mode=False, categories=CATEGORIES, max_objects_test=5):
    """Scraper principal que procesa todas las categorías"""
    
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
            # En modo test, verificar si ya alcanzamos el límite
            if test_mode and len(all_objects) >= max_objects_test:
                print(f"\n{'='*70}")
                print(f"✓ MODO TEST: Se alcanzó el límite de {max_objects_test} objetos")
                print(f"{'='*70}")
                break
            
            category_objects = scrape_category(category_name, category_url, session)
            
            # En modo test, limitar cuántos objetos agregar
            if test_mode:
                remaining = max_objects_test - len(all_objects)
                category_objects = category_objects[:remaining]
            
            all_objects.extend(category_objects)
            
            print(f"\n{'='*70}")
            print(f"✓ {category_name}: {len(category_objects)} objetos extraídos")
            print(f"  TOTAL ACUMULADO: {len(all_objects)} objetos")
            print(f"{'='*70}")
            
            # GUARDAR PROGRESO después de cada categoría
            if all_objects:
                print(f"\n💾 Guardando progreso automático...")
                saved = save_to_csv(all_objects, 'stolen_objects_ukraine_progress.csv')
                if saved:
                    print(f"✓ Progreso guardado: {len(all_objects)} objetos")
                else:
                    print(f"✗ Error al guardar progreso")
            
            time.sleep(2)  # Pausa entre categorías
            
        except KeyboardInterrupt:
            print(f"\n\n⚠ Interrupción detectada por el usuario")
            print(f"💾 Guardando progreso antes de salir...")
            if all_objects:
                saved = save_to_csv(all_objects, 'stolen_objects_ukraine_interrupted.csv')
                if not saved:
                    print(f"✗ No se pudo guardar el progreso")
            raise
            
        except Exception as e:
            print(f"\n✗ Error al procesar categoría {category_name}: {e}")
            continue
    
    return all_objects

def save_to_csv(objects, filename='stolen_objects_ukraine.csv'):
    """Guarda los objetos en un archivo CSV"""
    
    if not objects:
        print("\n⚠ No hay objetos para guardar")
        return False
    
    try:
        import os
        
        # Obtener ruta absoluta
        full_path = os.path.abspath(filename)
        
        # Definir campos en orden específico
        fieldnames = [
            'id', 'category', 'name', 'author', 'type', 'date', 
            'year_incident', 'place_incident', 'google_maps_link',
            'circumstances', 'url', 
        ]
        
        print(f"\n{'='*70}")
        print(f"💾 Guardando {len(objects)} objetos...")
        print(f"📁 Ubicación: {full_path}")
        print(f"{'='*70}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for obj in objects:
                row = {field: obj.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        # Verificar que el archivo se creó
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            file_size_mb = file_size / (1024 * 1024)
            print(f"\n✓✓✓ ARCHIVO GUARDADO EXITOSAMENTE ✓✓✓")
            print(f"📊 Tamaño: {file_size_mb:.2f} MB ({file_size:,} bytes)")
            print(f"📁 Ubicación completa: {full_path}")
            print(f"{'='*70}")
            return True
        else:
            print(f"\n✗ ERROR: El archivo no se creó")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR al guardar CSV: {e}")
        import traceback
        traceback.print_exc()
        return False

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
    
    # MODO TEST: Solo 5 objetos (para pruebas rápidas)
    print("\n⚠ MODO TEST ACTIVADO: Solo se extraerán los primeros 5 objetos")
    print("   Para procesar TODO, cambia test_mode=False en la línea siguiente\n")
    
    #objects = scrape_all_categories(test_mode=True, max_objects_test=5)
    
    # MODO COMPLETO: Descomentar la siguiente línea y comentar la anterior
    objects = scrape_all_categories(test_mode=False)
    
    # Guardar resultados finales
    if objects:
        print(f"\n{'='*70}")
        print(f"Preparando guardado final de {len(objects)} objetos...")
        print(f"{'='*70}\n")
        
        saved = save_to_csv(objects)
        
        if saved:
            print_statistics(objects)
            
            print(f"\n{'='*70}")
            print("✓✓✓ SCRAPING COMPLETADO EXITOSAMENTE ✓✓✓")
            print(f"{'='*70}")
            print(f"\n📁 Archivos generados:")
            print(f"   ✓ stolen_objects_ukraine.csv (archivo final)")
            print(f"   ✓ stolen_objects_ukraine_progress.csv (respaldo automático)")
            print(f"{'='*70}\n")
        else:
            print(f"\n✗ ERROR: No se pudo guardar el archivo final")
            print(f"Los datos están en memoria pero no se guardaron en disco")
            print(f"Intenta ejecutar manualmente:")
            print(f"   save_to_csv(objects, 'manual_save.csv')")
    else:
        print("\n⚠ No se pudieron extraer objetos")