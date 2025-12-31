from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
import os


def course_document_upload_path(instance, filename):
    """Genera la ruta de subida para documentos del curso"""
    # Organizar por curso y carpeta
    if instance.folder_id:
        return f'course_documents/{instance.folder.curso.id}/{instance.folder.id}/{filename}'
    else:
        # Fallback temporal si no hay folder asignado aún
        return f'course_documents/temp/{filename}'


class DocumentFolder(models.Model):
    """Carpeta para organizar documentos por curso"""
    curso = models.ForeignKey('principal.Curso', on_delete=models.CASCADE, 
                             related_name='document_folders', verbose_name='Curso')
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
        # Ejecutar validaciones antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)

    def get_new_documents_count(self, student):
        """Calcula el número de documentos nuevos en esta carpeta para un estudiante específico"""
        try:
            # Obtener el último acceso del estudiante a esta carpeta específica
            folder_access = FolderAccess.objects.get(
                folder=self,
                student=student
            )
            
            # Contar documentos subidos después del último acceso a la carpeta
            new_documents = self.documents.filter(
                uploaded_at__gt=folder_access.last_accessed
            ).count()
            
            return new_documents
            
        except FolderAccess.DoesNotExist:
            # Si nunca ha accedido a esta carpeta, todos los documentos son "nuevos"
            return self.documents.count()


class CourseDocument(models.Model):
    """Documento subido por el profesor"""

    folder = models.ForeignKey(DocumentFolder, on_delete=models.CASCADE, 
                              related_name='documents', verbose_name='Carpeta')
    name = models.CharField(max_length=255, blank=True, verbose_name='Nombre del documento')
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
        if self.folder_id:
            return f"{self.name} - {self.folder.name}"
        else:
            return f"{self.name} - Sin carpeta"

    def clean(self):
        """Validación personalizada del modelo"""
        # Validar nombre del documento
        if self.name:
            if len(self.name.strip()) > 200:  # Reducir límite para dar margen
                raise ValidationError({'name': 'El nombre del documento es demasiado largo (máximo 200 caracteres).'})
            # Limpiar espacios
            self.name = self.name.strip()

    def save(self, *args, **kwargs):
        """Override save para calcular tamaño del archivo"""
        if self.file and not self.file_size:
            self.file_size = self.file.size

        # Si no se proporciona un nombre, usar el nombre del archivo
        if not self.name and self.file:
            self.name = os.path.splitext(self.file.name)[0]

        # Solo ejecutar validaciones si el folder está asignado
        if self.folder_id:
            self.full_clean()

        super().save(*args, **kwargs)

        # Después de guardar, activar notificaciones para estudiantes
        if self.folder_id:
            self._activate_notifications()

    def _activate_notifications(self):
        """Activa las notificaciones de contenido nuevo para estudiantes del curso"""
        if not self.folder_id:
            return
            
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

    def get_file_icon(self):
        """Obtiene el icono de Material Icons apropiado según el tipo de archivo"""
        extension = self.get_file_extension().lower()
        
        # Mapeo de extensiones a iconos de Material Icons
        icon_map = {
            # Documentos PDF
            '.pdf': 'picture_as_pdf',
            
            # Documentos de Word
            '.doc': 'description',
            '.docx': 'description',
            
            # Presentaciones
            '.ppt': 'slideshow',
            '.pptx': 'slideshow',
            
            # Hojas de cálculo
            '.xls': 'table_chart',
            '.xlsx': 'table_chart',
            
            # Archivos de texto
            '.txt': 'text_snippet',
            
            # Archivos comprimidos
            '.zip': 'folder_zip',
            '.rar': 'folder_zip',
            '.7z': 'folder_zip',
            
            # Imágenes
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            
            # Otros archivos
            'default': 'insert_drive_file'
        }
        
        return icon_map.get(extension, icon_map['default'])

    def get_file_icon_color(self):
        """Obtiene el color apropiado para el icono según el tipo de archivo"""
        extension = self.get_file_extension().lower()
        
        # Mapeo de extensiones a colores
        color_map = {
            # PDF - Rojo
            '.pdf': 'text-red-600',
            
            # Word - Azul
            '.doc': 'text-blue-600',
            '.docx': 'text-blue-600',
            
            # PowerPoint - Naranja
            '.ppt': 'text-orange-600',
            '.pptx': 'text-orange-600',
            
            # Excel - Verde
            '.xls': 'text-green-600',
            '.xlsx': 'text-green-600',
            
            # Texto - Gris
            '.txt': 'text-gray-600',
            
            # Archivos comprimidos - Púrpura
            '.zip': 'text-purple-600',
            '.rar': 'text-purple-600',
            '.7z': 'text-purple-600',
            
            # Imágenes - Rosa
            '.jpg': 'text-pink-600',
            '.jpeg': 'text-pink-600',
            '.png': 'text-pink-600',
            '.gif': 'text-pink-600',
            '.bmp': 'text-pink-600',
            
            # Por defecto - Gris
            'default': 'text-gray-600'
        }
        
        return color_map.get(extension, color_map['default'])

    def get_file_icon_class(self):
        """Obtiene la clase CSS apropiada para el contenedor del icono según el tipo de archivo"""
        extension = self.get_file_extension().lower()
        
        # Mapeo de extensiones a clases CSS
        class_map = {
            # PDF
            '.pdf': 'document-icon-pdf',
            
            # Word
            '.doc': 'document-icon-word',
            '.docx': 'document-icon-word',
            
            # PowerPoint
            '.ppt': 'document-icon-powerpoint',
            '.pptx': 'document-icon-powerpoint',
            
            # Excel
            '.xls': 'document-icon-excel',
            '.xlsx': 'document-icon-excel',
            
            # Texto
            '.txt': 'document-icon-text',
            
            # Archivos comprimidos
            '.zip': 'document-icon-archive',
            '.rar': 'document-icon-archive',
            '.7z': 'document-icon-archive',
            
            # Imágenes
            '.jpg': 'document-icon-image',
            '.jpeg': 'document-icon-image',
            '.png': 'document-icon-image',
            '.gif': 'document-icon-image',
            '.bmp': 'document-icon-image',
            
            # Por defecto
            'default': 'document-icon-default'
        }
        
        return class_map.get(extension, class_map['default'])

    def get_file_type_name(self):
        """Obtiene el nombre descriptivo del tipo de archivo"""
        extension = self.get_file_extension().lower()
        
        # Mapeo de extensiones a nombres descriptivos
        type_map = {
            '.pdf': 'Documento PDF',
            '.doc': 'Documento Word',
            '.docx': 'Documento Word',
            '.ppt': 'Presentación PowerPoint',
            '.pptx': 'Presentación PowerPoint',
            '.xls': 'Hoja de cálculo Excel',
            '.xlsx': 'Hoja de cálculo Excel',
            '.txt': 'Archivo de texto',
            '.zip': 'Archivo comprimido ZIP',
            '.rar': 'Archivo comprimido RAR',
            '.7z': 'Archivo comprimido 7Z',
            '.jpg': 'Imagen JPEG',
            '.jpeg': 'Imagen JPEG',
            '.png': 'Imagen PNG',
            '.gif': 'Imagen GIF',
            '.bmp': 'Imagen BMP',
            'default': 'Archivo'
        }
        
        return type_map.get(extension, type_map['default'])


