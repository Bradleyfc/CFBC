"""
Servicio de monitoreo para el sistema de documentos
"""

import os
import psutil
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
from .models import CourseDocument, DocumentAccess, AuditLog
from .file_service import FileService
import logging

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Servicio para monitorear el sistema de documentos
    """
    
    @classmethod
    def get_system_health(cls):
        """
        Obtiene el estado de salud del sistema
        
        Returns:
            Diccionario con métricas de salud
        """
        try:
            health = {
                'timestamp': timezone.now(),
                'overall_status': 'healthy',
                'issues': [],
                'metrics': {}
            }
            
            # Verificar espacio en disco
            disk_health = cls._check_disk_space()
            health['metrics']['disk'] = disk_health
            if disk_health['status'] != 'healthy':
                health['issues'].append(f"Espacio en disco: {disk_health['message']}")
                health['overall_status'] = 'warning'
            
            # Verificar integridad de archivos
            file_health = cls._check_file_integrity()
            health['metrics']['files'] = file_health
            if file_health['status'] != 'healthy':
                health['issues'].append(f"Integridad de archivos: {file_health['message']}")
                health['overall_status'] = 'critical'
            
            # Verificar rendimiento
            performance_health = cls._check_performance()
            health['metrics']['performance'] = performance_health
            if performance_health['status'] != 'healthy':
                health['issues'].append(f"Rendimiento: {performance_health['message']}")
                if health['overall_status'] == 'healthy':
                    health['overall_status'] = 'warning'
            
            # Verificar seguridad
            security_health = cls._check_security()
            health['metrics']['security'] = security_health
            if security_health['status'] != 'healthy':
                health['issues'].append(f"Seguridad: {security_health['message']}")
                health['overall_status'] = 'critical'
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {
                'timestamp': timezone.now(),
                'overall_status': 'error',
                'issues': [f"Error en monitoreo: {str(e)}"],
                'metrics': {}
            }
    
    @classmethod
    def _check_disk_space(cls):
        """Verifica el espacio disponible en disco"""
        try:
            # Obtener información del disco donde está MEDIA_ROOT
            media_path = settings.MEDIA_ROOT
            disk_usage = psutil.disk_usage(media_path)
            
            # Calcular porcentajes
            used_percent = (disk_usage.used / disk_usage.total) * 100
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            # Determinar estado
            if used_percent > 90:
                status = 'critical'
                message = f"Espacio crítico: {used_percent:.1f}% usado"
            elif used_percent > 80:
                status = 'warning'
                message = f"Espacio bajo: {used_percent:.1f}% usado"
            else:
                status = 'healthy'
                message = f"Espacio suficiente: {free_percent:.1f}% libre"
            
            return {
                'status': status,
                'message': message,
                'total_bytes': disk_usage.total,
                'used_bytes': disk_usage.used,
                'free_bytes': disk_usage.free,
                'used_percent': used_percent,
                'free_percent': free_percent,
                'total_human': FileService.format_file_size(disk_usage.total),
                'used_human': FileService.format_file_size(disk_usage.used),
                'free_human': FileService.format_file_size(disk_usage.free),
            }
            
        except Exception as e:
            logger.error(f"Error checking disk space: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error verificando espacio: {str(e)}"
            }
    
    @classmethod
    def _check_file_integrity(cls):
        """Verifica la integridad de los archivos"""
        try:
            total_documents = CourseDocument.objects.count()
            missing_files = 0
            corrupted_files = 0
            
            # Verificar una muestra de archivos (para no sobrecargar el sistema)
            sample_size = min(100, total_documents)
            documents = CourseDocument.objects.order_by('?')[:sample_size]
            
            for doc in documents:
                if not doc.file:
                    missing_files += 1
                    continue
                
                # Verificar si el archivo existe
                if not default_storage.exists(doc.file.name):
                    missing_files += 1
                    continue
                
                # Verificar tamaño del archivo
                try:
                    actual_size = default_storage.size(doc.file.name)
                    if doc.file_size and actual_size != doc.file_size:
                        corrupted_files += 1
                except:
                    corrupted_files += 1
            
            # Calcular porcentajes
            if sample_size > 0:
                missing_percent = (missing_files / sample_size) * 100
                corrupted_percent = (corrupted_files / sample_size) * 100
            else:
                missing_percent = 0
                corrupted_percent = 0
            
            # Determinar estado
            if missing_percent > 5 or corrupted_percent > 5:
                status = 'critical'
                message = f"{missing_files} archivos faltantes, {corrupted_files} corruptos"
            elif missing_percent > 1 or corrupted_percent > 1:
                status = 'warning'
                message = f"{missing_files} archivos faltantes, {corrupted_files} corruptos"
            else:
                status = 'healthy'
                message = "Integridad de archivos correcta"
            
            return {
                'status': status,
                'message': message,
                'total_checked': sample_size,
                'missing_files': missing_files,
                'corrupted_files': corrupted_files,
                'missing_percent': missing_percent,
                'corrupted_percent': corrupted_percent,
            }
            
        except Exception as e:
            logger.error(f"Error checking file integrity: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error verificando integridad: {str(e)}"
            }
    
    @classmethod
    def _check_performance(cls):
        """Verifica el rendimiento del sistema"""
        try:
            # Verificar tiempo de respuesta promedio
            cache_key = 'document_performance_metrics'
            metrics = cache.get(cache_key, {})
            
            # Obtener estadísticas de acceso recientes
            recent_accesses = DocumentAccess.objects.filter(
                accessed_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            # Verificar carga del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Determinar estado basado en métricas
            issues = []
            
            if cpu_percent > 80:
                issues.append(f"CPU alta: {cpu_percent:.1f}%")
            
            if memory.percent > 85:
                issues.append(f"Memoria alta: {memory.percent:.1f}%")
            
            if recent_accesses > 1000:  # Más de 1000 accesos por hora
                issues.append(f"Carga alta: {recent_accesses} accesos/hora")
            
            # Determinar estado
            if len(issues) > 2:
                status = 'critical'
                message = "; ".join(issues)
            elif len(issues) > 0:
                status = 'warning'
                message = "; ".join(issues)
            else:
                status = 'healthy'
                message = "Rendimiento normal"
            
            return {
                'status': status,
                'message': message,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'recent_accesses': recent_accesses,
                'issues': issues,
            }
            
        except Exception as e:
            logger.error(f"Error checking performance: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error verificando rendimiento: {str(e)}"
            }
    
    @classmethod
    def _check_security(cls):
        """Verifica aspectos de seguridad"""
        try:
            # Verificar intentos de acceso no autorizado recientes
            recent_unauthorized = AuditLog.objects.filter(
                action='unauthorized_access',
                timestamp__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Verificar archivos sospechosos subidos recientemente
            recent_uploads = CourseDocument.objects.filter(
                uploaded_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Verificar patrones sospechosos
            issues = []
            
            if recent_unauthorized > 10:
                issues.append(f"{recent_unauthorized} accesos no autorizados en 24h")
            
            if recent_uploads > 100:  # Más de 100 subidas por día podría ser sospechoso
                issues.append(f"Actividad de subida alta: {recent_uploads} archivos/día")
            
            # Verificar permisos de archivos (solo en sistemas Unix)
            if hasattr(os, 'stat') and os.name != 'nt':
                try:
                    media_stat = os.stat(settings.MEDIA_ROOT)
                    if media_stat.st_mode & 0o002:  # World writable
                        issues.append("Directorio de medios escribible por todos")
                except:
                    pass
            
            # Determinar estado
            if len(issues) > 1:
                status = 'critical'
                message = "; ".join(issues)
            elif len(issues) > 0:
                status = 'warning'
                message = "; ".join(issues)
            else:
                status = 'healthy'
                message = "Sin problemas de seguridad detectados"
            
            return {
                'status': status,
                'message': message,
                'recent_unauthorized': recent_unauthorized,
                'recent_uploads': recent_uploads,
                'issues': issues,
            }
            
        except Exception as e:
            logger.error(f"Error checking security: {str(e)}")
            return {
                'status': 'error',
                'message': f"Error verificando seguridad: {str(e)}"
            }
    
    @classmethod
    def get_usage_statistics(cls, days=30):
        """
        Obtiene estadísticas de uso del sistema
        
        Args:
            days: Número de días para las estadísticas
            
        Returns:
            Diccionario con estadísticas de uso
        """
        try:
            since_date = timezone.now() - timedelta(days=days)
            
            # Estadísticas de documentos
            total_documents = CourseDocument.objects.count()
            recent_documents = CourseDocument.objects.filter(
                uploaded_at__gte=since_date
            ).count()
            
            # Estadísticas de acceso
            total_accesses = DocumentAccess.objects.count()
            recent_accesses = DocumentAccess.objects.filter(
                accessed_at__gte=since_date
            ).count()
            
            # Documentos más populares
            popular_documents = CourseDocument.objects.annotate(
                access_count=models.Count('documentaccess')
            ).order_by('-access_count')[:10]
            
            # Usuarios más activos
            from django.contrib.auth.models import User
            from django.db.models import Count
            
            active_uploaders = User.objects.filter(
                coursedocument__uploaded_at__gte=since_date
            ).annotate(
                upload_count=Count('coursedocument')
            ).order_by('-upload_count')[:10]
            
            active_downloaders = User.objects.filter(
                documentaccess__accessed_at__gte=since_date
            ).annotate(
                download_count=Count('documentaccess')
            ).order_by('-download_count')[:10]
            
            return {
                'period_days': days,
                'since_date': since_date,
                'documents': {
                    'total': total_documents,
                    'recent': recent_documents,
                    'growth_rate': (recent_documents / max(total_documents - recent_documents, 1)) * 100
                },
                'accesses': {
                    'total': total_accesses,
                    'recent': recent_accesses,
                    'daily_average': recent_accesses / days if days > 0 else 0
                },
                'popular_documents': [
                    {
                        'name': doc.name,
                        'course': doc.folder.curso.name,
                        'access_count': doc.access_count
                    }
                    for doc in popular_documents
                ],
                'active_uploaders': [
                    {
                        'name': user.get_full_name() or user.username,
                        'upload_count': user.upload_count
                    }
                    for user in active_uploaders
                ],
                'active_downloaders': [
                    {
                        'name': user.get_full_name() or user.username,
                        'download_count': user.download_count
                    }
                    for user in active_downloaders
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting usage statistics: {str(e)}")
            return {
                'error': str(e)
            }
    
    @classmethod
    def generate_health_report(cls):
        """
        Genera un reporte completo de salud del sistema
        
        Returns:
            Diccionario con reporte completo
        """
        try:
            report = {
                'generated_at': timezone.now(),
                'system_health': cls.get_system_health(),
                'usage_statistics': cls.get_usage_statistics(),
                'storage_statistics': FileService.get_storage_stats(),
            }
            
            # Agregar recomendaciones basadas en el estado
            recommendations = []
            
            health = report['system_health']
            if health['overall_status'] == 'critical':
                recommendations.append("Atención inmediata requerida para problemas críticos")
            elif health['overall_status'] == 'warning':
                recommendations.append("Revisar y resolver advertencias del sistema")
            
            # Recomendaciones específicas
            if 'disk' in health['metrics']:
                disk = health['metrics']['disk']
                if disk.get('used_percent', 0) > 80:
                    recommendations.append("Considerar limpiar archivos antiguos o expandir almacenamiento")
            
            if 'files' in health['metrics']:
                files = health['metrics']['files']
                if files.get('missing_files', 0) > 0:
                    recommendations.append("Ejecutar verificación de integridad y restaurar archivos faltantes")
            
            report['recommendations'] = recommendations
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report: {str(e)}")
            return {
                'generated_at': timezone.now(),
                'error': str(e)
            }