from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    
    def ready(self):
        """Import signals when app is ready"""
        # import chatbot.signals  # noqa  # Temporarily disabled
        
        # Descargar modelos automáticamente si no existen
        self._ensure_models_downloaded()
    
    def _ensure_models_downloaded(self):
        """Descarga automáticamente los modelos si no están disponibles"""
        
        # Solo ejecutar en el proceso principal (no en workers)
        if os.environ.get('RUN_MAIN') == 'true' or 'runserver' not in os.sys.argv:
            return
            
        try:
            # Verificar si los modelos ya están descargados
            from chatbot.services.semantic_search import SemanticSearchService
            from chatbot.services.llm_generator import LLMGeneratorService
            
            # Intentar cargar los servicios (esto descarga los modelos si no existen)
            logger.info("🤖 Verificando modelos del chatbot...")
            
            # Verificar modelo de embeddings
            try:
                search_service = SemanticSearchService()
                test_embedding = search_service.generate_embedding("test")
                logger.info("✅ Modelo de embeddings disponible")
            except Exception as e:
                logger.warning(f"⚠️  Modelo de embeddings no disponible: {e}")
                self._download_models_async()
                return
            
            # Verificar modelo LLM
            try:
                llm_service = LLMGeneratorService()
                if llm_service.is_available():
                    logger.info("✅ Modelo LLM disponible")
                else:
                    logger.info("ℹ️  Modelo LLM deshabilitado en configuración")
            except Exception as e:
                logger.warning(f"⚠️  Modelo LLM no disponible: {e}")
                self._download_models_async()
                return
                
            logger.info("🎉 Todos los modelos del chatbot están listos")
            
        except Exception as e:
            logger.error(f"❌ Error verificando modelos: {e}")
            self._download_models_async()
    
    def _download_models_async(self):
        """Descarga los modelos en segundo plano"""
        import threading
        
        def download_worker():
            try:
                logger.info("📥 Descargando modelos del chatbot en segundo plano...")
                logger.info("   Esto puede tomar varios minutos la primera vez...")
                
                # Importar y usar los servicios (esto fuerza la descarga)
                from chatbot.services.semantic_search import SemanticSearchService
                from chatbot.services.llm_generator import LLMGeneratorService
                
                # Descargar modelo de embeddings
                logger.info("📥 Descargando modelo de embeddings (~470 MB)...")
                search_service = SemanticSearchService()
                search_service.generate_embedding("test")
                logger.info("✅ Modelo de embeddings descargado")
                
                # Descargar modelo LLM
                logger.info("📥 Descargando modelo LLM (~308 MB)...")
                llm_service = LLMGeneratorService()
                if llm_service.is_available():
                    logger.info("✅ Modelo LLM descargado")
                
                logger.info("🎉 ¡Descarga de modelos completada!")
                
            except Exception as e:
                logger.error(f"❌ Error descargando modelos: {e}")
                logger.info("💡 Puedes descargarlos manualmente con: python manage.py download_models")
        
        # Ejecutar descarga en hilo separado para no bloquear Django
        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
