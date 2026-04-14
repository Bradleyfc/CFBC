from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import os


def course_document_upload_path(instance, filename):
    """Genera la ruta de subida para documentos del curso"""
    return f'course_documents/{instance.folder.curso.id}/{instance.folder.id}/{filename}'


class DocumentFolder(models.Model):
    """Carpeta para organizar documentos por curso"""
    curso = models.ForeignKey('principal.Curso', on_delete=models.CASCADE, related_name='document_folders', verbose_name='Curso')
    name = models.CharField(max_length=255, verbose_name='Nombre de la carpeta')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = '📁 Carpeta de Documentos'
        verbose_name_plural = '📁 Carpetas de Documentos'
        ordering = ['name']
        unique_together = [['curso', 'name']]  # No permitir carpetas con el mismo nombre en el mismo curso

    def __str__(self):
        return f"{self.name} - {self.curso.name}"

    def clean(self):
        from django.core.exceptions import ValidationError
        import re
        
        # Validar que el nombre no esté vacío después de quitar espacios
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'El nombre de la carpeta no puede estar vacío.'})
        
        # Validar caracteres especiales no permitidos
        if re.search(r'[<>:"/\\|?*]', self.name):
            raise ValidationError({'name': 'El nombre de la carpeta contiene caracteres no permitidos.'})
        
        # Validar longitud máxima
        if len(self.name.strip()) > 200:  # Reducir límite para dar margen
            raise ValidationError({'name': 'El nombre de la carpeta es demasiado largo (máximo 200 caracteres).'})
        
        # Limpiar espacios al inicio y final
        self.name = self.name.strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CourseDocument(models.Model):
    """Documento subido por el profesor"""
    
    folder = models.ForeignKey(DocumentFolder, on_delete=models.CASCADE, related_name='documents', verbose_name='Carpeta')
    name = models.CharField(max_length=255, verbose_name='Nombre del documento')
    file = models.FileField(
        upload_to=course_document_upload_path,
        verbose_name='Archivo'
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Subido por')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de subida')
    file_size = models.PositiveIntegerField(verbose_name='Tamaño del archivo (bytes)', editable=False)
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        verbose_name = '📄 Documento del Curso'
        verbose_name_plural = '📄 Documentos del Curso'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} - {self.folder.name}"

    def clean(self):
        """Validación personalizada del modelo"""
        # Validar nombre del documento
        if self.name:
            if len(self.name.strip()) > 200:
                raise ValidationError({'name': 'El nombre del documento es demasiado largo (máximo 200 caracteres).'})
            self.name = self.name.strip()

    def save(self, *args, **kwargs):
        """Override save para calcular tamaño del archivo"""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def _activate_notifications(self):
        """Activa las notificaciones de contenido nuevo para estudiantes del curso"""
        from principal.models import Matriculas
        
        # Obtener todos los estudiantes inscritos en el curso
        matriculas = Matriculas.objects.filter(course=self.folder.curso, activo=True)
        
        for matricula in matriculas:
            notification, created = NewContentNotification.objects.get_or_create(
                curso=self.folder.curso,
                student=matricula.student,
                defaults={'has_new_content': True}
            )
            if not created:
                notification.has_new_content = True
                notification.save()

    def get_file_extension(self):
        """Obtiene la extensión del archivo"""
        return os.path.splitext(self.file.name)[1].lower()

    def get_file_size_display(self):
        """Muestra el tamaño del archivo en formato legible"""
        if self.file_size < 1024:
            return f"{self.file_size} bytes"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class DocumentAccess(models.Model):
    """Registro de acceso a documentos por estudiantes"""
    document = models.ForeignKey(CourseDocument, on_delete=models.CASCADE, related_name='access_logs', verbose_name='Documento')
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Estudiante')
    accessed_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de acceso')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dirección IP')

    class Meta:
        verbose_name = '📊 Acceso a Documento'
        verbose_name_plural = '📊 Accesos a Documentos'
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.student.get_full_name() or self.student.username} - {self.document.name} - {self.accessed_at}"


class NewContentNotification(models.Model):
    """Seguimiento de contenido nuevo para mostrar indicadores"""
    curso = models.ForeignKey('principal.Curso', on_delete=models.CASCADE, verbose_name='Curso')
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Estudiante')
    has_new_content = models.BooleanField(default=False, verbose_name='Tiene contenido nuevo')
    last_checked = models.DateTimeField(auto_now=True, verbose_name='Última verificación')

    class Meta:
        verbose_name = '🔔 Notificación de Contenido Nuevo'
        verbose_name_plural = '🔔 Notificaciones de Contenido Nuevo'
        unique_together = [['curso', 'student']]

    def __str__(self):
        status = "Nuevo" if self.has_new_content else "Visto"
        return f"{self.student.get_full_name() or self.student.username} - {self.curso.name} - {status}"

    def mark_as_seen(self):
        """Marca el contenido como visto"""
        self.has_new_content = False
        self.save()


class AuditLog(models.Model):
    """Log de auditoría para operaciones del sistema de documentos"""
    
    ACTION_CHOICES = [
        ('folder_created', 'Carpeta Creada'),
        ('folder_deleted', 'Carpeta Eliminada'),
        ('document_uploaded', 'Documento Subido'),
        ('document_downloaded', 'Documento Descargado'),
        ('document_deleted', 'Documento Eliminado'),
        ('unauthorized_access', 'Acceso No Autorizado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Usuario')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, verbose_name='Acción')
    curso = models.ForeignKey('principal.Curso', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Curso')
    folder = models.ForeignKey(DocumentFolder, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Carpeta')
    document = models.ForeignKey(CourseDocument, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Documento')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y hora')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dirección IP')
    details = models.TextField(blank=True, null=True, verbose_name='Detalles adicionales')

    class Meta:
        verbose_name = '📋 Log de Auditoría'
        verbose_name_plural = '📋 Logs de Auditoría'
        ordering = ['-timestamp']

    def __str__(self):
        user_name = self.user.get_full_name() or self.user.username if self.user else "Usuario desconocido"
        return f"{user_name} - {self.get_action_display()} - {self.timestamp}"

    def clean(self):
        """Validación personalizada del modelo"""
        # Validar longitud de detalles
        if self.details and len(self.details) > 1000:  # Límite razonable para detalles
            raise ValidationError({'details': 'Los detalles son demasiado largos (máximo 1000 caracteres).'})
        
        # Validar que la acción esté en las opciones válidas
        valid_actions = [choice[0] for choice in self.ACTION_CHOICES]
        if self.action and self.action not in valid_actions:
            raise ValidationError({'action': f'Acción no válida. Debe ser una de: {", ".join(valid_actions)}'})

    @classmethod
    def log_action(cls, user, action, curso=None, folder=None, document=None, ip_address=None, details=None):
        """Método de conveniencia para crear logs de auditoría"""
        # Truncar detalles si son demasiado largos
        if details and len(details) > 1000:
            details = details[:997] + "..."
        
        return cls.objects.create(
            user=user,
            action=action,
            curso=curso,
            folder=folder,
            document=document,
            ip_address=ip_address,
            details=details
        )