from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from datos_archivados.services import MigracionService


class Command(BaseCommand):
    help = 'Migra datos automáticamente desde una base de datos MariaDB remota'

    def add_arguments(self, parser):
        parser.add_argument('--host', required=True, help='Host de la base de datos MariaDB')
        parser.add_argument('--database', required=True, help='Nombre de la base de datos')
        parser.add_argument('--user', required=True, help='Usuario de la base de datos')
        parser.add_argument('--password', required=True, help='Contraseña de la base de datos')
        parser.add_argument('--port', type=int, default=3306, help='Puerto de la base de datos (default: 3306)')
        parser.add_argument('--usuario-django', help='Username del usuario Django que ejecuta la migración (default: primer superuser)')

    def handle(self, *args, **options):
        # Obtener usuario Django
        if options['usuario_django']:
            try:
                usuario = User.objects.get(username=options['usuario_django'])
            except User.DoesNotExist:
                raise CommandError(f'Usuario "{options["usuario_django"]}" no existe')
        else:
            usuario = User.objects.filter(is_superuser=True).first()
            if not usuario:
                raise CommandError('No hay superusuarios disponibles. Cree uno o especifique --usuario-django')

        self.stdout.write(f'Iniciando migración automática con usuario: {usuario.username}')

        # Crear servicio de migración
        servicio = MigracionService(
            host=options['host'],
            database=options['database'],
            user=options['user'],
            password=options['password'],
            port=options['port']
        )

        try:
            # Probar conexión
            self.stdout.write('Probando conexión a MariaDB...')
            if not servicio.conectar_mariadb():
                raise CommandError('No se pudo conectar a la base de datos MariaDB. Verifique los datos de conexión.')
            
            servicio.desconectar_mariadb()
            self.stdout.write(self.style.SUCCESS('Conexión exitosa'))

            # Ejecutar migración automática
            self.stdout.write('Iniciando inspección y migración automática...')
            log_migracion = servicio.inspeccionar_y_migrar_automaticamente(usuario)

            if log_migracion.estado == 'completada':
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Migración completada exitosamente. '
                        f'Total de registros migrados: {log_migracion.usuarios_migrados}'
                    )
                )
                
                # Mostrar resumen
                resumen = servicio.obtener_resumen_migracion()
                if resumen:
                    self.stdout.write('\n--- RESUMEN DE MIGRACIÓN ---')
                    self.stdout.write(f'ID de migración: {resumen["id_migracion"]}')
                    self.stdout.write(f'Estado: {resumen["estado"]}')
                    self.stdout.write(f'Fecha inicio: {resumen["fecha_inicio"]}')
                    self.stdout.write(f'Fecha fin: {resumen["fecha_fin"]}')
                    self.stdout.write(f'Host origen: {resumen["host_origen"]}')
                    self.stdout.write(f'Base de datos origen: {resumen["base_datos_origen"]}')
                    self.stdout.write(f'Total registros: {resumen["total_registros"]}')
                    if 'tablas_procesadas' in resumen:
                        self.stdout.write(f'Tablas procesadas: {len(resumen["tablas_procesadas"])}')
                        for tabla in resumen['tablas_procesadas']:
                            self.stdout.write(f'  - {tabla}')
            else:
                raise CommandError(f'Migración falló con estado: {log_migracion.estado}. Errores: {log_migracion.errores}')

        except Exception as e:
            raise CommandError(f'Error durante la migración: {str(e)}')