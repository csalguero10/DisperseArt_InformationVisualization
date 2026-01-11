import pandas as pd

# Cargar el archivo CSV
df = pd.read_csv('data_stolen/stolen_objects_ukraine_jittered.csv')

# Convertir year_for_timeline a datetime (formato date)
df['year_for_timeline'] = pd.to_datetime(df['year_for_timeline'], format='%Y', errors='coerce')

# Convertir year_incident a datetime (formato date)
df['year_incident'] = pd.to_datetime(df['year_incident'], format='%Y', errors='coerce')

# Crear nuevas columnas con formato timestamp ISO 8601 para Kepler.gl
df['year_for_timeline_timestamp'] = df['year_for_timeline'].dt.strftime('%Y-%m-%dT%H:%M:%S')
df['year_incident_timestamp'] = df['year_incident'].dt.strftime('%Y-%m-%dT%H:%M:%S')

# Verificar el cambio
print("Tipo de dato de year_for_timeline:")
print(df['year_for_timeline'].dtype)
print("\nTipo de dato de year_incident:")
print(df['year_incident'].dtype)

print("\nPrimeras filas de todas las columnas:")
print(df[['year_for_timeline', 'year_for_timeline_timestamp', 'year_incident', 'year_incident_timestamp']].head(10))

print("\nEjemplo de formato timestamp:")
print(f"year_for_timeline_timestamp: {df['year_for_timeline_timestamp'].iloc[0]}")
print(f"year_incident_timestamp: {df['year_incident_timestamp'].iloc[0]}")

# Verificar valores nulos
print(f"\nValores nulos en year_for_timeline: {df['year_for_timeline'].isna().sum()}")
print(f"Valores nulos en year_incident: {df['year_incident'].isna().sum()}")
print(f"Valores nulos en year_for_timeline_timestamp: {df['year_for_timeline_timestamp'].isna().sum()}")
print(f"Valores nulos en year_incident_timestamp: {df['year_incident_timestamp'].isna().sum()}")

# Guardar el archivo modificado
df.to_csv('data_stolen/stolen_objects_ukraine_timestamp.csv', index=False)
print("\n✓ Archivo guardado como 'stolen_objects_ukraine_timestamp.csv'")
print("✓ year_for_timeline & year_incident: datetime64 (date)")
print("✓ year_for_timeline_timestamp & year_incident_timestamp: timestamp ISO 8601 para Kepler.gl")