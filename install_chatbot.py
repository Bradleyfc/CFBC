#!/usr/bin/env python
"""
Script de instalación completa del chatbot CFBC
Instala dependencias y descarga modelos automáticamente
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}:")
        print(f"   Comando: {command}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Instalación completa del sistema"""
    
    print("🚀 Instalación Completa del Chatbot Semántico CFBC")
    print("=" * 60)
    
    # 1. Instalar dependencias de Python
    if not run_command("pip install -r requirements.txt", "Instalación de dependencias Python"):
        print("💡 Intenta: pip install --upgrade pip")
        return False
    
    # 1.5. Ejecutar hook automático de modelos después de instalar dependencias
    print("\n🤖 Ejecutando configuración automática del chatbot...")
    try:
        from chatbot.install_hooks import post_install_setup
        post_install_setup()
    except Exception as e:
        print(f"⚠️  Error en configuración automática: {e}")
        print("💡 Continuando con instalación manual...")
    
    # 2. Aplicar migraciones
    if not run_command("python manage.py migrate", "Aplicación de migraciones de base de datos"):
        return False
    
    # 3. Cargar datos iniciales
    commands = [
        ("python manage.py loaddata chatbot/fixtures/categorias_faq.json", "Carga de categorías FAQ"),
        ("python manage.py loaddata chatbot/fixtures/faqs_iniciales.json", "Carga de FAQs iniciales"),
        ("python manage.py loaddata chatbot/fixtures/faq_variaciones.json", "Carga de variaciones FAQ"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    # 4. Descargar modelos de IA
    print("\n🤖 Descargando modelos de IA (esto puede tomar varios minutos)...")
    print("   📦 Modelo de embeddings: ~470 MB")
    print("   📦 Modelo LLM: ~308 MB")
    print("   💾 Total aproximado: ~800 MB")
    
    if not run_command("python manage.py download_models --verbose", "Descarga de modelos de IA"):
        print("💡 Los modelos se descargarán automáticamente al usar el chatbot")
    
    # 5. Construir índice semántico
    if not run_command("python manage.py rebuild_index", "Construcción del índice semántico"):
        return False
    
    # 6. Recopilar archivos estáticos
    if not run_command("python manage.py collectstatic --noinput", "Recopilación de archivos estáticos"):
        print("⚠️  Error recopilando archivos estáticos (no crítico)")
    
    print("\n🎉 ¡Instalación completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("   1. Ejecutar: python manage.py runserver")
    print("   2. Abrir: http://127.0.0.1:8000")
    print("   3. El widget del chatbot aparecerá automáticamente")
    print("\n📚 Documentación:")
    print("   - Configuración: chatbot/CONFIGURACION.md")
    print("   - Resumen técnico: chatbot/RESUMEN_IMPLEMENTACION.md")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Instalación fallida. Revisa los errores anteriores.")
        sys.exit(1)