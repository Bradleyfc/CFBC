"""
Celery tasks for the course documents application.
"""

import logging
import os
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import CourseDocument, DocumentFolder, DocumentAccess
from .file_service import process_document_file, generate_document_thumbnail
from .indicator_service import generate_folder_indicators

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_uploaded_document(self, document_id):
    """
    Process an uploaded document asynchronously.
    
    Args:
        document_id: ID of the uploaded document
    """
    try:
        document = CourseDocument.objects.select_related('folder').get(id=document_id)
        
        logger.info(f"Processing uploaded document: {document.name} (ID: {document_id})")
        
        # Process the document file (extract metadata, create thumbnails, etc.)
        file_info = process_document_file(document.file.path)
        
        # Update document metadata
        document.file_size = file_info.get('size', 0)
        document.metadata = file_info.get('metadata', {})
        document.processed = True
        document.processing_status = 'completed'
        document.processed_at = timezone.now()
        document.save(update_fields=[
            'file_size', 'metadata', 'processed', 
            'processing_status', 'processed_at'
        ])
        
        # Generate thumbnail if it's an image
        if file_info.get('type') in ['image/jpeg', 'image/png', 'image/gif']:
            generate_document_thumbnail(document)
        
        # Send notification to students in the folder
        if document.folder:
            send_document_notification.delay(document_id)
        
        logger.info(f"Document processing completed: {document.name} (ID: {document_id})")
        return {
            'status': 'success', 
            'document_id': document_id,
            'file_info': file_info,
        }
        
    except CourseDocument.DoesNotExist:
        logger.error(f"Document with ID {document_id} not found")
        return {'status': 'error', 'message': 'Document not found'}
    except Exception as exc:
        logger.error(f"Failed to process document {document_id}: {exc}")
        document.processing_status = 'failed'
        document.save(update_fields=['processing_status'])
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_document_notification(self, document_id):
    """
    Send notification to students when a new document is uploaded.
    
    Args:
        document_id: ID of the uploaded document
    """
    try:
        document = CourseDocument.objects.select_related(
            'folder', 'folder__curso', 'uploaded_by'
        ).get(id=document_id)
        
        if not document.folder:
            logger.info(f"Document {document_id} has no folder, skipping notification")
            return {'status': 'skipped', 'message': 'No folder assigned'}
        
        # Get students with access to the folder
        students = document.folder.students.all()
        
        if not students:
            logger.info(f"No students found for folder {document.folder.id}")
            return {'status': 'skipped', 'message': 'No students in folder'}
        
        emails = [student.email for student in students if student.email]
        
        subject = f'Nuevo documento disponible: {document.name}'
        context = {
            'document': document,
            'folder': document.folder,
            'curso': document.folder.curso,
        }
        
        message = render_to_string('course_documents/emails/new_document.txt', context)
        html_message = render_to_string('course_documents/emails/new_document.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Document notification sent to {len(emails)} students for document {document_id}")
        return {
            'status': 'success', 
            'document_id': document_id,
            'recipients_count': len(emails),
        }
        
    except CourseDocument.DoesNotExist:
        logger.error(f"Document with ID {document_id} not found")
        return {'status': 'error', 'message': 'Document not found'}
    except Exception as exc:
        logger.error(f"Failed to send document notification for document {document_id}: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def generate_folder_report(self, folder_id, report_type='usage'):
    """
    Generate reports for a document folder.
    
    Args:
        folder_id: ID of the folder
        report_type: Type of report ('usage', 'analytics', 'summary')
    """
    try:
        folder = DocumentFolder.objects.select_related('curso').get(id=folder_id)
        
        logger.info(f"Generating {report_type} report for folder: {folder.nombre} (ID: {folder_id})")
        
        if report_type == 'usage':
            report_data = generate_folder_usage_report(folder)
        elif report_type == 'analytics':
            report_data = generate_folder_analytics_report(folder)
        else:
            report_data = generate_folder_summary_report(folder)
        
        # Save report to file or database
        report_file = save_report_to_file(folder, report_type, report_data)
        
        logger.info(f"Report generated for folder {folder_id}: {report_file}")
        return {
            'status': 'success',
            'folder_id': folder_id,
            'report_type': report_type,
            'report_file': report_file,
        }
        
    except DocumentFolder.DoesNotExist:
        logger.error(f"Folder with ID {folder_id} not found")
        return {'status': 'error', 'message': 'Folder not found'}
    except Exception as exc:
        logger.error(f"Failed to generate report for folder {folder_id}: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=180)
def generate_performance_report(self, start_date=None, end_date=None):
    """
    Generate system performance report.
    
    Args:
        start_date: Start date for the report (YYYY-MM-DD)
        end_date: End date for the report (YYYY-MM-DD)
    """
    try:
        from datetime import datetime
        import json
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = timezone.now() - timezone.timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = timezone.now()
        
        # Generate performance statistics
        stats = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'documents': {
                'total_uploaded': CourseDocument.objects.filter(
                    uploaded_at__range=(start_date, end_date)
                ).count(),
                'total_size_mb': CourseDocument.objects.filter(
                    uploaded_at__range=(start_date, end_date)
                ).aggregate(total_size=models.Sum('file_size'))['total_size'] or 0,
                'by_type': list(CourseDocument.objects.filter(
                    uploaded_at__range=(start_date, end_date)
                ).values('metadata__type').annotate(count=models.Count('id'))),
            },
            'access': {
                'total_accesses': DocumentAccess.objects.filter(
                    accessed_at__range=(start_date, end_date)
                ).count(),
                'unique_students': DocumentAccess.objects.filter(
                    accessed_at__range=(start_date, end_date)
                ).values('student').distinct().count(),
                'popular_documents': list(DocumentAccess.objects.filter(
                    accessed_at__range=(start_date, end_date)
                ).values('document__name').annotate(
                    count=models.Count('id')
                ).order_by('-count')[:10]),
            },
            'folders': {
                'total_folders': DocumentFolder.objects.filter(
                    fecha_creacion__range=(start_date, end_date)
                ).count(),
                'documents_per_folder': CourseDocument.objects.filter(
                    uploaded_at__range=(start_date, end_date)
                ).values('folder').annotate(
                    count=models.Count('id')
                ).aggregate(avg=models.Avg('count'))['avg'] or 0,
            }
        }
        
        logger.info(f"Performance report generated for {start_date} to {end_date}")
        return {'status': 'success', 'report': stats}
        
    except Exception as exc:
        logger.error(f"Failed to generate performance report: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def backup_document_metadata(self):
    """
    Create a backup of document metadata.
    This task can be scheduled to run daily.
    """
    try:
        import json
        from datetime import datetime
        import os
        
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'documents')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'documents_backup_{timestamp}.json')
        
        # Export document metadata
        documents_data = list(CourseDocument.objects.all().values(
            'id', 'name', 'description', 'file', 'file_size',
            'uploaded_at', 'uploaded_by_id', 'folder_id',
            'metadata', 'processed', 'processing_status', 'processed_at'
        ))
        
        # Export folder metadata
        folders_data = list(DocumentFolder.objects.all().values(
            'id', 'nombre', 'descripcion', 'fecha_creacion',
            'curso_id', 'curso_academico', 'curso_id_original'
        ))
        
        backup_data = {
            'timestamp': timestamp,
            'documents_count': len(documents_data),
            'folders_count': len(folders_data),
            'documents': documents_data,
            'folders': folders_data,
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Document metadata backup created: {backup_file}")
        return {'status': 'success', 'backup_file': backup_file, 'timestamp': timestamp}
        
    except Exception as exc:
        logger.error(f"Failed to create document metadata backup: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def cleanup_old_documents(self, days_old=365):
    """
    Clean up old document access records and temporary files.
    
    Args:
        days_old: Number of days to keep records (default: 365)
    """
    try:
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Delete old document access records
        deleted_accesses = DocumentAccess.objects.filter(
            accessed_at__lt=cutoff_date
        ).delete()
        
        # Find and delete orphaned temporary files
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                file_time = os.path.getmtime(filepath)
                file_date = timezone.datetime.fromtimestamp(file_time, tz=timezone.utc)
                
                if file_date < cutoff_date:
                    os.remove(filepath)
                    logger.info(f"Deleted old temporary file: {filename}")
        
        logger.info(f"Cleanup completed: {deleted_accesses[0]} access records deleted")
        return {
            'status': 'success',
            'deleted_accesses': deleted_accesses[0],
            'cutoff_date': cutoff_date.isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"Failed to cleanup old documents: {exc}")
        self.retry(exc=exc)


# Helper functions
def generate_folder_usage_report(folder):
    """Generate usage report for a folder."""
    from django.db.models import Count, Sum, Avg
    from django.utils import timezone
    
    now = timezone.now()
    last_30_days = now - timezone.timedelta(days=30)
    
    return {
        'folder': {
            'id': folder.id,
            'nombre': folder.nombre,
            'curso': str(folder.curso) if folder.curso else None,
        },
        'documents': {
            'total': folder.documents.count(),
            'total_size_mb': folder.documents.aggregate(
                total_size=Sum('file_size')
            )['total_size'] or 0,
            'by_type': list(folder.documents.values(
                'metadata__type'
            ).annotate(count=Count('id'))),
        },
        'access': {
            'total_last_30_days': DocumentAccess.objects.filter(
                document__folder=folder,
                accessed_at__gte=last_30_days
            ).count(),
            'unique_students_last_30_days': DocumentAccess.objects.filter(
                document__folder=folder,
                accessed_at__gte=last_30_days
            ).values('student').distinct().count(),
            'most_accessed': list(DocumentAccess.objects.filter(
                document__folder=folder
            ).values(
                'document__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:5]),
        },
        'indicators': generate_folder_indicators(folder),
    }


def generate_folder_analytics_report(folder):
    """Generate analytics report for a folder."""
    from django.db.models import Count, DateField
    from django.db.models.functions import TruncDate
    
    # Get daily access statistics for the last 30 days
    daily_access = DocumentAccess.objects.filter(
        document__folder=folder,
        accessed_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).annotate(
        date=TruncDate('accessed_at', output_field=DateField())
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    return {
        'folder': {
            'id': folder.id,
            'nombre': folder.nombre,
        },
        'daily_access': list(daily_access),
        'student_engagement': {
            'total_students': folder.students.count(),
            'active_students': DocumentAccess.objects.filter(
                document__folder=folder,
                accessed_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).values('student').distinct().count(),
        },
    }


def generate_folder_summary_report(folder):
    """Generate summary report for a folder."""
    return {
        'folder': {
            'id': folder.id,
            'nombre': folder.nombre,
            'descripcion': folder.descripcion,
            'fecha_creacion': folder.fecha_creacion,
            'curso': str(folder.curso) if folder.curso else None,
        },
        'summary': {
            'documents_count': folder.documents.count(),
            'students_count': folder.students.count(),
            'total_downloads': DocumentAccess.objects.filter(
                document__folder=folder
            ).count(),
            'last_updated': folder.documents.order_by('-uploaded_at').first().uploaded_at if folder.documents.exists() else None,
        },
    }


def save_report_to_file(folder, report_type, report_data):
    """Save report data to a JSON file."""
    import json
    from datetime import datetime
    
    reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"report_{report_type}_{folder.id}_{timestamp}.json"
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    return filepath