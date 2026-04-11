#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name = 'historial_docenciaarea'
    ORDER BY ordinal_position
""")

print("Estructura de historial_docenciaarea:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]:20} {row[1]:20} NULL:{row[2]:5} Default:{row[3]}")
