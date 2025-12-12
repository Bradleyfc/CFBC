"""
Management command to rebuild the chatbot search index
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from chatbot.services.content_indexer import ContentIndexer


class Command(BaseCommand):
    help = 'Rebuild the chatbot search index from all content'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--content-type',
            choices=['faqs', 'cursos', 'noticias', 'all'],
            default='all',
            help='Type of content to index (default: all)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information'
        )
    
    def handle(self, *args, **options):
        start_time = timezone.now()
        
        self.stdout.write(
            self.style.SUCCESS('Starting chatbot index rebuild...')
        )
        
        indexer = ContentIndexer()
        
        try:
            content_type = options['content_type']
            
            if content_type == 'all':
                results = indexer.index_all()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully indexed:\n'
                        f'  - FAQs: {results["faqs"]} documents\n'
                        f'  - Cursos: {results["cursos"]} documents\n'
                        f'  - Noticias: {results["noticias"]} documents\n'
                        f'  - Total: {sum(results.values())} documents'
                    )
                )
            
            elif content_type == 'faqs':
                count = indexer.index_faqs()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully indexed {count} FAQ documents')
                )
            
            elif content_type == 'cursos':
                count = indexer.index_cursos()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully indexed {count} Curso documents')
                )
            
            elif content_type == 'noticias':
                count = indexer.index_noticias()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully indexed {count} Noticia documents')
                )
            
            # Show timing
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            self.stdout.write(
                self.style.SUCCESS(f'Index rebuild completed in {duration:.2f} seconds')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error rebuilding index: {e}')
            )
            raise