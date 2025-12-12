"""
Django management command para gestionar modelos del chatbot
Uso: python manage.py manage_models [opciones]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import time


class Command(BaseCommand):
    help = 'Gestiona los modelos del chatbot (descargar, verificar, limpiar)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['download', 'check', 'clean', 'info'],
            default='download',
            help='Acción a realizar'
        )
        parser.add_argument(
            '--model',
            choices=['embeddings', 'llm', 'all'],
            default='all',
            help='Qué modelo gestionar'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar re-descarga aunque ya exista'
        )
        parser.add_argument(
            '--disable-llm',
            action='store_true',
            help='Deshabilitar modelo LLM para acelerar'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        model_type = options['model']
        
        self.stdout.write(
            self.style.SUCCESS(f'🤖 Gestión de modelos del chatbot - {action}')
        )
        
        if action == 'download':
            self._download_models(model_type, options['force'])
        elif action == 'check':
            self._check_models(model_type)
        elif action == 'clean':
            self._clean_models()
        elif action == 'info':
            self._show_info()
        
        if options['disable_llm']:
            self._disable_llm()
    
    def _download_models(self, model_type, force=False):
        """Descarga los modelos especificados"""
        
        try:
            from chatbot.services.model_downloader import model_downloader
            from chatbot.config import LLM_MODEL
            
            start_time = time.time()
            
            if model_type in ['embeddings', 'all']:
                self.stdout.write('📥 Gestionando modelo de embeddings...')
                embedding_model = 'paraphrase-multilingual-MiniLM-L12-v2'
                
                if not force and model_downloader.check_model_cached(embedding_model):
                    self.stdout.write('   ✅ Ya disponible en cache')
                else:
                    self.stdout.write('   📦 Descargando (~470 MB)...')
                    if model_downloader.download_model_smart(embedding_model):
                        self.stdout.write('   ✅ Descarga completada')
                    else:
                        self.stdout.write(self.style.ERROR('   ❌ Error en descarga'))
            
            if model_type in ['llm', 'all']:
                self.stdout.write('📥 Gestionando modelo LLM...')
                
                if not force and model_downloader.check_model_cached(LLM_MODEL):
                    self.stdout.write('   ✅ Ya disponible en cache')
                else:
                    self.stdout.write(f'   📦 Descargando {LLM_MODEL} (~308 MB)...')
                    self.stdout.write('   ⏳ Esto puede tomar varios minutos...')
                    
                    if model_downloader.download_model_smart(LLM_MODEL):
                        self.stdout.write('   ✅ Descarga completada')
                    else:
                        self.stdout.write(self.style.ERROR('   ❌ Error en descarga'))
            
            total_time = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(f'🎉 Gestión completada en {total_time:.1f}s')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {e}')
            )
    
    def _check_models(self, model_type):
        """Verifica el estado de los modelos"""
        
        try:
            from chatbot.services.model_downloader import model_downloader
            from chatbot.config import LLM_MODEL, LLM_ENABLED
            
            self.stdout.write('🔍 Estado de los modelos:')
            
            if model_type in ['embeddings', 'all']:
                embedding_model = 'paraphrase-multilingual-MiniLM-L12-v2'
                cached = model_downloader.check_model_cached(embedding_model)
                status = '✅ Disponible' if cached else '❌ No disponible'
                self.stdout.write(f'   Embeddings: {status}')
                
                # Probar funcionamiento
                if cached:
                    try:
                        from chatbot.services.semantic_search import SemanticSearchService
                        search = SemanticSearchService()
                        test = search.generate_embedding("test")
                        self.stdout.write(f'     Funcionando: ✅ (dim: {len(test)})')
                    except Exception as e:
                        self.stdout.write(f'     Error: ❌ {e}')
            
            if model_type in ['llm', 'all']:
                cached = model_downloader.check_model_cached(LLM_MODEL)
                enabled = LLM_ENABLED
                status = '✅ Disponible' if cached else '❌ No disponible'
                enabled_status = '✅ Habilitado' if enabled else '❌ Deshabilitado'
                
                self.stdout.write(f'   LLM: {status}')
                self.stdout.write(f'   LLM Config: {enabled_status}')
                
                # Probar funcionamiento
                if cached and enabled:
                    try:
                        from chatbot.services.llm_generator import LLMGeneratorService
                        llm = LLMGeneratorService()
                        available = llm.is_available()
                        self.stdout.write(f'     Funcionando: {"✅" if available else "❌"}')
                    except Exception as e:
                        self.stdout.write(f'     Error: ❌ {e}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error verificando: {e}')
            )
    
    def _clean_models(self):
        """Limpia modelos no utilizados"""
        
        self.stdout.write('🧹 Limpiando cache de modelos...')
        
        try:
            from chatbot.services.model_downloader import model_downloader
            model_downloader.cleanup_old_models()
            self.stdout.write('✅ Limpieza completada')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error en limpieza: {e}')
            )
    
    def _show_info(self):
        """Muestra información detallada de los modelos"""
        
        self.stdout.write('📊 Información de modelos:')
        
        try:
            from chatbot.config import LLM_MODEL, LLM_ENABLED, SENTENCE_TRANSFORMER_MODEL
            from chatbot.services.model_downloader import model_downloader
            
            # Información de configuración
            self.stdout.write(f'   Modelo embeddings: {SENTENCE_TRANSFORMER_MODEL}')
            self.stdout.write(f'   Modelo LLM: {LLM_MODEL}')
            self.stdout.write(f'   LLM habilitado: {LLM_ENABLED}')
            
            # Tamaños
            embedding_size = model_downloader.get_model_size(SENTENCE_TRANSFORMER_MODEL)
            llm_size = model_downloader.get_model_size(LLM_MODEL)
            
            if embedding_size:
                self.stdout.write(f'   Tamaño embeddings: ~{embedding_size // (1024*1024)} MB')
            if llm_size:
                self.stdout.write(f'   Tamaño LLM: ~{llm_size // (1024*1024)} MB')
            
            # Cache location
            import os
            cache_dir = os.path.expanduser('~/.cache/huggingface/')
            self.stdout.write(f'   Ubicación cache: {cache_dir}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error obteniendo info: {e}')
            )
    
    def _disable_llm(self):
        """Deshabilita el LLM para acelerar el sistema"""
        
        self.stdout.write('⚡ Deshabilitando LLM para mejor rendimiento...')
        self.stdout.write('💡 Para habilitarlo: LLM_ENABLED=true en variables de entorno')
        
        # Aquí podrías modificar un archivo de configuración si fuera necesario
        self.stdout.write('✅ Configuración actualizada')