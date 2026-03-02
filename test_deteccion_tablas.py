
# Ejecutar en Django shell: python manage.py shell

from datos_archivados.historical_data_saver import (
    es_tabla_docencia,
    son_todas_tablas_docencia,
    DOCENCIA_TABLES_MAPPING
)

# Probar con tablas de ejemplo
tablas_prueba = [
    'Docencia_area',
    'Docencia_coursecategory',
    'Docencia_courseinformation',
    'Usuario_user',  # Esta NO es de docencia
]

print("\nProbando es_tabla_docencia:")
print("-" * 50)
for tabla in tablas_prueba:
    resultado = es_tabla_docencia(tabla)
    print(f"{tabla}: {resultado}")

print("\nProbando son_todas_tablas_docencia:")
print("-" * 50)
solo_docencia = ['Docencia_area', 'Docencia_coursecategory']
mixtas = ['Docencia_area', 'Usuario_user']

print(f"Solo docencia {solo_docencia}: {son_todas_tablas_docencia(solo_docencia)}")
print(f"Mixtas {mixtas}: {son_todas_tablas_docencia(mixtas)}")

print("\nMapeo completo:")
print("-" * 50)
for tabla, modelo in DOCENCIA_TABLES_MAPPING.items():
    print(f"{tabla} -> {modelo}")
