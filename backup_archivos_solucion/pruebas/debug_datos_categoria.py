"""
Script para debuggear los datos de Docencia_coursecategory
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.models import DatoArchivadoDinamico
import json

# Obtener el primer registro de Docencia_coursecategory
registro = DatoArchivadoDinamico.objects.filter(tabla_origen='Docencia_coursecategory').first()

if registro:
    print("Datos originales del registro:")
    print(json.dumps(registro.datos_originales, indent=2))
else:
    print("No se encontró ningún registro de Docencia_coursecategory")
