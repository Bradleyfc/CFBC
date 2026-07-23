"""
Celery tasks for the blog application.
"""

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Noticia, Comentario
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id):
    """
    Send welcome email to new users.
    
    Args:
        user_id: ID of the user to send welcome email to
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = 'Bienvenido/a al Centro Fray Bartolome de las Casas'
        message = render_to_string('blog/emails/welcome_email.txt', {
            'user': user,
        })
        html_message = render_to_string('blog/emails/welcome_email.html', {
            'user': user,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to user {user.email}")
        return {'status': 'success', 'user_id': user_id, 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'status': 'error', 'message': 'User not found'}
    except Exception as exc:
        logger.error(f"Failed to send welcome email to user {user_id}: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_comment_notification(self, comment_id):
    """
    Send notification email when a new comment is posted.
    
    Args:
        comment_id: ID of the comment that was posted
    """
    try:
        comment = Comentario.objects.select_related('noticia', 'autor').get(id=comment_id)
        noticia = comment.noticia
        
        # Get the author of the news article
        noticia_author = noticia.autor
        
        subject = f'Nuevo comentario en tu noticia: {noticia.titulo}'
        message = render_to_string('blog/emails/comment_notification.txt', {
            'comment': comment,
            'noticia': noticia,
        })
        html_message = render_to_string('blog/emails/comment_notification.html', {
            'comment': comment,
            'noticia': noticia,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[noticia_author.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Comment notification sent to {noticia_author.email} for comment {comment_id}")
        return {'status': 'success', 'comment_id': comment_id, 'recipient': noticia_author.email}
        
    except Comentario.DoesNotExist:
        logger.error(f"Comment with ID {comment_id} not found")
        return {'status': 'error', 'message': 'Comment not found'}
    except Exception as exc:
        logger.error(f"Failed to send comment notification for comment {comment_id}: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def send_comment_reply_notification(self, comment_id, reply_comment_id):
    """
    Send notification email when someone replies to a comment.
    
    Args:
        comment_id: ID of the parent comment
        reply_comment_id: ID of the reply comment
    """
    try:
        parent_comment = Comentario.objects.select_related('autor').get(id=comment_id)
        reply_comment = Comentario.objects.select_related('autor', 'noticia').get(id=reply_comment_id)
        
        subject = f'Alguien respondió a tu comentario en: {reply_comment.noticia.titulo}'
        message = render_to_string('blog/emails/comment_reply_notification.txt', {
            'parent_comment': parent_comment,
            'reply_comment': reply_comment,
        })
        html_message = render_to_string('blog/emails/comment_reply_notification.html', {
            'parent_comment': parent_comment,
            'reply_comment': reply_comment,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_comment.autor.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Comment reply notification sent to {parent_comment.autor.email}")
        return {'status': 'success', 'parent_comment_id': comment_id, 'reply_comment_id': reply_comment_id}
        
    except Comentario.DoesNotExist:
        logger.error(f"Comment not found: parent={comment_id}, reply={reply_comment_id}")
        return {'status': 'error', 'message': 'Comment not found'}
    except Exception as exc:
        logger.error(f"Failed to send comment reply notification: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=180)
def generate_blog_statistics_report(self, start_date=None, end_date=None):
    """
    Generate blog statistics report for a given date range.
    
    Args:
        start_date: Start date for the report (YYYY-MM-DD)
        end_date: End date for the report (YYYY-MM-DD)
    """
    try:
        from datetime import datetime
        import json
        from django.db.models import Count, Avg
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = timezone.now() - timezone.timedelta(days=30)
            
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = timezone.now()
        
        # Generate statistics
        stats = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'noticias': {
                'total': Noticia.objects.filter(
                    fecha_creacion__range=(start_date, end_date)
                ).count(),
                'by_status': list(Noticia.objects.filter(
                    fecha_creacion__range=(start_date, end_date)
                ).values('estado').annotate(count=Count('id'))),
                'by_category': list(Noticia.objects.filter(
                    fecha_creacion__range=(start_date, end_date)
                ).values('categoria__nombre').annotate(count=Count('id'))),
            },
            'comentarios': {
                'total': Comentario.objects.filter(
                    fecha_creacion__range=(start_date, end_date)
                ).count(),
                'avg_per_noticia': Comentario.objects.filter(
                    fecha_creacion__range=(start_date, end_date)
                ).values('noticia').annotate(count=Count('id')).aggregate(
                    avg=Avg('count')
                )['avg'] or 0,
                'by_author': list(Comentario.objects.filter(
                    fecha_creacion__range=(start_date, end_date)
                ).values('autor__username').annotate(count=Count('id')).order_by('-count')[:10]),
            }
        }
        
        logger.info(f"Blog statistics report generated for {start_date} to {end_date}")
        return {'status': 'success', 'report': stats}
        
    except Exception as exc:
        logger.error(f"Failed to generate blog statistics report: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def backup_blog_data(self):
    """
    Create a backup of blog data (noticias, comentarios, etc.).
    This task can be scheduled to run daily or weekly.
    """
    try:
        import json
        from datetime import datetime
        import os
        
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'blog')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'blog_backup_{timestamp}.json')
        
        # Export noticias
        noticias_data = list(Noticia.objects.all().values(
            'id', 'titulo', 'resumen', 'contenido', 'estado', 'visibilidad',
            'destacada', 'fecha_creacion', 'fecha_publicacion', 'categoria_id',
            'autor_id', 'notas_editor', 'permitir_comentarios'
        ))
        
        # Export comentarios
        comentarios_data = list(Comentario.objects.all().values(
            'id', 'contenido', 'fecha_creacion', 'noticia_id', 'autor_id',
            'activo', 'nota_moderacion', 'fijado'
        ))
        
        backup_data = {
            'timestamp': timestamp,
            'noticias_count': len(noticias_data),
            'comentarios_count': len(comentarios_data),
            'noticias': noticias_data,
            'comentarios': comentarios_data,
        }
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Blog data backup created: {backup_file}")
        return {'status': 'success', 'backup_file': backup_file, 'timestamp': timestamp}
        
    except Exception as exc:
        logger.error(f"Failed to create blog data backup: {exc}")
        self.retry(exc=exc)