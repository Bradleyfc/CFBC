from django.apps import AppConfig


class EvaluacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'evaluaciones'
    verbose_name = 'Evaluaciones'

    def ready(self):
        import evaluaciones.signals  # noqa: F401
