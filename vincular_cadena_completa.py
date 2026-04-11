#!/usr/bin/env python3
"""
Script para vincular toda la cadena de relaciones de usuarios históricos.

CADENA DE RELACIONES:
1. auth_user (ID antiguo -> ID nuevo) - MAPEO BASE
2. Docencia_studentpersonalinformation (user_id) -> auth_user
3. Docencia_application (student_id) -> Docencia_studentpersonalinformation
4. Docencia_enrollment (student_id) -> Docencia_studentpersonalinformation
5. Otras tablas que usan student_id
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.contrib.auth.models import User
from datos_archivados.models import DatoArchivadoDinamico
from historial.models import (
    HistoricalEnrollmentApplication,
    HistoricalAccountNumber,
    HistoricalEnrollment,
    HistoricalApplication
)

print("=" * 80)
print("VINCULACIÓN COMPLETA DE CADENA DE USUARIOS")
print("=" * 80)

# PASO 1: Crear mapeo base auth_user (old_id -> new_id)
print("\n1. Creando mapeo base de auth_user...")
auth_users_archivados = DatoArchivadoDinamico.objects.filter(tabla_origen='auth_user')
mapeo_auth_user = {}
usuarios_actuales_email = {u.email.lower(): u for u in User.objects.all() if u.email}

for dato in auth_users_archivados:
    old_id = dato.datos_originales.get('id')
    email = dato.datos_originales.get('email', '').lower()
    if email and email in usuarios_actuales_email:
        mapeo_auth_user[int(old_id)] = usuarios_actuales_email[email].id

print(f"   ✓ {len(mapeo_auth_user)} usuarios mapeados")
print(f"   Ejemplo: {list(mapeo_auth_user.items())[:3]}")

# PASO 2: Crear mapeo de Docencia_studentpersonalinformation
print("\n2. Creando mapeo de studentpersonalinformation...")
student_info = DatoArchivadoDinamico.objects.filter(
    tabla_origen='Docencia_studentpersonalinformation'
)
mapeo_student_info = {}  # student_info_id -> new_user_id

for dato in student_info:
    student_info_id = dato.datos_originales.get('id')
    old_user_id = dato.datos_originales.get('user_id')
    
    if old_user_id and int(old_user_id) in mapeo_auth_user:
        new_user_id = mapeo_auth_user[int(old_user_id)]
        mapeo_student_info[int(student_info_id)] = new_user_id

print(f"   ✓ {len(mapeo_student_info)} student_info mapeados")
print(f"   Ejemplo: {list(mapeo_student_info.items())[:3]}")

# PASO 3: Actualizar HistoricalApplication
print("\n3. Actualizando HistoricalApplication...")
apps_actualizadas = 0
apps_sin_mapeo = 0

for app in HistoricalApplication.objects.filter(usuario__isnull=True).select_related('dato_archivado'):
    if app.dato_archivado:
        student_id = app.dato_archivado.datos_originales.get('student_id')
        
        if student_id:
            student_id = int(student_id)
            # Buscar en mapeo de student_info
            if student_id in mapeo_student_info:
                app.usuario_id = mapeo_student_info[student_id]
                app.save()
                apps_actualizadas += 1
            # O buscar directamente en mapeo de auth_user
            elif student_id in mapeo_auth_user:
                app.usuario_id = mapeo_auth_user[student_id]
                app.save()
                apps_actualizadas += 1
            else:
                apps_sin_mapeo += 1
    
    if apps_actualizadas % 100 == 0 and apps_actualizadas > 0:
        print(f"   Procesadas: {apps_actualizadas}...")

print(f"   ✓ {apps_actualizadas} aplicaciones actualizadas")
print(f"   ⚠ {apps_sin_mapeo} sin mapeo disponible")

# PASO 4: Actualizar HistoricalEnrollment
print("\n4. Actualizando HistoricalEnrollment...")
mats_actualizadas = 0
mats_sin_mapeo = 0

for mat in HistoricalEnrollment.objects.filter(usuario__isnull=True).select_related('dato_archivado'):
    if mat.dato_archivado:
        student_id = mat.dato_archivado.datos_originales.get('student_id')
        
        if student_id:
            student_id = int(student_id)
            if student_id in mapeo_student_info:
                mat.usuario_id = mapeo_student_info[student_id]
                mat.save()
                mats_actualizadas += 1
            elif student_id in mapeo_auth_user:
                mat.usuario_id = mapeo_auth_user[student_id]
                mat.save()
                mats_actualizadas += 1
            else:
                mats_sin_mapeo += 1

print(f"   ✓ {mats_actualizadas} matrículas actualizadas")
print(f"   ⚠ {mats_sin_mapeo} sin mapeo disponible")

# PASO 5: Actualizar HistoricalEnrollmentApplication
print("\n5. Actualizando HistoricalEnrollmentApplication...")
sols_actualizadas = 0
sols_sin_mapeo = 0

for sol in HistoricalEnrollmentApplication.objects.filter(usuario__isnull=True).select_related('dato_archivado'):
    if sol.dato_archivado:
        # Esta tabla puede tener user_id directo o student_id
        user_id = sol.dato_archivado.datos_originales.get('user_id') or \
                  sol.dato_archivado.datos_originales.get('student_id')
        
        if user_id:
            user_id = int(user_id)
            if user_id in mapeo_auth_user:
                sol.usuario_id = mapeo_auth_user[user_id]
                sol.save()
                sols_actualizadas += 1
            elif user_id in mapeo_student_info:
                sol.usuario_id = mapeo_student_info[user_id]
                sol.save()
                sols_actualizadas += 1
            else:
                sols_sin_mapeo += 1

print(f"   ✓ {sols_actualizadas} solicitudes actualizadas")
print(f"   ⚠ {sols_sin_mapeo} sin mapeo disponible")

# PASO 6: Actualizar HistoricalAccountNumber
print("\n6. Actualizando HistoricalAccountNumber...")
cuentas_actualizadas = 0
cuentas_sin_mapeo = 0

for cuenta in HistoricalAccountNumber.objects.filter(usuario__isnull=True).select_related('dato_archivado'):
    if cuenta.dato_archivado:
        user_id = cuenta.dato_archivado.datos_originales.get('user_id') or \
                  cuenta.dato_archivado.datos_originales.get('student_id')
        
        if user_id:
            user_id = int(user_id)
            if user_id in mapeo_auth_user:
                cuenta.usuario_id = mapeo_auth_user[user_id]
                cuenta.save()
                cuentas_actualizadas += 1
            elif user_id in mapeo_student_info:
                cuenta.usuario_id = mapeo_student_info[user_id]
                cuenta.save()
                cuentas_actualizadas += 1
            else:
                cuentas_sin_mapeo += 1

print(f"   ✓ {cuentas_actualizadas} cuentas actualizadas")
print(f"   ⚠ {cuentas_sin_mapeo} sin mapeo disponible")

# RESUMEN FINAL
print("\n" + "=" * 80)
print("RESUMEN FINAL")
print("=" * 80)
print(f"Mapeo base (auth_user): {len(mapeo_auth_user)} usuarios")
print(f"Mapeo student_info: {len(mapeo_student_info)} registros")
print()
print(f"Aplicaciones vinculadas: {apps_actualizadas}")
print(f"Matrículas vinculadas: {mats_actualizadas}")
print(f"Solicitudes vinculadas: {sols_actualizadas}")
print(f"Cuentas vinculadas: {cuentas_actualizadas}")
print()
print(f"Total vinculado: {apps_actualizadas + mats_actualizadas + sols_actualizadas + cuentas_actualizadas}")
print("\n✓ VINCULACIÓN COMPLETADA")
print("=" * 80)

# Verificar resultados
print("\nVERIFICACIÓN:")
print(f"  Aplicaciones con usuario: {HistoricalApplication.objects.filter(usuario__isnull=False).count()}")
print(f"  Matrículas con usuario: {HistoricalEnrollment.objects.filter(usuario__isnull=False).count()}")
print(f"  Solicitudes con usuario: {HistoricalEnrollmentApplication.objects.filter(usuario__isnull=False).count()}")
print(f"  Cuentas con usuario: {HistoricalAccountNumber.objects.filter(usuario__isnull=False).count()}")
