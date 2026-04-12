#!/usr/bin/env python
"""
Script para configurar grupos por defecto del sistema
Ejecutar después de las migraciones iniciales
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    print("Asegúrate de que:")
    print("1. Estás en el directorio raíz del proyecto")
    print("2. El archivo cfbc/settings.py existe")
    print("3. Las dependencias están instaladas")
    sys.exit(1)

from django.contrib.auth.models import Group
from principal.config_grupos import GRUPOS_SISTEMA
from principal.config_grupos import GRUPOS_SISTEMA, configurar_permisos_grupo
from principal.utils import verificar_grupos_configurados

def main():
    print("=== Configuración Automática de Grupos del Sistema ===")
    print(f"Configurando {len(GRUPOS_SISTEMA)} grupos por defecto...\n")
    
    # Verificar estado inicial
    verificacion_inicial = verificar_grupos_configurados()
    print(f"Estado inicial: {verificacion_inicial['total_configurados']}/{verificacion_inicial['total_definidos']} grupos configurados")
    
    if verificacion_inicial['configurados_correctamente']:
        print("✅ Todos los grupos ya están configurados correctamente")
        respuesta = input("\n¿Deseas reconfigurar los permisos? (s/N): ").lower()
        if respuesta != 's':
            print("Configuración cancelada")
            return
    
    grupos_creados = 0
    grupos_actualizados = 0
    grupos_existentes = 0
    errores = 0
    
    for config_grupo in GRUPOS_SISTEMA:
        nombre_grupo = config_grupo['nombre']
        try:
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            
            if created:
                grupos_creados += 1
                print(f"✓ Grupo '{nombre_grupo}' creado")
            else:
                grupos_existentes += 1
                print(f"○ Grupo '{nombre_grupo}' ya existe")
            
            # Configurar o reconfigurar permisos
            try:
                # Limpiar permisos existentes para reconfigurar
                grupo.permissions.clear()
                configurar_permisos_grupo(grupo, config_grupo)
                
                if created:
                    print(f"  → Permisos configurados para {nombre_grupo}")
                else:
                    grupos_actualizados += 1
                    print(f"  → Permisos actualizados para {nombre_grupo}")
                    
            except Exception as e:
                print(f"  ⚠️  Error configurando permisos para {nombre_grupo}: {e}")
                
        except Exception as e:
            errores += 1
            print(f"❌ Error configurando grupo '{nombre_grupo}': {e}")
    
    print("\n" + "="*60)
    print("RESUMEN DE CONFIGURACIÓN:")
    print(f"✓ Grupos creados: {grupos_creados}")
    print(f"⟳ Grupos actualizados: {grupos_actualizados}")
    print(f"○ Grupos que ya existían: {grupos_existentes}")
    print(f"❌ Errores: {errores}")
    print(f"📊 Total procesados: {len(GRUPOS_SISTEMA)}")
    
    # Verificación final
    verificacion_final = verificar_grupos_configurados()
    print(f"\nEstado final: {verificacion_final['total_configurados']}/{verificacion_final['total_definidos']} grupos configurados")
    
    if verificacion_final['configurados_correctamente'] and errores == 0:
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\n📋 Grupos disponibles en el administrador de Django:")
        for config in GRUPOS_SISTEMA:
            print(f"  • {config['nombre']}: {config['descripcion']}")
    else:
        print(f"\n⚠️  Configuración completada con {errores} errores")
        if verificacion_final['faltantes']:
            print(f"Grupos faltantes: {', '.join(verificacion_final['faltantes'])}")
    
    print("\n🔗 Enlaces útiles:")
    print("  • Admin Django: http://localhost:8000/admin/auth/group/")
    print("  • Verificar configuración: python manage.py configurar_grupos --info")
    print("  • Setup completo: python manage.py setup_inicial")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Configuración cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("Para más información, ejecuta: python manage.py configurar_grupos --info")