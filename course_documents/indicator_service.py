from django.db import transaction
from django.utils import timezone
import logging

from principal.models import Matriculas
from .models import NewContentNotification, AuditLog

logger = logging.getLogger(__name__)


class ContentIndicatorService:
    """
    Servicio para gestionar indicadores de contenido nuevo
    """
    
    @staticmethod
    def activate_indicators_for_course(curso, exclude_user=None):
        """
        Activa indicadores de contenido nuevo para todos los estudiantes de un curso
        
        Args:
            curso: El curso para el cual activar indicadores
            exclude_user: Usuario a excluir (típicamente el profesor que subió el contenido)
        """
        try:
            # Obtener estudiantes inscritos en el curso
            enrolled_students = Matriculas.objects.filter(
                course=curso,
                activo=True
            ).select_related('student')
            
            activated_count = 0
            
            with transaction.atomic():
                for matricula in enrolled_students:
                    student = matricula.student
                    
                    # Excluir usuario si se especifica (ej: el profesor)
                    if exclude_user and student == exclude_user:
                        continue
                    
                    # Crear o actualizar notificación de contenido nuevo
                    notification, created = NewContentNotification.objects.get_or_create(
                        curso=curso,
                        student=student,
                        defaults={
                            'has_new_content': True
                        }
                    )
                    
                    # Si ya existía pero no tenía contenido nuevo, activarlo
                    if not created and not notification.has_new_content:
                        notification.has_new_content = True
                        notification.save()
                        activated_count += 1
                    elif created:
                        activated_count += 1
                    
                    # Registrar activación de indicador
                    AuditLog.log_action(
                        user=student,
                        action='indicator_activated',
                        curso=curso,
                        details=f'Indicador de contenido nuevo activado para estudiante'
                    )
            
            logger.info(f"Indicadores activados para {activated_count} estudiantes en curso '{curso.name}'")
            return activated_count
            
        except Exception as e:
            logger.error(f"Error activando indicadores para curso {curso.name}: {str(e)}")
            return 0
    
    @staticmethod
    def deactivate_indicator_for_student(curso, student):
        """
        Desactiva el indicador de contenido nuevo para un estudiante específico
        
        Args:
            curso: El curso
            student: El estudiante
        """
        try:
            notification = NewContentNotification.objects.get(
                curso=curso,
                student=student
            )
            
            if notification.has_new_content:
                notification.mark_as_seen()
                
                # Registrar desactivación de indicador
                AuditLog.log_action(
                    user=student,
                    action='indicator_deactivated',
                    curso=curso,
                    details=f'Indicador de contenido nuevo desactivado para estudiante'
                )
                
                logger.info(f"Indicador desactivado para estudiante {student.username} en curso '{curso.name}'")
                return True
            
            return False
            
        except NewContentNotification.DoesNotExist:
            # Si no existe la notificación, no hay nada que desactivar
            return False
        except Exception as e:
            logger.error(f"Error desactivando indicador para estudiante {student.username}: {str(e)}")
            return False
    
    @staticmethod
    def get_courses_with_new_content_for_student(student):
        """
        Obtiene lista de cursos que tienen contenido nuevo para un estudiante
        
        Args:
            student: El estudiante
            
        Returns:
            QuerySet de cursos con contenido nuevo
        """
        try:
            notifications = NewContentNotification.objects.filter(
                student=student,
                has_new_content=True
            ).select_related('curso')
            
            course_ids = [notification.curso.id for notification in notifications]
            
            # Obtener cursos donde el estudiante está inscrito y tiene contenido nuevo
            from principal.models import Curso
            courses_with_new_content = Curso.objects.filter(
                id__in=course_ids,
                matriculas__student=student,
                matriculas__activo=True
            ).distinct()
            
            return courses_with_new_content
            
        except Exception as e:
            logger.error(f"Error obteniendo cursos con contenido nuevo para {student.username}: {str(e)}")
            return Curso.objects.none()
    
    @staticmethod
    def has_new_content(curso, student):
        """
        Verifica si un curso tiene contenido nuevo para un estudiante específico
        
        Args:
            curso: El curso
            student: El estudiante
            
        Returns:
            Boolean indicando si hay contenido nuevo
        """
        try:
            notification = NewContentNotification.objects.get(
                curso=curso,
                student=student
            )
            return notification.has_new_content
            
        except NewContentNotification.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error verificando contenido nuevo: {str(e)}")
            return False
    
    @staticmethod
    def get_indicator_stats_for_course(curso):
        """
        Obtiene estadísticas de indicadores para un curso
        
        Args:
            curso: El curso
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            total_students = Matriculas.objects.filter(
                course=curso,
                activo=True
            ).count()
            
            students_with_new_content = NewContentNotification.objects.filter(
                curso=curso,
                has_new_content=True
            ).count()
            
            students_without_indicators = total_students - NewContentNotification.objects.filter(
                curso=curso
            ).count()
            
            return {
                'total_students': total_students,
                'students_with_new_content': students_with_new_content,
                'students_seen_content': NewContentNotification.objects.filter(
                    curso=curso,
                    has_new_content=False
                ).count(),
                'students_without_indicators': students_without_indicators,
                'percentage_with_new_content': (
                    (students_with_new_content / total_students * 100) 
                    if total_students > 0 else 0
                )
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de indicadores: {str(e)}")
            return {
                'total_students': 0,
                'students_with_new_content': 0,
                'students_seen_content': 0,
                'students_without_indicators': 0,
                'percentage_with_new_content': 0
            }
    
    @staticmethod
    def cleanup_old_indicators(days_old=30):
        """
        Limpia indicadores antiguos (para mantenimiento)
        
        Args:
            days_old: Días de antigüedad para considerar indicadores como antiguos
            
        Returns:
            Número de indicadores limpiados
        """
        try:
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=days_old)
            
            old_indicators = NewContentNotification.objects.filter(
                last_checked__lt=cutoff_date,
                has_new_content=False
            )
            
            count = old_indicators.count()
            old_indicators.delete()
            
            logger.info(f"Limpiados {count} indicadores antiguos")
            return count
            
        except Exception as e:
            logger.error(f"Error limpiando indicadores antiguos: {str(e)}")
            return 0
    
    @staticmethod
    def reset_all_indicators_for_course(curso):
        """
        Resetea todos los indicadores de un curso (para mantenimiento)
        
        Args:
            curso: El curso
            
        Returns:
            Número de indicadores reseteados
        """
        try:
            indicators = NewContentNotification.objects.filter(curso=curso)
            count = indicators.count()
            
            for indicator in indicators:
                indicator.has_new_content = False
                indicator.save()
            
            # Registrar reset masivo
            AuditLog.log_action(
                user=None,
                action='indicators_reset',
                curso=curso,
                details=f'Todos los indicadores del curso fueron reseteados ({count} indicadores)'
            )
            
            logger.info(f"Reseteados {count} indicadores para curso '{curso.name}'")
            return count
            
        except Exception as e:
            logger.error(f"Error reseteando indicadores para curso {curso.name}: {str(e)}")
            return 0


class IndicatorTemplateContext:
    """
    Servicio para agregar contexto de indicadores a templates
    """
    
    @staticmethod
    def add_indicator_context_for_student(context, student):
        """
        Agrega contexto de indicadores para un estudiante a un template context
        
        Args:
            context: Diccionario de contexto del template
            student: El estudiante
            
        Returns:
            Contexto actualizado con información de indicadores
        """
        try:
            # Obtener cursos con contenido nuevo
            courses_with_new_content = ContentIndicatorService.get_courses_with_new_content_for_student(student)
            
            # Crear diccionario de cursos con contenido nuevo para fácil lookup
            new_content_course_ids = set(course.id for course in courses_with_new_content)
            
            # Agregar información de indicadores a cursos existentes en el contexto
            if 'enrolled_courses' in context:
                for course in context['enrolled_courses']:
                    course.has_new_content_indicator = course.id in new_content_course_ids
            
            if 'courses' in context:
                for course in context['courses']:
                    course.has_new_content_indicator = course.id in new_content_course_ids
            
            # Agregar estadísticas generales
            context['new_content_stats'] = {
                'total_courses_with_new_content': len(new_content_course_ids),
                'courses_with_new_content_ids': list(new_content_course_ids)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error agregando contexto de indicadores: {str(e)}")
            return context
    
    @staticmethod
    def add_indicator_context_for_teacher(context, teacher):
        """
        Agrega contexto de indicadores para un profesor a un template context
        
        Args:
            context: Diccionario de contexto del template
            teacher: El profesor
            
        Returns:
            Contexto actualizado con estadísticas de indicadores
        """
        try:
            # Agregar estadísticas de indicadores a cursos del profesor
            if 'assigned_courses' in context:
                for course in context['assigned_courses']:
                    course.indicator_stats = ContentIndicatorService.get_indicator_stats_for_course(course)
            
            return context
            
        except Exception as e:
            logger.error(f"Error agregando contexto de indicadores para profesor: {str(e)}")
            return context