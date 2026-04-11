#!/usr/bin/env python
"""
Script simple para actualizar las funciones de procesamiento.
"""

# Leer el archivo
with open('datos_archivados/historical_data_saver.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Mapeo de tabla_origen a nombre de tabla para mapeo
tabla_mapeo = {
    'Docencia_coursecategory': 'Docencia_coursecategory',
    'Docencia_courseinformation': 'Docencia_courseinformation',
    'Docencia_courseinformation_adminteachers': 'Docencia_courseinformation_adminteachers',
    'Docencia_subjectinformation': 'Docencia_subjectinformation',
    'Docencia_edition': 'Docencia_edition',
    'Docencia_enrollmentapplication': 'Docencia_enrollmentapplication',
    'Docencia_accountnumber': 'Docencia_accountnumber',
    'Docencia_enrollmentpay': 'Docencia_enrollmentpay',
    'Docencia_enrollment': 'Docencia_enrollment',
    'Docencia_application': 'Docencia_application',
}

funciones_actualizadas = 0
i = 0
while i < len(lines):
    line = lines[i]
    
    # Buscar líneas que contienen tabla_origen= (excepto Docencia_area que ya está actualizada)
    if "tabla_origen='" in line and 'Docencia_area' not in line:
        # Extraer el nombre de la tabla
        for tabla_nombre in tabla_mapeo.keys():
            if tabla_nombre in line:
                # Buscar hacia atrás para encontrar "datos = dato.datos_originales"
                for j in range(i-1, max(0, i-10), -1):
                    if 'datos = dato.datos_originales' in lines[j]:
                        # Insertar la línea de mapeo después de esta línea
                        indent = '                '  # 16 espacios
                        nueva_linea = f'{indent}# Aplicar mapeo de campos\n'
                        nueva_linea += f'{indent}datos_mapeados = aplicar_mapeo_campos(datos, \'{tabla_nombre}\')\n'
                        nueva_linea += '\n'
                        
                        # Insertar después de la línea j
                        lines.insert(j+1, nueva_linea)
                        
                        # Ahora buscar la línea copiar_campos_a_modelo_historico después de la inserción
                        # y cambiar 'datos' por 'datos_mapeados'
                        for k in range(j+2, min(len(lines), j+20)):
                            if 'copiar_campos_a_modelo_historico' in lines[k] and ', datos,' in lines[k]:
                                lines[k] = lines[k].replace(', datos,', ', datos_mapeados,')
                                funciones_actualizadas += 1
                                print(f"✓ Actualizada función para {tabla_nombre}")
                                break
                        
                        i = k  # Saltar a después de donde hicimos cambios
                        break
                break
    
    i += 1

# Guardar el archivo
with open('datos_archivados/historical_data_saver.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\n✓ Archivo actualizado. {funciones_actualizadas} funciones modificadas.")
