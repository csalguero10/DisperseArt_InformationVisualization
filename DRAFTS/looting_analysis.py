import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# 1. CARGAR Y PREPARAR DATOS
# ============================================================================

def load_and_prepare_data(csv_path='raw_data/stolen_objects_ukraine.csv'):
    """Carga y prepara los datos para análisis de russification"""
    
    print("="*70)
    print("ANÁLISIS: LOOTING COMO ESTRATEGIA DE RUSSIFICATION")
    print("="*70)
    
    df = pd.read_csv(csv_path)
    print(f"\n✓ Datos cargados: {len(df)} objetos robados")
    
    # Convertir año a numérico - MEJORADO
    def extract_year(year_value):
        """Extrae el año de diferentes formatos"""
        if pd.isna(year_value):
            return None
        
        year_str = str(year_value).strip()
        
        # Buscar 4 dígitos que parezcan un año (1900-2099)
        import re
        match = re.search(r'(19\d{2}|20\d{2})', year_str)
        if match:
            return int(match.group(1))
        
        # Intentar conversión directa
        try:
            year = int(float(year_str))
            if 1900 <= year <= 2099:
                return year
        except:
            pass
        
        return None
    
    df['year_int'] = df['year_incident'].apply(extract_year)
    
    valid_years = df['year_int'].notna().sum()
    print(f"  Años válidos extraídos: {valid_years}/{len(df)} ({valid_years/len(df)*100:.1f}%)")
    
    if valid_years == 0:
        print("\n⚠ ADVERTENCIA: No se pudieron extraer años válidos")
        print("  Primeros valores de 'year_incident':")
        print(df['year_incident'].head(10))
        print("\n  Por favor verifica que la columna 'year_incident' existe y tiene años")
    
    # Identificar períodos clave
    df['period'] = df['year_int'].apply(lambda x: 
        'Pre-2014 (antes anexión Crimea)' if pd.notna(x) and x < 2014 
        else '2014-2021 (anexión Crimea)' if pd.notna(x) and x < 2022 
        else '2022-2025 (invasión a gran escala)' if pd.notna(x) and x >= 2022 
        else 'Fecha desconocida'
    )
    
    # Clasificar tipos de objetos por relevancia cultural
    def classify_cultural_significance(row):
        """Clasifica objetos según su importancia para identidad ucraniana"""
        name = str(row.get('name', '')).lower()
        obj_type = str(row.get('type', '')).lower()
        category = str(row.get('category', '')).lower()
        
        # Objetos de alta significancia para identidad ucraniana
        if any(word in name or word in obj_type for word in 
               ['icon', 'religious', 'orthodox', 'church', 'cross', 'gospel']):
            return 'Religioso/Identitario'
        
        elif any(word in category for word in ['painting', 'graphics']):
            return 'Arte Nacional'
        
        elif 'book' in obj_type or 'manuscript' in obj_type or 'document' in name:
            return 'Documentos Históricos'
        
        elif any(word in obj_type for word in ['ceramic', 'archaeological', 'ancient']):
            return 'Patrimonio Arqueológico'
        
        elif 'weapon' in obj_type or 'military' in name:
            return 'Historia Militar'
        
        else:
            return 'Otros'
    
    df['cultural_significance'] = df.apply(classify_cultural_significance, axis=1)
    
    # Identificar objetos de museos específicos atacados
    df['museum_targeted'] = df['place_incident'].apply(lambda x: 
        'Kherson Art Museum' if 'Kherson' in str(x) and 'Museum' in str(x)
        else 'Mariupol' if 'Mariupol' in str(x)
        else 'Crimea sites' if 'Crimea' in str(x) or 'Crimean' in str(x)
        else 'Other'
    )
    
    print(f"\n✓ Datos procesados")
    print(f"  Períodos identificados: {df['period'].value_counts().to_dict()}")
    print(f"  Tipos de significancia cultural: {df['cultural_significance'].nunique()}")
    
    return df

# ============================================================================
# 2. VISUALIZACIÓN 1: Timeline con Eventos Clave
# ============================================================================

