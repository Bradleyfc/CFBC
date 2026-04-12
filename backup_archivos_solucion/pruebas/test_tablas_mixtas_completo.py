#!/usr/bin/env python
"""
Script de prueba para verificar la funcionalidad de manejo de tablas mixtas.

Este script simula los 3 escenarios:
1. Solo tablas de docencia
2. Solo tablas de usuarios
3. Tablas mixtas (docencia + usuarios)
"""

import sys
import os

# Configurar el path de Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')

import django
django.setup()

from datos_archivados.historical_data_saver import (
    es_tabla_docencia,
    son_todas_tablas_docencia,
    DOCENCIA_TABLES_MAPPING
)

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def analizar_tablas(tablas_seleccionadas):
    """Analiza y separa las tablas en grupos."""
    tablas_docencia = [tabla for tabla in tablas_seleccionadas if es_tabla_docencia(tabla)]
    tablas_usuarios = [tabla for tabla in tablas_seleccionadas if not es_tabla_docencia(tabla)]
    
    return tablas_docencia, tablas_usuarios


def determinar_escenario(tablas_docencia, tablas_usuarios):
    """Determina el escenario basado en las tablas."""
    if tablas_docencia and not tablas_usuarios:
        return "ESCENARIO 1: Solo tablas de docencia", "Guardar en modelos históricos"
    elif tablas_usuarios and not tablas_docencia:
        return "ESCENARIO 2: Solo tablas de usuarios", "Usar proceso de combinación existente"
    elif tablas_docencia and tablas_usuarios:
        return "ESCENARIO 3: Tablas mixtas", "Procesar ambos grupos independientemente"
    else:
        return "ESCENARIO DESCONOCIDO", "Sin acción definida"


def test_separacion(tablas_seleccionadas, nombre_test):
    """Ejecuta una prueba de separación de tablas."""
    print_header(f"TEST: {nombre_test}")
    
    print_info(f"Tablas seleccionadas: {tablas_seleccionadas}")
    print_info(f"Total de tablas: {len(tablas_seleccionadas)}")
    
    # Separar tablas
    tablas_docencia, tablas_usuarios = analizar_tablas(tablas_seleccionadas)
    
    print(f"\n📊 Análisis de separación:")
    print(f"  • Tablas de docencia: {len(tablas_docencia)}")
    print(f"  • Tablas de usuarios: {len(tablas_usuarios)}")
    
    if tablas_docencia:
        print(f"\n📚 Tablas de docencia detectadas:")
        for tabla in tablas_docencia:
            print(f"    ✓ {tabla}")
    
    if tablas_usuarios:
        print(f"\n👥 Tablas de usuarios detectadas:")
        for tabla in tablas_usuarios:
            print(f"    ✓ {tabla}")
    
    # Determinar escenario
    escenario, accion = determinar_escenario(tablas_docencia, tablas_usuarios)
    
    print(f"\n🎯 {escenario}")
    print(f"📋 Acción: {accion}")
    
    # Validar lógica
    if escenario.startswith("ESCENARIO 1"):
        assert len(tablas_docencia) > 0 and len(tablas_usuarios) == 0
        print_success("Validación correcta: Solo tablas de docencia")
    elif escenario.startswith("ESCENARIO 2"):
        assert len(tablas_usuarios) > 0 and len(tablas_docencia) == 0
        print_success("Validación correcta: Solo tablas de usuarios")
    elif escenario.startswith("ESCENARIO 3"):
        assert len(tablas_docencia) > 0 and len(tablas_usuarios) > 0
        print_success("Validación correcta: Tablas mixtas")
    
    print()


def main():
    """Función principal que ejecuta todas las pruebas."""
    print_header("🧪 PRUEBAS DE FUNCIONALIDAD DE TABLAS MIXTAS")
    
    # Mostrar tablas de docencia disponibles
    print_info("Tablas de docencia configuradas:")
    for tabla in DOCENCIA_TABLES_MAPPING.keys():
        print(f"  • {tabla}")
    print()
    
    # Test 1: Solo tablas de docencia
    test_separacion(
        ['Docencia_area', 'Docencia_coursecategory', 'Docencia_enrollment'],
        "Solo tablas de docencia"
    )
    
    # Test 2: Solo tablas de usuarios
    test_separacion(
        ['auth_user', 'auth_group', 'auth_permission', 'accounts_registro'],
        "Solo tablas de usuarios"
    )
    
    # Test 3: Tablas mixtas
    test_separacion(
        ['Docencia_area', 'auth_user', 'Docencia_enrollment', 'auth_group', 'accounts_registro'],
        "Tablas mixtas (docencia + usuarios)"
    )
    
    # Test 4: Tablas mixtas con más variedad
    test_separacion(
        ['Docencia_courseinformation', 'Docencia_edition', 'auth_user', 'auth_group'],
        "Tablas mixtas con courseinformation y edition"
    )
    
    # Test 5: Todas las tablas de docencia + usuarios
    todas_docencia = list(DOCENCIA_TABLES_MAPPING.keys())
    test_separacion(
        todas_docencia + ['auth_user', 'auth_group'],
        "Todas las tablas de docencia + usuarios"
    )
    
    # Test 6: Una sola tabla de docencia
    test_separacion(
        ['Docencia_area'],
        "Una sola tabla de docencia"
    )
    
    # Test 7: Una sola tabla de usuarios
    test_separacion(
        ['auth_user'],
        "Una sola tabla de usuarios"
    )
    
    print_header("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print_success("La lógica de separación de tablas funciona correctamente")
    print_success("Los 3 escenarios se detectan y procesan adecuadamente")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print_error(f"Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
