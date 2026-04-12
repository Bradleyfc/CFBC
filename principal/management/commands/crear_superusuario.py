"""
Comando para crear superusuario y grupos automáticamente
"""
from django.contrib.auth.management.commands.createsuperuser import Command as BaseCreateSuperUserCommand
from django.core.management import call_command
from django.contrib.auth.models import User
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
            self.stdout.write(self.style.SUCCESS('🚀 Creando superusuario...'))
            super().handle(*args, **options)
            
            # Después de crear el superusuario, crear los grupos (a menos que se especifique lo contrario)
            if not options.get('skip_groups'):
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('🔧 Configurando grupos del sistema...'))
                call_command('setup_grupos', verbosity=options.get('verbosity', 1))
                
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('✅ ¡Configuración completa!'))
                self.stdout.write('🎯 Superusuario creado y grupos configurados exitosamente')
                self.stdout.write('\n📋 Próximos pasos:')
                self.stdout.write('  • Inicia el servidor: python3 manage.py runserver')
                self.stdout.write('  • Accede al admin: http://localhost:8000/admin/')
                self.stdout.write('  • Verifica grupos: python3 manage.py verificar_grupos')
            else:
                self.stdout.write(self.style.WARNING('\n⚠️  Grupos no configurados (--skip-groups especificado)'))
                self.stdout.write('Para configurar grupos manualmente: python3 manage.py setup_grupos')
            
        except Exception as e:
            error_msg = str(e)
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando superusuario: {error_msg}')
            )
            
            # Intentar crear grupos de todas formas si el superusuario ya existe
            if ("already exists" in error_msg.lower() or 
                "ya existe" in error_msg.lower() or
                "username is already taken" in error_msg.lower()):
                
                if not options.get('skip_groups'):
                    self.stdout.write('\n' + '='*60)
                    self.stdout.write(self.style.WARNING('⚠️  El superusuario ya existe, pero configurando grupos...'))
                    call_command('setup_grupos', verbosity=options.get('verbosity', 1))
                    
                    self.stdout.write('\n' + '='*60)
                    self.stdout.write(self.style.SUCCESS('✅ ¡Grupos configurados exitosamente!'))
            else:
                # Para otros errores, sugerir comandos alternativos
                self.stdout.write('\n💡 Comandos alternativos:')
                self.stdout.write('  • Crear solo grupos: python3 manage.py setup_grupos')
                self.stdout.write('  • Crear superusuario sin grupos: python3 manage.py crear_superusuario --skip-groups')
                raise