def create_timeline_with_conflict_events(df):
    """Timeline de robos con eventos clave del conflicto"""
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Contar robos por año (solo años válidos)
    yearly_thefts = df[df['year_int'].notna()]['year_int'].value_counts().sort_index()
    
    if len(yearly_thefts) == 0:
        print("⚠ No hay datos válidos para el timeline")
        plt.close()
        return
    
    # Gráfico de barras
    bars = ax.bar(yearly_thefts.index, yearly_thefts.values, 
                   color='darkred', alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Añadir líneas verticales para períodos con labels
    ax.axvline(x=2014, color='orange', linestyle='--', linewidth=3, alpha=0.7, label='2014: Anexión de Crimea')
    ax.axvline(x=2022, color='red', linestyle='--', linewidth=3, alpha=0.7, label='2022: Invasión a Gran Escala')
    
    # Añadir texto directamente en el gráfico (más simple, sin flechas)
    max_val = yearly_thefts.max()
    
    # Solo añadir texto si 2014 está en el rango de años
    if 2014 >= yearly_thefts.index.min() and 2014 <= yearly_thefts.index.max():
        ax.text(2014, max_val * 1.05, 'Anexión\nde Crimea', 
                ha='center', va='bottom', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))
    
    # Solo añadir texto si 2022 está en el rango de años
    if 2022 >= yearly_thefts.index.min() and 2022 <= yearly_thefts.index.max():
        ax.text(2022, max_val * 1.05, 'Invasión a\nGran Escala', 
                ha='center', va='bottom', fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='red', alpha=0.3))
    
    ax.set_xlabel('Año', fontsize=14, fontweight='bold')
    ax.set_ylabel('Número de Objetos Robados', fontsize=14, fontweight='bold')
    ax.set_title('TIMELINE: Intensificación del Saqueo Cultural (Looting)\nen Contexto del Conflicto Ruso-Ucraniano', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, max_val * 1.2)  # Espacio para los labels
    
    plt.savefig('viz_1_timeline_looting_russification.png', dpi=300, bbox_inches='tight')
    print("✓ Visualización 1 guardada: viz_1_timeline_looting_russification.png")
    plt.close()

# ============================================================================
# 3. VISUALIZACIÓN 2: Tipos de Objetos por Período
# ============================================================================

