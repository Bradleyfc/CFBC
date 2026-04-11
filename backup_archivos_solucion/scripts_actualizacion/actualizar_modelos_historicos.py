#!/usr/bin/env python
"""
Script para agregar los campos de auditoría faltantes a todos los modelos históricos.
"""

# Definición de los campos de auditoría que deben agregarse a cada modelo
CAMPOS_AUDITORIA = '''    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(related_name)s'
    )
    
'''

# Mapeo de modelos a sus related_names
MODELOS_RELATED_NAMES = {
    'HistoricalArea': 'historical_areas',
    'HistoricalCourseCategory': 'historical_course_categories',
    'HistoricalCourseInformation': 'historical_course_informations',
    'HistoricalCourseInformationAdminTeachers': 'historical_course_information_admin_teachers',
    'HistoricalEnrollmentApplication': 'historical_enrollment_applications',
    'HistoricalEnrollmentPay': 'historical_enrollment_pays',
    'HistoricalAccountNumber': 'historical_account_numbers',
    'HistoricalEnrollment': 'historical_enrollments',
    'HistoricalSubjectInformation': 'historical_subject_informations',
    'HistoricalEdition': 'historical_editions',
    'HistoricalApplication': 'historical_applications',
}

print("Este script debe ejecutarse manualmente editando historial/models.py")
print("\nPara cada modelo histórico, agrega estos campos ANTES de los campos de datos:\n")

for modelo, related_name in MODELOS_RELATED_NAMES.items():
    campos = CAMPOS_AUDITORIA.replace('%(related_name)s', related_name)
    print(f"\n{'='*80}")
    print(f"Modelo: {modelo}")
    print(f"{'='*80}")
    print(campos)
