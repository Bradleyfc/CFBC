from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from principal.models import Curso, Matriculas


class TeacherPermissionMixin:
    """Mixin para verificar permisos de profesor"""
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            raise PermissionDenied("Debe iniciar sesión para acceder a esta página.")
        
        # Obtener el curso
        curso_id = kwargs.get('curso_id')
        if curso_id:
            curso = get_object_or_404(Curso, id=curso_id)
            
            # Verificar que el usuario sea el profesor del curso
            if curso.teacher != request.user:
                raise PermissionDenied("No tienes permisos para acceder a los documentos de este curso.")
        
        return super().dispatch(request, *args, **kwargs)


class StudentPermissionMixin:
    """Mixin para verificar permisos de estudiante"""
    
    def dispatch(self, request, *args, **kwargs):
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            raise PermissionDenied("Debe iniciar sesión para acceder a esta página.")
        
        # Obtener el curso
        curso_id = kwargs.get('curso_id')
        if curso_id:
            curso = get_object_or_404(Curso, id=curso_id)
            
            # Verificar que el usuario esté inscrito en el curso
            if not Matriculas.objects.filter(
                course=curso,
                student=request.user,
                activo=True
            ).exists():
                raise PermissionDenied("No tienes acceso a los documentos de este curso.")
        
        return super().dispatch(request, *args, **kwargs)