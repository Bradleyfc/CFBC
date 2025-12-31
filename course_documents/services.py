from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from principal.models import Matriculas
from .models import NewContentNotification


class NotificationService:
    """Servicio para manejo de notificaciones de documentos"""
    
    @classmethod
    def notify_new_document(cls, document):
        """Notifica a los estudiantes sobre un nuevo documento"""
        curso = document.folder.curso
        
        # Obtener estudiantes inscritos en el curso
        matriculas = Matriculas.objects.filter(course=curso, activo=True)
        
        for matricula in matriculas:
            # Crear o actualizar notificación
            notification, created = NewContentNotification.objects.get_or_create(
                curso=curso,
                student=matricula.student,
                defaults={'has_new_content': True}
            )
            
            if not created:
                notification.has_new_content = True
                notification.save()
            
            # Enviar email si está configurado
            if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                cls._send_email_notification(matricula.student, document)
    
    @classmethod
    def _send_email_notification(cls, student, document):
        """Envía notificación por email"""
        try:
            subject = f'Nuevo documento disponible en {document.folder.curso.name}'
            
            # Renderizar template HTML
            html_message = render_to_string('course_documents/emails/new_document.html', {
                'student': student,
                'document': document,
                'curso': document.folder.curso,
                'folder': document.folder
            })
            
            # Versión texto plano
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            print(f"Error enviando email a {student.email}: {e}")
    
    @classmethod
    def update_content_indicators(cls, curso):
        """Actualiza los indicadores de contenido nuevo para un curso"""
        # Obtener estudiantes inscritos
        matriculas = Matriculas.objects.filter(course=curso, activo=True)
        
        for matricula in matriculas:
            # Crear notificación si no existe
            notification, created = NewContentNotification.objects.get_or_create(
                curso=curso,
                student=matricula.student,
                defaults={'has_new_content': True}
            )
            
            if not created and not notification.has_new_content:
                notification.has_new_content = True
                notification.save()
    
    @classmethod
    def mark_content_as_seen(cls, curso, student):
        """Marca el contenido como visto por un estudiante"""
        try:
            notification = NewContentNotification.objects.get(
                curso=curso,
                student=student
            )
            notification.mark_as_seen()
            return True
        except NewContentNotification.DoesNotExist:
            return False