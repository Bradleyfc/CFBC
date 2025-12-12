"""
Django management command para descargar modelos del chatbot
Uso: python manage.py download_models
"""

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Descarga todos los modelos necesarios para el chatbot'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar re-descarga de modelos aunque ya existan'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada del proceso'
        )
    
    def handle(self, *args, **options):
        start_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS('🤖 Iniciando descarga de modelos del chatbot...')
        )
        
        try:
            # Importar servicios
            from chatbot.services.semantic_search import SemanticSearchService
            from chatbot.services.llm_generator import LLMGeneratorService
            
            # 1. Descargar modelo de embeddings
            self.stdout.write('📥 Descargando modelo de embeddings semánticos...')
            if options['verbose']:
                self.stdout.write('   Modelo: paraphrase-multilingual-MiniLM-L12-v2')
                self.stdout.write('   Tamaño: ~470 MB')
            
            search_service = SemanticSearchService()
            self.stdout.write(
                self.style.SUCCESS('   ✅ Modelo de embeddings listo')
            )
            
            # 2. Descargar modelo LLM
            self.stdout.write('📥 Descargando modelo LLM...')
            if options['verbose']:
                self.stdout.write('   Modelo: google/flan-t5-small')
                self.stdout.write('   Tamaño: ~308 MB')
            
            llm_service = LLMGeneratorService()
            self.stdout.write(
                self.style.SUCCESS('   ✅ Modelo LLM listo')
            )
            
            # 3. Verificar funcionamiento
            self.stdout.write('🔍 Verificando modelos...')
            
            # Probar embeddings
            test_embedding = search_service.generate_embedding("test")
            if options['verbose']:
                self.stdout.write(f'   Dimensión embeddings: {len(test_embedding)}')
            
            # Probar LLM
            if llm_service.is_available():
                self.stdout.write('   ✅ LLM verificado')
            else:
                self.stdout.write(
                    self.style.WARNING('   ⚠️  LLM no disponible')
                )
            
            # Tiempo total
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Modelos descargados exitosamente en {duration:.1f} segundos'
                )
            )
            
            if options['verbose']:
                self.stdout.write('\n📍 Información adicional:')
                self.stdout.write('   Cache: ~/.cache/huggingface/')
                self.stdout.write('   Espacio total: ~800 MB')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error descargando modelos: {e}')
            )
            self.stdout.write('\n🔧 Soluciones:')
            self.stdout.write('   1. Verificar conexión a internet')
            self.stdout.write('   2. Verificar dependencias instaladas')
            self.stdout.write('   3. Verificar espacio en disco')
            raise