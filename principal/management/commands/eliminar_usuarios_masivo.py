from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Elimina usuarios de forma masiva de manera eficiente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Eliminar TODOS los usuarios (excepto superusuarios)',
        )
        parser.add_argument(
            '--sin-registro',
            action='store_true',
            help='Eliminar solo usuarios sin registro asociado',
        )
        parser.add_argument(
            '--inactivos',
            action='store_true',
            help='Eliminar solo usuarios inactivos',
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirmar la eliminación (requerido para ejecutar)',
        )
        parser.add_argument(
            '--lote',
            type=int,
            default=1000,
            help='Número de usuarios a eliminar por lote (default: 1000)',
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING(
                    'ADVERTENCIA: Esta operación eliminará usuarios de forma permanente.\n'
                    'Usa --confirmar para ejecutar la eliminación.'
                )
            )
            return

        # Construir queryset base
        queryset = User.objects.all()

        # Excluir superusuarios siempre
        queryset = queryset.filter(is_superuser=False)

        # Aplicar filtros según opciones
        if options['sin_registro']:
            queryset = queryset.filter(registro__isnull=True)
            self.stdout.write('Filtrando usuarios sin registro asociado...')
        
        if options['inactivos']:
            queryset = queryset.filter(is_active=False)
            self.stdout.write('Filtrando usuarios inactivos...')

        if not options['todos'] and not options['sin_registro'] and not options['inactivos']:
            self.stdout.write(
                self.style.ERROR(
                    'Debes especificar al menos una opción: --todos, --sin-registro, o --inactivos'
                )
            )
            return

        # Contar usuarios a eliminar
        total_usuarios = queryset.count()
        
        if total_usuarios == 0:
            self.stdout.write(self.style.SUCCESS('No hay usuarios que coincidan con los criterios.'))
            return

        self.stdout.write(f'Se eliminarán {total_usuarios} usuarios...')

        # Confirmar operación
        if total_usuarios > 100:
            respuesta = input(f'¿Estás seguro de eliminar {total_usuarios} usuarios? (sí/no): ')
            if respuesta.lower() not in ['sí', 'si', 'yes', 'y']:
                self.stdout.write('Operación cancelada.')
                return

        # Eliminar en lotes para evitar problemas de memoria
        lote_size = options['lote']
        eliminados = 0
        errores = 0

        self.stdout.write(f'Eliminando usuarios en lotes de {lote_size}...')

        try:
            while True:
                # Obtener un lote de IDs de usuarios
                ids_lote = list(queryset.values_list('id', flat=True)[:lote_size])
                
                if not ids_lote:
                    break

                try:
                    with transaction.atomic():
                        # Eliminar el lote actual
                        usuarios_lote = User.objects.filter(id__in=ids_lote)
                        count = usuarios_lote.count()
                        usuarios_lote.delete()
                        eliminados += count
                        
                        self.stdout.write(f'Eliminados {eliminados}/{total_usuarios} usuarios...')

                except Exception as e:
                    errores += len(ids_lote)
                    logger.error(f'Error eliminando lote: {str(e)}')
                    self.stdout.write(
                        self.style.ERROR(f'Error eliminando lote de {len(ids_lote)} usuarios: {str(e)}')
                    )

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nOperación interrumpida por el usuario.'))
            
        except Exception as e:
            logger.error(f'Error general en eliminación masiva: {str(e)}')
            self.stdout.write(self.style.ERROR(f'Error general: {str(e)}'))

        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Eliminación completada:'))
        self.stdout.write(f'- Usuarios eliminados: {eliminados}')
        if errores > 0:
            self.stdout.write(self.style.WARNING(f'- Errores: {errores}'))
        
        # Verificar usuarios restantes
        usuarios_restantes = User.objects.count()
        superusuarios = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(f'- Usuarios restantes: {usuarios_restantes}')
        self.stdout.write(f'- Superusuarios (no eliminados): {superusuarios}')
        self.stdout.write('='*50)