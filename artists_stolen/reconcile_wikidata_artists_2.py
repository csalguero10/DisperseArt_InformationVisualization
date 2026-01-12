#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Reconciliación de Artistas con Wikidata
Alternativa al servicio de reconciliación de OpenRefine

Uso:
    python reconcile_wikidata.py artists_for_openrefine.csv

Autor: Claude
Fecha: 2026-01-09
"""

import pandas as pd
import requests
import time
import json
from urllib.parse import quote
from datetime import datetime

class WikidataReconciler:
    """Clase para reconciliar artistas con Wikidata"""
    
    def __init__(self):
        self.base_url = "https://www.wikidata.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArtistReconciliation/1.0 (Ukrainian Heritage Project)'
        })
    
    def search_entity(self, artist_name, limit=5):
        """
        Busca una entidad en Wikidata
        
        Args:
            artist_name (str): Nombre del artista a buscar
            limit (int): Número máximo de resultados
        
        Returns:
            list: Lista de candidatos encontrados
        """
        params = {
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "type": "item",
            "limit": limit,
            "search": artist_name
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get("search", [])
            
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Error en petición: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"  ⚠️  Error decodificando JSON: {e}")
            return []
    
    def get_entity_data(self, entity_id):
        """
        Obtiene datos detallados de una entidad
        
        Args:
            entity_id (str): ID de Wikidata (ej: Q123456)
        
        Returns:
            dict: Datos de la entidad
        """
        params = {
            "action": "wbgetentities",
            "format": "json",
            "ids": entity_id,
            "props": "claims|labels|descriptions",
            "languages": "en"
        }
        
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "entities" in data and entity_id in data["entities"]:
                return data["entities"][entity_id]
                
        except Exception as e:
            print(f"  ⚠️  Error obteniendo datos de {entity_id}: {e}")
        
        return None
    
    def extract_claim_value(self, claims, property_id):
        """
        Extrae el valor de una propiedad de las claims
        
        Args:
            claims (dict): Claims de la entidad
            property_id (str): ID de la propiedad (ej: P569 para fecha de nacimiento)
        
        Returns:
            str: Valor de la propiedad o None
        """
        if property_id not in claims:
            return None
        
        try:
            claim = claims[property_id][0]  # Primera claim
            mainsnak = claim.get("mainsnak", {})
            datavalue = mainsnak.get("datavalue", {})
            
            if datavalue.get("type") == "time":
                # Fecha
                time_value = datavalue.get("value", {}).get("time", "")
                # Extraer solo el año: +1862-08-27T00:00:00Z -> 1862
                if time_value.startswith("+") or time_value.startswith("-"):
                    year = time_value[1:5]
                    return year
                return time_value[:4]
            
            elif datavalue.get("type") == "wikibase-entityid":
                # Entidad (para nacionalidad, ocupación, etc.)
                return datavalue.get("value", {}).get("id", "")
            
            elif datavalue.get("type") == "string":
                # String simple
                return datavalue.get("value", "")
        
        except (IndexError, KeyError, TypeError) as e:
            pass
        
        return None
    
    def is_painter(self, entity_data):
        """
        Verifica si una entidad es un pintor
        
        Args:
            entity_data (dict): Datos de la entidad
        
        Returns:
            bool: True si es pintor
        """
        if not entity_data or "claims" not in entity_data:
            return False
        
        claims = entity_data["claims"]
        
        # P106 = occupation
        if "P106" in claims:
            for claim in claims["P106"]:
                try:
                    occupation_id = claim["mainsnak"]["datavalue"]["value"]["id"]
                    # Q1028181 = painter
                    if occupation_id == "Q1028181":
                        return True
                except (KeyError, TypeError):
                    pass
        
        return False
    
    def reconcile_artist(self, artist_name, verified_name=None, cyrillic=None):
        """
        Reconcilia un artista con Wikidata usando múltiples variantes del nombre
        
        Args:
            artist_name (str): Nombre del artista
            verified_name (str): Nombre verificado/corregido
            cyrillic (str): Nombre en cirílico
        
        Returns:
            dict: Información del artista reconciliado
        """
        print(f"  🔍 Buscando: {artist_name}")
        
        # Buscar candidatos con todas las variantes disponibles
        all_candidates = []
        search_names = [artist_name]
        
        # Agregar variantes si están disponibles
        if verified_name and verified_name != artist_name and pd.notna(verified_name):
            search_names.append(verified_name)
            print(f"     También: {verified_name}")
        
        if cyrillic and pd.notna(cyrillic):
            search_names.append(cyrillic)
            print(f"     También: {cyrillic}")
        
        # Buscar con cada variante
        for name in search_names:
            candidates = self.search_entity(name, limit=5)
            all_candidates.extend(candidates)
            if candidates:
                print(f"     ✓ {len(candidates)} resultados con '{name}'")
        
        # Eliminar duplicados por ID
        seen_ids = set()
        unique_candidates = []
        for candidate in all_candidates:
            entity_id = candidate.get("id")
            if entity_id not in seen_ids:
                seen_ids.add(entity_id)
                unique_candidates.append(candidate)
        
        candidates = unique_candidates
        
        if not candidates:
            print(f"  ❌ Sin resultados")
            return {
                'artist_name': artist_name,
                'wikidata_id': None,
                'wikidata_label': None,
                'description': None,
                'birth_year': None,
                'death_year': None,
                'is_painter': False,
                'match_score': 0
            }
        
        # Buscar el mejor candidato (que sea pintor)
        best_candidate = None
        best_score = 0
        
        for candidate in candidates:
            entity_id = candidate.get("id")
            
            # Obtener datos completos
            entity_data = self.get_entity_data(entity_id)
            
            if entity_data and self.is_painter(entity_data):
                # Este candidato es pintor, darle prioridad
                match_score = 100  # Score máximo para pintores
                
                if match_score > best_score:
                    best_score = match_score
                    best_candidate = {
                        'entity_id': entity_id,
                        'entity_data': entity_data,
                        'candidate_info': candidate
                    }
                    break  # Usar el primer pintor encontrado
        
        # Si no encontramos pintores, usar el primer resultado
        if not best_candidate and candidates:
            candidate = candidates[0]
            entity_id = candidate.get("id")
            entity_data = self.get_entity_data(entity_id)
            
            best_candidate = {
                'entity_id': entity_id,
                'entity_data': entity_data,
                'candidate_info': candidate
            }
            best_score = 50  # Score bajo para no-pintores
        
        if not best_candidate:
            print(f"  ❌ Sin candidatos válidos")
            return {
                'artist_name': artist_name,
                'wikidata_id': None,
                'wikidata_label': None,
                'description': None,
                'birth_year': None,
                'death_year': None,
                'is_painter': False,
                'match_score': 0
            }
        
        # Extraer información
        entity_id = best_candidate['entity_id']
        entity_data = best_candidate['entity_data']
        candidate_info = best_candidate['candidate_info']
        
        claims = entity_data.get("claims", {}) if entity_data else {}
        
        birth_year = self.extract_claim_value(claims, "P569")  # Fecha de nacimiento
        death_year = self.extract_claim_value(claims, "P570")  # Fecha de muerte
        
        result = {
            'artist_name': artist_name,
            'wikidata_id': entity_id,
            'wikidata_label': candidate_info.get("label", ""),
            'description': candidate_info.get("description", ""),
            'birth_year': birth_year,
            'death_year': death_year,
            'is_painter': self.is_painter(entity_data),
            'match_score': best_score,
            'url': f"https://www.wikidata.org/wiki/{entity_id}"
        }
        
        print(f"  ✅ Encontrado: {result['wikidata_label']} ({entity_id})")
        if birth_year or death_year:
            print(f"     {birth_year or '?'}-{death_year or '?'}")
        if result['description']:
            print(f"     {result['description']}")
        
        return result


def reconcile_csv(input_file, output_file='data_stolen/artists_stolen/corrected_artists_reconciled.csv'):
    """
    Reconcilia artistas desde un CSV
    
    Args:
        input_file (str): Ruta al CSV de entrada
        output_file (str): Ruta al CSV de salida
    """
    import os
    
    print("="*80)
    print("🎨 RECONCILIACIÓN DE ARTISTAS CON WIKIDATA")
    print("="*80)
    print()
    
    # Cargar CSV
    try:
        df = pd.read_csv(input_file)
        print(f"✅ Cargado: {input_file}")
        print(f"📊 Total de artistas: {len(df)}")
        print()
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo {input_file}")
        return
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        return
    
    # Crear directorio de salida si no existe
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"📁 Creado directorio: {output_dir}")
    
    # Inicializar reconciliador
    reconciler = WikidataReconciler()
    
    # Procesar artistas
    results = []
    start_time = datetime.now()
    
    for idx, row in df.iterrows():
        artist_name = row.get('artist_name', '')
        verified_name = row.get('verified_name', '')
        cyrillic = row.get('cyrillic', '')
        
        if pd.isna(artist_name) or artist_name == '':
            continue
        
        print(f"\n[{idx+1}/{len(df)}]", end=" ")
        
        # Reconciliar con todas las variantes
        result = reconciler.reconcile_artist(artist_name, verified_name, cyrillic)
        
        # Agregar información adicional del CSV original
        result['works_count'] = row.get('works_count', 1)
        
        results.append(result)
        
        # Pausa para no saturar la API
        time.sleep(0.5)
        
        # Guardar progreso cada 20 artistas
        if (idx + 1) % 20 == 0:
            temp_df = pd.DataFrame(results)
            # Guardar archivo temporal en el directorio actual
            temp_filename = 'temp_reconciliation_progress.csv'
            temp_df.to_csv(temp_filename, index=False)
            print(f"\n  💾 Progreso guardado: {idx+1}/{len(df)} artistas")
    
    # Guardar resultados finales
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_file, index=False)
    
    # Estadísticas
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("📊 RESULTADOS DE LA RECONCILIACIÓN")
    print("="*80)
    
    total = len(results_df)
    matched = results_df['wikidata_id'].notna().sum()
    painters = results_df['is_painter'].sum()
    high_confidence = (results_df['match_score'] >= 90).sum()
    
    print(f"\n✅ Artistas reconciliados: {matched}/{total} ({matched/total*100:.1f}%)")
    print(f"🎨 Confirmados como pintores: {painters} ({painters/total*100:.1f}%)")
    print(f"⭐ Alta confianza (score ≥90): {high_confidence} ({high_confidence/total*100:.1f}%)")
    print(f"⏱️  Tiempo total: {duration/60:.1f} minutos")
    print(f"\n📁 Archivo guardado: {output_file}")
    
    # Mostrar algunos ejemplos
    print("\n" + "="*80)
    print("🔍 EJEMPLOS DE RECONCILIACIÓN")
    print("="*80)
    
    matched_df = results_df[results_df['wikidata_id'].notna()].head(10)
    for idx, row in matched_df.iterrows():
        print(f"\n✅ {row['artist_name']}")
        print(f"   → {row['wikidata_label']} ({row['wikidata_id']})")
        if row['birth_year'] or row['death_year']:
            print(f"   → {row['birth_year'] or '?'}-{row['death_year'] or '?'}")
        if row['description']:
            print(f"   → {row['description']}")
    
    # Artistas no reconciliados
    unmatched_df = results_df[results_df['wikidata_id'].isna()]
    if len(unmatched_df) > 0:
        print("\n" + "="*80)
        print("❌ ARTISTAS SIN RECONCILIAR (Requieren búsqueda manual)")
        print("="*80)
        for idx, row in unmatched_df.head(20).iterrows():
            print(f"  • {row['artist_name']}")
        
        if len(unmatched_df) > 20:
            print(f"  ... y {len(unmatched_df)-20} más")
    
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)
    print(f"\n💡 Siguiente paso:")
    print(f"   1. Revisa el archivo: {output_file}")
    print(f"   2. Para artistas no reconciliados, búscalos manualmente en:")
    print(f"      https://www.wikidata.org/")
    print(f"   3. Importa el CSV en OpenRefine para extraer más propiedades")
    print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data_stolen/artists_stolen/name_corrections_applied (2).csv"
    
    reconcile_csv(input_file)