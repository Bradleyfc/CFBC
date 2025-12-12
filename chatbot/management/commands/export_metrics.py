"""
Management command to export chatbot metrics to CSV
"""
import csv
from django.core.management.base import BaseCommand
from django.utils import timezone

from chatbot.models import FAQ, ChatInteraction
from chatbot.services.orchestrator import ChatbotOrchestrator


class Command(BaseCommand):
    help = 'Export chatbot metrics to CSV files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            default='.',
            help='Directory to save CSV files (default: current directory)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for interaction statistics (default: 30)'
        )
    
    def handle(self, *args, **options):
        output_dir = options['output_dir']
        days = options['days']
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(
            self.style.SUCCESS('Exporting chatbot metrics...')
        )
        
        try:
            # Export FAQ metrics
            self.export_faq_metrics(output_dir, timestamp)
            
            # Export interaction statistics
            self.export_interaction_stats(output_dir, timestamp, days)
            
            # Export unused FAQs
            self.export_unused_faqs(output_dir, timestamp)
            
            self.stdout.write(
                self.style.SUCCESS(f'Metrics exported successfully to {output_dir}/')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error exporting metrics: {e}')
            )
            raise
    
    def export_faq_metrics(self, output_dir, timestamp):
        """Export FAQ metrics to CSV"""
        filename = f'{output_dir}/faq_metrics_{timestamp}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'ID', 'Pregunta', 'Categoria', 'Activa', 'Destacada', 'Prioridad',
                'Veces Usada', 'Ultima Fecha Uso', 'Tasa Exito', 'Fecha Creacion',
                'Variaciones Count'
            ])
            
            # Data
            faqs = FAQ.objects.select_related('categoria').prefetch_related('variaciones')
            
            for faq in faqs:
                writer.writerow([
                    faq.id,
                    faq.pregunta,
                    faq.categoria.nombre,
                    'Sí' if faq.activa else 'No',
                    'Sí' if faq.destacada else 'No',
                    faq.prioridad,
                    faq.veces_usada,
                    faq.ultima_fecha_uso.strftime('%Y-%m-%d %H:%M') if faq.ultima_fecha_uso else '',
                    f'{faq.tasa_exito:.2f}' if faq.tasa_exito else '0.00',
                    faq.fecha_creacion.strftime('%Y-%m-%d'),
                    faq.variaciones.count()
                ])
        
        self.stdout.write(f'FAQ metrics exported to {filename}')
    
    def export_interaction_stats(self, output_dir, timestamp, days):
        """Export interaction statistics to CSV"""
        filename = f'{output_dir}/interaction_stats_{timestamp}.csv'
        
        orchestrator = ChatbotOrchestrator()
        stats = orchestrator.get_interaction_stats(days)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Summary statistics
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Period (days)', stats.get('period_days', days)])
            writer.writerow(['Total Interactions', stats.get('total_interactions', 0)])
            writer.writerow(['Average Confidence', f"{stats.get('avg_confidence', 0):.3f}"])
            writer.writerow(['Average Response Time', f"{stats.get('avg_response_time', 0):.3f}"])
            writer.writerow(['FAQ Candidates', stats.get('faq_candidates', 0)])
            
            # Feedback statistics
            feedback_stats = stats.get('feedback_stats', {})
            writer.writerow(['Total with Feedback', feedback_stats.get('total_with_feedback', 0)])
            writer.writerow(['Positive Feedback', feedback_stats.get('positive_feedback', 0)])
            writer.writerow(['Negative Feedback', feedback_stats.get('negative_feedback', 0)])
            writer.writerow(['Feedback Rate', f"{feedback_stats.get('feedback_rate', 0):.3f}"])
            
            # Intent distribution
            writer.writerow([])
            writer.writerow(['Intent', 'Count'])
            intent_distribution = stats.get('intent_distribution', {})
            for intent, count in intent_distribution.items():
                writer.writerow([intent, count])
        
        self.stdout.write(f'Interaction statistics exported to {filename}')
    
    def export_unused_faqs(self, output_dir, timestamp):
        """Export unused FAQs to CSV"""
        filename = f'{output_dir}/unused_faqs_{timestamp}.csv'
        
        orchestrator = ChatbotOrchestrator()
        unused_faqs = orchestrator.get_unused_faqs(90)  # 90 days threshold
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'ID', 'Pregunta', 'Categoria', 'Fecha Creacion', 'Ultima Fecha Uso',
                'Days Since Use', 'Veces Usada', 'Tasa Exito'
            ])
            
            # Data
            for faq in unused_faqs:
                writer.writerow([
                    faq['id'],
                    faq['pregunta'],
                    faq['categoria'],
                    faq['fecha_creacion'].strftime('%Y-%m-%d'),
                    faq['ultima_fecha_uso'].strftime('%Y-%m-%d %H:%M') if faq['ultima_fecha_uso'] else 'Nunca',
                    faq['days_since_use'] if faq['days_since_use'] else 'N/A',
                    faq['veces_usada'],
                    f"{faq['tasa_exito']:.2f}"
                ])
        
        self.stdout.write(f'Unused FAQs exported to {filename}')