#!/usr/bin/env python
"""
Actualiza todas las funciones restantes agregando campos de auditoría y mapeo.
"""

with open('datos_archivados/historical_data_saver.py', 'r') as f:
    lines = f.readlines()

# Definir las actualizaciones necesarias
# Formato: (línea_aproximada, nombre_variable, tabla_origen, línea_buscar)
actualizaciones = [
    (401, 'curso', 'Docencia_courseinformation', '                curso = ModeloHistorico()\n'),
    (499, 'asignatura', 'Docencia_subjectinformation', '                asignatura = ModeloHistorico()\n'),
    (541, 'edicion', 'Docencia_edition', '                edicion = ModeloHistorico()\n'),
    (592, 'solicitud', 'Docencia_enrollmentapplication', '                solicitud = ModeloHistorico()\n'),
    (640, 'cuenta', 'Docencia_accountnumber', '                cuenta = ModeloHistorico()\n'),
    (687, 'pago', 'Docencia_enrollmentpay', '                pago = ModeloHistorico()\n'),
    (729, 'inscripcion', 'Docencia_enrollment', '                inscripcion = ModeloHistorico()\n'),
    (780, 'aplicacion', 'Docencia_application', '                aplicacion = ModeloHistorico()\n'),
]

# También necesitamos actualizar admin_teachers
# Buscar la línea específica
for i, line in enumerate(lines):
    if 'admin_teacher = ModeloHistorico()' in line:
        actualizaciones.insert(0, (i+1, 'admin_teacher', 'Docencia_courseinformation_adminteachers', line))
        break

funciones_actualizadas = 0

for linea_aprox, variable, tabla, linea_buscar in actualizaciones:
    # Buscar la línea exacta
    for i, line in enumerate(lines):
        if line == linea_buscar:
            # Insertar mapeo ANTES de esta línea
            indent = '                '
            mapeo_line = f'{indent}# Aplicar mapeo de campos\n'
            mapeo_line += f'{indent}datos_mapeados = aplicar_mapeo_campos(datos, \'{tabla}\')\n'
            mapeo_line += '\n'
            lines.insert(i, mapeo_line)
            
            # Reemplazar la línea actual con la versión con argumentos
            nuevo_objeto = f'{indent}{variable} = ModeloHistorico(\n'
            nuevo_objeto += f'{indent}    id_original=id_original,\n'
            nuevo_objeto += f'{indent}    tabla_origen=\'{tabla}\',\n'
            nuevo_objeto += f'{indent}    dato_archivado=dato\n'
            nuevo_objeto += f'{indent})\n'
            lines[i+3] = nuevo_objeto  # +3 porque insertamos 3 líneas antes
            
            # Buscar y reemplazar copiar_campos_a_modelo_historico
            for j in range(i+4, min(len(lines), i+10)):
                if 'copiar_campos_a_modelo_historico' in lines[j] and f'{variable}, datos,' in lines[j]:
                    lines[j] = lines[j].replace(f'{variable}, datos,', f'{variable}, datos_mapeados,')
                    break
            
            funciones_actualizadas += 1
            print(f"✓ Actualizada función para {tabla}")
            break

# Guardar el archivo
with open('datos_archivados/historical_data_saver.py', 'w') as f:
    f.writelines(lines)

print(f"\n✓ Archivo actualizado. {funciones_actualizadas} funciones modificadas.")
