#!/usr/bin/env python
"""
Actualiza la función _procesar_categorias
"""

with open('datos_archivados/historical_data_saver.py', 'r') as f:
    contenido = f.read()

# Buscar y reemplazar _procesar_categorias
viejo = '''def _procesar_categorias(datos_tabla, ModeloHistorico, mapeo_categorias, logger):
    """Procesa y guarda categorías en HistoricalCourseCategory."""
    registros_guardados = 0
    
    # Primer paso: crear todas las categorías sin parent
    categorias_pendientes = []
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                parent_id = datos.get('parent_id')
                
                # Crear categoría
                categoria = ModeloHistorico()
                copiar_campos_a_modelo_historico(
                    categoria, datos, 
                    campos_excluir=['id', 'pk', 'parent_id', 'parent'], 
                    logger=logger
                )
                categoria.save()'''

nuevo = '''def _procesar_categorias(datos_tabla, ModeloHistorico, mapeo_categorias, logger):
    """Procesa y guarda categorías en HistoricalCourseCategory."""
    registros_guardados = 0
    
    # Primer paso: crear todas las categorías sin parent
    categorias_pendientes = []
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                parent_id = datos.get('parent_id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_coursecategory')
                
                # Crear categoría
                categoria = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_coursecategory',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    categoria, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'parent_id', 'parent'], 
                    logger=logger
                )
                categoria.save()'''

if viejo in contenido:
    contenido = contenido.replace(viejo, nuevo)
    with open('datos_archivados/historical_data_saver.py', 'w') as f:
        f.write(contenido)
    print("✓ Función _procesar_categorias actualizada")
else:
    print("⚠ No se encontró el patrón exacto")