def create_cultural_targeting_analysis(df):
    """Análisis de targeting de objetos culturalmente significativos"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))
    
    # Gráfico 1: Stacked bar por período y tipo
    period_culture = pd.crosstab(df['period'], df['cultural_significance'])
    period_culture = period_culture[['Religioso/Identitario', 'Arte Nacional', 
                                      'Documentos Históricos', 'Patrimonio Arqueológico', 
                                      'Historia Militar', 'Otros']]
    
    period_culture.plot(kind='bar', stacked=True, ax=ax1, 
                        colormap='tab10', edgecolor='black', linewidth=1)
    ax1.set_xlabel('Período', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Número de Objetos Robados', fontsize=12, fontweight='bold')
    ax1.set_title('Targeting de Objetos por Significancia Cultural\n(Evidencia de Russification Estratégica)', 
                  fontsize=13, fontweight='bold')
    ax1.legend(title='Tipo de Objeto', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Gráfico 2: Proporción de objetos identitarios
    identity_objects = df[df['cultural_significance'].isin(['Religioso/Identitario', 'Arte Nacional', 'Documentos Históricos'])]
    period_identity = identity_objects.groupby('period').size()
    total_by_period = df.groupby('period').size()
    proportion = (period_identity / total_by_period * 100).fillna(0)
    
    colors = ['#ff6b6b' if x > 50 else '#4ecdc4' for x in proportion.values]
    bars = ax2.barh(proportion.index, proportion.values, color=colors, edgecolor='black', linewidth=1.5)
    
    ax2.set_xlabel('% de Objetos Identitarios/Culturales', fontsize=12, fontweight='bold')
    ax2.set_title('Proporción de Objetos de Alta Significancia\nCultural Ucraniana por Período', 
                  fontsize=13, fontweight='bold')
    ax2.axvline(x=50, color='red', linestyle='--', linewidth=2, alpha=0.5, label='50% umbral')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='x')
    
    # Añadir valores en las barras
    for i, (idx, val) in enumerate(proportion.items()):
        ax2.text(val + 2, i, f'{val:.1f}%', va='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('viz_2_cultural_targeting.png', dpi=300, bbox_inches='tight')
    print("✓ Visualización 2 guardada: viz_2_cultural_targeting.png")
    plt.close()

# ============================================================================
# 4. VISUALIZACIÓN 3: Mapa de Calor Geográfico + Temporal
# ============================================================================

def create_geographic_temporal_heatmap(df):
    """Heatmap geográfico-temporal del saqueo"""
    
    # Preparar datos - solo con años válidos
    df_clean = df[df['year_int'].notna() & df['place_incident'].notna()].copy()
    
    if len(df_clean) == 0:
        print("⚠ No hay datos con año y lugar válidos para el heatmap")
        return
    
    # Simplificar lugares para visualización
    df_clean['region'] = df_clean['place_incident'].apply(lambda x: 
        'Crimea' if 'Crimea' in str(x) or 'Sevastopol' in str(x)
        else 'Kherson' if 'Kherson' in str(x)
        else 'Mariupol' if 'Mariupol' in str(x)
        else 'Donetsk' if 'Donetsk' in str(x)
        else 'Luhansk' if 'Luhansk' in str(x)
        else 'Kyiv' if 'Kyiv' in str(x) or 'Kiev' in str(x)
        else 'Other'
    )
    
    # Crear matriz de calor
    heatmap_data = pd.crosstab(df_clean['region'], df_clean['year_int'])
    
    if heatmap_data.empty or heatmap_data.size == 0:
        print("⚠ No hay suficientes datos para crear el heatmap")
        return
    
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', 
                linewidths=0.5, cbar_kws={'label': 'Número de Objetos Robados'},
                ax=ax)
    
    ax.set_xlabel('Año del Saqueo', fontsize=13, fontweight='bold')
    ax.set_ylabel('Región', fontsize=13, fontweight='bold')
    ax.set_title('HEATMAP: Patrón Geográfico-Temporal del Saqueo Cultural\n(Targeting Sistemático de Regiones Ucranianas)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('viz_3_geographic_temporal_heatmap.png', dpi=300, bbox_inches='tight')
    print("✓ Visualización 3 guardada: viz_3_geographic_temporal_heatmap.png")
    plt.close()

# ============================================================================
# 5. ANÁLISIS ESTADÍSTICO
# ============================================================================

def generate_statistical_analysis(df):
    """Genera estadísticas clave para la narrativa de russification"""
    
    print("\n" + "="*70)
    print("ESTADÍSTICAS CLAVE: LOOTING COMO RUSSIFICATION")
    print("="*70)
    
    # 1. Incremento temporal
    pre_2014 = len(df[df['year_int'] < 2014])
    period_2014_2021 = len(df[(df['year_int'] >= 2014) & (df['year_int'] < 2022)])
    post_2022 = len(df[df['year_int'] >= 2022])
    
    print(f"\n1. ESCALADA TEMPORAL:")
    print(f"   Pre-2014: {pre_2014} objetos")
    print(f"   2014-2021 (anexión Crimea): {period_2014_2021} objetos")
    print(f"   2022-2025 (invasión): {post_2022} objetos")
    print(f"   Incremento 2022+: {(post_2022/period_2014_2021 - 1)*100:.1f}% vs período anterior" if period_2014_2021 > 0 else "")
    
    # 2. Targeting de objetos identitarios
    identity_types = ['Religioso/Identitario', 'Arte Nacional', 'Documentos Históricos']
    identity_count = len(df[df['cultural_significance'].isin(identity_types)])
    total = len(df)
    
    print(f"\n2. TARGETING CULTURAL:")
    print(f"   Objetos de alta significancia ucraniana: {identity_count} ({identity_count/total*100:.1f}%)")
    print(f"   Distribución por tipo:")
    for sig_type in df['cultural_significance'].value_counts().head(6).items():
        print(f"     - {sig_type[0]}: {sig_type[1]} ({sig_type[1]/total*100:.1f}%)")
    
    # 3. Regiones más afectadas
    print(f"\n3. PATRÓN GEOGRÁFICO:")
    print(f"   Top 5 regiones afectadas:")
    top_regions = df['place_incident'].value_counts().head(5)
    for region, count in top_regions.items():
        if pd.notna(region):
            print(f"     - {region[:60]}: {count} objetos")
    
    # 4. Museos específicamente atacados
    museum_attacks = df[df['place_incident'].str.contains('Museum|museum', na=False, case=False)]
    print(f"\n4. ATAQUES A MUSEOS:")
    print(f"   Total de objetos robados de museos: {len(museum_attacks)}")
    print(f"   Museos más afectados:")
    museums = museum_attacks['place_incident'].value_counts().head(5)
    for museum, count in museums.items():
        print(f"     - {museum[:60]}: {count} objetos")
    
    # Guardar estadísticas en CSV
    stats_df = pd.DataFrame({
        'Métrica': [
            'Total objetos robados',
            'Período pre-2014',
            'Período 2014-2021',
            'Período 2022-2025',
            'Objetos identitarios (%)',
            'Objetos de museos',
        ],
        'Valor': [
            total,
            pre_2014,
            period_2014_2021,
            post_2022,
            f"{identity_count/total*100:.1f}%",
            len(museum_attacks),
        ]
    })
    
    stats_df.to_csv('statistics_russification_analysis.csv', index=False)
    print("\n✓ Estadísticas guardadas en: statistics_russification_analysis.csv")
    
    return df  # Retornar el dataframe procesado

# ============================================================================
# 6. EXPORTAR CSV PROCESADO
# ============================================================================

def export_processed_data(df):
    """Exporta el CSV con todas las clasificaciones y análisis"""
    
    print("\n" + "="*70)
    print("EXPORTANDO DATOS PROCESADOS")
    print("="*70)
    
    # CSV principal con todas las clasificaciones
    df.to_csv('stolen_objects_processed_russification.csv', index=False, encoding='utf-8')
    print("✓ stolen_objects_processed_russification.csv - Dataset completo procesado")
    
    # CSV de objetos identitarios (solo los más relevantes)
    identity_types = ['Religioso/Identitario', 'Arte Nacional', 'Documentos Históricos']
    identity_df = df[df['cultural_significance'].isin(identity_types)]
    identity_df.to_csv('stolen_objects_identity_focused.csv', index=False, encoding='utf-8')
    print(f"✓ stolen_objects_identity_focused.csv - {len(identity_df)} objetos identitarios")
    
    # CSV agregado por período y tipo
    period_summary = df.groupby(['period', 'cultural_significance']).agg({
        'id': 'count',
        'name': lambda x: '; '.join(x.dropna().astype(str).head(3))  # Ejemplos
    }).rename(columns={'id': 'count', 'name': 'examples'}).reset_index()
    period_summary.to_csv('summary_by_period_and_type.csv', index=False, encoding='utf-8')
    print("✓ summary_by_period_and_type.csv - Resumen agregado")
    
    # CSV de timeline (para gráficos externos)
    timeline_df = df.groupby('year_int').agg({
        'id': 'count',
        'cultural_significance': lambda x: x.value_counts().index[0] if len(x) > 0 else 'Unknown'
    }).rename(columns={'id': 'count', 'cultural_significance': 'most_common_type'}).reset_index()
    timeline_df.to_csv('timeline_yearly_thefts.csv', index=False, encoding='utf-8')
    print("✓ timeline_yearly_thefts.csv - Timeline anual")
    
    # CSV geográfico (con coordenadas)
    geo_df = df[df['latitude'].notna() & df['longitude'].notna()][
        ['id', 'name', 'year_int', 'period', 'cultural_significance', 
         'latitude', 'longitude', 'place_incident', 'category']
    ]
    geo_df.to_csv('stolen_objects_geographic.csv', index=False, encoding='utf-8')
    print(f"✓ stolen_objects_geographic.csv - {len(geo_df)} objetos con coordenadas")
    
    print(f"\nTOTAL: 5 archivos CSV generados")

# ============================================================================
# 7. GENERAR REPORTE
# ============================================================================

def generate_research_report(df):
    """Genera un reporte en markdown para el proyecto"""
    
    report = """# REPORTE: Looting como Estrategia de Russification

