"""
Comando para crear superusuario y grupos del sistema automáticamente
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from principal.config_grupos import GRUPOS_SISTEMA, configurar_permisos_grupo
import getpass
import sys

class Command(BaseCommand):
    help = 'Crea un superusuario y configura los grupos del sistema automáticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            help='Username para el superusuario',
        )
        parser.add_argument(
            '--email',
            help='Email para el superusuario',
        )
        parser.add_argument(
            '--password',
            help='Contraseña para el superusuario (no recomendado por seguridad)',
        )
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Solo crear grupos, no crear superusuario',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== CONFIGURACIÓN INICIAL DEL SISTEMA ===')
        )
        
        # Crear superusuario si no se omite
        if not options['skip_superuser']:
            self.crear_superusuario(options)
        
        # Crear grupos del sistema
        self.crear_grupos_sistema()

    def crear_superusuario(self, options):
        """Crea el superusuario"""
        self.stdout.write('\n1. Creando superusuario...')
        
        try:
            # Obtener datos del superusuario
            username = options.get('username')
            email = options.get('email')
            password = options.get('password')
            
            if not username:
                username = input('Username: ')
            
            if not email:
                email = input('Email: ')
            
            if not password:
                password = getpass.getpass('Password: ')
                password_confirm = getpass.getpass('Password (again): ')
                
                if password != password_confirm:
                    self.stdout.write(
                        self.style.ERROR('Las contraseñas no coinciden')
                    )
                    sys.exit(1)
            
            # Verificar si ya existe
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'El usuario "{username}" ya existe')
                )
                return
            
            # Crear superusuario
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Superusuario "{username}" creado exitosamente')
            )
            
        except KeyboardInterrupt:
            self.stdout.write('\nOperación cancelada')
            sys.exit(1)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando superusuario: {e}')
            )

    def crear_grupos_sistema(self):
        """Crea los grupos del sistema"""
        self.stdout.write('\n2. Configurando grupos del sistema...')
        
        grupos_creados = 0
        grupos_existentes = 0
        
        try:
            for config_grupo in GRUPOS_SISTEMA:
                nombre_grupo = config_grupo['nombre']
                
                # Verificar si el grupo ya existe
                if Group.objects.filter(name=nombre_grupo).exists():
                    grupos_existentes += 1
                    self.stdout.write(f'○ Grupo "{nombre_grupo}" ya existe')
                    continue
                
                # Crear el grupo
                try:
                    grupo = Group.objects.create(name=nombre_grupo)
                    grupos_creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Grupo "{nombre_grupo}" creado')
                    )
                    
                    # Configurar permisos
                    try:
                        configurar_permisos_grupo(grupo, config_grupo)
                        self.stdout.write(f'  → Permisos configurados')
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  Error configurando permisos: {e}')
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error creando grupo "{nombre_grupo}": {e}')
                    )
            
            # Resumen final
            self.mostrar_resumen(grupos_creados, grupos_existentes)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error general configurando grupos: {e}')
            )

    def mostrar_resumen(self, grupos_creados, grupos_existentes):
        """Muestra el resumen final"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('RESUMEN DE CONFIGURACIÓN:')
        self.stdout.write(f'✓ Grupos creados: {grupos_creados}')
        self.stdout.write(f'○ Grupos que ya existían: {grupos_existentes}')
        self.stdout.write(f'📊 Total de grupos: {len(GRUPOS_SISTEMA)}')
        
        if grupos_creados > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 ¡{grupos_creados} grupos configurados exitosamente!')
            )
            
            # Mostrar lista de grupos
            self.stdout.write('\n📋 Grupos disponibles:')
            for config_grupo in GRUPOS_SISTEMA:
                self.stdout.write(f'  • {config_grupo["nombre"]}: {config_grupo["descripcion"]}')
            
            self.stdout.write('\n🔗 Enlaces útiles:')
            self.stdout.write('  • Admin Django: http://localhost:8000/admin/auth/group/')
            self.stdout.write('  • Verificar grupos: python3 manage.py verificar_grupos')
            self.stdout.write('  • Iniciar servidor: python3 manage.py runserver')
            
        else:
            self.stdout.write(
                self.style.WARNING('\nTodos los grupos ya estaban configurados.')
            )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('¡Configuración inicial completada!')
        )