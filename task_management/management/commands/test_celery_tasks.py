"""
Django management command to test Celery task execution.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from blog.tasks import send_welcome_email, generate_blog_statistics_report, backup_blog_data
from course_documents.tasks import generate_performance_report, backup_document_metadata
import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Test Celery task execution'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-type',
            type=str,
            choices=['email', 'report', 'backup', 'all'],
            default='all',
            help='Type of tasks to test'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID for email task testing'
        )

    def handle(self, *args, **options):
        task_type = options['task_type']
        user_id = options['user_id']
        
        self.stdout.write(self.style.SUCCESS('Starting Celery task tests...'))
        
        if task_type in ['email', 'all']:
            self.test_email_tasks(user_id)
        
        if task_type in ['report', 'all']:
            self.test_report_tasks()
        
        if task_type in ['backup', 'all']:
            self.test_backup_tasks()
        
        self.stdout.write(self.style.SUCCESS('Celery task tests completed!'))

    def test_email_tasks(self, user_id=None):
        """Test email-related tasks."""
        self.stdout.write(self.style.MIGRATE_HEADING('Testing email tasks...'))
        
        if not user_id:
            # Get a test user
            user = User.objects.filter(is_active=True).first()
            if user:
                user_id = user.id
            else:
                self.stdout.write(self.style.WARNING('No active users found for email testing'))
                return
        
        try:
            # Test welcome email task
            self.stdout.write('Testing send_welcome_email task...')
            result = send_welcome_email.delay(user_id)
            
            # Wait for task completion
            self.wait_for_task(result, timeout=30)
            
            if result.successful():
                self.stdout.write(self.style.SUCCESS('✓ send_welcome_email task completed successfully'))
                self.stdout.write(f'Result: {result.result}')
            else:
                self.stdout.write(self.style.ERROR('✗ send_welcome_email task failed'))
                if result.result:
                    self.stdout.write(f'Error: {result.result}')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing email tasks: {e}'))

    def test_report_tasks(self):
        """Test report generation tasks."""
        self.stdout.write(self.style.MIGRATE_HEADING('Testing report tasks...'))
        
        try:
            # Test blog statistics report
            self.stdout.write('Testing generate_blog_statistics_report task...')
            result = generate_blog_statistics_report.delay()
            
            # Wait for task completion
            self.wait_for_task(result, timeout=60)
            
            if result.successful():
                self.stdout.write(self.style.SUCCESS('✓ generate_blog_statistics_report task completed successfully'))
                report = result.result.get('report', {})
                self.stdout.write(f'Report generated: {report.get("noticias", {}).get("total", 0)} noticias analyzed')
            else:
                self.stdout.write(self.style.ERROR('✗ generate_blog_statistics_report task failed'))
            
            # Test performance report
            self.stdout.write('Testing generate_performance_report task...')
            result = generate_performance_report.delay()
            
            # Wait for task completion
            self.wait_for_task(result, timeout=60)
            
            if result.successful():
                self.stdout.write(self.style.SUCCESS('✓ generate_performance_report task completed successfully'))
                report = result.result.get('report', {})
                self.stdout.write(f'Performance report generated for period: {report.get("period", {}).get("start")} to {report.get("period", {}).get("end")}')
            else:
                self.stdout.write(self.style.ERROR('✗ generate_performance_report task failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing report tasks: {e}'))

    def test_backup_tasks(self):
        """Test backup tasks."""
        self.stdout.write(self.style.MIGRATE_HEADING('Testing backup tasks...'))
        
        try:
            # Test blog backup
            self.stdout.write('Testing backup_blog_data task...')
            result = backup_blog_data.delay()
            
            # Wait for task completion
            self.wait_for_task(result, timeout=120)
            
            if result.successful():
                self.stdout.write(self.style.SUCCESS('✓ backup_blog_data task completed successfully'))
                self.stdout.write(f'Backup file: {result.result.get("backup_file", "N/A")}')
            else:
                self.stdout.write(self.style.ERROR('✗ backup_blog_data task failed'))
            
            # Test document metadata backup
            self.stdout.write('Testing backup_document_metadata task...')
            result = backup_document_metadata.delay()
            
            # Wait for task completion
            self.wait_for_task(result, timeout=120)
            
            if result.successful():
                self.stdout.write(self.style.SUCCESS('✓ backup_document_metadata task completed successfully'))
                self.stdout.write(f'Backup file: {result.result.get("backup_file", "N/A")}')
            else:
                self.stdout.write(self.style.ERROR('✗ backup_document_metadata task failed'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error testing backup tasks: {e}'))

    def wait_for_task(self, async_result, timeout=30):
        """Wait for a Celery task to complete."""
        self.stdout.write(f'Waiting for task {async_result.id} to complete (timeout: {timeout}s)...')
        
        start_time = time.time()
        while not async_result.ready() and (time.time() - start_time) < timeout:
            time.sleep(1)
            self.stdout.write('.', ending='')
            self.stdout.flush()
        
        self.stdout.write('')  # New line
        
        if not async_result.ready():
            self.stdout.write(self.style.WARNING(f'Task {async_result.id} timed out after {timeout} seconds'))