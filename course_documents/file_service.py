import os
import hashlib
import mimetypes
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.storage import default_storage


class FileService:
    """Servicio para manejo de archivos de documentos de curso"""
    
    # Tipos de archivo permitidos
    ALLOWED_EXTENSIONS = [
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
        'txt', 'zip', 'rar', '7z', 'jpg', 'jpeg', 'png', 'gif'
    ]
    
    # Tamaño máximo de archivo (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB en bytes
    
    @classmethod
    def validate_file(cls, file):
        """Valida un archivo subido"""
        if not file:
            raise ValidationError("Debe seleccionar un archivo.")
        
        # Verificar tamaño del archivo
        if file.size > cls.MAX_FILE_SIZE:
            size_mb = cls.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(f"El archivo es demasiado grande. Tamaño máximo permitido: {size_mb:.0f}MB")
        
        # Verificar extensión del archivo
        file_extension = cls.get_file_extension(file.name)
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            allowed_extensions_str = ', '.join(cls.ALLOWED_EXTENSIONS)
            raise ValidationError(f"Tipo de archivo no permitido. Extensiones permitidas: {allowed_extensions_str}")
        
        # Verificar que el archivo no esté vacío
        if file.size == 0:
            raise ValidationError("El archivo está vacío.")
    
    @classmethod
    def get_file_extension(cls, filename):
        """Obtiene la extensión del archivo en minúsculas"""
        if not filename:
            return ''
        
        # Obtener la extensión y convertir a minúsculas
        _, extension = os.path.splitext(filename)
        return extension.lower().lstrip('.')
    
    @classmethod
    def generate_secure_filename(cls, filename, curso_id, folder_id):
        """Genera un nombre de archivo seguro"""
        # Obtener la extensión
        name, ext = os.path.splitext(filename)
        
        # Crear un hash único basado en el nombre original y timestamp
        import time
        unique_string = f"{name}_{curso_id}_{folder_id}_{int(time.time())}"
        file_hash = hashlib.md5(unique_string.encode()).hexdigest()[:8]
        
        # Limpiar el nombre original
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name[:50]  # Limitar longitud
        
        return f"{clean_name}_{file_hash}{ext}"
    
    @classmethod
    def get_upload_path(cls, curso_id, folder_id, filename):
        """Genera la ruta de subida para un archivo"""
        return f'course_documents/{curso_id}/{folder_id}/{filename}'
    
    @classmethod
    def delete_file(cls, file_path):
        """Elimina un archivo físico del almacenamiento"""
        try:
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
                return True
        except Exception as e:
            print(f"Error al eliminar archivo {file_path}: {e}")
        return False
    
    @classmethod
    def get_file_info(cls, file_path):
        """Obtiene información detallada de un archivo"""
        try:
            if default_storage.exists(file_path):
                size = default_storage.size(file_path)
                modified_time = default_storage.get_modified_time(file_path)
                content_type, _ = mimetypes.guess_type(file_path)
                
                return {
                    'size': size,
                    'size_display': cls.format_file_size(size),
                    'modified_time': modified_time,
                    'content_type': content_type or 'application/octet-stream',
                    'extension': cls.get_file_extension(file_path)
                }
        except Exception as e:
            print(f"Error al obtener información del archivo {file_path}: {e}")
        return None
    
    @classmethod
    def format_file_size(cls, size_bytes):
        """Formatea el tamaño del archivo en formato legible"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"