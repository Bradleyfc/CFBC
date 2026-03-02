"""
Script para agregar completar_campos_obligatorios a todas las funciones de procesamiento
"""
import re

# Leer el archivo
with open('datos_archivados/historical_data_saver.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Patrón para encontrar las líneas donde se llama a copiar_campos_a_modelo_historico seguido de .save()
# Queremos insertar completar_campos_obligatorios entre estas dos líneas

# Buscar el patrón: copiar_campos_a_modelo_historico(...)\n...save()
patron = r'(copiar_campos_a_modelo_historico\([^)]+\)[^\n]*\n)(\s+)([a-z_]+\.save\(\))'

def reemplazo(match):
    linea_copiar = match.group(1)
    indentacion = match.group(2)
    linea_save = match.group(3)
    
    # Extraer el nombre del objeto (area, categoria, curso, etc.)
    objeto_match = re.search(r'([a-z_]+)\.save\(\)', linea_save)
    if objeto_match:
        nombre_objeto = objeto_match.group(1)
        return f"{linea_copiar}{indentacion}completar_campos_obligatorios({nombre_objeto}, logger=logger)\n{indentacion}{linea_save}"
    return match.group(0)

# Aplicar el reemplazo
contenido_nuevo = re.sub(patron, reemplazo, contenido)

# Guardar el archivo
with open('datos_archivados/historical_data_saver.py', 'w', encoding='utf-8') as f:
    f.write(contenido_nuevo)

print("✅ Archivo actualizado con completar_campos_obligatorios en todas las funciones")
