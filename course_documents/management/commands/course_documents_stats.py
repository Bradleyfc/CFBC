from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Avg
from course_documents.models import CourseDocument, DocumentFolder, DocumentAccess
from course_documents.file_service import FileService
from principal.models import Curso, CursoAcademico
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Genera estadísticas detalladas del sistema de documentos de cursos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--curso-id',
            type=int,
            help='ID del curso específico para estadísticas detalladas',
        )
        parser.add_argument(
            '--format',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Formato de salida (table, json, csv)',
        )
        parser.add_argument(
            '--include-users',
            action='store_true',
            help='Incluir estadísticas por usuario',
        )

    def handle(self, *args, **options):
        curso_id = options.get('curso_id')
        output_format = options.get('format')
        include_users = options.get('include_users')

        if curso_id:
            self.show_course_stats(curso_id, output_format, include_users)
        else:
            self.show_general_stats(output_format, include_users)

    def show_general_stats(self, output_format, include_users):
        """Muestra estadísticas generales del sistema"""
        
        # Estadísticas básicas
        total_courses = Curso.objects.count()
        courses_with_documents = Curso.objects.filter(document_folders__isnull=False).distinct().count()
        total_folders = DocumentFolder.objects.count()
        total_documents = CourseDocument.objects.count()
        total_downloads = DocumentAccess.objects.count()
        
        # Estadísticas de almacenamiento
        storage_stats = FileService.get_storage_stats()
        
        # Estadísticas por curso académico
        curso_academico_activo = CursoAcademico.objects.filter(activo=True).first()
        
        if output_format == 'table':
            self.stdout.write("\n" + "="*60)
            self.stdout.write("ESTADÍSTICAS GENERALES DEL SISTEMA DE DOCUMENTOS")
            self.stdout.write("="*60)
            
            self.stdout.write(f"\n📊 RESUMEN GENERAL:")
            self.stdout.write(f"  Total de cursos: {total_courses}")
            self.stdout.write(f"  Cursos con documentos: {courses_with_documents}")
            self.stdout.write(f"  Total de carpetas: {total_folders}")
            self.stdout.write(f"  Total de documentos: {total_documents}")
            self.stdout.write(f"  Total de descargas: {total_downloads}")
            
            if curso_academico_activo:
                active_courses = Curso.objects.filter(curso_academico=curso_academico_activo).count()
                self.stdout.write(f"  Cursos en período activo ({curso_academico_activo.nombre}): {active_courses}")
            
            self.stdout.write(f"\n💾 ALMACENAMIENTO:")
            self.stdout.write(f"  Espacio total utilizado: {storage_stats['total_size_human']}")
            self.stdout.write(f"  Tamaño promedio por documento: {FileService.format_file_size(storage_stats['average_size_bytes'])}")
            
            if storage_stats['extensions']:
                self.stdout.write(f"\n📁 TIPOS DE ARCHIVO:")
                for ext, count in sorted(storage_stats['extensions'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_documents * 100) if total_documents > 0 else 0
                    self.stdout.write(f"  .{ext}: {count} ({percentage:.1f}%)")
            
            # Top cursos por actividad
            self.show_top_courses_stats()
            
            if include_users:
                self.show_user_stats()
                
        elif output_format == 'json':
            import json
            data = {
                'general': {
                    'total_courses': total_courses,
                    'courses_with_documents': courses_with_documents,
                    'total_folders': total_folders,
                    'total_documents': total_documents,
                    'total_downloads': total_downloads,
                },
                'storage': storage_stats,
            }
            
            if include_users:
                data['users'] = self.get_user_stats_data()
                
            self.stdout.write(json.dumps(data, indent=2, ensure_ascii=False))

    def show_course_stats(self, curso_id, output_format, include_users):
        """Muestra estadísticas detalladas de un curso específico"""
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Curso con ID {curso_id} no encontrado'))
            return

        # Estadísticas del curso
        folders = DocumentFolder.objects.filter(curso=curso)
        documents = CourseDocument.objects.filter(folder__curso=curso)
        downloads = DocumentAccess.objects.filter(document__folder__curso=curso)
        
        storage_stats = FileService.get_storage_stats(curso_id)
        
        if output_format == 'table':
            self.stdout.write(f"\n" + "="*60)
            self.stdout.write(f"ESTADÍSTICAS DEL CURSO: {curso.name}")
            self.stdout.write("="*60)
            
            self.stdout.write(f"\n📚 INFORMACIÓN DEL CURSO:")
            self.stdout.write(f"  Nombre: {curso.name}")
            self.stdout.write(f"  Profesor: {curso.teacher.get_full_name() or curso.teacher.username}")
            self.stdout.write(f"  Curso académico: {curso.curso_academico.nombre if curso.curso_academico else 'No asignado'}")
            self.stdout.write(f"  Estado: {curso.get_status_display()}")
            
            # Estudiantes inscritos
            from principal.models import Matriculas
            estudiantes = Matriculas.objects.filter(course=curso, activo=True).count()
            self.stdout.write(f"  Estudiantes inscritos: {estudiantes}")
            
            self.stdout.write(f"\n📊 ESTADÍSTICAS DE DOCUMENTOS:")
            self.stdout.write(f"  Carpetas: {folders.count()}")
            self.stdout.write(f"  Documentos: {documents.count()}")
            self.stdout.write(f"  Descargas totales: {downloads.count()}")
            
            if documents.exists():
                avg_downloads = downloads.count() / documents.count()
                self.stdout.write(f"  Promedio de descargas por documento: {avg_downloads:.1f}")
            
            self.stdout.write(f"\n💾 ALMACENAMIENTO:")
            self.stdout.write(f"  Espacio utilizado: {storage_stats['total_size_human']}")
            
            if storage_stats['extensions']:
                self.stdout.write(f"\n📁 TIPOS DE ARCHIVO:")
                for ext, count in storage_stats['extensions'].items():
                    self.stdout.write(f"  .{ext}: {count}")
            
            # Documentos más descargados
            popular_docs = documents.annotate(
                download_count=Count('documentaccess')
            ).order_by('-download_count')[:5]
            
            if popular_docs:
                self.stdout.write(f"\n🔥 DOCUMENTOS MÁS DESCARGADOS:")
                for doc in popular_docs:
                    self.stdout.write(f"  {doc.name}: {doc.download_count} descargas")

    def show_top_courses_stats(self):
        """Muestra estadísticas de los cursos más activos"""
        top_courses = Curso.objects.annotate(
            document_count=Count('document_folders__documents'),
            download_count=Count('document_folders__documents__documentaccess')
        ).filter(document_count__gt=0).order_by('-download_count')[:5]
        
        if top_courses:
            self.stdout.write(f"\n🏆 TOP 5 CURSOS POR ACTIVIDAD:")
            for i, curso in enumerate(top_courses, 1):
                teacher_name = curso.teacher.get_full_name() or curso.teacher.username
                self.stdout.write(f"  {i}. {curso.name} ({teacher_name})")
                self.stdout.write(f"     Documentos: {curso.document_count}, Descargas: {curso.download_count}")

    def show_user_stats(self):
        """Muestra estadísticas por usuario"""
        # Profesores más activos
        active_teachers = User.objects.filter(
            groups__name='Profesores',
            coursedocument__isnull=False
        ).annotate(
            document_count=Count('coursedocument')
        ).order_by('-document_count')[:5]
        
        if active_teachers:
            self.stdout.write(f"\n👨‍🏫 PROFESORES MÁS ACTIVOS:")
            for teacher in active_teachers:
                name = teacher.get_full_name() or teacher.username
                self.stdout.write(f"  {name}: {teacher.document_count} documentos subidos")
        
        # Estudiantes más activos
        active_students = User.objects.filter(
            groups__name='Estudiantes',
            documentaccess__isnull=False
        ).annotate(
            download_count=Count('documentaccess')
        ).order_by('-download_count')[:5]
        
        if active_students:
            self.stdout.write(f"\n👨‍🎓 ESTUDIANTES MÁS ACTIVOS:")
            for student in active_students:
                name = student.get_full_name() or student.username
                self.stdout.write(f"  {name}: {student.download_count} descargas")

    def get_user_stats_data(self):
        """Obtiene datos de estadísticas de usuarios para JSON"""
        active_teachers = User.objects.filter(
            groups__name='Profesores',
            coursedocument__isnull=False
        ).annotate(
            document_count=Count('coursedocument')
        ).order_by('-document_count')[:10]
        
        active_students = User.objects.filter(
            groups__name='Estudiantes',
            documentaccess__isnull=False
        ).annotate(
            download_count=Count('documentaccess')
        ).order_by('-download_count')[:10]
        
        return {
            'active_teachers': [
                {
                    'name': teacher.get_full_name() or teacher.username,
                    'document_count': teacher.document_count
                }
                for teacher in active_teachers
            ],
            'active_students': [
                {
                    'name': student.get_full_name() or student.username,
                    'download_count': student.download_count
                }
                for student in active_students
            ]
        }