from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from course_documents.backup_service import BackupService
import os


class Command(BaseCommand):
    help = 'Gestiona backups del sistema de documentos de cursos'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['create', 'restore', 'cleanup', 'info', 'list'],
            help='Acción a realizar'
        )
        
        parser.add_argument(
            '--type',
            choices=['full', 'incremental'],
            default='full',
            help='Tipo de backup (solo para create)'
        )
        
        parser.add_argument(
            '--since',
            type=str,
            help='Fecha desde la cual hacer backup incremental (formato: YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--file',
            type=str,
            help='Archivo de backup para restaurar o obtener info'
        )
        
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Sobrescribir archivos existentes al restaurar'
        )
        
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Días de backups a mantener en cleanup (default: 30)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'create':
                self.create_backup(options)
            elif action == 'restore':
                self.restore_backup(options)
            elif action == 'cleanup':
                self.cleanup_backups(options)
            elif action == 'info':
                self.show_backup_info(options)
            elif action == 'list':
                self.list_backups()
                
        except Exception as e:
            raise CommandError(f'Error ejecutando acción {action}: {str(e)}')

    def create_backup(self, options):
        """Crea un backup"""
        backup_type = options['type']
        
        self.stdout.write(f"Creando backup {backup_type}...")
        
        if backup_type == 'full':
            backup_file = BackupService.create_full_backup()
            
        elif backup_type == 'incremental':
            since_str = options.get('since')
            if not since_str:
                # Por defecto, backup incremental desde hace 7 días
                since_date = timezone.now() - timedelta(days=7)
            else:
                try:
                    since_date = datetime.strptime(since_str, '%Y-%m-%d')
                    since_date = timezone.make_aware(since_date)
                except ValueError:
                    raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')
            
            backup_file = BackupService.create_incremental_backup(since_date)
            
            if not backup_file:
                self.stdout.write(
                    self.style.WARNING('No hay documentos para respaldar en el período especificado')
                )
                return
        
        if backup_file:
            file_size = BackupService.get_backup_info(backup_file)['file_size_human']
            self.stdout.write(
                self.style.SUCCESS(f'Backup creado exitosamente: {backup_file} ({file_size})')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Error creando el backup')
            )

    def restore_backup(self, options):
        """Restaura un backup"""
        backup_file = options.get('file')
        if not backup_file:
            raise CommandError('Debe especificar el archivo de backup con --file')
        
        if not os.path.exists(backup_file):
            raise CommandError(f'Archivo de backup no encontrado: {backup_file}')
        
        overwrite = options.get('overwrite', False)
        
        self.stdout.write(f"Restaurando backup desde: {backup_file}")
        
        if overwrite:
            self.stdout.write(
                self.style.WARNING('ADVERTENCIA: Se sobrescribirán archivos existentes')
            )
        
        # Confirmar acción
        confirm = input('¿Continuar con la restauración? (s/N): ')
        if confirm.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            self.stdout.write('Restauración cancelada')
            return
        
        restored_count = BackupService.restore_backup(backup_file, overwrite)
        
        self.stdout.write(
            self.style.SUCCESS(f'Restauración completada: {restored_count} archivos restaurados')
        )

    def cleanup_backups(self, options):
        """Limpia backups antiguos"""
        keep_days = options.get('keep_days', 30)
        
        self.stdout.write(f"Limpiando backups más antiguos que {keep_days} días...")
        
        deleted_count = BackupService.cleanup_old_backups(keep_days)
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Limpieza completada: {deleted_count} backups antiguos eliminados')
            )
        else:
            self.stdout.write('No hay backups antiguos para eliminar')

    def show_backup_info(self, options):
        """Muestra información de un backup"""
        backup_file = options.get('file')
        if not backup_file:
            raise CommandError('Debe especificar el archivo de backup con --file')
        
        info = BackupService.get_backup_info(backup_file)
        
        if not info:
            raise CommandError(f'No se pudo obtener información del backup: {backup_file}')
        
        self.stdout.write(f"\n=== INFORMACIÓN DEL BACKUP ===")
        self.stdout.write(f"Archivo: {info['file_path']}")
        self.stdout.write(f"Tamaño: {info['file_size_human']}")
        self.stdout.write(f"Creado: {info['created_at']}")
        self.stdout.write(f"Modificado: {info['modified_at']}")
        self.stdout.write(f"Archivos en backup: {info['file_count']}")
        
        if info.get('metadata'):
            metadata = info['metadata']
            self.stdout.write(f"\n=== METADATOS ===")
            self.stdout.write(f"Tipo: {metadata.get('backup_type', 'desconocido')}")
            self.stdout.write(f"Versión: {metadata.get('version', 'desconocida')}")
            self.stdout.write(f"Total documentos: {metadata.get('total_documents', 0)}")
            self.stdout.write(f"Total carpetas: {metadata.get('total_folders', 0)}")
            
            if metadata.get('since_date'):
                self.stdout.write(f"Desde fecha: {metadata['since_date']}")
            
            if metadata.get('storage_stats'):
                stats = metadata['storage_stats']
                self.stdout.write(f"Espacio total: {stats.get('total_size_human', 'desconocido')}")

    def list_backups(self):
        """Lista todos los backups disponibles"""
        from course_documents.settings import COURSE_DOCUMENTS_BACKUP_PATH
        from django.conf import settings
        
        backup_dir = os.path.join(settings.MEDIA_ROOT, COURSE_DOCUMENTS_BACKUP_PATH)
        
        if not os.path.exists(backup_dir):
            self.stdout.write('No hay directorio de backups')
            return
        
        backup_files = [
            f for f in os.listdir(backup_dir) 
            if f.startswith('course_documents_backup_') and f.endswith('.zip')
        ]
        
        if not backup_files:
            self.stdout.write('No hay backups disponibles')
            return
        
        self.stdout.write(f"\n=== BACKUPS DISPONIBLES ({len(backup_files)}) ===")
        
        # Ordenar por fecha de modificación (más reciente primero)
        backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)), reverse=True)
        
        for filename in backup_files:
            file_path = os.path.join(backup_dir, filename)
            info = BackupService.get_backup_info(file_path)
            
            if info:
                backup_type = 'desconocido'
                if info.get('metadata'):
                    backup_type = info['metadata'].get('backup_type', 'desconocido')
                
                self.stdout.write(
                    f"  {filename} ({info['file_size_human']}) - {backup_type} - {info['created_at']}"
                )
            else:
                self.stdout.write(f"  {filename} (info no disponible)")