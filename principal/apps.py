from django.apps import AppConfig


class PrincipalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'principal'

    def ready(self):
        # Solo importar signals, NO ejecutar consultas de base de datos
        try:
            import principal.signals
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error importando signals: {e}")
        
        # NO ejecutar verificación de grupos aquí para evitar el warning
        # Los grupos se crearán con el middleware en la primera petición
