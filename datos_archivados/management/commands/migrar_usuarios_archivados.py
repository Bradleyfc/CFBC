from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from datos_archivados.models import UsuarioArchivado
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migra usuarios archivados al sistema actual de autenticación'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--password-default',
            type=str,
            default='temporal123',
            help='Contraseña por defecto para usuarios migrados'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo simulación sin hacer cambios'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar migración incluso si el usuario ya existe'
        )
    
    def handle(self, *args, **options):
        password_default = options['password_default']
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO SIMULACIÓN - No se harán cambios reales')
            )
        
        # Obtener usuarios archivados sin usuario actual vinculado
        usuarios_archivados = UsuarioArchivado.objects.filter(usuario_actual__isnull=True)
        
        if force:
            usuarios_archivados = UsuarioArchivado.objects.all()
        
        total_usuarios = usuarios_archivados.count()
        self.stdout.write(f'Usuarios archivados a procesar: {total_usuarios}')
        
        migrados = 0
        errores = 0
        ya_existen = 0
        
        for usuario_archivado in usuarios_archivados:
            try:
                with transaction.atomic():
                    # Verificar si ya existe un usuario con ese username
                    user_existente = User.objects.filter(
                        username=usuario_archivado.username
                    ).first()
                    
                    if user_existente and not force:
                        if not usuario_archivado.usuario_actual:
                            # Vincular con el usuario existente
                            if not dry_run:
                                usuario_archivado.usuario_actual = user_existente
                                usuario_archivado.save()
                            ya_existen += 1
                            self.stdout.write(
                                f'✓ Vinculado usuario existente: {usuario_archivado.username}'
                            )
                        continue
                    
                    # Crear nuevo usuario o actualizar existente
                    if user_existente and force:
                        user = user_existente
                        # Actualizar datos
                        user.email = usuario_archivado.email or user.email
                        user.first_name = usuario_archivado.first_name or user.first_name
                        user.last_name = usuario_archivado.last_name or user.last_name
                        user.is_active = usuario_archivado.is_active
                        if not dry_run:
                            user.save()
                    else:
                        # Crear nuevo usuario
                        if not dry_run:
                            user = User.objects.create_user(
                                username=usuario_archivado.username,
                                email=usuario_archivado.email or '',
                                first_name=usuario_archivado.first_name or '',
                                last_name=usuario_archivado.last_name or '',
                                password=password_default,
                                is_active=usuario_archivado.is_active
                            )
                        else:
                            user = None
                    
                    # Asignar siempre al grupo Estudiantes
                    if not dry_run and user:
                        try:
                            grupo_estudiantes = Group.objects.get(name='Estudiantes')
                            user.groups.add(grupo_estudiantes)
                            self.stdout.write(
                                f'✓ Usuario {usuario_archivado.username} agregado al grupo Estudiantes'
                            )
                        except Group.DoesNotExist:
                            # Crear el grupo si no existe
                            grupo_estudiantes = Group.objects.create(name='Estudiantes')
                            user.groups.add(grupo_estudiantes)
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Grupo "Estudiantes" no existía, se creó y se agregó {usuario_archivado.username}'
                                )
                            )
                    
                    # Vincular usuario archivado con usuario actual
                    if not dry_run and user:
                        usuario_archivado.usuario_actual = user
                        usuario_archivado.save()
                    
                    migrados += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Migrado: {usuario_archivado.username} -> {user.username if user else "SIMULACIÓN"}'
                        )
                    )
                    
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error migrando {usuario_archivado.username}: {str(e)}'
                    )
                )
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'RESUMEN DE MIGRACIÓN:')
        self.stdout.write(f'Total procesados: {total_usuarios}')
        self.stdout.write(f'Migrados exitosamente: {migrados}')
        self.stdout.write(f'Ya existían: {ya_existen}')
        self.stdout.write(f'Errores: {errores}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nEsto fue una simulación. Ejecuta sin --dry-run para aplicar cambios.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n¡Migración completada!')
            )
            self.stdout.write(
                f'IMPORTANTE: Los usuarios migrados tienen la contraseña: "{password_default}"'
            )
            self.stdout.write(
                'Se recomienda que cambien sus contraseñas en el primer login.'
            )