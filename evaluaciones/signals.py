import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import Evaluacion

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Evaluacion)
def marcar_recien_publicada(sender, instance, **kwargs):
    """
    Antes de guardar, detecta si la evaluación está pasando de
    cualquier estado → 'publicada' por primera vez.
    Guarda el flag en la instancia para que post_save lo lea.
    """
    if not instance.pk:
        # Objeto nuevo: si ya viene publicada, marcar como recién publicada
        instance._recien_publicada = (instance.estado == 'publicada')
        return

    try:
        anterior = Evaluacion.objects.get(pk=instance.pk)
        # Solo notificar si el estado anterior NO era publicada y ahora sí lo es
        instance._recien_publicada = (
            anterior.estado != 'publicada' and instance.estado == 'publicada'
        )
    except Evaluacion.DoesNotExist:
        instance._recien_publicada = False


@receiver(post_save, sender=Evaluacion)
def notificar_nueva_evaluacion(sender, instance, created, **kwargs):
    """
    Envía un correo a todos los estudiantes matriculados cuando una evaluación
    se publica por primera vez (creada publicada o cambiada de borrador a publicada).
    """
    if not getattr(instance, '_recien_publicada', False):
        return

    from principal.models import Matriculas

    matriculas = Matriculas.objects.filter(
        course=instance.curso,
        activo=True,
    ).select_related('student')

    if not matriculas.exists():
        return

    site_name = getattr(settings, 'SITE_NAME', 'Plataforma Educativa')
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')

    for matricula in matriculas:
        student = matricula.student
        if not student.email:
            continue

        context = {
            'student_name': student.get_full_name() or student.username,
            'curso': instance.curso,
            'evaluacion': instance,
            'teacher_name': (
                instance.curso.teacher.get_full_name()
                or instance.curso.teacher.username
            ),
            'site_name': site_name,
            'evaluacion_url': f"{site_url}/evaluaciones/mis-evaluaciones/{instance.curso.pk}/",
        }

        subject = f'Nueva evaluación disponible en {instance.curso.name}'
        message = render_to_string('evaluaciones/emails/nueva_evaluacion.txt', context)
        html_message = render_to_string('evaluaciones/emails/nueva_evaluacion.html', context)

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
            logger.warning(
                'Error enviando email de evaluación "%s" a %s: %s',
                instance.titulo, student.email, e
            )
