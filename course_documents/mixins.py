from django.contrib.auth.models import Group
from .indicator_service import ContentIndicatorService, IndicatorTemplateContext


class DocumentsProfileMixin:
    """
    Mixin para agregar funcionalidad de documentos al perfil de usuario
    """
    
    def get_context_data(self, **kwargs):
        """
        Extiende el contexto con información de documentos e indicadores
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_authenticated:
            return context
        
        # Obtener grupo del usuario
        user_group = user.groups.first()
        group_name = user_group.name if user_group else None
        
        if group_name == 'Profesores':
            # Agregar contexto para profesores
            context = self._add_teacher_context(context, user)
            
        elif group_name == 'Estudiantes':
            # Agregar contexto para estudiantes
            context = self._add_student_context(context, user)
        
        return context
    
    def _add_teacher_context(self, context, teacher):
        """
        Agrega contexto específico para profesores
        
        Args:
            context: Contexto del template
            teacher: Usuario profesor
            
        Returns:
            Contexto actualizado
        """
        # Agregar estadísticas de indicadores para cursos del profesor
        if 'assigned_courses' in context:
            for course in context['assigned_courses']:
                # Agregar estadísticas de indicadores
                course.indicator_stats = ContentIndicatorService.get_indicator_stats_for_course(course)
                
                # Agregar URL del dashboard del profesor
                course.teacher_dashboard_url = f'/course-documents/teacher/{course.id}/'
                
                # Verificar si el curso tiene carpetas/documentos
                from .models import DocumentFolder
                course.has_documents = DocumentFolder.objects.filter(curso=course).exists()
        
        # Agregar estadísticas generales del profesor
        if 'assigned_courses' in context:
            total_courses = len(context['assigned_courses'])
            courses_with_documents = sum(1 for course in context['assigned_courses'] if getattr(course, 'has_documents', False))
            total_students_with_new_content = sum(
                course.indicator_stats.get('students_with_new_content', 0) 
                for course in context['assigned_courses']
            )
            
            context['teacher_document_stats'] = {
                'total_courses': total_courses,
                'courses_with_documents': courses_with_documents,
                'total_students_with_new_content': total_students_with_new_content,
            }
        
        return context
    
    def _add_student_context(self, context, student):
        """
        Agrega contexto específico para estudiantes
        
        Args:
            context: Contexto del template
            student: Usuario estudiante
            
        Returns:
            Contexto actualizado
        """
        # Agregar indicadores de contenido nuevo usando el servicio
        context = IndicatorTemplateContext.add_indicator_context_for_student(context, student)
        
        # Agregar URLs del dashboard del estudiante y verificar documentos disponibles
        if 'enrolled_courses' in context:
            for course in context['enrolled_courses']:
                # Agregar URL del dashboard del estudiante
                course.student_dashboard_url = f'/course-documents/student/{course.id}/'
                
                # Verificar si el curso tiene documentos disponibles
                from .models import DocumentFolder, CourseDocument
                course.has_available_documents = CourseDocument.objects.filter(
                    folder__curso=course
                ).exists()
                
                # Agregar información del indicador de contenido nuevo
                course.has_new_content_indicator = ContentIndicatorService.has_new_content(course, student)
        
        # También agregar para cursos pendientes si existen
        if 'pending_courses' in context:
            for course in context['pending_courses']:
                course.student_dashboard_url = f'/course-documents/student/{course.id}/'
                course.has_available_documents = CourseDocument.objects.filter(
                    folder__curso=course
                ).exists()
                course.has_new_content_indicator = ContentIndicatorService.has_new_content(course, student)
        
        # Agregar estadísticas generales del estudiante
        enrolled_courses = context.get('enrolled_courses', [])
        courses_with_new_content = sum(1 for course in enrolled_courses if getattr(course, 'has_new_content_indicator', False))
        courses_with_documents = sum(1 for course in enrolled_courses if getattr(course, 'has_available_documents', False))
        
        context['student_document_stats'] = {
            'total_enrolled_courses': len(enrolled_courses),
            'courses_with_new_content': courses_with_new_content,
            'courses_with_documents': courses_with_documents,
        }
        
        return context


class DocumentsCourseMixin:
    """
    Mixin para agregar funcionalidad de documentos a vistas de cursos
    """
    
    def get_context_data(self, **kwargs):
        """
        Agrega información de documentos a cursos
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.is_authenticated:
            return context
        
        # Agregar información de documentos a cursos en el contexto
        courses_key = None
        if 'courses' in context:
            courses_key = 'courses'
        elif 'grouped_courses' in context:
            # Para vistas con cursos agrupados (como HomeView)
            for group in context['grouped_courses']:
                for course in group:
                    self._add_course_document_info(course, user)
            return context
        
        if courses_key and courses_key in context:
            for course in context[courses_key]:
                self._add_course_document_info(course, user)
        
        return context
    
    def _add_course_document_info(self, course, user):
        """
        Agrega información de documentos a un curso específico
        
        Args:
            course: Objeto curso
            user: Usuario actual
        """
        # Verificar si el curso tiene documentos
        from .models import DocumentFolder, CourseDocument
        course.has_documents = CourseDocument.objects.filter(folder__curso=course).exists()
        
        # Agregar URLs según el rol del usuario
        user_group = user.groups.first()
        group_name = user_group.name if user_group else None
        
        if group_name == 'Profesores' and course.teacher == user:
            course.teacher_dashboard_url = f'/course-documents/teacher/{course.id}/'
        elif group_name == 'Estudiantes':
            # Verificar si el estudiante está inscrito
            from principal.models import Matriculas
            is_enrolled = Matriculas.objects.filter(
                course=course,
                student=user,
                activo=True
            ).exists()
            
            if is_enrolled:
                course.student_dashboard_url = f'/course-documents/student/{course.id}/'
                course.has_new_content_indicator = ContentIndicatorService.has_new_content(course, user)


