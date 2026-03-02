#!/usr/bin/env python
"""
Script para completar los campos de auditoría en los modelos que faltan.
"""

import re

# Leer el archivo
with open('historial/models.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Modelos que necesitan actualización con sus líneas aproximadas
ACTUALIZACIONES = [
    {
        'modelo': 'HistoricalEnrollmentApplication',
        'related_name': 'historical_enrollment_applications',
        'buscar': 'class HistoricalEnrollmentApplication(models.Model):',
        'insertar_antes': '    fecha_solicitud = models.DateTimeField()'
    },
    {
        'modelo': 'HistoricalEnrollmentPay',
        'related_name': 'historical_enrollment_pays',
        'buscar': 'class HistoricalEnrollmentPay(models.Model):',
        'insertar_antes': '    solicitud = models.ForeignKey('
    },
    {
        'modelo': 'HistoricalEdition',
        'related_name': 'historical_editions',
        'buscar': 'class HistoricalEdition(models.Model):',
        'insertar_antes': '    curso = models.ForeignKey('
    },
    {
        'modelo': 'HistoricalEnrollment',
        'related_name': 'historical_enrollments',
        'buscar': 'class HistoricalEnrollment(models.Model):',
        'insertar_antes': '    estudiante = models.ForeignKey('
    },
    {
        'modelo': 'HistoricalApplication',
        'related_name': 'historical_applications',
        'buscar': 'class HistoricalApplication(models.Model):',
        'insertar_antes': '    usuario = models.ForeignKey('
    },
]

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
    
    # Campos de datos
'''

modelos_actualizados = 0

for actualizacion in ACTUALIZACIONES:
    # Verificar si ya tiene id_original
    clase_inicio = contenido.find(actualizacion['buscar'])
    if clase_inicio == -1:
        print(f"⚠ No se encontró: {actualizacion['modelo']}")
        continue
    
    clase_fin = contenido.find('class ', clase_inicio + 10)
    if clase_fin == -1:
        clase_fin = len(contenido)
    
    clase_contenido = contenido[clase_inicio:clase_fin]
    
    if 'id_original' in clase_contenido:
        print(f"○ Ya tiene campos de auditoría: {actualizacion['modelo']}")
        continue
    
    # Buscar donde insertar
    insertar_pos = contenido.find(actualizacion['insertar_antes'], clase_inicio)
    if insertar_pos == -1:
        print(f"⚠ No se encontró punto de inserción para: {actualizacion['modelo']}")
        continue
    
    # Insertar campos de auditoría
    campos = generar_campos_auditoria(actualizacion['related_name'])
    contenido = contenido[:insertar_pos] + campos + contenido[insertar_pos:]
    modelos_actualizados += 1
    print(f"✓ Actualizado: {actualizacion['modelo']}")

# Guardar el archivo
if modelos_actualizados > 0:
    with open('historial/models.py', 'w', encoding='utf-8') as f:
        f.write(contenido)
    print(f"\n✓ Archivo actualizado. {modelos_actualizados} modelos modificados.")
else:
    print("\n○ No se realizaron cambios.")
