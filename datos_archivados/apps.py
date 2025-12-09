from django.apps import AppConfig


class DatosArchivadosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datos_archivados'
    verbose_name = 'Datos Archivados'
    
    def ready(self):
        # Importar señales si las hay
        try:
            import datos_archivados.signals
        except ImportError:
            pass