class DocumentsContextProcessor:
    """
    Procesador de contexto para agregar información global de documentos
    """
    
    @staticmethod
    def documents_context(request):
        """
        Agrega contexto global de documentos
        
        Args:
            request: Request HTTP
            
        Returns:
            Diccionario con contexto global
        """
        context = {}
        
        if not request.user.is_authenticated:
            return context
        
        user_group = request.user.groups.first()
        group_name = user_group.name if user_group else None
        
        # Agregar información global según el rol
        if group_name == 'Estudiantes':
            # Obtener cursos con contenido nuevo para mostrar en navegación global
            courses_with_new_content = ContentIndicatorService.get_courses_with_new_content_for_student(request.user)
            context['global_new_content_count'] = courses_with_new_content.count()
            context['has_global_new_content'] = courses_with_new_content.exists()
        
        elif group_name == 'Profesores':
            # Obtener estadísticas globales para profesores
            from principal.models import Curso, CursoAcademico
            curso_academico_activo = CursoAcademico.objects.filter(activo=True).first()
            
            if curso_academico_activo:
                teacher_courses = Curso.objects.filter(
                    teacher=request.user,
                    curso_academico=curso_academico_activo
                )
                
                total_students_with_new_content = 0
                for course in teacher_courses:
                    stats = ContentIndicatorService.get_indicator_stats_for_course(course)
                    total_students_with_new_content += stats.get('students_with_new_content', 0)
                
                context['global_teacher_stats'] = {
                    'total_courses': teacher_courses.count(),
                    'total_students_with_new_content': total_students_with_new_content,
                }
        
        return context


def documents_context(request):
    """
    Function-based context processor for documents
    
    Args:
        request: Request HTTP
        
    Returns:
        Diccionario con contexto global
    """
    processor = DocumentsContextProcessor()
    return processor.documents_context(request)