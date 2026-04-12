#!/usr/bin/env python3
"""
Script de prueba para verificar la lógica de separación de tablas
"""

# Simular la función es_tabla_docencia
DOCENCIA_TABLES = [
    'Docencia_area',
    'Docencia_coursecategory',
    'Docencia_courseinformation_adminteachers',
    'Docencia_courseinformation',
    'Docencia_enrollmentapplication',
    'Docencia_enrollmentpay',
    'Docencia_accountnumber',
    'Docencia_enrollment',
    'Docencia_subjectinformation',
    'Docencia_edition',
    'Docencia_application',
]

def es_tabla_docencia(tabla_nombre):
    """Verifica si una tabla es de docencia"""
    return tabla_nombre in DOCENCIA_TABLES

def test_separacion(tablas_seleccionadas, nombre_test):
    """Prueba la separación de tablas"""
    print(f"\n{'='*70}")
    print(f"TEST: {nombre_test}")
    print(f"{'='*70}")
    print(f"Tablas seleccionadas: {tablas_seleccionadas}")
    
    # Separar tablas
    tablas_docencia = [tabla for tabla in tablas_seleccionadas if es_tabla_docencia(tabla)]
    tablas_usuarios = [tabla for tabla in tablas_seleccionadas if not es_tabla_docencia(tabla)]
    
    print(f"\nTablas de docencia: {len(tablas_docencia)}")
    for tabla in tablas_docencia:
        print(f"  • {tabla}")
    
    print(f"\nTablas de usuarios: {len(tablas_usuarios)}")
    for tabla in tablas_usuarios:
        print(f"  • {tabla}")
    
    # Determinar escenario
    if tablas_docencia and not tablas_usuarios:
        escenario = "ESCENARIO 1: Solo tablas de docencia"
        accion = "Guardar en modelos históricos"
    elif tablas_usuarios and not tablas_docencia:
        escenario = "ESCENARIO 2: Solo tablas de usuarios"
        accion = "Usar proceso de combinación existente"
    elif tablas_docencia and tablas_usuarios:
        escenario = "ESCENARIO 3: Tablas mixtas"
        accion = "Procesar ambos grupos independientemente"
    else:
        escenario = "ERROR: No hay tablas seleccionadas"
        accion = "N/A"
    
    print(f"\n🎯 {escenario}")
    print(f"📋 Acción: {accion}")
    print(f"{'='*70}")

# ============================================================
# PRUEBAS
# ============================================================

# Test 1: Solo tablas de docencia
test_separacion(
    ['Docencia_area', 'Docencia_coursecategory', 'Docencia_enrollment'],
    "Solo tablas de docencia"
)

# Test 2: Solo tablas de usuarios
test_separacion(
    ['auth_user', 'auth_group', 'accounts_registro'],
    "Solo tablas de usuarios"
)

# Test 3: Tablas mixtas
test_separacion(
    ['Docencia_area', 'auth_user', 'Docencia_enrollment', 'auth_group', 'accounts_registro'],
    "Tablas mixtas (docencia + usuarios)"
)

# Test 4: Todas las tablas de docencia
test_separacion(
    DOCENCIA_TABLES,
    "Todas las 11 tablas de docencia"
)

# Test 5: Tablas mixtas con todas las de docencia
test_separacion(
    DOCENCIA_TABLES + ['auth_user', 'auth_group'],
    "Todas las tablas de docencia + usuarios"
)

print("\n" + "="*70)
print("✅ TODAS LAS PRUEBAS COMPLETADAS")
print("="*70)