## Pregunta de Investigación Principal

**¿Existe una correlación temporal entre la intensificación del conflicto armado y el saqueo sistemático de patrimonio cultural ucraniano como mecanismo de Russification?**

## Hallazgos Clave

### 1. Escalada Temporal del Saqueo
"""
    
    pre_2014 = len(df[df['year_int'] < 2014])
    period_2014_2021 = len(df[(df['year_int'] >= 2014) & (df['year_int'] < 2022)])
    post_2022 = len(df[df['year_int'] >= 2022])
    
    report += f"""
- **Pre-2014**: {pre_2014} objetos robados
- **2014-2021** (anexión Crimea): {period_2014_2021} objetos robados
- **2022-2025** (invasión a gran escala): {post_2022} objetos robados

**Conclusión**: {'Se observa una escalada significativa' if post_2022 > period_2014_2021 else 'Patrón continuo'} en el saqueo cultural coincidiendo con la intensificación del conflicto.

### 2. Targeting Cultural Selectivo
"""
    
    identity_types = ['Religioso/Identitario', 'Arte Nacional', 'Documentos Históricos']
    identity_count = len(df[df['cultural_significance'].isin(identity_types)])
    total = len(df)
    
    report += f"""
- **{identity_count/total*100:.1f}%** de los objetos robados tienen alta significancia para la identidad ucraniana
- Tipos prioritarios:
"""
    
    for sig_type, count in df['cultural_significance'].value_counts().head(5).items():
        report += f"  - {sig_type}: {count} objetos ({count/total*100:.1f}%)\n"
    
    report += """
