"""
Comando personalizado para crear superusuario y grupos automáticamente
"""
from django.contrib.auth.management.commands.createsuperuser import Command as BaseCreateSuperUserCommand
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class Command(BaseCreateSuperUserCommand):
    help = 'Crea un superusuario y configura los grupos del sistema automáticamente'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--skip-groups',
            action='store_true',
            help='No crear grupos del sistema automáticamente',
        )

    def handle(self, *args, **options):
        try:
            # Ejecutar el comando original de createsuperuser
            self.stdout.write('Creando superusuario...')
            super().handle(*args, **options)
            
            # Después de crear el superusuario, crear los grupos (a menos que se especifique lo contrario)
            if not options.get('skip_groups'):
                self.stdout.write('\nConfigurando grupos del sistema...')
                call_command('setup_grupos', verbosity=options.get('verbosity', 1))
            
        except Exception as e:
            error_msg = str(e)
            self.stdout.write(
                self.style.ERROR(f'Error creando superusuario: {error_msg}')
            )
            
            # Intentar crear grupos de todas formas si el superusuario ya existe
            if ("already exists" in error_msg.lower() or 
                "ya existe" in error_msg.lower() or
                "username is already taken" in error_msg.lower()):
                
                if not options.get('skip_groups'):
                    self.stdout.write('El superusuario ya existe, pero configurando grupos...')
                    call_command('setup_grupos', verbosity=options.get('verbosity', 1))
            else:
                # Para otros errores, sugerir comandos alternativos
                self.stdout.write('\nComandos alternativos:')
                self.stdout.write('• Crear solo grupos: python3 manage.py setup_grupos')
                self.stdout.write('• Crear superusuario sin grupos: python3 manage.py createsuperuser --skip-groups')
                raise