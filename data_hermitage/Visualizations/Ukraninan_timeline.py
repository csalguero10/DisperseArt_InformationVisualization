import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, FancyBboxPatch
import numpy as np

# Configurar estilo
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 9

# Datos de los periodos
periods = [
    {"name": "Paleolithic\nPeriod", "date": "c. 1.4M – 10,000 BC", "year": -1400000, "emphasis": True},
    {"name": "Mesolithic /\nEpipaleolithic", "date": "c. 10,000 – 7000 BC", "year": -10000, "emphasis": False},
    {"name": "Early Neolithic /\nPre-Neolithic", "date": "c. 7000 – 5050 BC", "year": -7000, "emphasis": False},
    {"name": "Neolithic\nPeriod", "date": "c. 5050 – 2950 BC", "year": -5050, "emphasis": False},
    {"name": "Bronze Age", "date": "c. 4500 – 1950 BC", "year": -4500, "emphasis": True},
    {"name": "Iron Age", "date": "c. 1200 – 700 BC", "year": -1200, "emphasis": False},
    {"name": "Scythian–Sarmatian\nEra", "date": "c. 700 – 250 BC", "year": -700, "emphasis": True},
    {"name": "Greek and\nRoman Period", "date": "250 BC – 375 AD", "year": -250, "emphasis": False},
    {"name": "Migration\nPeriod", "date": "370s – 7th c. AD", "year": 370, "emphasis": False},
    {"name": "Early Medieval –\nBulgar & Khazar", "date": "7th – 9th centuries", "year": 650, "emphasis": False},
    {"name": "Kievan Rus'\nPeriod", "date": "839 – 1240", "year": 839, "emphasis": True},
    {"name": "Mongol Invasion\n& Domination", "date": "1239 – 14th c.", "year": 1239, "emphasis": False},
    {"name": "Kingdom of\nGalicia–Volhynia", "date": "1197 – 1340", "year": 1197, "emphasis": False},
    {"name": "Lithuanian and\nPolish Period", "date": "1340 – 1648", "year": 1340, "emphasis": False},
    {"name": "Cossack\nHetmanate", "date": "1648 – 1764", "year": 1648, "emphasis": True},
    {"name": "Ukraine under\nRussian Empire", "date": "1764 – 1917", "year": 1764, "emphasis": False},
    {"name": "First\nIndependence", "date": "1917 – 1921", "year": 1917, "emphasis": False},
    {"name": "Soviet\nPeriod", "date": "1921 – 1991", "year": 1921, "emphasis": True},
    {"name": "Independence\nPeriod", "date": "1991 – present", "year": 1991, "emphasis": True}
]

# Crear figura
fig, ax = plt.subplots(figsize=(24, 8))
ax.set_xlim(-0.5, len(periods) - 0.5)
ax.set_ylim(-3, 3)
ax.axis('off')

# Título
fig.text(0.5, 0.95, 'UKRAINIAN HISTORICAL PERIODS TIMELINE', 
         ha='center', fontsize=24, fontweight='bold', color='#5C3317')

# Colores
line_color = '#D4634A'
point_color = '#C94A38'
emphasis_color = '#E85D4A'
text_color = '#5C3317'

# Dibujar línea principal
y_line = 0
ax.plot([0, len(periods)-1], [y_line, y_line], color=line_color, linewidth=3, zorder=1)

# Dibujar cada periodo
for i, period in enumerate(periods):
    x = i
    
    # Alternar posición arriba/abajo
    is_top = i % 2 == 0
    y_text = 1.5 if is_top else -1.5
    y_date = 1.0 if is_top else -1.0
    va_text = 'bottom' if is_top else 'top'
    va_date = 'bottom' if is_top else 'top'
    
    # Línea vertical conectora (punteada)
    line_height = 0.8 if is_top else -0.8
    ax.plot([x, x], [y_line, line_height], color=line_color, 
            linewidth=1, linestyle='--', alpha=0.6, zorder=2)
    
    # Punto en la línea principal
    ax.plot(x, y_line, 'o', color=point_color, markersize=10, 
            markeredgecolor='white', markeredgewidth=2, zorder=4)
    
    # Punto pequeño en la conexión
    ax.plot(x, line_height, 'o', color=emphasis_color if period['emphasis'] else line_color, 
            markersize=6, zorder=3)
    
    # Texto del nombre del periodo
    ax.text(x, y_text, period['name'], 
            ha='center', va=va_text, fontsize=10, fontweight='bold',
            color=text_color, zorder=5)
    
    # Texto de la fecha
    ax.text(x, y_date, period['date'], 
            ha='center', va=va_date, fontsize=8, 
            color=text_color, style='italic', zorder=5)

# Añadir decoración de puntos pequeños (como en la imagen de referencia)
np.random.seed(42)
for _ in range(30):
    x_rand = np.random.uniform(-0.5, len(periods) - 0.5)
    y_rand = np.random.uniform(-2.5, 2.5)
    if abs(y_rand) > 0.3:  # Evitar la línea principal
        size = np.random.uniform(2, 4)
        alpha = np.random.uniform(0.2, 0.4)
        ax.plot(x_rand, y_rand, 'o', color=emphasis_color, 
                markersize=size, alpha=alpha, zorder=1)

plt.tight_layout()
plt.savefig('ukrainian_timeline.png', dpi=300, bbox_inches='tight', 
            facecolor="#FFFFFF")
print("✓ Timeline guardada como 'ukrainian_timeline.png'")

# Imprimir información
print("\n" + "="*70)
print("PERIODOS HISTÓRICOS DE UCRANIA")
print("="*70)
for i, period in enumerate(periods, 1):
    emphasis = " [DESTACADO]" if period['emphasis'] else ""
    print(f"{i:2d}. {period['name'].replace(chr(10), ' '):<35} | {period['date']}{emphasis}")

plt.show()