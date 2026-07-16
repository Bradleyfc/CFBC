from django.apps import AppConfig


class CourseDocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'course_documents'
    verbose_name = 'Gestión de Documentos de Cursos'

    def ready(self):
        """Initialize signals and cache configuration."""
        import course_documents.signals
        
        # Import and setup cache signals
        try:
            from cfbc.cache_signals import setup_cache_signals
            setup_cache_signals()
        except ImportError as e:
            # Log error but don't crash if cache utils aren't available
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not setup cache signals: {e}")