**Conclusión**: El perfil de objetos robados sugiere un targeting estratégico de símbolos de identidad ucraniana, consistente con una estrategia de Russification.

### 3. Patrón Geográfico

"""
    
    report += "Regiones más afectadas:\n"
    for region, count in df['place_incident'].value_counts().head(5).items():
        if pd.notna(region):
            report += f"- {region[:50]}: {count} objetos\n"
    
    report += """
## Visualizaciones Generadas

1. **Timeline con Eventos Clave**: Muestra la correlación temporal entre escalada del conflicto y aumento de saqueo
2. **Targeting Cultural**: Demuestra la selectividad en tipos de objetos robados
3. **Heatmap Geográfico-Temporal**: Revela patrones espaciales del saqueo

## Metodología

- Fuente de datos: Portal gubernamental ucraniano de sanciones (war-sanctions.gur.gov.ua)
- Total de objetos analizados: """ + str(total) + """
- Período analizado: """ + str(int(df['year_int'].min())) + "-" + str(int(df['year_int'].max())) + """
- Clasificación de significancia cultural basada en tipo, categoría y contexto del objeto

## Referencias para Marco Teórico

- UNESCO (2023). Lista de Patrimonio Mundial en Peligro
- Concepto de "Russification" como política cultural
- Convención de La Haya (1954) sobre protección de bienes culturales en conflictos armados
"""
    
    with open('RESEARCH_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✓ Reporte de investigación guardado en: RESEARCH_REPORT.md")

# ============================================================================
# 7. EJECUTAR TODO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("ANÁLISIS COMPLETO: LOOTING Y RUSSIFICATION")
    print("="*70 + "\n")
    
    # Cargar datos
    df = load_and_prepare_data()
    
    # Generar visualizaciones
    print("\n" + "="*70)
    print("GENERANDO VISUALIZACIONES")
    print("="*70)
    create_timeline_with_conflict_events(df)
    create_cultural_targeting_analysis(df)
    create_geographic_temporal_heatmap(df)
    
    # Análisis estadístico
    df_with_stats = generate_statistical_analysis(df)
    
    # Exportar CSVs procesados
    export_processed_data(df)
    
    # Reporte
    generate_research_report(df)
    
    print("\n" + "="*70)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*70)
    print("\nArchivos generados:")
    print("\n📊 VISUALIZACIONES:")
    print("  - viz_1_timeline_looting_russification.png")
    print("  - viz_2_cultural_targeting.png")
    print("  - viz_3_geographic_temporal_heatmap.png")
    print("\n📄 DATASETS CSV:")
    print("  - stolen_objects_processed_russification.csv (dataset completo)")
    print("  - stolen_objects_identity_focused.csv (solo objetos identitarios)")
    print("  - summary_by_period_and_type.csv (resumen agregado)")
    print("  - timeline_yearly_thefts.csv (timeline anual)")
    print("  - stolen_objects_geographic.csv (datos con coordenadas)")
    print("  - statistics_russification_analysis.csv (estadísticas clave)")
    print("\n📝 REPORTE:")
    print("  - RESEARCH_REPORT.md")
    print("\n" + "="*70 + "\n")