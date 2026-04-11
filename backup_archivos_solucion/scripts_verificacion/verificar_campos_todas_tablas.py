#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from datos_archivados.models import DatoArchivadoDinamico

tablas = [
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

print("Campos de cada tabla de docencia:\n")
print("="*80)

for tabla in tablas:
    dato = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).first()
    if dato:
        print(f"\n{tabla}:")
        print(f"  Campos: {list(dato.datos_originales.keys())}")
        print(f"  Ejemplo de datos:")
        for k, v in list(dato.datos_originales.items())[:5]:
            print(f"    {k}: {v}")
    else:
        print(f"\n{tabla}: NO HAY DATOS")
