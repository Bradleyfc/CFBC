#!/usr/bin/env python
"""
Instalador inteligente que descarga modelos automáticamente
después de instalar las dependencias del chatbot
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description, check=True):
    """Ejecuta un comando con manejo de errores"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {description} completado")
            return True
        else:
            print(f"⚠️  {description} con advertencias:")
            if result.stderr:
                print(f"   {result.stderr.strip()}")
            return not check
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}:")
        print(f"   Comando: {command}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_chatbot_dependencies():
    """Verifica si las dependencias del chatbot están instaladas"""
    chatbot_packages = [
        'sentence_transformers',
        'transformers',
        'torch', 
        'faiss',
        'numpy'
    ]
    
    installed = []
    missing = []
    
    for package in chatbot_packages:
        try:
            __import__(package.replace('-', '_'))
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    return installed, missing

def install_chatbot_complete():
    """Instalación completa del chatbot con modelos"""
    
    print("🤖 Instalación Completa del Chatbot Semántico CFBC")
    print("=" * 60)
    
    # 1. Verificar estado actual
    installed, missing = check_chatbot_dependencies()
    
    if missing:
        print(f"📦 Instalando dependencias del chatbot: {', '.join(missing)}")
        
        # Instalar dependencias específicas del chatbot
        if not run_command("pip install -r requirements-chatbot.txt", 
                          "Instalación de dependencias del chatbot"):
            return False
        
        print("⏳ Esperando que las dependencias se instalen completamente...")
        time.sleep(2)
    else:
        print("✅ Dependencias del chatbot ya instaladas")
    
    # 2. Verificar instalación
    installed, missing = check_chatbot_dependencies()
    if missing:
        print(f"❌ Dependencias aún faltantes: {', '.join(missing)}")
        return False
    
    # 3. Descargar modelos automáticamente
    print("\n🚀 Iniciando descarga automática de modelos...")
    
    try:
        # Ejecutar hook de post-instalación
        from chatbot.install_hooks import post_install_setup
        post_install_setup()
        
    except ImportError:
        # Si no se puede importar, ejecutar como script externo
        if not run_command("python chatbot/install_hooks.py", 
                          "Descarga de modelos del chatbot"):
            print("⚠️  Modelos no descargados automáticamente")
            print("💡 Se descargarán al usar el chatbot por primera vez")
    
    # 4. Configuración adicional
    print("\n🔧 Configuración adicional...")
    
    # Aplicar migraciones si es necesario
    if Path("manage.py").exists():
        run_command("python manage.py migrate", "Migraciones de base de datos", check=False)
        
        # Cargar datos iniciales si existen
        fixtures_dir = Path("chatbot/fixtures")
        if fixtures_dir.exists():
            for fixture in fixtures_dir.glob("*.json"):
                run_command(f"python manage.py loaddata {fixture}", 
                           f"Carga de {fixture.name}", check=False)
        
        # Construir índice
        run_command("python manage.py rebuild_index", "Construcción del índice semántico", check=False)
    
    print("\n🎉 ¡Instalación completa del chatbot terminada!")
    print("\n📋 Para usar el chatbot:")
    print("   1. python manage.py runserver")
    print("   2. Abrir http://127.0.0.1:8000")
    print("   3. El widget aparecerá automáticamente")
    
    return True

def install_dependencies_only():
    """Instala solo las dependencias generales del proyecto"""
    
    print("📦 Instalando dependencias generales del proyecto...")
    
    if not run_command("pip install -r requirements.txt", 
                      "Instalación de dependencias generales"):
        return False
    
    # Verificar si se instalaron dependencias del chatbot
    installed, missing = check_chatbot_dependencies()
    
    if len(installed) >= 3:  # Si se instalaron al menos 3 dependencias del chatbot
        print("\n🤖 ¡Dependencias del chatbot detectadas!")
        print("🚀 Iniciando configuración automática...")
        
        # Ejecutar configuración automática
        try:
            from chatbot.install_hooks import post_install_setup
            post_install_setup()
        except Exception as e:
            print(f"⚠️  Error en configuración automática: {e}")
            print("💡 Ejecuta manualmente: python chatbot/install_hooks.py")
    
    return True

def main():
    """Función principal con detección automática"""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--chatbot-only":
            return install_chatbot_complete()
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python install_with_models.py              # Instalación automática")
            print("  python install_with_models.py --chatbot-only  # Solo chatbot")
            return True
    
    # Detección automática
    print("🔍 Detectando tipo de instalación necesaria...")
    
    # Verificar si requirements.txt existe
    if Path("requirements.txt").exists():
        return install_dependencies_only()
    else:
        return install_chatbot_complete()

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Instalación fallida. Revisa los errores anteriores.")
        sys.exit(1)