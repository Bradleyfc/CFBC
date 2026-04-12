"""
Servicio de backup para documentos de cursos
"""

import os
import shutil
import zipfile
import json
from datetime import datetime, timedelta
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.management.base import BaseCommand
from .models import CourseDocument, DocumentFolder
from .file_service import FileService
import logging

logger = logging.getLogger(__name__)


class BackupService:
    """
    Servicio para crear y gestionar backups de documentos
    """
    
    @classmethod
    def create_full_backup(cls, backup_path=None):
        """
        Crea un backup completo de todos los documentos
        
        Args:
            backup_path: Ruta donde crear el backup (opcional)
            
        Returns:
            Ruta del archivo de backup creado
        """
        try:
            from .settings import COURSE_DOCUMENTS_BACKUP_PATH
            
            if not backup_path:
                backup_path = COURSE_DOCUMENTS_BACKUP_PATH
            
            # Crear directorio de backup si no existe
            backup_dir = os.path.join(settings.MEDIA_ROOT, backup_path)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nombre del archivo de backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"course_documents_backup_{timestamp}.zip"
            backup_file_path = os.path.join(backup_dir, backup_filename)
            
            # Crear archivo ZIP
            with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Agregar metadatos del backup
                metadata = cls._create_backup_metadata()
                backup_zip.writestr('backup_metadata.json', json.dumps(metadata, indent=2, default=str))
                
                # Agregar todos los archivos de documentos
                documents = CourseDocument.objects.all()
                
                for doc in documents:
                    if doc.file and default_storage.exists(doc.file.name):
                        try:
                            # Leer archivo
                            with default_storage.open(doc.file.name, 'rb') as file_obj:
                                file_content = file_obj.read()
                            
                            # Agregar al ZIP con estructura de carpetas
                            zip_path = cls._get_backup_file_path(doc)
                            backup_zip.writestr(zip_path, file_content)
                            
                        except Exception as e:
                            logger.error(f"Error backing up file {doc.file.name}: {str(e)}")
                            continue
            
            logger.info(f"Full backup created successfully: {backup_file_path}")
            return backup_file_path
            
        except Exception as e:
            logger.error(f"Error creating full backup: {str(e)}")
            raise
    
    @classmethod
    def create_incremental_backup(cls, since_date, backup_path=None):
        """
        Crea un backup incremental desde una fecha específica
        
        Args:
            since_date: Fecha desde la cual hacer el backup
            backup_path: Ruta donde crear el backup (opcional)
            
        Returns:
            Ruta del archivo de backup creado
        """
        try:
            from .settings import COURSE_DOCUMENTS_BACKUP_PATH
            
            if not backup_path:
                backup_path = COURSE_DOCUMENTS_BACKUP_PATH
            
            # Crear directorio de backup si no existe
            backup_dir = os.path.join(settings.MEDIA_ROOT, backup_path)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nombre del archivo de backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            since_str = since_date.strftime('%Y%m%d')
            backup_filename = f"course_documents_incremental_{since_str}_to_{timestamp}.zip"
            backup_file_path = os.path.join(backup_dir, backup_filename)
            
            # Obtener documentos modificados desde la fecha
            documents = CourseDocument.objects.filter(uploaded_at__gte=since_date)
            
            if not documents.exists():
                logger.info("No documents to backup in incremental backup")
                return None
            
            # Crear archivo ZIP
            with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Agregar metadatos del backup
                metadata = cls._create_backup_metadata(incremental=True, since_date=since_date)
                backup_zip.writestr('backup_metadata.json', json.dumps(metadata, indent=2, default=str))
                
                # Agregar archivos modificados
                for doc in documents:
                    if doc.file and default_storage.exists(doc.file.name):
                        try:
                            # Leer archivo
                            with default_storage.open(doc.file.name, 'rb') as file_obj:
                                file_content = file_obj.read()
                            
                            # Agregar al ZIP
                            zip_path = cls._get_backup_file_path(doc)
                            backup_zip.writestr(zip_path, file_content)
                            
                        except Exception as e:
                            logger.error(f"Error backing up file {doc.file.name}: {str(e)}")
                            continue
            
            logger.info(f"Incremental backup created successfully: {backup_file_path}")
            return backup_file_path
            
        except Exception as e:
            logger.error(f"Error creating incremental backup: {str(e)}")
            raise
    
    @classmethod
    def restore_backup(cls, backup_file_path, overwrite=False):
        """
        Restaura un backup
        
        Args:
            backup_file_path: Ruta del archivo de backup
            overwrite: Si sobrescribir archivos existentes
            
        Returns:
            Número de archivos restaurados
        """
        try:
            if not os.path.exists(backup_file_path):
                raise FileNotFoundError(f"Backup file not found: {backup_file_path}")
            
            restored_count = 0
            
            with zipfile.ZipFile(backup_file_path, 'r') as backup_zip:
                # Leer metadatos
                try:
                    metadata_content = backup_zip.read('backup_metadata.json')
                    metadata = json.loads(metadata_content.decode('utf-8'))
                    logger.info(f"Restoring backup created on {metadata.get('created_at')}")
                except:
                    logger.warning("Could not read backup metadata")
                
                # Restaurar archivos
                for file_info in backup_zip.filelist:
                    if file_info.filename == 'backup_metadata.json':
                        continue
                    
                    try:
                        # Extraer archivo
                        file_content = backup_zip.read(file_info.filename)
                        
                        # Determinar ruta de destino
                        restore_path = cls._get_restore_path(file_info.filename)
                        
                        # Verificar si ya existe
                        if default_storage.exists(restore_path) and not overwrite:
                            logger.info(f"Skipping existing file: {restore_path}")
                            continue
                        
                        # Crear directorio si no existe
                        restore_dir = os.path.dirname(restore_path)
                        if restore_dir:
                            full_restore_dir = os.path.join(settings.MEDIA_ROOT, restore_dir)
                            os.makedirs(full_restore_dir, exist_ok=True)
                        
                        # Escribir archivo
                        with default_storage.open(restore_path, 'wb') as dest_file:
                            dest_file.write(file_content)
                        
                        restored_count += 1
                        logger.info(f"Restored file: {restore_path}")
                        
                    except Exception as e:
                        logger.error(f"Error restoring file {file_info.filename}: {str(e)}")
                        continue
            
            logger.info(f"Backup restoration completed: {restored_count} files restored")
            return restored_count
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            raise
    
    @classmethod
    def cleanup_old_backups(cls, keep_days=30, backup_path=None):
        """
        Limpia backups antiguos
        
        Args:
            keep_days: Días de backups a mantener
            backup_path: Ruta de backups (opcional)
            
        Returns:
            Número de backups eliminados
        """
        try:
            from .settings import COURSE_DOCUMENTS_BACKUP_PATH
            
            if not backup_path:
                backup_path = COURSE_DOCUMENTS_BACKUP_PATH
            
            backup_dir = os.path.join(settings.MEDIA_ROOT, backup_path)
            
            if not os.path.exists(backup_dir):
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_count = 0
            
            for filename in os.listdir(backup_dir):
                if not filename.startswith('course_documents_backup_'):
                    continue
                
                file_path = os.path.join(backup_dir, filename)
                
                # Verificar fecha de modificación
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {filename}")
                    except Exception as e:
                        logger.error(f"Error deleting backup {filename}: {str(e)}")
            
            logger.info(f"Backup cleanup completed: {deleted_count} old backups deleted")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
            return 0
    
    @classmethod
    def _create_backup_metadata(cls, incremental=False, since_date=None):
        """Crea metadatos del backup"""
        metadata = {
            'created_at': datetime.now(),
            'backup_type': 'incremental' if incremental else 'full',
            'version': '1.0',
            'total_documents': CourseDocument.objects.count(),
            'total_folders': DocumentFolder.objects.count(),
        }
        
        if incremental and since_date:
            metadata['since_date'] = since_date
            metadata['incremental_documents'] = CourseDocument.objects.filter(
                uploaded_at__gte=since_date
            ).count()
        
        # Estadísticas de almacenamiento
        storage_stats = FileService.get_storage_stats()
        metadata['storage_stats'] = storage_stats
        
        return metadata
    
    @classmethod
    def _get_backup_file_path(cls, document):
        """Genera la ruta del archivo en el backup"""
        curso_name = document.folder.curso.name.replace(' ', '_').replace('/', '_')
        folder_name = document.folder.name.replace(' ', '_').replace('/', '_')
        
        return f"courses/{curso_name}/folders/{folder_name}/{document.file.name.split('/')[-1]}"
    
    @classmethod
    def _get_restore_path(cls, backup_file_path):
        """Convierte la ruta del backup a ruta de restauración"""
        # Simplificado: mantener la estructura original
        return backup_file_path.replace('courses/', 'course_documents/')
    
    @classmethod
    def get_backup_info(cls, backup_file_path):
        """
        Obtiene información de un archivo de backup
        
        Args:
            backup_file_path: Ruta del archivo de backup
            
        Returns:
            Diccionario con información del backup
        """
        try:
            if not os.path.exists(backup_file_path):
                return None
            
            info = {
                'file_path': backup_file_path,
                'file_size': os.path.getsize(backup_file_path),
                'file_size_human': FileService.format_file_size(os.path.getsize(backup_file_path)),
                'created_at': datetime.fromtimestamp(os.path.getctime(backup_file_path)),
                'modified_at': datetime.fromtimestamp(os.path.getmtime(backup_file_path)),
            }
            
            # Leer metadatos si están disponibles
            try:
                with zipfile.ZipFile(backup_file_path, 'r') as backup_zip:
                    metadata_content = backup_zip.read('backup_metadata.json')
                    metadata = json.loads(metadata_content.decode('utf-8'))
                    info['metadata'] = metadata
                    
                    # Contar archivos en el backup
                    file_count = len([f for f in backup_zip.filelist if f.filename != 'backup_metadata.json'])
                    info['file_count'] = file_count
                    
            except:
                info['metadata'] = None
                info['file_count'] = 0
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting backup info: {str(e)}")
            return None