from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from .models import CourseDocument, AuditLog
from principal.models import Matriculas


@receiver(post_save, sender=CourseDocument)
def send_new_document_notification(sender, instance, created, **kwargs):
    """Envía notificación por email cuando se sube un nuevo documento"""
    if created:  # Solo para documentos nuevos
        # Obtener todos los estudiantes inscritos en el curso
        matriculas = Matriculas.objects.filter(course=instance.folder.curso, activo=True)
        
        for matricula in matriculas:
            student = matricula.student
            
            # Preparar el contexto para el email
            context = {
                'student_name': student.get_full_name() or student.username,
                'course_name': instance.folder.curso.name,
                'folder_name': instance.folder.name,
                'document_name': instance.name,
                'teacher_name': instance.uploaded_by.get_full_name() or instance.uploaded_by.username,
                'dashboard_url': f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/course-documents/student/{instance.folder.curso.id}/",
            }
            
            # Renderizar el contenido del email
            subject = f'Nuevo documento disponible en {instance.folder.curso.name}'
            message = render_to_string('course_documents/emails/new_document.txt', context)
            html_message = render_to_string('course_documents/emails/new_document.html', context)
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[student.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                # Log del error de envío de email
                AuditLog.log_action(
                    user=instance.uploaded_by,
                    action='document_uploaded',
                    curso=instance.folder.curso,
                    folder=instance.folder,
                    document=instance,
                    details=f'Error enviando email a {student.email}: {str(e)}'
                )


@receiver(post_save, sender=CourseDocument)
def log_document_upload(sender, instance, created, **kwargs):
    """Registra la subida de documentos en el log de auditoría"""
    if created:
        AuditLog.log_action(
            user=instance.uploaded_by,
            action='document_uploaded',
            curso=instance.folder.curso,
            folder=instance.folder,
            document=instance,
            details=f'Documento "{instance.name}" subido a la carpeta "{instance.folder.name}"'
        )


@receiver(post_delete, sender=CourseDocument)
def log_document_deletion(sender, instance, **kwargs):
    """Registra la eliminación de documentos en el log de auditoría"""
    AuditLog.log_action(
        user=None,  # No sabemos quién lo eliminó en este punto
        action='document_deleted',
        curso=instance.folder.curso,
        folder=instance.folder,
        details=f'Documento "{instance.name}" eliminado de la carpeta "{instance.folder.name}"'
    )