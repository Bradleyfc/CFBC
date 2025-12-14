from django.core.management.base import BaseCommand, CommandError
from course_documents.file_service import FileService
from course_documents.models import CourseDocument
from principal.models import Curso


class Command(BaseCommand):
    help = 'Limpia archivos huérfanos y optimiza el almacenamiento de documentos de cursos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--curso-id',
            type=int,
            help='ID del curso específico a limpiar (opcional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué archivos se eliminarían sin eliminarlos realmente',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostrar estadísticas de almacenamiento',
        )

    def handle(self, *args, **options):
        curso_id = options.get('curso_id')
        dry_run = options.get('dry_run')
        show_stats = options.get('stats')

        # Mostrar estadísticas si se solicita
        if show_stats:
            self.show_storage_stats(curso_id)
            return

        # Validar curso si se especifica
        if curso_id:
            try:
                curso = Curso.objects.get(id=curso_id)
                self.stdout.write(f"Limpiando archivos para el curso: {curso.name}")
            except Curso.DoesNotExist:
                raise CommandError(f'El curso con ID {curso_id} no existe')
        else:
            self.stdout.write("Limpiando archivos de todos los cursos")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("MODO DRY-RUN: No se eliminarán archivos realmente")
            )

        # Realizar limpieza
        try:
            if not dry_run:
                deleted_count = FileService.cleanup_orphaned_files(curso_id)
                self.stdout.write(
                    self.style.SUCCESS(f'Limpieza completada: {deleted_count} archivos huérfanos eliminados')
                )
            else:
                # En modo dry-run, solo mostrar qué se eliminaría
                self.show_orphaned_files(curso_id)

        except Exception as e:
            raise CommandError(f'Error durante la limpieza: {str(e)}')

    def show_storage_stats(self, curso_id=None):
        """Muestra estadísticas de almacenamiento"""
        stats = FileService.get_storage_stats(curso_id)
        
        if curso_id:
            try:
                curso = Curso.objects.get(id=curso_id)
                self.stdout.write(f"\n=== Estadísticas para el curso: {curso.name} ===")
            except Curso.DoesNotExist:
                self.stdout.write(f"\n=== Estadísticas para curso ID: {curso_id} (no encontrado) ===")
        else:
            self.stdout.write("\n=== Estadísticas generales de almacenamiento ===")

        self.stdout.write(f"Total de documentos: {stats['total_documents']}")
        self.stdout.write(f"Espacio total utilizado: {stats['total_size_human']}")
        
        if stats['total_documents'] > 0:
            avg_size = FileService.format_file_size(stats['average_size_bytes'])
            self.stdout.write(f"Tamaño promedio por documento: {avg_size}")

        if stats['extensions']:
            self.stdout.write("\nDistribución por tipo de archivo:")
            for ext, count in sorted(stats['extensions'].items()):
                self.stdout.write(f"  .{ext}: {count} archivo{'s' if count != 1 else ''}")

    def show_orphaned_files(self, curso_id=None):
        """Muestra archivos huérfanos que se eliminarían"""
        from django.core.files.storage import default_storage
        from django.conf import settings
        import os
        import glob

        # Obtener archivos registrados
        if curso_id:
            registered_files = set(
                CourseDocument.objects.filter(
                    folder__curso_id=curso_id
                ).values_list('file', flat=True)
            )
            base_path = os.path.join(FileService.UPLOAD_PATH, f'curso_{curso_id}')
        else:
            registered_files = set(
                CourseDocument.objects.all().values_list('file', flat=True)
            )
            base_path = FileService.UPLOAD_PATH

        orphaned_files = []

        # Buscar archivos huérfanos
        if hasattr(default_storage, 'path') and default_storage.exists(base_path):
            full_base_path = default_storage.path(base_path)
            
            for file_path in glob.glob(os.path.join(full_base_path, '**', '*'), recursive=True):
                if os.path.isfile(file_path):
                    relative_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                    
                    if relative_path not in registered_files:
                        file_size = os.path.getsize(file_path)
                        orphaned_files.append((relative_path, file_size))

        if orphaned_files:
            self.stdout.write(f"\nArchivos huérfanos encontrados ({len(orphaned_files)}):")
            total_size = 0
            
            for file_path, file_size in orphaned_files:
                size_str = FileService.format_file_size(file_size)
                self.stdout.write(f"  {file_path} ({size_str})")
                total_size += file_size
            
            total_size_str = FileService.format_file_size(total_size)
            self.stdout.write(f"\nEspacio total a liberar: {total_size_str}")
        else:
            self.stdout.write("\nNo se encontraron archivos huérfanos.")