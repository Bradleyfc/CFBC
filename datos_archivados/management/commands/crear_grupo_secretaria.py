from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User


class Command(BaseCommand):
    help = 'Crea el grupo Secretaria y opcionalmente asigna usuarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            help='Username del usuario a agregar al grupo Secretaria'
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Lista todos los usuarios del grupo Secretaria'
        )

    def handle(self, *args, **options):
        # Crear o obtener el grupo Secretaria
        grupo_secretaria, created = Group.objects.get_or_create(name='Secretaria')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Grupo "Secretaria" creado exitosamente')
            )
        else:
            self.stdout.write('El grupo "Secretaria" ya existe')

        # Si se especifica un usuario, agregarlo al grupo
        if options['usuario']:
            try:
                usuario = User.objects.get(username=options['usuario'])
                usuario.groups.add(grupo_secretaria)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Usuario "{usuario.username}" agregado al grupo Secretaria'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'Usuario "{options["usuario"]}" no existe'
                    )
                )

        # Si se especifica listar, mostrar todos los usuarios del grupo
        if options['listar']:
            usuarios_secretaria = User.objects.filter(groups=grupo_secretaria)
            if usuarios_secretaria.exists():
                self.stdout.write('\nUsuarios en el grupo Secretaria:')
                for usuario in usuarios_secretaria:
                    self.stdout.write(f'  - {usuario.username} ({usuario.get_full_name()})')
            else:
                self.stdout.write('No hay usuarios en el grupo Secretaria')

        # Mostrar información adicional
        total_usuarios = User.objects.filter(groups=grupo_secretaria).count()
        self.stdout.write(f'\nTotal de usuarios en el grupo Secretaria: {total_usuarios}')
        
        if total_usuarios == 0:
            self.stdout.write(
                self.style.WARNING(
                    '\nPara agregar un usuario al grupo Secretaria, ejecute:'
                )
            )
            self.stdout.write('python manage.py crear_grupo_secretaria --usuario <username>')