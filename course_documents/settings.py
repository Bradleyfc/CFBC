"""
Configuraciones específicas para el sistema de documentos de cursos
"""

import os
from django.conf import settings

# Configuraciones de archivos
COURSE_DOCUMENTS_MAX_FILE_SIZE = getattr(settings, 'COURSE_DOCUMENTS_MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB

COURSE_DOCUMENTS_ALLOWED_EXTENSIONS = getattr(settings, 'COURSE_DOCUMENTS_ALLOWED_EXTENSIONS', [
    # Documentos
    'pdf', 'doc', 'docx', 'odt', 'rtf',
    # Presentaciones
    'ppt', 'pptx', 'odp',
    # Hojas de cálculo
    'xls', 'xlsx', 'ods', 'csv',
    # Texto
    'txt', 'md',
    # Archivos comprimidos
    'zip', 'rar', '7z', 'tar', 'gz',
    # Imágenes
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
    # Audio/Video (para cursos multimedia)
    'mp3', 'wav', 'mp4', 'avi', 'mov', 'wmv',
])

COURSE_DOCUMENTS_UPLOAD_PATH = getattr(settings, 'COURSE_DOCUMENTS_UPLOAD_PATH', 'course_documents/')

# Configuraciones de seguridad
COURSE_DOCUMENTS_SCAN_UPLOADS = getattr(settings, 'COURSE_DOCUMENTS_SCAN_UPLOADS', True)
COURSE_DOCUMENTS_QUARANTINE_PATH = getattr(settings, 'COURSE_DOCUMENTS_QUARANTINE_PATH', 'quarantine/')

# Configuraciones de limpieza automática
COURSE_DOCUMENTS_AUTO_CLEANUP = getattr(settings, 'COURSE_DOCUMENTS_AUTO_CLEANUP', True)
COURSE_DOCUMENTS_CLEANUP_DAYS = getattr(settings, 'COURSE_DOCUMENTS_CLEANUP_DAYS', 30)  # Días para mantener archivos huérfanos

# Configuraciones de notificaciones
COURSE_DOCUMENTS_EMAIL_NOTIFICATIONS = getattr(settings, 'COURSE_DOCUMENTS_EMAIL_NOTIFICATIONS', True)
COURSE_DOCUMENTS_EMAIL_BATCH_SIZE = getattr(settings, 'COURSE_DOCUMENTS_EMAIL_BATCH_SIZE', 50)

# Configuraciones de logging
COURSE_DOCUMENTS_LOG_DOWNLOADS = getattr(settings, 'COURSE_DOCUMENTS_LOG_DOWNLOADS', True)
COURSE_DOCUMENTS_LOG_UPLOADS = getattr(settings, 'COURSE_DOCUMENTS_LOG_UPLOADS', True)

# Configuraciones de rendimiento
COURSE_DOCUMENTS_CACHE_TIMEOUT = getattr(settings, 'COURSE_DOCUMENTS_CACHE_TIMEOUT', 3600)  # 1 hora
COURSE_DOCUMENTS_THUMBNAIL_SIZE = getattr(settings, 'COURSE_DOCUMENTS_THUMBNAIL_SIZE', (200, 200))

# Configuraciones de acceso - ELIMINADAS las restricciones de velocidad
# COURSE_DOCUMENTS_DOWNLOAD_RATE_LIMIT eliminado - sin límites de velocidad

# Configuraciones de backup
COURSE_DOCUMENTS_BACKUP_ENABLED = getattr(settings, 'COURSE_DOCUMENTS_BACKUP_ENABLED', False)
COURSE_DOCUMENTS_BACKUP_PATH = getattr(settings, 'COURSE_DOCUMENTS_BACKUP_PATH', 'backups/course_documents/')

def get_upload_settings():
    """
    Retorna un diccionario con todas las configuraciones de subida
    """
    return {
        'max_file_size': COURSE_DOCUMENTS_MAX_FILE_SIZE,
        'max_file_size_mb': COURSE_DOCUMENTS_MAX_FILE_SIZE / (1024 * 1024),
        'allowed_extensions': COURSE_DOCUMENTS_ALLOWED_EXTENSIONS,
        'upload_path': COURSE_DOCUMENTS_UPLOAD_PATH,
        'scan_uploads': COURSE_DOCUMENTS_SCAN_UPLOADS,
        'auto_cleanup': COURSE_DOCUMENTS_AUTO_CLEANUP,
        'email_notifications': COURSE_DOCUMENTS_EMAIL_NOTIFICATIONS,
        'log_downloads': COURSE_DOCUMENTS_LOG_DOWNLOADS,
        'log_uploads': COURSE_DOCUMENTS_LOG_UPLOADS,
    }

def get_security_settings():
    """
    Retorna configuraciones de seguridad
    """
    return {
        'scan_uploads': COURSE_DOCUMENTS_SCAN_UPLOADS,
        'quarantine_path': COURSE_DOCUMENTS_QUARANTINE_PATH,
        # download_rate_limit eliminado - sin límites de velocidad
    }

def get_performance_settings():
    """
    Retorna configuraciones de rendimiento
    """
    return {
        'cache_timeout': COURSE_DOCUMENTS_CACHE_TIMEOUT,
        'thumbnail_size': COURSE_DOCUMENTS_THUMBNAIL_SIZE,
        'email_batch_size': COURSE_DOCUMENTS_EMAIL_BATCH_SIZE,
    }