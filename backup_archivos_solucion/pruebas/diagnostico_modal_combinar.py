#!/usr/bin/env python
"""
Script de diagnóstico para el problema del modal de combinación de tablas.
Verifica por qué no se guardan registros en la app historial cuando se combinan
las 11 tablas de docencia.
"""

import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.models import DatoArchivadoDinamico
from datos_archivados.historical_data_saver import (
    DOCENCIA_TABLES_MAPPING,
    es_tabla_docencia,
    son_todas_tablas_docencia,
    guardar_datos_docencia_en_historial
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

# Colores para la consola
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def verificar_paso_1_datos_archivados():
    """Verifica que existan datos en DatoArchivadoDinamico para las 11 tablas de docencia"""
    print_header("PASO 1: Verificar datos en DatoArchivadoDinamico")
    
    tablas_docencia = list(DOCENCIA_TABLES_MAPPING.keys())
    print_info(f"Tablas de docencia esperadas: {len(tablas_docencia)}")
    
    resultados = {}
    for tabla in tablas_docencia:
        count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
        resultados[tabla] = count
        
        if count > 0:
            print_success(f"{tabla}: {count} registros")
        else:
            print_error(f"{tabla}: 0 registros - NO HAY DATOS PARA COMBINAR")
    
    total_registros = sum(resultados.values())
    print_info(f"\nTotal de registros archivados: {total_registros}")
    
    if total_registros == 0:
        print_error("❌ PROBLEMA ENCONTRADO: No hay datos archivados para combinar")
        return False
    
    return True


def verificar_paso_2_modelos_historicos():
    """Verifica que los modelos históricos existan y estén accesibles"""
    print_header("PASO 2: Verificar modelos históricos")
    
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
    
    for nombre, modelo in modelos.items():
        try:
            count = modelo.objects.count()
            print_success(f"{nombre}: {count} registros existentes")
        except Exception as e:
            print_error(f"{nombre}: Error al acceder - {str(e)}")
            return False
    
    return True


def verificar_paso_3_mapeo_tablas():
    """Verifica que el mapeo de tablas sea correcto"""
    print_header("PASO 3: Verificar mapeo de tablas")
    
    print_info("Mapeo definido en DOCENCIA_TABLES_MAPPING:")
    for tabla_origen, modelo_destino in DOCENCIA_TABLES_MAPPING.items():
        print(f"  {tabla_origen} → {modelo_destino}")
    
    # Verificar que todas las tablas se detecten correctamente
    tablas_test = list(DOCENCIA_TABLES_MAPPING.keys())
    if son_todas_tablas_docencia(tablas_test):
        print_success("Todas las tablas se detectan correctamente como tablas de docencia")
        return True
    else:
        print_error("Algunas tablas no se detectan como tablas de docencia")
        return False


def verificar_paso_4_estructura_datos():
    """Verifica la estructura de los datos archivados"""
    print_header("PASO 4: Verificar estructura de datos archivados")
    
    # Tomar una muestra de cada tabla
    for tabla in DOCENCIA_TABLES_MAPPING.keys():
        registro = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).first()
        if registro:
            print_info(f"\n{tabla}:")
            print(f"  ID Original: {registro.id_original}")
            print(f"  Fecha archivo: {registro.fecha_archivo}")
            
            # Verificar que datos_originales sea un dict válido
            try:
                if isinstance(registro.datos_originales, str):
                    datos = json.loads(registro.datos_originales)
                else:
                    datos = registro.datos_originales
                
                print_success(f"  Datos originales: {len(datos)} campos")
                print(f"  Campos: {', '.join(list(datos.keys())[:5])}...")
            except Exception as e:
                print_error(f"  Error al parsear datos_originales: {str(e)}")
        else:
            print_warning(f"{tabla}: No hay registros para verificar")
    
    return True


def simular_guardado():
    """Simula el proceso de guardado para detectar errores"""
    print_header("PASO 5: Simular proceso de guardado")
    
    tablas_docencia = list(DOCENCIA_TABLES_MAPPING.keys())
    
    # Verificar que hay datos
    total_datos = sum(
        DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
        for tabla in tablas_docencia
    )
    
    if total_datos == 0:
        print_error("No hay datos para simular el guardado")
        return False
    
    print_info(f"Intentando guardar {total_datos} registros...")
    
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        
        # Crear un handler para capturar los logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Ejecutar la función de guardado
        resultado = guardar_datos_docencia_en_historial(tablas_docencia, logger)
        
        print_info("\nResultado del guardado:")
        print(json.dumps(resultado, indent=2, default=str))
        
        if resultado.get('total_registros_guardados', 0) > 0:
            print_success(f"✓ Se guardaron {resultado['total_registros_guardados']} registros")
            return True
        else:
            print_error("✗ No se guardó ningún registro")
            return False
            
    except Exception as e:
        print_error(f"Error durante el guardado: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def verificar_paso_6_registros_guardados():
    """Verifica si se guardaron registros en los modelos históricos"""
    print_header("PASO 6: Verificar registros guardados en historial")
    
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
    
    total_guardados = 0
    for nombre, modelo in modelos.items():
        count = modelo.objects.count()
        total_guardados += count
        if count > 0:
            print_success(f"{nombre}: {count} registros")
        else:
            print_warning(f"{nombre}: 0 registros")
    
    print_info(f"\nTotal de registros en historial: {total_guardados}")
    
    return total_guardados > 0


def main():
    print_header("DIAGNÓSTICO: Modal de Combinación de Tablas")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    pasos = [
        ("Datos archivados disponibles", verificar_paso_1_datos_archivados),
        ("Modelos históricos accesibles", verificar_paso_2_modelos_historicos),
        ("Mapeo de tablas correcto", verificar_paso_3_mapeo_tablas),
        ("Estructura de datos válida", verificar_paso_4_estructura_datos),
        ("Simulación de guardado", simular_guardado),
        ("Registros guardados", verificar_paso_6_registros_guardados),
    ]
    
    resultados = []
    for nombre, funcion in pasos:
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
        except Exception as e:
            print_error(f"Error en {nombre}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            resultados.append((nombre, False))
    
    # Resumen final
    print_header("RESUMEN DEL DIAGNÓSTICO")
    
    for nombre, resultado in resultados:
        if resultado:
            print_success(f"{nombre}")
        else:
            print_error(f"{nombre}")
    
    pasos_exitosos = sum(1 for _, r in resultados if r)
    print_info(f"\nPasos exitosos: {pasos_exitosos}/{len(pasos)}")
    
    if pasos_exitosos == len(pasos):
        print_success("\n✓ Todos los pasos pasaron correctamente")
        print_info("El problema podría estar en el frontend (JavaScript) o en la vista de Django")
    else:
        print_error("\n✗ Se encontraron problemas en el proceso")
        print_info("Revisa los pasos fallidos arriba para identificar la causa")


if __name__ == '__main__':
    main()
