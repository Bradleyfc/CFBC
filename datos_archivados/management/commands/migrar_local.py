from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from datos_archivados.services import MigracionService
import getpass

class Command(BaseCommand):
    help = 'Migra datos desde una base de datos MariaDB/MySQL local'

    def add_arguments(self, parser):
        parser.add_argument('--host', default='localhost', help='Host de la base de datos (default: localhost)')
        parser.add_argument('--port', type=int, default=3306, help='Puerto de la base de datos (default: 3306)')
        parser.add_argument('--database', required=True, help='Nombre de la base de datos')
        parser.add_argument('--user', default='root', help='Usuario de la base de datos (default: root)')
        parser.add_argument('--password', help='Contraseña de la base de datos')
        parser.add_argument('--usuario-django', help='Username del usuario Django para el log')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Migración Local de Datos Archivados ==='))
        
        # Obtener contraseña si no se proporcionó
        password = options['password']
        if not password:
            password = getpass.getpass('Contraseña de la base de datos: ')
        
        # Configuración de conexión
        config = {
            'host': options['host'],
            'database': options['database'],
            'user': options['user'],
            'password': password,
            'port': options['port']
        }
        
        self.stdout.write(f"Conectando a: {config['user']}@{config['host']}:{config['port']}/{config['database']}")
        
        # Obtener usuario Django
        usuario_django = None
        if options['usuario_django']:
            try:
                usuario_django = User.objects.get(username=options['usuario_django'])
            except User.DoesNotExist:
                raise CommandError(f'Usuario Django "{options["usuario_django"]}" no encontrado')
        else:
            # Usar el primer superusuario disponible
            usuario_django = User.objects.filter(is_superuser=True).first()
            if not usuario_django:
                usuario_django = User.objects.first()
            if not usuario_django:
                raise CommandError('No hay usuarios en el sistema. Crea un superusuario primero.')
        
        self.stdout.write(f"Usuario Django para el log: {usuario_django.username}")
        
        # Crear servicio de migración
        servicio = MigracionService(**config)
        
        # Probar conexión
        self.stdout.write('Probando conexión...')
        if not servicio.conectar_mariadb():
            raise CommandError('No se pudo conectar a la base de datos. Verifica la configuración.')
        
        self.stdout.write(self.style.SUCCESS('✅ Conexión exitosa!'))
        servicio.desconectar_mariadb()
        
        # Ejecutar migración
        self.stdout.write('Iniciando migración automática...')
        try:
            log_migracion = servicio.inspeccionar_y_migrar_automaticamente(usuario_django)
            
            self.stdout.write(self.style.SUCCESS('\n=== Resultado de la Migración ==='))
            self.stdout.write(f'Estado: {log_migracion.estado}')
            self.stdout.write(f'Registros migrados: {log_migracion.usuarios_migrados}')
            self.stdout.write(f'Fecha inicio: {log_migracion.fecha_inicio}')
            self.stdout.write(f'Fecha fin: {log_migracion.fecha_fin}')
            
            if log_migracion.errores:
                self.stdout.write(self.style.WARNING(f'Errores: {log_migracion.errores}'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ Migración completada!'))
            self.stdout.write('Puedes ver los datos en: http://localhost:8000/datos-archivados/')
            
        except Exception as e:
            raise CommandError(f'Error durante la migración: {str(e)}')