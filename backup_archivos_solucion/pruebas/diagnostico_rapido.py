#!/usr/bin/env python
"""
Script de diagnóstico rápido para el problema de guardado en historial.
Ejecuta todas las verificaciones básicas en un solo comando.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.models import DatoArchivadoDinamico
from historial.models import (
    HistoricalArea,
    HistoricalCourseCategory,
    HistoricalCourseInformation,
)

def print_header(titulo):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 80)
    print(titulo.center(80))
    print("=" * 80)


def verificacion_1_datos_disponibles():
    """Verificación 1: ¿Hay datos en DatoArchivadoDinamico?"""
    print_header("VERIFICACIÓN 1: DATOS DISPONIBLES")
    
    total = DatoArchivadoDinamico.objects.count()
    print(f"\n📊 Total de registros en DatoArchivadoDinamico: {total}")
    
    if total == 0:
        print("\n❌ PROBLEMA ENCONTRADO: No hay datos en DatoArchivadoDinamico")
        print("   Causa: Los datos no se han migrado desde MariaDB")
        print("   Solución: Ejecutar el proceso de migración/importación primero")
        return False
    
    print("\n✅ Hay datos disponibles")
    
    # Ver tablas únicas
    tablas = list(DatoArchivadoDinamico.objects.values_list('tabla_origen', flat=True).distinct())
    print(f"\n📋 Tablas únicas encontradas ({len(tablas)}):")
    for tabla in sorted(tablas):
        count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
        print(f"   • {tabla}: {count} registros")
    
    return True


def verificacion_2_tablas_docencia():
    """Verificación 2: ¿Hay datos para las tablas de docencia?"""
    print_header("VERIFICACIÓN 2: TABLAS DE DOCENCIA")
    
    tablas_docencia = [
        'Docencia_area',
        'Docencia_coursecategory',
        'Docencia_courseinformation',
        'Docencia_courseinformation_adminteachers',
        'Docencia_enrollmentapplication',
        'Docencia_enrollmentpay',
        'Docencia_accountnumber',
        'Docencia_enrollment',
        'Docencia_subjectinformation',
        'Docencia_edition',
        'Docencia_application',
    ]
    
    tablas_con_datos = []
    tablas_sin_datos = []
    
    print("\n📊 Verificando tablas de docencia:")
    for tabla in tablas_docencia:
        count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
        if count > 0:
            print(f"   ✅ {tabla}: {count} registros")
            tablas_con_datos.append(tabla)
        else:
            print(f"   ❌ {tabla}: 0 registros")
            tablas_sin_datos.append(tabla)
    
    print(f"\n📈 Resumen:")
    print(f"   Tablas con datos: {len(tablas_con_datos)}")
    print(f"   Tablas sin datos: {len(tablas_sin_datos)}")
    
    if len(tablas_con_datos) == 0:
        print("\n❌ PROBLEMA ENCONTRADO: Ninguna tabla de docencia tiene datos")
        print("   Posibles causas:")
        print("   1. Los datos no se han migrado")
        print("   2. Los nombres de tabla son diferentes")
        print("\n   Verificando nombres alternativos...")
        
        # Buscar variaciones
        todas_tablas = list(DatoArchivadoDinamico.objects.values_list('tabla_origen', flat=True).distinct())
        variaciones_encontradas = []
        
        for tabla_esperada in tablas_docencia:
            nombre_base = tabla_esperada.lower().replace('docencia_', '')
            for tabla_real in todas_tablas:
                if nombre_base in tabla_real.lower():
                    variaciones_encontradas.append((tabla_esperada, tabla_real))
        
        if variaciones_encontradas:
            print("\n   ⚠️  Posibles variaciones de nombres encontradas:")
            for esperada, real in variaciones_encontradas:
                count = DatoArchivadoDinamico.objects.filter(tabla_origen=real).count()
                print(f"      {esperada} → {real} ({count} registros)")
            print("\n   Solución: Actualizar DOCENCIA_TABLES_MAPPING con los nombres correctos")
        
        return False
    
    print(f"\n✅ {len(tablas_con_datos)} tablas de docencia tienen datos")
    return True


def verificacion_3_modelos_historicos():
    """Verificación 3: ¿Hay datos en los modelos históricos?"""
    print_header("VERIFICACIÓN 3: MODELOS HISTÓRICOS")
    
    modelos = {
        'HistoricalArea': HistoricalArea,
        'HistoricalCourseCategory': HistoricalCourseCategory,
        'HistoricalCourseInformation': HistoricalCourseInformation,
    }
    
    total_registros = 0
    
    print("\n📊 Estado de los modelos históricos:")
    for nombre, modelo in modelos.items():
        count = modelo.objects.count()
        total_registros += count
        if count > 0:
            print(f"   ✅ {nombre}: {count} registros")
        else:
            print(f"   ➖ {nombre}: 0 registros")
    
    if total_registros == 0:
        print("\n⚠️  Los modelos históricos están vacíos")
        print("   Esto es normal si aún no se ha ejecutado el guardado")
        print("   O indica que el guardado no está funcionando")
    else:
        print(f"\n✅ Total de registros históricos: {total_registros}")
    
    return True


def verificacion_4_deteccion_tablas():
    """Verificación 4: ¿La función de detección funciona?"""
    print_header("VERIFICACIÓN 4: DETECCIÓN DE TABLAS")
    
    from datos_archivados.historical_data_saver import (
        es_tabla_docencia,
        DOCENCIA_TABLES_MAPPING
    )
    
    print(f"\n📋 Mapeo DOCENCIA_TABLES_MAPPING ({len(DOCENCIA_TABLES_MAPPING)} tablas):")
    for tabla in DOCENCIA_TABLES_MAPPING.keys():
        print(f"   • {tabla}")
    
    # Probar la función
    print("\n🧪 Probando función es_tabla_docencia:")
    pruebas = [
        ('Docencia_area', True),
        ('Docencia_coursecategory', True),
        ('Usuario_user', False),
        ('Auth_user', False),
    ]
    
    todas_correctas = True
    for tabla, esperado in pruebas:
        resultado = es_tabla_docencia(tabla)
        correcto = resultado == esperado
        simbolo = "✅" if correcto else "❌"
        print(f"   {simbolo} es_tabla_docencia('{tabla}') = {resultado} (esperado: {esperado})")
        if not correcto:
            todas_correctas = False
    
    if todas_correctas:
        print("\n✅ La función de detección funciona correctamente")
    else:
        print("\n❌ PROBLEMA: La función de detección no funciona correctamente")
    
    return todas_correctas


def generar_reporte():
    """Genera un reporte con recomendaciones."""
    print_header("REPORTE Y RECOMENDACIONES")
    
    print("\n📋 RESUMEN DE VERIFICACIONES:")
    print("   1. Datos disponibles en DatoArchivadoDinamico")
    print("   2. Datos para tablas de docencia")
    print("   3. Estado de modelos históricos")
    print("   4. Función de detección de tablas")
    
    print("\n📝 PRÓXIMOS PASOS:")
    print("   1. Si no hay datos en DatoArchivadoDinamico:")
    print("      → Ejecutar proceso de migración/importación desde MariaDB")
    print()
    print("   2. Si los nombres de tabla son diferentes:")
    print("      → Actualizar DOCENCIA_TABLES_MAPPING en historical_data_saver.py")
    print()
    print("   3. Si hay datos pero no se guardan:")
    print("      → Ejecutar: python test_guardado_historial_debug.py")
    print("      → Revisar logs de Django cuando se ejecuta 'Combinar Tablas'")
    print()
    print("   4. Para más detalles:")
    print("      → Leer: DIAGNOSTICO_PROBLEMA_GUARDADO_HISTORIAL.md")
    print("      → Leer: INSTRUCCIONES_DIAGNOSTICO.md")


def main():
    """Función principal."""
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO RÁPIDO - PROBLEMA DE GUARDADO EN HISTORIAL".center(80))
    print("=" * 80)
    
    try:
        # Ejecutar verificaciones
        v1 = verificacion_1_datos_disponibles()
        v2 = verificacion_2_tablas_docencia()
        v3 = verificacion_3_modelos_historicos()
        v4 = verificacion_4_deteccion_tablas()
        
        # Generar reporte
        generar_reporte()
        
        # Resultado final
        print_header("RESULTADO FINAL")
        
        if not v1:
            print("\n❌ PROBLEMA CRÍTICO: No hay datos en DatoArchivadoDinamico")
            print("   Solución: Migrar datos desde MariaDB primero")
        elif not v2:
            print("\n❌ PROBLEMA: No hay datos para tablas de docencia")
            print("   Solución: Verificar nombres de tabla o migrar datos")
        elif not v4:
            print("\n❌ PROBLEMA: La función de detección no funciona")
            print("   Solución: Revisar código de es_tabla_docencia")
        else:
            print("\n✅ Todas las verificaciones básicas pasaron")
            print("   Si el problema persiste:")
            print("   → Ejecutar: python test_guardado_historial_debug.py")
            print("   → Revisar logs de Django en tiempo real")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error durante el diagnóstico: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
