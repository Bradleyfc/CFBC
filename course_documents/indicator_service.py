from .models import NewContentNotification


class ContentIndicatorService:
    """Servicio para manejo de indicadores de contenido nuevo"""
    
    @classmethod
    def has_new_content(cls, curso, student):
        """Verifica si hay contenido nuevo para un estudiante en un curso"""
        try:
            notification = NewContentNotification.objects.get(
                curso=curso,
                student=student
            )
            return notification.has_new_content
        except NewContentNotification.DoesNotExist:
            return False
    
    @classmethod
    def activate_indicator_for_course(cls, curso):
        """Activa el indicador de contenido nuevo para todos los estudiantes de un curso"""
        from principal.models import Matriculas
        
        # Obtener estudiantes inscritos
        matriculas = Matriculas.objects.filter(course=curso, activo=True)
        
        for matricula in matriculas:
            notification, created = NewContentNotification.objects.get_or_create(
                curso=curso,
                student=matricula.student,
                defaults={'has_new_content': True}
            )
            
            if not created:
                notification.has_new_content = True
                notification.save()
    
    @classmethod
    def deactivate_indicator_for_student(cls, curso, student):
        """Desactiva el indicador de contenido nuevo para un estudiante específico"""
        try:
            notification = NewContentNotification.objects.get(
                curso=curso,
                student=student
            )
            if notification.has_new_content:
                notification.has_new_content = False
                # IMPORTANTE: Actualizar last_checked para reflejar que el estudiante vio el contenido
                from django.utils import timezone
                notification.last_checked = timezone.now()
                notification.save()
                return True
        except NewContentNotification.DoesNotExist:
            pass
        return False
    
    @classmethod
    def update_last_checked(cls, curso, student):
        """Actualiza la fecha de última verificación para un estudiante en un curso"""
        from django.utils import timezone
        
        notification, created = NewContentNotification.objects.get_or_create(
            curso=curso,
            student=student,
            defaults={
                'has_new_content': False,
                'last_checked': timezone.now()
            }
        )
        
        if not created:
            notification.last_checked = timezone.now()
            # Solo desactivar has_new_content si NO hay documentos nuevos en ninguna carpeta
            notification.has_new_content = cls.has_new_documents_in_any_folder(curso, student)
            notification.save()
        
        return notification
    
    @classmethod
    def has_new_documents_in_any_folder(cls, curso, student):
        """Verifica si hay documentos nuevos en cualquier carpeta del curso"""
        from .models import DocumentFolder
        
        folders = DocumentFolder.objects.filter(curso=curso, documents__isnull=False).distinct()
        
        for folder in folders:
            if folder.get_new_documents_count(student) > 0:
                return True
        
        return False
    
    @classmethod
    def get_courses_with_new_content(cls, student):
        """Obtiene los cursos que tienen contenido nuevo para un estudiante"""
        notifications = NewContentNotification.objects.filter(
            student=student,
            has_new_content=True
        ).select_related('curso')
        
        return [notification.curso for notification in notifications]