import os
import mimetypes
import hashlib
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)


class FileService:
    """
    Servicio para gestión de archivos de documentos de cursos
    """
    
    # Configuración por defecto si no está en settings
    MAX_FILE_SIZE = getattr(settings, 'COURSE_DOCUMENTS_MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
    ALLOWED_EXTENSIONS = getattr(settings, 'COURSE_DOCUMENTS_ALLOWED_EXTENSIONS', [
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 
        'txt', 'zip', 'rar', '7z', 'jpg', 'jpeg', 'png', 'gif'
    ])
    UPLOAD_PATH = getattr(settings, 'COURSE_DOCUMENTS_UPLOAD_PATH', 'course_documents/')
    
    @classmethod
    def validate_file(cls, file):
        """
        Valida un archivo antes de subirlo
        
        Args:
            file: Archivo a validar
            
        Returns:
            True si es válido
            
        Raises:
            ValidationError: Si el archivo no es válido
        """
        # Verificar tamaño
        if file.size > cls.MAX_FILE_SIZE:
            size_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(f'El archivo es demasiado grande. Tamaño máximo: {size_mb}MB')
        
        # Verificar que no esté vacío
        if file.size == 0:
            raise ValidationError('El archivo está vacío')
        
        # Verificar extensión
        extension = cls.get_file_extension(file.name)
        if extension not in cls.ALLOWED_EXTENSIONS:
            allowed_str = ', '.join(cls.ALLOWED_EXTENSIONS)
            raise ValidationError(f'Tipo de archivo no permitido. Extensiones permitidas: {allowed_str}')
        
        # Verificar nombre del archivo
        if not file.name or len(file.name.strip()) == 0:
            raise ValidationError('El archivo debe tener un nombre válido')
        
        return True
    
    @classmethod
    def get_file_extension(cls, filename):
        """
        Obtiene la extensión del archivo en minúsculas
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Extensión sin el punto
        """
        if not filename:
            return ''
        
        _, extension = os.path.splitext(filename)
        return extension.lower().lstrip('.')
    
    @classmethod
    def generate_secure_filename(cls, original_filename, curso_id, folder_id):
        """
        Genera un nombre de archivo seguro y único
        
        Args:
            original_filename: Nombre original del archivo
            curso_id: ID del curso
            folder_id: ID de la carpeta
            
        Returns:
            Nombre de archivo seguro
        """
        # Obtener extensión
        extension = cls.get_file_extension(original_filename)
        
        # Limpiar nombre base
        name_without_ext = os.path.splitext(original_filename)[0]
        clean_name = slugify(name_without_ext)
        
        # Si el nombre queda vacío después de slugify, usar un nombre por defecto
        if not clean_name:
            clean_name = 'documento'
        
        # Generar hash único basado en timestamp y contenido
        import time
        unique_hash = hashlib.md5(f"{curso_id}_{folder_id}_{clean_name}_{time.time()}".encode()).hexdigest()[:8]
        
        # Construir nombre final
        secure_filename = f"{clean_name}_{unique_hash}.{extension}"
        
        return secure_filename
    
    @classmethod
    def get_upload_path(cls, curso_id, folder_id, filename):
        """
        Genera la ruta de subida para un archivo
        
        Args:
            curso_id: ID del curso
            folder_id: ID de la carpeta
            filename: Nombre del archivo
            
        Returns:
            Ruta completa para el archivo
        """
        return os.path.join(
            cls.UPLOAD_PATH,
            f'curso_{curso_id}',
            f'folder_{folder_id}',
            filename
        )
    
    @classmethod
    def save_file(cls, file, curso_id, folder_id, custom_name=None):
        """
        Guarda un archivo de forma segura
        
        Args:
            file: Archivo a guardar
            curso_id: ID del curso
            folder_id: ID de la carpeta
            custom_name: Nombre personalizado (opcional)
            
        Returns:
            Tupla (ruta_del_archivo, nombre_seguro)
        """
        try:
            # Validar archivo
            cls.validate_file(file)
            
            # Generar nombre seguro
            original_name = custom_name or file.name
            secure_filename = cls.generate_secure_filename(original_name, curso_id, folder_id)
            
            # Generar ruta completa
            file_path = cls.get_upload_path(curso_id, folder_id, secure_filename)
            
            # Asegurar que el directorio existe
            directory = os.path.dirname(file_path)
            if not default_storage.exists(directory):
                # Crear directorio si no existe
                os.makedirs(os.path.join(settings.MEDIA_ROOT, directory), exist_ok=True)
            
            # Guardar archivo
            saved_path = default_storage.save(file_path, file)
            
            logger.info(f"Archivo guardado exitosamente: {saved_path}")
            
            return saved_path, secure_filename
            
        except Exception as e:
            logger.error(f"Error guardando archivo: {str(e)}")
            raise ValidationError(f"Error al guardar el archivo: {str(e)}")
    
    @classmethod
    def delete_file(cls, file_path):
        """
        Elimina un archivo de forma segura
        
        Args:
            file_path: Ruta del archivo a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            if file_path and default_storage.exists(file_path):
                default_storage.delete(file_path)
                logger.info(f"Archivo eliminado exitosamente: {file_path}")
                return True
            else:
                logger.warning(f"Archivo no encontrado para eliminar: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error eliminando archivo {file_path}: {str(e)}")
            return False
    
    @classmethod
    def get_file_info(cls, file_path):
        """
        Obtiene información de un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Diccionario con información del archivo
        """
        try:
            if not default_storage.exists(file_path):
                return None
            
            # Obtener información básica
            file_size = default_storage.size(file_path)
            file_url = default_storage.url(file_path)
            
            # Obtener tipo MIME
            content_type, _ = mimetypes.guess_type(file_path)
            
            # Obtener extensión
            extension = cls.get_file_extension(file_path)
            
            return {
                'path': file_path,
                'url': file_url,
                'size': file_size,
                'size_human': cls.format_file_size(file_size),
                'content_type': content_type or 'application/octet-stream',
                'extension': extension,
                'exists': True
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información del archivo {file_path}: {str(e)}")
            return None
    
    @classmethod
    def format_file_size(cls, size_bytes):
        """
        Formatea el tamaño del archivo en formato legible
        
        Args:
            size_bytes: Tamaño en bytes
            
        Returns:
            Tamaño formateado (ej: "1.5 MB")
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @classmethod
    def cleanup_orphaned_files(cls, curso_id=None):
        """
        Limpia archivos huérfanos (sin registro en base de datos)
        
        Args:
            curso_id: ID del curso específico (opcional)
            
        Returns:
            Número de archivos eliminados
        """
        try:
            from .models import CourseDocument
            
            # Construir ruta base
            if curso_id:
                base_path = os.path.join(cls.UPLOAD_PATH, f'curso_{curso_id}')
            else:
                base_path = cls.UPLOAD_PATH
            
            if not default_storage.exists(base_path):
                return 0
            
            # Obtener todos los archivos registrados en la base de datos
            if curso_id:
                registered_files = set(
                    CourseDocument.objects.filter(
                        folder__curso_id=curso_id
                    ).values_list('file', flat=True)
                )
            else:
                registered_files = set(
                    CourseDocument.objects.all().values_list('file', flat=True)
                )
            
            # Buscar archivos en el sistema de archivos
            deleted_count = 0
            
            # Esta implementación depende del backend de storage
            # Para desarrollo local con FileSystemStorage
            if hasattr(default_storage, 'path'):
                import glob
                full_base_path = default_storage.path(base_path)
                
                for file_path in glob.glob(os.path.join(full_base_path, '**', '*'), recursive=True):
                    if os.path.isfile(file_path):
                        # Convertir a ruta relativa
                        relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                        
                        # Si no está registrado en la base de datos, eliminarlo
                        if relative_path not in registered_files:
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                logger.info(f"Archivo huérfano eliminado: {relative_path}")
                            except Exception as e:
                                logger.error(f"Error eliminando archivo huérfano {relative_path}: {str(e)}")
            
            logger.info(f"Limpieza completada: {deleted_count} archivos huérfanos eliminados")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error en limpieza de archivos huérfanos: {str(e)}")
            return 0
    
    @classmethod
    def get_storage_stats(cls, curso_id=None):
        """
        Obtiene estadísticas de almacenamiento
        
        Args:
            curso_id: ID del curso específico (opcional)
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            from .models import CourseDocument
            
            # Filtrar por curso si se especifica
            if curso_id:
                documents = CourseDocument.objects.filter(folder__curso_id=curso_id)
            else:
                documents = CourseDocument.objects.all()
            
            # Calcular estadísticas
            total_documents = documents.count()
            total_size = sum(doc.file_size or 0 for doc in documents)
            
            # Estadísticas por tipo de archivo
            extensions = {}
            for doc in documents:
                ext = cls.get_file_extension(doc.file.name)
                extensions[ext] = extensions.get(ext, 0) + 1
            
            return {
                'total_documents': total_documents,
                'total_size_bytes': total_size,
                'total_size_human': cls.format_file_size(total_size),
                'extensions': extensions,
                'average_size_bytes': total_size / total_documents if total_documents > 0 else 0,
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de almacenamiento: {str(e)}")
            return {
                'total_documents': 0,
                'total_size_bytes': 0,
                'total_size_human': '0 B',
                'extensions': {},
                'average_size_bytes': 0,
            }