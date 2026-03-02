#!/usr/bin/env python3
"""Script para modificar la vista combinar_datos_seleccionadas"""

# Leer el archivo
with open('datos_archivados/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar la línea donde insertar el código (después de limpiar cache)
insert_line = None
for i, line in enumerate(lines):
    if 'Cache de interrupción limpiado al inicio de combinación selectiva' in line:
        insert_line = i + 1
        break

if insert_line is None:
    print("ERROR: No se encontró la línea de inserción")
    exit(1)

print(f"Insertando código en la línea {insert_line + 1}")

# Código a insertar
codigo_nuevo = '''            
            # DETECTAR SI SON TABLAS DE DOCENCIA PARA GUARDAR EN HISTORIAL
            from .historical_data_saver import son_todas_tablas_docencia, guardar_datos_docencia_en_historial
            
            if son_todas_tablas_docencia(tablas_seleccionadas):
                logger.info("🎯 DETECTADAS TABLAS DE DOCENCIA - Guardando en modelos históricos")
                
                try:
                    # Guardar en historial en lugar de combinar
                    estadisticas = guardar_datos_docencia_en_historial(tablas_seleccionadas, logger)
                    
                    # Marcar como completado
                    resultado_final = {
                        'fecha_inicio': timezone.now().isoformat(),
                        'fecha_fin': timezone.now().isoformat(),
                        'tipo_combinacion': 'guardar_historial_docencia',
                        'tablas_procesadas': tablas_seleccionadas,
                        **estadisticas
                    }
                    cache.set('ultima_combinacion_completada', resultado_final, timeout=300)
                    cache.delete('combinacion_en_progreso')
                    
                    logger.info("=== GUARDADO EN HISTORIAL COMPLETADO EXITOSAMENTE ===")
                    logger.info(f"Total de registros guardados: {estadisticas.get('total_registros_guardados', 0)}")
                    
                    return  # Salir de la función sin ejecutar la combinación normal
                    
                except Exception as e:
                    logger.error(f"Error guardando datos de docencia en historial: {str(e)}", exc_info=True)
                    
                    # Guardar error en cache
                    error_info = {
                        'estado': 'error',
                        'mensaje': f'Error guardando en historial: {str(e)}',
                        'fecha_error': timezone.now().isoformat(),
                        'tipo_combinacion': 'guardar_historial_docencia'
                    }
                    cache.set('combinacion_error', error_info, timeout=300)
                    cache.delete('combinacion_en_progreso')
                    raise
'''

# Insertar el código
lines.insert(insert_line, codigo_nuevo)

# Escribir el archivo modificado
with open('datos_archivados/views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ Archivo modificado exitosamente")
