"""
Middleware para el sistema de documentos de cursos
"""

import time
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)


# Middleware de rate limiting ELIMINADO COMPLETAMENTE
# Los profesores y estudiantes necesitan libertad total para subir y descargar archivos
# Solo se mantiene el control de tamaño de archivo (10MB máximo) y validaciones de seguridad


class FileSecurityMiddleware(MiddlewareMixin):
    """
    Middleware para seguridad adicional en archivos
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Verificar headers sospechosos en subidas
        if request.method == 'POST' and self._is_file_upload(request):
            if not self._validate_upload_headers(request):
                logger.warning(f"Suspicious upload headers from {request.META.get('REMOTE_ADDR')}")
                return HttpResponseTooManyRequests("Petición sospechosa detectada")
        
        return None
    
    def _is_file_upload(self, request):
        """Determina si la petición incluye archivos"""
        return bool(request.FILES)
    
    def _validate_upload_headers(self, request):
        """Valida headers de la petición de subida"""
        # Verificar User-Agent sospechoso
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
        
        if any(agent in user_agent for agent in suspicious_agents):
            return False
        
        # Verificar Content-Type
        content_type = request.META.get('CONTENT_TYPE', '')
        if not content_type.startswith('multipart/form-data'):
            return False
        
        return True


class FileAuditMiddleware(MiddlewareMixin):
    """
    Middleware para auditoría de operaciones con archivos
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Registrar operaciones con archivos
        if self._should_audit(request):
            self._log_file_operation(request)
        
        return None
    
    def _should_audit(self, request):
        """Determina si se debe auditar la operación"""
        from .settings import COURSE_DOCUMENTS_LOG_UPLOADS, COURSE_DOCUMENTS_LOG_DOWNLOADS
        
        # Auditar subidas
        if request.method == 'POST' and request.FILES and COURSE_DOCUMENTS_LOG_UPLOADS:
            return True
        
        # Auditar descargas (sin restricciones de velocidad, solo logging)
        if (request.method == 'GET' and 
            '/course-documents/' in request.path and 
            '/download/' in request.path and 
            COURSE_DOCUMENTS_LOG_DOWNLOADS):
            return True
        
        return False
    
    def _log_file_operation(self, request):
        """Registra la operación con archivos"""
        try:
            operation_type = 'upload' if request.FILES else 'download'
            user_id = request.user.id if request.user.is_authenticated else None
            ip_address = self._get_client_ip(request)
            
            logger.info(f"File {operation_type} - User: {user_id}, IP: {ip_address}, Path: {request.path}")
            
        except Exception as e:
            logger.error(f"Error logging file operation: {str(e)}")
    
    def _get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip