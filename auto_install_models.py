#!/usr/bin/env python
"""
Monitor automático que descarga modelos cuando se instalan las dependencias del chatbot
Uso: python auto_install_models.py &  # Ejecutar en segundo plano
"""

import time
import sys
import os
import threading
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot_install.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChatbotInstallMonitor:
    """Monitor que detecta cuándo se instalan las dependencias del chatbot"""
    
    def __init__(self):
        self.chatbot_packages = [
            'sentence_transformers',
            'transformers', 
            'torch',
            'faiss',
            'numpy'
        ]
        self.models_downloaded = False
        self.monitoring = True
    
    def check_dependencies(self):
        """Verifica qué dependencias del chatbot están instaladas"""
        installed = []
        for package in self.chatbot_packages:
            try:
                __import__(package.replace('-', '_'))
                installed.append(package)
            except ImportError:
                pass
        return installed
    
    def are_models_needed(self):
        """Verifica si los modelos necesitan ser descargados"""
        if self.models_downloaded:
            return False
            
        # Verificar si los modelos ya existen en cache
        cache_dir = Path.home() / '.cache' / 'huggingface' / 'transformers'
        if cache_dir.exists():
            # Buscar modelos específicos
            model_files = list(cache_dir.glob('**/pytorch_model.bin')) + \
                         list(cache_dir.glob('**/model.safetensors'))
            if len(model_files) >= 2:  # Al menos 2 modelos
                logger.info("✅ Modelos ya descargados previamente")
                self.models_downloaded = True
                return False
        
        return True
    
    def download_models(self):
        """Descarga los modelos del chatbot"""
        if not self.are_models_needed():
            return True
            
        logger.info("🤖 Iniciando descarga automática de modelos...")
        
        try:
            # Configurar Django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
            
            # Ejecutar hook de instalación
            from chatbot.install_hooks import download_models
            success = download_models()
            
            if success:
                self.models_downloaded = True
                logger.info("🎉 Modelos descargados automáticamente")
            else:
                logger.warning("⚠️  Error descargando modelos automáticamente")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en descarga automática: {e}")
            return False
    
    def monitor_installation(self):
        """Monitorea la instalación de dependencias"""
        logger.info("👀 Monitoreando instalación de dependencias del chatbot...")
        
        last_installed_count = len(self.check_dependencies())
        
        while self.monitoring:
            try:
                current_installed = self.check_dependencies()
                current_count = len(current_installed)
                
                # Si se instalaron nuevas dependencias del chatbot
                if current_count > last_installed_count and current_count >= 3:
                    logger.info(f"📦 Detectadas {current_count} dependencias del chatbot instaladas")
                    logger.info(f"   Paquetes: {', '.join(current_installed)}")
                    
                    # Esperar un poco para que termine la instalación
                    time.sleep(5)
                    
                    # Descargar modelos automáticamente
                    self.download_models()
                    
                    # Detener monitoreo
                    self.monitoring = False
                    break
                
                last_installed_count = current_count
                time.sleep(2)  # Verificar cada 2 segundos
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoreo detenido por usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")
                time.sleep(5)
    
    def start_monitoring(self):
        """Inicia el monitoreo en un hilo separado"""
        monitor_thread = threading.Thread(target=self.monitor_installation, daemon=True)
        monitor_thread.start()
        return monitor_thread


def main():
    """Función principal"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        # Solo verificar estado actual
        monitor = ChatbotInstallMonitor()
        installed = monitor.check_dependencies()
        print(f"Dependencias instaladas: {len(installed)}")
        print(f"Paquetes: {', '.join(installed) if installed else 'Ninguno'}")
        print(f"Modelos necesarios: {'Sí' if monitor.are_models_needed() else 'No'}")
        return
    
    # Monitoreo automático
    monitor = ChatbotInstallMonitor()
    
    # Verificar estado inicial
    installed = monitor.check_dependencies()
    if len(installed) >= 3:
        logger.info(f"✅ Dependencias del chatbot ya instaladas: {', '.join(installed)}")
        if monitor.are_models_needed():
            logger.info("🚀 Descargando modelos...")
            monitor.download_models()
        else:
            logger.info("✅ Sistema completo, no se necesita acción")
        return
    
    # Iniciar monitoreo
    logger.info("🔍 Iniciando monitoreo automático...")
    logger.info("💡 Ejecuta 'pip install -r requirements.txt' en otra terminal")
    
    try:
        monitor_thread = monitor.start_monitoring()
        
        # Mantener el script corriendo
        while monitor.monitoring:
            time.sleep(1)
            
        logger.info("✅ Monitoreo completado")
        
    except KeyboardInterrupt:
        logger.info("🛑 Detenido por usuario")
        monitor.monitoring = False


if __name__ == "__main__":
    main()