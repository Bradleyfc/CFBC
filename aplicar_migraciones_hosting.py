#!/usr/bin/env python
"""
Script para aplicar migraciones en el hosting
Ejecutar con: python aplicar_migraciones_hosting.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    """Aplicar migraciones pendientes"""
    print("🔄 Aplicando migraciones pendientes...")
    
    try:
        # Mostrar estado actual de migraciones
        print("\n📋 Estado actual de migraciones:")
        execute_from_command_line(['manage.py', 'showmigrations', 'datos_archivados'])
        
        # Aplicar migraciones
        print("\n🚀 Aplicando migraciones...")
        execute_from_command_line(['manage.py', 'migrate', 'datos_archivados'])
        
        print("\n✅ Migraciones aplicadas exitosamente!")
        
        # Verificar estado final
        print("\n📋 Estado final de migraciones:")
        execute_from_command_line(['manage.py', 'showmigrations', 'datos_archivados'])
        
    except Exception as e:
        print(f"\n❌ Error al aplicar migraciones: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()