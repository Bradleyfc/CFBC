"""
Script de prueba para diagnosticar el problema de guardado en historial.
Este script verifica:
1. Si hay datos en DatoArchivadoDinamico para las tablas de docencia
2. Si la función guardar_datos_docencia_en_historial se ejecuta correctamente
3. Si los datos se guardan en los modelos históricos
"""

import os
import sys
import django
import logging

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.models import DatoArchivadoDinamico
from datos_archivados.historical_data_saver import (
    guardar_datos_docencia_en_historial,
    DOCENCIA_TABLES_MAPPING,
    es_tabla_docencia
)
from historial.models import (
    HistoricalArea,
    HistoricalCourseCategory,
    HistoricalCourseInformation,
    HistoricalCourseInformationAdminTeachers,
    HistoricalEnrollmentApplication,
    HistoricalEnrollmentPay,
    HistoricalAccountNumber,
    HistoricalEnrollment,
    HistoricalSubjectInformation,
    HistoricalEdition,
    HistoricalApplication,
)

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verificar_datos_disponibles():
    """Verifica si hay datos en DatoArchivadoDinamico para tablas de docencia."""
    print("\n" + "=" * 80)
    print("PASO 1: VERIFICANDO DATOS DISPONIBLES EN DatoArchivadoDinamico")
    print("=" * 80)
    
    tablas_con_datos = []
    
    for tabla_nombre in DOCENCIA_TABLES_MAPPING.keys():
        count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla_nombre).count()
        print(f"\n📊 {tabla_nombre}: {count} registros")
        
        if count > 0:
            tablas_con_datos.append(tabla_nombre)
            # Mostrar un ejemplo de datos
            ejemplo = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla_nombre).first()
            print(f"   Ejemplo de datos_originales:")
            print(f"   ID original: {ejemplo.id_original}")
            print(f"   Campos disponibles: {list(ejemplo.datos_originales.keys())}")
            print(f"   Primeros 3 campos: {dict(list(ejemplo.datos_originales.items())[:3])}")
    
    print(f"\n✅ Total de tablas con datos: {len(tablas_con_datos)}")
    print(f"   Tablas: {tablas_con_datos}")
    
    return tablas_con_datos


def verificar_modelos_historicos_antes():
    """Verifica el estado de los modelos históricos antes del guardado."""
    print("\n" + "=" * 80)
    print("PASO 2: VERIFICANDO ESTADO DE MODELOS HISTÓRICOS (ANTES)")
    print("=" * 80)
    
    modelos = {
        'HistoricalArea': HistoricalArea,
        'HistoricalCourseCategory': HistoricalCourseCategory,
        'HistoricalCourseInformation': HistoricalCourseInformation,
        'HistoricalCourseInformationAdminTeachers': HistoricalCourseInformationAdminTeachers,
        'HistoricalEnrollmentApplication': HistoricalEnrollmentApplication,
        'HistoricalEnrollmentPay': HistoricalEnrollmentPay,
        'HistoricalAccountNumber': HistoricalAccountNumber,
        'HistoricalEnrollment': HistoricalEnrollment,
        'HistoricalSubjectInformation': HistoricalSubjectInformation,
        'HistoricalEdition': HistoricalEdition,
        'HistoricalApplication': HistoricalApplication,
    }
    
    estado_antes = {}
    for nombre, modelo in modelos.items():
        count = modelo.objects.count()
        estado_antes[nombre] = count
        print(f"📊 {nombre}: {count} registros")
    
    return estado_antes


