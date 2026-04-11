"""
Comando para configurar grupos por defecto del sistema
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from principal.config_grupos import GRUPOS_SISTEMA, obtener_nombres_grupos, configurar_permisos_grupo
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Configura los grupos por defecto del sistema con sus permisos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de permisos incluso si el grupo ya existe'
        )
        parser.add_argument(
            '--info',
            action='store_true',
            help='Mostrar información de los grupos configurados'
        )

    def handle(self, *args, **options):
        if options['info']:
            self.mostrar_info_grupos()
            return

        self.stdout.write(
            self.style.SUCCESS('=== Configuración de Grupos por Defecto ===')
        )
        
        force = options['force']
        grupos_creados = 0
        grupos_actualizados = 0
        grupos_existentes = 0

        for config_grupo in GRUPOS_SISTEMA:
            nombre_grupo = config_grupo['nombre']
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            
            if created:
                grupos_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Grupo "{nombre_grupo}" creado')
                )
                
                # Configurar permisos
                configurar_permisos_grupo(grupo, config_grupo)
                self.stdout.write(f'  → Permisos configurados')
                    
            elif force:
                # Reconfigurar permisos si se fuerza
                grupo.permissions.clear()
                configurar_permisos_grupo(grupo, config_grupo)
                grupos_actualizados += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Grupo "{nombre_grupo}" actualizado (permisos reconfigurados)')
                )
            else:
                grupos_existentes += 1
                self.stdout.write(f'○ Grupo "{nombre_grupo}" ya existe')

        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'RESUMEN:')
        self.stdout.write(f'Grupos creados: {grupos_creados}')
        self.stdout.write(f'Grupos actualizados: {grupos_actualizados}')
        self.stdout.write(f'Grupos que ya existían: {grupos_existentes}')
        self.stdout.write(f'Total de grupos configurados: {len(GRUPOS_SISTEMA)}')
        
        if grupos_creados > 0 or grupos_actualizados > 0:
            self.stdout.write(
                self.style.SUCCESS('\n¡Configuración completada exitosamente!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nTodos los grupos ya estaban configurados.')
            )
            
        self.stdout.write('\nPuedes usar --info para ver detalles de los grupos configurados.')

    def mostrar_info_grupos(self):
        """Muestra información detallada de los grupos configurados"""
        self.stdout.write(
            self.style.SUCCESS('=== Información de Grupos Configurados ===')
        )
        
        nombres_grupos = obtener_nombres_grupos()
        
        for config_grupo in GRUPOS_SISTEMA:
            nombre_grupo = config_grupo['nombre']
            try:
                grupo = Group.objects.get(name=nombre_grupo)
                
                self.stdout.write(f'\n📋 {nombre_grupo}')
                self.stdout.write(f'   ID: {grupo.id}')
                self.stdout.write(f'   Descripción: {config_grupo.get("descripcion", "Sin descripción")}')
                self.stdout.write(f'   Usuarios asignados: {grupo.user_set.count()}')
                self.stdout.write(f'   Permisos asignados: {grupo.permissions.count()}')
                
                # Mostrar modelos y acciones configuradas
                if 'permisos_modelos' in config_grupo:
                    self.stdout.write('   Modelos configurados:')
                    for app, modelos in config_grupo['permisos_modelos'].items():
                        self.stdout.write(f'     {app}: {", ".join(modelos)}')
                    self.stdout.write(f'   Acciones: {", ".join(config_grupo.get("acciones", []))}')
                
                if grupo.permissions.exists():
                    self.stdout.write('   Permisos asignados (primeros 5):')
                    for permiso in grupo.permissions.all()[:5]:
                        self.stdout.write(f'     - {permiso.name}')
                    if grupo.permissions.count() > 5:
                        self.stdout.write(f'     ... y {grupo.permissions.count() - 5} más')
                        
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ {nombre_grupo} - NO CONFIGURADO')
                )
        
        self.stdout.write(f'\nTotal de grupos definidos: {len(GRUPOS_SISTEMA)}')
        self.stdout.write(f'Grupos configurados: {Group.objects.filter(name__in=nombres_grupos).count()}')