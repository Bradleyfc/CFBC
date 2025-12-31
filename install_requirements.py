#!/usr/bin/env python3
"""
Script para instalar dependencias del sistema de documentos
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}:")
        print(f"   Comando: {command}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Función principal"""
    print("🚀 Instalador de dependencias - Sistema de Documentos CFBC")
    print("=" * 60)
    
    # Verificar que estamos en un entorno virtual
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  ADVERTENCIA: No se detectó un entorno virtual activo")
        response = input("¿Continuar de todos modos? (y/N): ")
        if response.lower() != 'y':
            print("❌ Instalación cancelada")
            return
    
    # Actualizar pip
    if not run_command("python -m pip install --upgrade pip", "Actualizando pip"):
        return
    
    # Instalar dependencias principales
    if not run_command("pip install -r requirements.txt", "Instalando dependencias principales"):
        return
    
    # Preguntar por dependencias opcionales
    print("\n📦 Dependencias opcionales disponibles:")
    print("   - Almacenamiento en la nube (AWS S3, Google Cloud)")
    print("   - Procesamiento avanzado de documentos")
    print("   - Herramientas de desarrollo y testing")
    print("   - Monitoreo y performance")
    
    install_optional = input("\n¿Instalar dependencias opcionales? (y/N): ")
    if install_optional.lower() == 'y':
        if not run_command("pip install -r requirements-optional.txt", "Instalando dependencias opcionales"):
            print("⚠️  Algunas dependencias opcionales fallaron, pero las principales están instaladas")
    
    # Verificar instalación de Django
    try:
        import django
        print(f"\n✅ Django {django.get_version()} instalado correctamente")
    except ImportError:
        print("\n❌ Error: Django no se instaló correctamente")
        return
    
    # Instrucciones finales
    print("\n🎉 ¡Instalación completada!")
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar migraciones: python manage.py migrate")
    print("   2. Compilar Tailwind CSS: python manage.py tailwind build")
    print("   3. Crear superusuario: python manage.py createsuperuser")
    print("   4. Iniciar servidor: python manage.py runserver")
    
    print("\n📚 Funcionalidades del sistema de documentos:")
    print("   ✅ Subida de múltiples tipos de archivo")
    print("   ✅ Organización por carpetas")
    print("   ✅ Control de permisos por rol")
    print("   ✅ Notificaciones automáticas")
    print("   ✅ Auditoría de accesos")
    print("   ✅ Interfaz glassmorphism moderna")

if __name__ == "__main__":
    main()