def ejecutar_guardado_prueba(tablas_con_datos):
    """Ejecuta el guardado en historial con logging detallado."""
    print("\n" + "=" * 80)
    print("PASO 3: EJECUTANDO GUARDADO EN HISTORIAL")
    print("=" * 80)
    
    if not tablas_con_datos:
        print("❌ No hay tablas con datos para procesar")
        return None
    
    print(f"\n🚀 Iniciando guardado para {len(tablas_con_datos)} tablas...")
    print(f"   Tablas: {tablas_con_datos}")
    
    try:
        estadisticas = guardar_datos_docencia_en_historial(tablas_con_datos, logger)
        print("\n✅ Guardado completado exitosamente")
        print(f"\n📊 Estadísticas:")
        for key, value in estadisticas.items():
            print(f"   {key}: {value}")
        return estadisticas
    except Exception as e:
        print(f"\n❌ Error durante el guardado: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def verificar_modelos_historicos_despues(estado_antes):
    """Verifica el estado de los modelos históricos después del guardado."""
    print("\n" + "=" * 80)
    print("PASO 4: VERIFICANDO ESTADO DE MODELOS HISTÓRICOS (DESPUÉS)")
    print("=" * 80)
    
    modelos = {
        'HistoricalArea': HistoricalArea,
        'HistoricalCourseCategory': HistoricalCourseCategory,
        'HistoricalCourseInformation': HistoricalCourseInformation,
        'HistoricalCourseInformationAdminTeachers': HistoricalCourseInformationAdminTeachers,
        'HistoricalEnrollmentApplication': HistoricalEnrollmentApplication,
        'HistoricalEnrollmentPay': HistoricalEnrollmentPay,
        'HistoricalAccountNumber': HistoricalAccountNumber,
        'HistoricalEnrollment': HistoricalEnrollment,
        'HistoricalSubjectInformation': HistoricalSubjectInformation,
        'HistoricalEdition': HistoricalEdition,
        'HistoricalApplication': HistoricalApplication,
    }
    
    cambios_detectados = False
    for nombre, modelo in modelos.items():
        count_despues = modelo.objects.count()
        count_antes = estado_antes.get(nombre, 0)
        diferencia = count_despues - count_antes
        
        if diferencia > 0:
            print(f"✅ {nombre}: {count_antes} → {count_despues} (+{diferencia})")
            cambios_detectados = True
        elif diferencia < 0:
            print(f"⚠️  {nombre}: {count_antes} → {count_despues} ({diferencia})")
        else:
            print(f"➖ {nombre}: {count_despues} registros (sin cambios)")
    
    if not cambios_detectados:
        print("\n❌ NO SE DETECTARON CAMBIOS EN LOS MODELOS HISTÓRICOS")
        print("   Esto indica que los datos NO se están guardando correctamente")
    else:
        print("\n✅ Se detectaron cambios en los modelos históricos")


def verificar_query_datos_tabla():
    """Verifica específicamente el query que se usa en el código."""
    print("\n" + "=" * 80)
    print("PASO 5: VERIFICANDO QUERY ESPECÍFICO")
    print("=" * 80)
    
    # Probar con una tabla específica
    tabla_prueba = 'Docencia_area'
    print(f"\n🔍 Probando query para: {tabla_prueba}")
    
    # Este es el query exacto que se usa en el código
    datos_tabla = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla_prueba)
    count = datos_tabla.count()
    
    print(f"   Query: DatoArchivadoDinamico.objects.filter(tabla_origen='{tabla_prueba}')")
    print(f"   Resultado: {count} registros")
    
    if count > 0:
        print(f"\n   ✅ El query funciona correctamente")
        print(f"   Mostrando primer registro:")
        primer_registro = datos_tabla.first()
        print(f"      - ID: {primer_registro.id}")
        print(f"      - ID Original: {primer_registro.id_original}")
        print(f"      - Tabla Origen: {primer_registro.tabla_origen}")
        print(f"      - Datos Originales: {primer_registro.datos_originales}")
    else:
        print(f"\n   ❌ El query no retorna datos")
        print(f"   Verificando si hay datos con otros nombres de tabla...")
        
        # Buscar variaciones del nombre
        variaciones = [
            'docencia_area',
            'Docencia_Area',
            'DOCENCIA_AREA',
            'Area',
            'area'
        ]
        
        for variacion in variaciones:
            count_var = DatoArchivadoDinamico.objects.filter(tabla_origen=variacion).count()
            if count_var > 0:
                print(f"      ⚠️  Encontrados {count_var} registros con nombre: '{variacion}'")


def main():
    """Función principal que ejecuta todas las verificaciones."""
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO DE GUARDADO EN HISTORIAL")
    print("=" * 80)
    
    # Paso 1: Verificar datos disponibles
    tablas_con_datos = verificar_datos_disponibles()
    
    # Paso 2: Estado antes
    estado_antes = verificar_modelos_historicos_antes()
    
    # Paso 3: Ejecutar guardado
    estadisticas = ejecutar_guardado_prueba(tablas_con_datos)
    
    # Paso 4: Estado después
    verificar_modelos_historicos_despues(estado_antes)
    
    # Paso 5: Verificar query específico
    verificar_query_datos_tabla()
    
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO COMPLETADO")
    print("=" * 80)


if __name__ == '__main__':
    main()
