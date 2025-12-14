from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
import logging

from principal.models import Matriculas
from .models import CourseDocument, NewContentNotification, AuditLog
from .indicator_service import ContentIndicatorService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio para envío de notificaciones por email y gestión de indicadores
    """
    
    @staticmethod
    def notify_new_document(document: CourseDocument):
        """
        Envía notificación a estudiantes inscritos cuando se sube un documento
        
        Args:
            document: El documento que fue subido
        """
        try:
            curso = document.folder.curso
            
            # Obtener estudiantes inscritos en el curso
            enrolled_students = Matriculas.objects.filter(
                course=curso,
                activo=True
            ).select_related('student')
            
            if not enrolled_students.exists():
                logger.info(f"No hay estudiantes inscritos en el curso {curso.name}")
                return
            
            # Preparar datos para el email
            email_context = {
                'curso': curso,
                'folder': document.folder,
                'document': document,
                'teacher': document.uploaded_by,
                'upload_date': document.uploaded_at,
                'dashboard_url': NotificationService._get_dashboard_url(curso.id),
                'site_name': getattr(settings, 'SITE_NAME', 'Sistema de Cursos'),
            }
            
            # Renderizar templates de email
            subject = f"Nuevo documento disponible en {curso.name}"
            text_content = render_to_string(
                'course_documents/emails/new_document.txt', 
                email_context
            )
            html_content = render_to_string(
                'course_documents/emails/new_document.html', 
                email_context
            )
            
            # Enviar emails individuales
            successful_sends = 0
            failed_sends = 0
            
            for matricula in enrolled_students:
                student = matricula.student
                
                try:
                    # Personalizar contexto para cada estudiante
                    personal_context = email_context.copy()
                    personal_context['student'] = student
                    personal_context['student_name'] = student.get_full_name() or student.username
                    
                    # Renderizar contenido personalizado
                    personal_text = render_to_string(
                        'course_documents/emails/new_document.txt', 
                        personal_context
                    )
                    personal_html = render_to_string(
                        'course_documents/emails/new_document.html', 
                        personal_context
                    )
                    
                    # Crear y enviar email
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=personal_text,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[student.email]
                    )
                    email.attach_alternative(personal_html, "text/html")
                    email.send()
                    
                    successful_sends += 1
                    
                    # Registrar envío exitoso
                    AuditLog.log_action(
                        user=student,
                        action='email_sent',
                        curso=curso,
                        folder=document.folder,
                        document=document,
                        details=f'Email de notificación enviado a {student.email}'
                    )
                    
                except Exception as e:
                    failed_sends += 1
                    logger.error(f"Error enviando email a {student.email}: {str(e)}")
                    
                    # Registrar error de envío
                    AuditLog.log_action(
                        user=student,
                        action='email_error',
                        curso=curso,
                        folder=document.folder,
                        document=document,
                        details=f'Error enviando email a {student.email}: {str(e)}'
                    )
            
            # Log resumen
            logger.info(
                f"Notificaciones enviadas para documento '{document.name}' en curso '{curso.name}': "
                f"{successful_sends} exitosos, {failed_sends} fallidos"
            )
            
            # Registrar resumen en audit log
            AuditLog.log_action(
                user=document.uploaded_by,
                action='notification_batch_sent',
                curso=curso,
                folder=document.folder,
                document=document,
                details=f'Lote de notificaciones enviado: {successful_sends} exitosos, {failed_sends} fallidos'
            )
            
        except Exception as e:
            logger.error(f"Error en notify_new_document: {str(e)}")
            
            # Registrar error general
            AuditLog.log_action(
                user=document.uploaded_by,
                action='notification_error',
                curso=document.folder.curso,
                folder=document.folder,
                document=document,
                details=f'Error general en notificaciones: {str(e)}'
            )
    
    @staticmethod
    def update_content_indicators(curso):
        """
        Actualiza indicadores de contenido nuevo para estudiantes del curso
        
        Args:
            curso: El curso para el cual actualizar indicadores
        """
        try:
            # Usar el servicio de indicadores para activar indicadores
            activated_count = ContentIndicatorService.activate_indicators_for_course(curso)
            
            logger.info(f"Indicadores de contenido actualizados para curso '{curso.name}': {activated_count} activados")
            
        except Exception as e:
            logger.error(f"Error actualizando indicadores para curso {curso.name}: {str(e)}")
    
    @staticmethod
    def _get_dashboard_url(curso_id):
        """
        Genera URL completa para el dashboard del estudiante
        
        Args:
            curso_id: ID del curso
            
        Returns:
            URL completa del dashboard
        """
        try:
            # Generar URL relativa
            relative_url = reverse('course_documents:student_dashboard', kwargs={'curso_id': curso_id})
            
            # Obtener dominio base
            base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
            
            # Combinar para URL completa
            full_url = f"{base_url.rstrip('/')}{relative_url}"
            
            return full_url
            
        except Exception as e:
            logger.error(f"Error generando URL del dashboard: {str(e)}")
            return "#"
    
    @staticmethod
    def send_test_notification(user_email, curso_name):
        """
        Envía una notificación de prueba (para testing)
        
        Args:
            user_email: Email del destinatario
            curso_name: Nombre del curso
        """
        try:
            subject = f"Notificación de prueba - {curso_name}"
            message = f"Esta es una notificación de prueba para el curso {curso_name}"
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )
            
            logger.info(f"Notificación de prueba enviada a {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación de prueba: {str(e)}")
            return False
    
    @staticmethod
    def retry_failed_notifications():
        """
        Reintenta envío de notificaciones fallidas (para uso con tareas programadas)
        """
        try:
            # Buscar logs de errores de email recientes (últimas 24 horas)
            from datetime import timedelta
            
            recent_errors = AuditLog.objects.filter(
                action='email_error',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).select_related('document', 'curso', 'user')
            
            retry_count = 0
            
            for error_log in recent_errors:
                if error_log.document and error_log.user:
                    try:
                        # Reintentar notificación
                        NotificationService.notify_new_document(error_log.document)
                        retry_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error en reintento de notificación: {str(e)}")
            
            logger.info(f"Reintentadas {retry_count} notificaciones fallidas")
            return retry_count
            
        except Exception as e:
            logger.error(f"Error en retry_failed_notifications: {str(e)}")
            return 0


class EmailTemplateService:
    """
    Servicio para gestión de templates de email
    """
    
    @staticmethod
    def get_email_context(document: CourseDocument, student=None):
        """
        Genera contexto base para templates de email
        
        Args:
            document: Documento para el cual generar contexto
            student: Estudiante específico (opcional)
            
        Returns:
            Diccionario con contexto para templates
        """
        curso = document.folder.curso
        
        context = {
            'document': document,
            'folder': document.folder,
            'curso': curso,
            'teacher': document.uploaded_by,
            'teacher_name': document.uploaded_by.get_full_name() or document.uploaded_by.username,
            'upload_date': document.uploaded_at,
            'dashboard_url': NotificationService._get_dashboard_url(curso.id),
            'site_name': getattr(settings, 'SITE_NAME', 'Sistema de Cursos'),
            'site_url': getattr(settings, 'BASE_URL', 'http://localhost:8000'),
        }
        
        if student:
            context.update({
                'student': student,
                'student_name': student.get_full_name() or student.username,
            })
        
        return context