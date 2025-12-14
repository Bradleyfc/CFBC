"""
Servicio de seguridad para validación de archivos
"""

import os
import hashlib
import mimetypes
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SecurityService:
    """
    Servicio para validaciones de seguridad en archivos
    """
    
    # Tipos MIME peligrosos que nunca deben permitirse
    DANGEROUS_MIME_TYPES = {
        'application/x-executable',
        'application/x-msdownload',
        'application/x-msdos-program',
        'application/x-dosexec',
        'application/x-winexe',
        'application/x-sh',
        'application/x-csh',
        'application/x-shellscript',
        'text/x-shellscript',
        'application/javascript',
        'text/javascript',
        'application/x-javascript',
        'text/x-php',
        'application/x-php',
        'text/x-python',
        'application/x-python-code',
    }
    
    # Extensiones peligrosas
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'vbe', 'js', 'jse',
        'wsf', 'wsh', 'msc', 'msi', 'msp', 'dll', 'application', 'gadget',
        'hta', 'cpl', 'jar', 'php', 'py', 'rb', 'pl', 'sh', 'bash', 'zsh', 'fish'
    }
    
    @classmethod
    def validate_file_security(cls, file):
        """
        Realiza validaciones de seguridad básicas en un archivo
        
        Args:
            file: Archivo a validar
            
        Returns:
            True si es seguro
            
        Raises:
            ValidationError: Si el archivo es peligroso
        """
        try:
            # Validar extensión
            cls._validate_extension(file.name)
            
            # Validar tipo MIME básico
            cls._validate_mime_type(file)
            
            # Validar tamaño y estructura
            cls._validate_file_structure(file)
            
            logger.info(f"Archivo validado exitosamente: {file.name}")
            return True
            
        except ValidationError:
            logger.warning(f"Archivo rechazado por validación de seguridad: {file.name}")
            raise
        except Exception as e:
            logger.error(f"Error en validación de seguridad para {file.name}: {str(e)}")
            # No bloquear por errores internos, solo log
            return True
    
    @classmethod
    def _validate_extension(cls, filename):
        """Valida que la extensión no sea peligrosa"""
        if not filename:
            raise ValidationError("El archivo debe tener un nombre válido")
        
        extension = os.path.splitext(filename)[1].lower().lstrip('.')
        
        if extension in cls.DANGEROUS_EXTENSIONS:
            raise ValidationError(f"Tipo de archivo no permitido por seguridad: .{extension}")
        
        # Validar extensiones dobles (ej: archivo.pdf.exe)
        parts = filename.lower().split('.')
        if len(parts) > 2:
            for part in parts[1:-1]:  # Excluir nombre base y extensión final
                if part in cls.DANGEROUS_EXTENSIONS:
                    raise ValidationError("Archivo con extensión doble sospechosa detectado")
    
    @classmethod
    def _validate_mime_type(cls, file):
        """Valida el tipo MIME del archivo"""
        try:
            # Usar mimetypes estándar
            mime_type, _ = mimetypes.guess_type(file.name)
            if mime_type and mime_type in cls.DANGEROUS_MIME_TYPES:
                raise ValidationError(f"Tipo de archivo no permitido: {mime_type}")
                
        except Exception as e:
            logger.error(f"Error validando MIME type: {str(e)}")
            # No bloquear por errores en validación MIME
            pass
    
    @classmethod
    def _validate_file_structure(cls, file):
        """Valida la estructura del archivo"""
        # Validar que el archivo no esté corrupto
        if file.size == 0:
            raise ValidationError("El archivo está vacío")
        
        # Validar tamaño máximo
        max_size = getattr(settings, 'COURSE_DOCUMENTS_MAX_FILE_SIZE', 10 * 1024 * 1024)
        if file.size > max_size:
            size_mb = max_size / (1024 * 1024)
            raise ValidationError(f"El archivo es demasiado grande (máximo {size_mb:.0f}MB)")
    
    @classmethod
    def calculate_file_hash(cls, file):
        """
        Calcula el hash SHA-256 de un archivo
        
        Args:
            file: Archivo para calcular hash
            
        Returns:
            Hash SHA-256 en hexadecimal
        """
        try:
            file.seek(0)
            hash_sha256 = hashlib.sha256()
            
            for chunk in iter(lambda: file.read(4096), b""):
                hash_sha256.update(chunk)
            
            file.seek(0)
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculando hash de archivo: {str(e)}")
            return None