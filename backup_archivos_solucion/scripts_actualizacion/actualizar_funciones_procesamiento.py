#!/usr/bin/env python
"""
Script para actualizar todas las funciones de procesamiento para usar mapeos de campos.
"""

import re

# Leer el archivo
with open('datos_archivados/historical_data_saver.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar y reemplazar en _procesar_areas
contenido = contenido.replace(
    '''                datos = dato.datos_originales
                id_original = datos.get('id')

                # Crear nueva área histórica''',
    '''                datos = dato.datos_originales
                id_original = datos.get('id')

                # Aplicar mapeo de campos de inglés a español
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_area')

                # Crear nueva área histórica'''
)

contenido = contenido.replace(
    '''                copiar_campos_a_modelo_historico(area, datos, campos_excluir=['id', 'pk'], logger=logger)''',
    '''                copiar_campos_a_modelo_historico(area, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)'''
)

# Guardar el archivo
with open('datos_archivados/historical_data_saver.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✓ Función _procesar_areas actualizada")
