from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from principal.models import Curso, Matriculas
from .models import AuditLog


class TeacherPermissionMixin(UserPassesTestMixin):
    """
    Mixin para verificar que el usuario es profesor del curso
    """
    
    def test_func(self):
        """Verifica que el usuario sea profesor y esté asignado al curso"""
        if not self.request.user.is_authenticated:
            return False
        
        # Verificar que el usuario pertenece al grupo de profesores
        if not self.request.user.groups.filter(name='Profesores').exists():
            return False
        
        # Obtener el ID del curso de la URL
        curso_id = self.kwargs.get('curso_id')
        if not curso_id:
            return False
        
        # Verificar que el curso existe y el usuario es el profesor asignado
        try:
            curso = Curso.objects.get(id=curso_id)
            return curso.teacher == self.request.user
        except Curso.DoesNotExist:
            return False

    def handle_no_permission(self):
        """Maneja el caso cuando no se tienen permisos"""
        # Log del intento de acceso no autorizado
        curso_id = self.kwargs.get('curso_id')
        ip_address = self.get_client_ip()
        
        try:
            curso = Curso.objects.get(id=curso_id) if curso_id else None
        except Curso.DoesNotExist:
            curso = None
            
        AuditLog.log_action(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='unauthorized_access',
            curso=curso,
            ip_address=ip_address,
            details=f'Intento de acceso no autorizado al dashboard de profesor para curso {curso_id}'
        )
        
        raise PermissionDenied("No tienes permisos para acceder a este curso.")

    def get_client_ip(self):
        """Obtiene la dirección IP del cliente"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class StudentPermissionMixin(UserPassesTestMixin):
    """
    Mixin para verificar que el usuario es estudiante inscrito en el curso
    """
    
    def test_func(self):
        """Verifica que el usuario sea estudiante y esté inscrito en el curso"""
        if not self.request.user.is_authenticated:
            return False
        
        # Verificar que el usuario pertenece al grupo de estudiantes
        if not self.request.user.groups.filter(name='Estudiantes').exists():
            return False
        
        # Obtener el ID del curso de la URL
        curso_id = self.kwargs.get('curso_id')
        if not curso_id:
            return False
        
        # Verificar que el estudiante está inscrito en el curso
        try:
            matricula = Matriculas.objects.get(
                course_id=curso_id,
                student=self.request.user,
                activo=True
            )
            return True
        except Matriculas.DoesNotExist:
            return False

    def handle_no_permission(self):
        """Maneja el caso cuando no se tienen permisos"""
        # Log del intento de acceso no autorizado
        curso_id = self.kwargs.get('curso_id')
        ip_address = self.get_client_ip()
        
        try:
            curso = Curso.objects.get(id=curso_id) if curso_id else None
        except Curso.DoesNotExist:
            curso = None
            
        AuditLog.log_action(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='unauthorized_access',
            curso=curso,
            ip_address=ip_address,
            details=f'Intento de acceso no autorizado al dashboard de estudiante para curso {curso_id}'
        )
        
        raise PermissionDenied("No tienes permisos para acceder a este curso o no estás inscrito.")

    def get_client_ip(self):
        """Obtiene la dirección IP del cliente"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class DocumentAccessMixin:
    """
    Mixin para verificar acceso a documentos específicos
    """
    
    def check_document_access(self, document):
        """
        Verifica que el usuario tenga acceso al documento
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        # Si es profesor, verificar que sea el profesor del curso
        if user.groups.filter(name='Profesores').exists():
            return document.folder.curso.teacher == user
        
        # Si es estudiante, verificar que esté inscrito en el curso
        elif user.groups.filter(name='Estudiantes').exists():
            try:
                Matriculas.objects.get(
                    course=document.folder.curso,
                    student=user,
                    activo=True
                )
                return True
            except Matriculas.DoesNotExist:
                return False
        
        return False

    def log_document_access(self, document, action='document_downloaded'):
        """
        Registra el acceso a un documento
        """
        ip_address = self.get_client_ip()
        
        AuditLog.log_action(
            user=self.request.user,
            action=action,
            curso=document.folder.curso,
            folder=document.folder,
            document=document,
            ip_address=ip_address,
            details=f'Acceso al documento "{document.name}" en la carpeta "{document.folder.name}"'
        )

    def get_client_ip(self):
        """Obtiene la dirección IP del cliente"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


def require_teacher_access(view_func):
    """
    Decorador para vistas que requieren acceso de profesor
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Debes iniciar sesión.")
        
        if not request.user.groups.filter(name='Profesores').exists():
            raise PermissionDenied("Solo los profesores pueden acceder a esta función.")
        
        curso_id = kwargs.get('curso_id')
        if curso_id:
            try:
                curso = Curso.objects.get(id=curso_id)
                if curso.teacher != request.user:
                    # Log del intento no autorizado
                    AuditLog.log_action(
                        user=request.user,
                        action='unauthorized_access',
                        curso=curso,
                        details=f'Intento de acceso no autorizado a curso {curso.name}'
                    )
                    raise PermissionDenied("No eres el profesor de este curso.")
            except Curso.DoesNotExist:
                raise PermissionDenied("El curso no existe.")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_student_access(view_func):
    """
    Decorador para vistas que requieren acceso de estudiante
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Debes iniciar sesión.")
        
        if not request.user.groups.filter(name='Estudiantes').exists():
            raise PermissionDenied("Solo los estudiantes pueden acceder a esta función.")
        
        curso_id = kwargs.get('curso_id')
        if curso_id:
            try:
                matricula = Matriculas.objects.get(
                    course_id=curso_id,
                    student=request.user,
                    activo=True
                )
            except Matriculas.DoesNotExist:
                # Log del intento no autorizado
                try:
                    curso = Curso.objects.get(id=curso_id) if curso_id else None
                except Curso.DoesNotExist:
                    curso = None
                    
                AuditLog.log_action(
                    user=request.user,
                    action='unauthorized_access',
                    curso=curso,
                    details=f'Intento de acceso no autorizado a curso {curso_id} - no inscrito'
                )
                raise PermissionDenied("No estás inscrito en este curso.")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper