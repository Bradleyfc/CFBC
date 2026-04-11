"""
Script para arreglar el problema de scope en combinar_datos_seleccionadas
"""

# Leer el archivo
with open('datos_archivados/views.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Cambio 1: Agregar parámetro a la función
contenido = contenido.replace(
    '    def ejecutar_combinacion_seleccionada():',
    '    def ejecutar_combinacion_seleccionada(tablas_seleccionadas):'
)

# Cambio 2: Pasar el parámetro al llamar la función
contenido = contenido.replace(
    '        ejecutar_combinacion_seleccionada()',
    '        ejecutar_combinacion_seleccionada(tablas_seleccionadas)'
)

# Guardar el archivo
with open('datos_archivados/views.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Archivo views.py actualizado con el fix de scope")
