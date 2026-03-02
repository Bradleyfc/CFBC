"""
Script para simular exactamente lo que hace el modal cuando seleccionas las 11 tablas
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from datos_archivados.views import combinar_datos_seleccionadas
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear un usuario admin para la prueba
try:
    user = User.objects.get(username='admin')
except User.DoesNotExist:
    user = User.objects.create_superuser('admin', 'admin@test.com', 'admin')

# Crear cliente de prueba
client = Client()
client.force_login(user)

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
print("SIMULACIÓN DEL MODAL DE COMBINACIÓN SELECTIVA")
print("="*80 + "\n")

print(f"Enviando petición POST con {len(tablas_docencia)} tablas de docencia...")
print(f"Tablas: {tablas_docencia}\n")

# Hacer la petición POST como lo hace el modal
response = client.post(
    '/datos-archivados/combinar-datos-seleccionadas/',
    data=json.dumps({'tablas_seleccionadas': tablas_docencia}),
    content_type='application/json'
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}\n")

if response.json().get('success'):
    print("✅ La petición fue exitosa")
    print("⏳ Esperando 30 segundos para que el proceso en segundo plano termine...")
    
    import time
    time.sleep(30)
    
    # Verificar resultados
    from historial.models import (
        HistoricalArea,
        HistoricalCourseCategory,
        HistoricalCourseInformation,
        HistoricalEnrollmentApplication,
    )
    
    print("\n" + "="*80)
    print("VERIFICACIÓN DE RESULTADOS")
    print("="*80)
    print(f"HistoricalArea: {HistoricalArea.objects.count()} registros")
    print(f"HistoricalCourseCategory: {HistoricalCourseCategory.objects.count()} registros")
    print(f"HistoricalCourseInformation: {HistoricalCourseInformation.objects.count()} registros")
    print(f"HistoricalEnrollmentApplication: {HistoricalEnrollmentApplication.objects.count()} registros")
    
    # Verificar cache
    from django.core.cache import cache
    resultado_cache = cache.get('ultima_combinacion_completada')
    if resultado_cache:
        print("\n📊 Resultado en cache:")
        print(json.dumps(resultado_cache, indent=2, default=str))
    else:
        print("\n⚠️ No hay resultado en cache")
        
        # Verificar si hay error
        error_cache = cache.get('combinacion_error')
        if error_cache:
            print("\n❌ Error en cache:")
            print(json.dumps(error_cache, indent=2, default=str))
else:
    print(f"❌ Error: {response.json().get('error')}")

print("\n" + "="*80)
