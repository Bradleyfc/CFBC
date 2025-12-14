from django.apps import AppConfig


class CourseDocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'course_documents'
    verbose_name = 'Gestión de Documentos de Cursos'

    def ready(self):
        import course_documents.signals
