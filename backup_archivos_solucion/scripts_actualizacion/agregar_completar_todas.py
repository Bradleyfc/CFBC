"""
Script para agregar completar_campos_obligatorios antes de TODAS las llamadas a .save()
en las funciones _procesar_
"""

# Leer el archivo
with open('datos_archivados/historical_data_saver.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

nuevas_lineas = []
i = 0
while i < len(lineas):
    linea = lineas[i]
    nuevas_lineas.append(linea)
    
    # Si encontramos una línea con .save() que NO sea categoria.save() en el segundo paso
    # y que esté dentro de una función _procesar_
    if '.save()' in linea and not linea.strip().startswith('#'):
        # Verificar si la línea anterior ya tiene completar_campos_obligatorios
        if i > 0 and 'completar_campos_obligatorios' not in lineas[i-1]:
            # Extraer el nombre del objeto
            objeto = linea.strip().split('.save()')[0].strip()
            # Obtener la indentación
            indentacion = linea[:len(linea) - len(linea.lstrip())]
            
            # Insertar la llamada a completar_campos_obligatorios ANTES del .save()
            linea_completar = f"{indentacion}completar_campos_obligatorios({objeto}, logger=logger)\n"
            
            # Insertar antes de la línea actual
            nuevas_lineas.insert(-1, linea_completar)
    
    i += 1

# Guardar el archivo
with open('datos_archivados/historical_data_saver.py', 'w', encoding='utf-8') as f:
    f.writelines(nuevas_lineas)

print("✅ Archivo actualizado con completar_campos_obligatorios antes de todos los .save()")
