"""
Comando para configuración inicial completa del sistema
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from principal.utils import (
    verificar_grupos_configurados, 
    configurar_usuario_inicial,
    obtener_usuarios_por_grupo
)
from principal.signals import crear_grupos_por_defecto
import getpass

class Command(BaseCommand):
    help = 'Configuración inicial completa del sistema (grupos, usuario admin, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-admin',
            action='store_true',
            help='Omitir creación de usuario administrador'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Username para el usuario administrador (default: admin)'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            help='Email para el usuario administrador'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== CONFIGURACIÓN INICIAL DEL SISTEMA ===')
        )
        
        # 1. Verificar y configurar grupos
        self.stdout.write('\n1. Configurando grupos del sistema...')
        self.configurar_grupos()
        
        # 2. Configurar usuario administrador
        if not options['skip_admin']:
            self.stdout.write('\n2. Configurando usuario administrador...')
            self.configurar_admin(options)
        
        # 3. Mostrar resumen
        self.stdout.write('\n3. Resumen de configuración...')
        self.mostrar_resumen()
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 ¡Configuración inicial completada!')
        )

    def configurar_grupos(self):
        """Configura los grupos del sistema"""
        verificacion = verificar_grupos_configurados()
        
        if verificacion['configurados_correctamente']:
            self.stdout.write('✓ Todos los grupos ya están configurados')
        else:
            self.stdout.write(f'⚠️  Faltan {len(verificacion["faltantes"])} grupos por configurar')
            
            # Forzar creación de grupos
            from django.apps import apps
            app_config = apps.get_app_config('principal')
            crear_grupos_por_defecto(sender=app_config)
            
            # Verificar nuevamente
            verificacion_nueva = verificar_grupos_configurados()
            if verificacion_nueva['configurados_correctamente']:
                self.stdout.write('✓ Grupos configurados exitosamente')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Error configurando algunos grupos')
                )

    def configurar_admin(self, options):
        """Configura el usuario administrador inicial"""
        username = options['admin_username']
        email = options['admin_email']
        
        # Verificar si ya existe un superusuario
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('✓ Ya existe un usuario administrador')
            return
        
        # Solicitar email si no se proporcionó
        if not email:
            email = input('Email del administrador: ')
        
        # Solicitar contraseña
        password = getpass.getpass('Contraseña del administrador: ')
        password_confirm = getpass.getpass('Confirmar contraseña: ')
        
        if password != password_confirm:
            self.stdout.write(
                self.style.ERROR('❌ Las contraseñas no coinciden')
            )
            return
        
        # Crear usuario administrador
        usuario = configurar_usuario_inicial(
            username=username,
            email=email,
            password=password,
            grupos=['Administración', 'Profesores']  # Grupos por defecto para admin
        )
        
        if usuario:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Usuario administrador "{username}" creado')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Error creando usuario administrador')
            )

    def mostrar_resumen(self):
        """Muestra un resumen de la configuración"""
        # Verificación de grupos
        verificacion = verificar_grupos_configurados()
        self.stdout.write(f'📊 Grupos configurados: {verificacion["total_configurados"]}/{verificacion["total_definidos"]}')
        
        # Estadísticas de usuarios
        total_usuarios = User.objects.count()
        superusuarios = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(f'👥 Total usuarios: {total_usuarios}')
        self.stdout.write(f'🔑 Superusuarios: {superusuarios}')
        
        # Usuarios por grupo
        estadisticas = obtener_usuarios_por_grupo()
        self.stdout.write('\n📋 Usuarios por grupo:')
        for grupo, stats in estadisticas.items():
            self.stdout.write(f'   {grupo}: {stats["total_usuarios"]} usuarios')
        
        self.stdout.write('\n🌐 URLs importantes:')
        self.stdout.write('   Admin: http://localhost:8000/admin/')
        self.stdout.write('   Blog: http://localhost:8000/noticias/')
        self.stdout.write('   Sistema: http://localhost:8000/')