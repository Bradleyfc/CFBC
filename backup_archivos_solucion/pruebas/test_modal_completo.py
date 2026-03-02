"""
Script de prueba completo que simula el flujo del modal de combinación de tablas.
"""
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.models import DatoArchivadoDinamico
from datos_archivados.historical_data_saver import (
    es_tabla_docencia,
    son_todas_tablas_docencia,
    guardar_datos_docencia_en_historial
)
from historial.models import (
    HistoricalArea,
    HistoricalCourseCategory,
    HistoricalCourseInformation,
    HistoricalCourseInformationAdminTeachers,
    HistoricalSubjectInformation,
    HistoricalEdition,
    HistoricalEnrollmentApplication,
    HistoricalAccountNumber,
    HistoricalEnrollmentPay,
    HistoricalEnrollment,
    HistoricalApplication
)
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*80)
    print("PRUEBA COMPLETA DEL MODAL DE COMBINACIÓN DE TABLAS")
    print("="*80 + "\n")
    
    # Paso 1: Verificar que existen datos archivados
    print("PASO 1: Verificando datos archivados...")
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
    
    datos_por_tabla = {}
    total_registros = 0
    
    for tabla in tablas_docencia:
        count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
        datos_por_tabla[tabla] = count
        total_registros += count
        print(f"  - {tabla}: {count} registros")
    
    if total_registros == 0:
        print("\n❌ ERROR: No hay datos archivados para procesar")
        return
    
    print(f"\n✅ Total de registros archivados: {total_registros}")
    
    # Paso 2: Verificar que son tablas de docencia
    print("\nPASO 2: Verificando que son tablas de docencia...")
    if son_todas_tablas_docencia(tablas_docencia):
        print("✅ Todas las tablas son de docencia")
    else:
        print("❌ ERROR: Algunas tablas no son de docencia")
        for tabla in tablas_docencia:
            if not es_tabla_docencia(tabla):
                print(f"  - {tabla} NO es tabla de docencia")
        return
    
    # Paso 3: Limpiar registros históricos previos
    print("\nPASO 3: Limpiando registros históricos previos...")
    modelos_historicos = [
        HistoricalArea,
        HistoricalCourseCategory,
        HistoricalCourseInformation,
        HistoricalCourseInformationAdminTeachers,
        HistoricalSubjectInformation,
        HistoricalEdition,
        HistoricalEnrollmentApplication,
        HistoricalAccountNumber,
        HistoricalEnrollmentPay,
        HistoricalEnrollment,
        HistoricalApplication
    ]
    
    for modelo in modelos_historicos:
        count = modelo.objects.count()
        if count > 0:
            modelo.objects.all().delete()
            print(f"  - Eliminados {count} registros de {modelo.__name__}")
    
    print("✅ Registros históricos limpiados")
    
    # Paso 4: Ejecutar el guardado (simulando el modal)
    print("\nPASO 4: Ejecutando guardado en historial...")
    print("  (Esto simula lo que hace el modal al presionar 'Combinar Tablas')")
    
    try:
        resultado = guardar_datos_docencia_en_historial(
            tablas_seleccionadas=tablas_docencia,
            logger=logger
        )
        
        if resultado['success']:
            print(f"\n✅ Guardado exitoso!")
            print(f"  - Total guardado: {resultado['total_guardado']} registros")
            print(f"\n  Desglose por tabla:")
            for tabla, count in resultado['por_tabla'].items():
                print(f"    - {tabla}: {count} registros")
        else:
            print(f"\n❌ ERROR en el guardado:")
            print(f"  - {resultado['message']}")
            if 'error' in resultado:
                print(f"  - Error: {resultado['error']}")
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN durante el guardado:")
        print(f"  - {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 5: Verificar registros guardados
    print("\nPASO 5: Verificando registros guardados en historial...")
    total_en_historial = 0
    
    for modelo in modelos_historicos:
        count = modelo.objects.count()
        total_en_historial += count
        if count > 0:
            print(f"  - {modelo.__name__}: {count} registros")
    
    print(f"\n✅ Total en historial: {total_en_historial} registros")
    
    # Paso 6: Verificar campos de auditoría
    print("\nPASO 6: Verificando campos de auditoría...")
    campos_ok = True
    
    for modelo in modelos_historicos:
        if modelo.objects.exists():
            primer_registro = modelo.objects.first()
            if not hasattr(primer_registro, 'id_original'):
                print(f"  ❌ {modelo.__name__} no tiene campo id_original")
                campos_ok = False
            if not hasattr(primer_registro, 'tabla_origen'):
                print(f"  ❌ {modelo.__name__} no tiene campo tabla_origen")
                campos_ok = False
            if not hasattr(primer_registro, 'fecha_consolidacion'):
                print(f"  ❌ {modelo.__name__} no tiene campo fecha_consolidacion")
                campos_ok = False
    
    if campos_ok:
        print("✅ Todos los modelos tienen campos de auditoría")
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN FINAL")
    print("="*80)
    print(f"Registros archivados: {total_registros}")
    print(f"Registros guardados en historial: {total_en_historial}")
    
    if total_en_historial > 0:
        print("\n✅ ¡ÉXITO! El modal de combinación está funcionando correctamente")
    else:
        print("\n❌ FALLO: No se guardaron registros en el historial")
    
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
