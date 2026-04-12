"""
Comando para agregar superusuarios existentes al grupo Administración
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction

class Command(BaseCommand):
    help = 'Agrega superusuarios existentes al grupo Administración'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username específico del superusuario a agregar al grupo Administración',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Agregar todos los superusuarios al grupo Administración',
        )

    def handle(self, *args, **options):
        """
        Agrega superusuarios al grupo Administración
        """
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('Agregando superusuarios al grupo Administración...')
        )
        
        try:
            with transaction.atomic():
                # Crear o obtener el grupo Administración
                grupo_admin, created = Group.objects.get_or_create(name='Administración')
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS('✓ Grupo "Administración" creado')
                    )
                else:
                    self.stdout.write('○ Grupo "Administración" ya existe')
                
                usuarios_procesados = 0
                usuarios_agregados = 0
                usuarios_ya_en_grupo = 0
                
                # Determinar qué usuarios procesar
                if options['username']:
                    # Usuario específico
                    try:
                        usuario = User.objects.get(username=options['username'])
                        if not usuario.is_superuser:
                            self.stdout.write(
                                self.style.ERROR(f'❌ El usuario "{options["username"]}" no es superusuario')
                            )
                            return
                        usuarios = [usuario]
                    except User.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Usuario "{options["username"]}" no encontrado')
                        )
                        return
                        
                elif options['all']:
                    # Todos los superusuarios
                    usuarios = User.objects.filter(is_superuser=True)
                    if not usuarios.exists():
                        self.stdout.write(
                            self.style.WARNING('⚠️  No se encontraron superusuarios en el sistema')
                        )
                        return
                else:
                    # Por defecto, mostrar opciones disponibles
                    superusuarios = User.objects.filter(is_superuser=True)
                    if not superusuarios.exists():
                        self.stdout.write(
                            self.style.WARNING('⚠️  No se encontraron superusuarios en el sistema')
                        )
                        return
                    
                    self.stdout.write('\n📋 Superusuarios disponibles:')
                    for user in superusuarios:
                        en_grupo = "✓" if user.groups.filter(name='Administración').exists() else "○"
                        self.stdout.write(f'  {en_grupo} {user.username} ({user.email or "sin email"})')
                    
                    self.stdout.write('\n💡 Uso:')
                    self.stdout.write('  • Agregar usuario específico: --username <username>')
                    self.stdout.write('  • Agregar todos: --all')
                    return
                
                # Procesar usuarios
                for usuario in usuarios:
                    usuarios_procesados += 1
                    
                    if usuario.groups.filter(name='Administración').exists():
                        usuarios_ya_en_grupo += 1
                        self.stdout.write(
                            self.style.WARNING(f'○ "{usuario.username}" ya está en el grupo Administración')
                        )
                    else:
                        usuario.groups.add(grupo_admin)
                        usuarios_agregados += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ "{usuario.username}" agregado al grupo Administración')
                        )
                
                # Resumen
                self.stdout.write('\n' + '='*60)
                self.stdout.write('RESUMEN:')
                self.stdout.write(f'📊 Usuarios procesados: {usuarios_procesados}')
                self.stdout.write(f'✓ Usuarios agregados al grupo: {usuarios_agregados}')
                self.stdout.write(f'○ Usuarios que ya estaban en el grupo: {usuarios_ya_en_grupo}')
                
                if usuarios_agregados > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'\n🎉 ¡{usuarios_agregados} superusuario(s) agregado(s) exitosamente!')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('\nTodos los superusuarios ya estaban en el grupo Administración.')
                    )
                
                # Mostrar estado final del grupo
                total_miembros = grupo_admin.user_set.count()
                self.stdout.write(f'\n👥 Total de miembros en grupo Administración: {total_miembros}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error procesando superusuarios: {e}')
            )
            raise