#!/usr/bin/env python
"""
Hooks de instalación para el chatbot
Se ejecutan automáticamente después de instalar las dependencias
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Verifica que las dependencias del chatbot estén instaladas"""
    required_packages = [
        'sentence_transformers',
        'transformers', 
        'torch',
        'faiss',
        'numpy'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    return missing


def download_models():
    """Descarga los modelos necesarios para el chatbot con optimizaciones"""
    
    logger.info("🤖 Iniciando descarga optimizada de modelos del chatbot...")
    logger.info("=" * 60)
    
    # Verificar dependencias
    missing = check_dependencies()
    if missing:
        logger.error(f"❌ Dependencias faltantes: {', '.join(missing)}")
        logger.info("💡 Ejecuta: pip install -r requirements.txt")
        return False
    
    try:
        # Configurar Django si es necesario
        if 'DJANGO_SETTINGS_MODULE' not in os.environ:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
        
        # Importar Django
        import django
        django.setup()
        
        # Usar descargador optimizado
        from chatbot.services.model_downloader import model_downloader
        
        # 1. Modelo de embeddings
        embedding_model = 'paraphrase-multilingual-MiniLM-L12-v2'
        logger.info(f"📥 Verificando modelo de embeddings: {embedding_model}")
        
        if model_downloader.check_model_cached(embedding_model):
            logger.info("   ✅ Modelo de embeddings ya disponible")
        else:
            logger.info("   📦 Descargando modelo de embeddings (~470 MB)...")
            if model_downloader.download_model_smart(embedding_model):
                logger.info("   ✅ Modelo de embeddings descargado")
            else:
                logger.warning("   ⚠️  Error descargando embeddings, se descargará al usar")
        
        # Verificar que funcione
        try:
            from chatbot.services.semantic_search import SemanticSearchService
            search_service = SemanticSearchService()
            test_embedding = search_service.generate_embedding("prueba")
            logger.info(f"   ✅ Embeddings funcionando (dimensión: {len(test_embedding)})")
        except Exception as e:
            logger.warning(f"   ⚠️  Error verificando embeddings: {e}")
        
        # 2. Modelo LLM (opcional y más lento)
        from chatbot.config import LLM_ENABLED, LLM_MODEL
        
        if LLM_ENABLED:
            logger.info(f"📥 Verificando modelo LLM: {LLM_MODEL}")
            
            if model_downloader.check_model_cached(LLM_MODEL):
                logger.info("   ✅ Modelo LLM ya disponible")
            else:
                logger.info("   📦 Descargando modelo LLM (~308 MB)...")
                logger.info("   ⏳ Esta descarga puede tomar varios minutos...")
                
                if model_downloader.download_model_smart(LLM_MODEL):
                    logger.info("   ✅ Modelo LLM descargado")
                else:
                    logger.warning("   ⚠️  Error descargando LLM, se descargará al usar")
            
            # Verificar LLM
            try:
                from chatbot.services.llm_generator import LLMGeneratorService
                llm_service = LLMGeneratorService()
                if llm_service.is_available():
                    logger.info("   ✅ LLM funcionando correctamente")
                else:
                    logger.info("   ℹ️  LLM no disponible (normal si está deshabilitado)")
            except Exception as e:
                logger.warning(f"   ⚠️  Error verificando LLM: {e}")
        else:
            logger.info("ℹ️  Modelo LLM deshabilitado en configuración")
            logger.info("   💡 Para habilitarlo: LLM_ENABLED=true en variables de entorno")
        
        logger.info("🎉 ¡Descarga de modelos completada!")
        logger.info("📍 Ubicación: ~/.cache/huggingface/")
        logger.info("💾 Espacio utilizado: ~470-800 MB (según configuración)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error descargando modelos: {e}")
        logger.info("🔧 Soluciones:")
        logger.info("   1. Verificar conexión a internet")
        logger.info("   2. Verificar espacio en disco (necesario: 1GB)")
        logger.info("   3. Ejecutar manualmente: python manage.py download_models")
        logger.info("   4. Deshabilitar LLM: LLM_ENABLED=false")
        return False


def post_install_setup():
    """Configuración completa post-instalación"""
    
    logger.info("🚀 Configuración post-instalación del chatbot")
    logger.info("=" * 50)
    
    # 1. Descargar modelos
    if not download_models():
        logger.warning("⚠️  Modelos no descargados, se descargarán al usar el chatbot")
    
    # 2. Verificar estructura de directorios
    logger.info("📁 Verificando estructura de directorios...")
    
    base_dir = Path(__file__).parent.parent
    required_dirs = [
        base_dir / 'chatbot_data',
        base_dir / 'chatbot_data' / 'faiss_index',
        base_dir / 'chatbot_data' / 'models'
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"   ✅ {dir_path.name}")
    
    # 3. Información final
    logger.info("🎯 Próximos pasos:")
    logger.info("   1. python manage.py migrate")
    logger.info("   2. python manage.py loaddata chatbot/fixtures/*.json")
    logger.info("   3. python manage.py rebuild_index")
    logger.info("   4. python manage.py runserver")
    
    logger.info("✅ Configuración post-instalación completada")


if __name__ == "__main__":
    post_install_setup()