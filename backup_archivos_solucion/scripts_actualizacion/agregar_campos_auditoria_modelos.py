#!/usr/bin/env python
"""
Script para agregar campos de auditoría a los modelos históricos que no los tienen.
"""

import re

# Leer el archivo
with open('historial/models.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Definir los campos de auditoría
def generar_campos_auditoria(related_name):
    return f'''    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='{related_name}'
    )
    
'''

# Mapeo de modelos a sus related_names y primer campo de datos
MODELOS_INFO = {
    'HistoricalCourseCategory': {
        'related_name': 'historical_course_categories',
        'primer_campo': 'nombre = models.CharField'
    },
    'HistoricalCourseInformation': {
        'related_name': 'historical_course_informations',
        'primer_campo': 'nombre = models.CharField'
    },
    'HistoricalCourseInformationAdminTeachers': {
        'related_name': 'historical_course_information_admin_teachers',
        'primer_campo': 'curso = models.ForeignKey'
    },
    'HistoricalEnrollmentApplication': {
        'related_name': 'historical_enrollment_applications',
        'primer_campo': 'usuario = models.ForeignKey'
    },
    'HistoricalAccountNumber': {
        'related_name': 'historical_account_numbers',
        'primer_campo': 'numero_cuenta = models.CharField'
    },
    'HistoricalEnrollmentPay': {
        'related_name': 'historical_enrollment_pays',
        'primer_campo': 'solicitud = models.ForeignKey'
    },
    'HistoricalSubjectInformation': {
        'related_name': 'historical_subject_informations',
        'primer_campo': 'nombre = models.CharField'
    },
    'HistoricalEdition': {
        'related_name': 'historical_editions',
        'primer_campo': 'curso = models.ForeignKey'
    },
    'HistoricalEnrollment': {
        'related_name': 'historical_enrollments',
        'primer_campo': 'estudiante = models.ForeignKey'
    },
    'HistoricalApplication': {
        'related_name': 'historical_applications',
        'primer_campo': 'usuario = models.ForeignKey'
    },
}

# Procesar cada modelo
modelos_actualizados = 0
for modelo, info in MODELOS_INFO.items():
    # Buscar el patrón: class ModeloName(models.Model): ... """...""" primer_campo
    patron = rf'(class {modelo}\(models\.Model\):.*?""".*?""")\s+({info["primer_campo"]})'
    
    # Verificar si ya tiene los campos de auditoría
    if f'class {modelo}' in contenido:
        # Buscar si ya tiene id_original
        clase_inicio = contenido.find(f'class {modelo}')
        clase_fin = contenido.find('class ', clase_inicio + 10)
        if clase_fin == -1:
            clase_fin = len(contenido)
        
        clase_contenido = contenido[clase_inicio:clase_fin]
        
        if 'id_original' not in clase_contenido:
            # Agregar campos de auditoría
            campos_auditoria = generar_campos_auditoria(info['related_name'])
            reemplazo = rf'\1\n{campos_auditoria}    # Campos de datos\n    \2'
            
            contenido_nuevo = re.sub(patron, reemplazo, contenido, flags=re.DOTALL)
            
            if contenido_nuevo != contenido:
                contenido = contenido_nuevo
                modelos_actualizados += 1
                print(f"✓ Actualizado: {modelo}")
            else:
                print(f"⚠ No se pudo actualizar: {modelo}")
        else:
            print(f"○ Ya tiene campos de auditoría: {modelo}")

# Guardar el archivo actualizado
if modelos_actualizados > 0:
    with open('historial/models.py', 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"\n✓ Archivo actualizado. {modelos_actualizados} modelos modificados.")
else:
    print("\n○ No se realizaron cambios.")
