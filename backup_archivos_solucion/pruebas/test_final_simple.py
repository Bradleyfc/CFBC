"""
Prueba simple del guardado en historial
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.historical_data_saver import guardar_datos_docencia_en_historial
from historial.models import (
    HistoricalArea,
    HistoricalCourseCategory,
    HistoricalCourseInformation,
    HistoricalEnrollmentApplication,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tablas de docencia
tablas_docencia = [
    'Docencia_area',
    'Docencia_coursecategory',
    'Docencia_courseinformation',
    'Docencia_courseinformation_adminteachers',
    'Docencia_subjectinformation',
    'Docencia_edition',
    'Docencia_enrollmentapplication',
    'Docencia_accountnumber',
    'Docencia_enrollmentpay',
    'Docencia_enrollment',
    'Docencia_application'
]

print("\n" + "="*80)
print("PRUEBA DE GUARDADO EN HISTORIAL")
print("="*80 + "\n")

# Ejecutar guardado
resultado = guardar_datos_docencia_en_historial(
    tablas_seleccionadas=tablas_docencia,
    logger=logger
)

print("\n" + "="*80)
print("RESULTADO")
print("="*80)
print(f"Total registros guardados: {resultado['total_registros_guardados']}")
print(f"Tablas procesadas: {resultado['tablas_procesadas']}")

# Verificar registros
print("\n" + "="*80)
print("VERIFICACIÓN")
print("="*80)
print(f"HistoricalArea: {HistoricalArea.objects.count()} registros")
print(f"HistoricalCourseCategory: {HistoricalCourseCategory.objects.count()} registros")
print(f"HistoricalCourseInformation: {HistoricalCourseInformation.objects.count()} registros")
print(f"HistoricalEnrollmentApplication: {HistoricalEnrollmentApplication.objects.count()} registros")

print("\n✅ ¡PRUEBA COMPLETADA!")