class FolderAccess(models.Model):
    """Registro de acceso a carpetas por estudiantes"""
    folder = models.ForeignKey(DocumentFolder, on_delete=models.CASCADE, 
                              related_name='access_logs', verbose_name='Carpeta')
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Estudiante')
    last_accessed = models.DateTimeField(auto_now=True, verbose_name='Último acceso')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Primer acceso')

    class Meta:
        verbose_name = '📂 Acceso a Carpeta'
        verbose_name_plural = '📂 Accesos a Carpetas'
        unique_together = [['folder', 'student']]
        ordering = ['-last_accessed']

    def __str__(self):
        return f"{self.student.get_full_name() or self.student.username} - {self.folder.name} - {self.last_accessed}"


class DocumentAccess(models.Model):
    """Registro de acceso a documentos por estudiantes"""
    document = models.ForeignKey(CourseDocument, on_delete=models.CASCADE, 
                                related_name='access_logs', verbose_name='Documento')
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
    curso = models.ForeignKey('principal.Curso', on_delete=models.CASCADE, 
                             null=True, blank=True, verbose_name='Curso')
    folder = models.ForeignKey(DocumentFolder, on_delete=models.SET_NULL, 
                              null=True, blank=True, verbose_name='Carpeta')
    document = models.ForeignKey(CourseDocument, on_delete=models.SET_NULL, 
                                null=True, blank=True, verbose_name='Documento')
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