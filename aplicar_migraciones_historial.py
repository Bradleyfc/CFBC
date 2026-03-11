#!/usr/bin/env python
"""
Script para aplicar las migraciones de la app historial.
Ejecutar este script si aparece el error: relation "historial_docenciaapplication" does not exist
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    print("=" * 60)
    print("APLICANDO MIGRACIONES DE HISTORIAL")
    print("=" * 60)
    
    try:
        # Mostrar estado actual de migraciones
        print("\n📋 Estado actual de migraciones de historial:")
        execute_from_command_line(['manage.py', 'showmigrations', 'historial'])
        
        # Aplicar migraciones
        print("\n🚀 Aplicando migraciones de historial...")
        execute_from_command_line(['manage.py', 'migrate', 'historial'])
        
        print("\n✅ Migraciones aplicadas exitosamente!")
        
        # Verificar estado final
        print("\n📋 Estado final de migraciones:")
        execute_from_command_line(['manage.py', 'showmigrations', 'historial'])
        
        # Verificar tablas creadas
        print("\n🔍 Verificando tablas en la base de datos...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'historial_%'
                ORDER BY table_name
            """)
            tablas = cursor.fetchall()
            
            if tablas:
                print(f"\n✓ Se encontraron {len(tablas)} tablas de historial:")
                for tabla in tablas:
                    print(f"  • {tabla[0]}")
            else:
                print("\n⚠️  No se encontraron tablas de historial")
        
        print("\n" + "=" * 60)
        print("PROCESO COMPLETADO")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
