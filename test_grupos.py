#!/usr/bin/env python
"""
Script simple para probar la configuración de grupos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')

try:
    django.setup()
    print("✓ Django configurado correctamente")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

try:
    from django.contrib.auth.models import Group
    from principal.signals import GRUPOS_SISTEMA
    
    print(f"\n📋 Verificando {len(GRUPOS_SISTEMA)} grupos...")
    
    for config_grupo in GRUPOS_SISTEMA:
        nombre = config_grupo['nombre']
        existe = Group.objects.filter(name=nombre).exists()
        
        if existe:
            grupo = Group.objects.get(name=nombre)
            print(f"✓ {nombre} - Existe ({grupo.permissions.count()} permisos)")
        else:
            print(f"❌ {nombre} - No existe")
    
    total_configurados = Group.objects.filter(
        name__in=[g['nombre'] for g in GRUPOS_SISTEMA]
    ).count()
    
    print(f"\n📊 Resumen: {total_configurados}/{len(GRUPOS_SISTEMA)} grupos configurados")
    
    if total_configurados == len(GRUPOS_SISTEMA):
        print("🎉 ¡Todos los grupos están configurados!")
    else:
        print("⚠️  Algunos grupos faltan por configurar")
        print("Ejecuta: python manage.py migrate")
        print("O inicia el servidor: python manage.py runserver")

except Exception as e:
    print(f"❌ Error verificando grupos: {e}")
    import traceback
    traceback.print_exc()