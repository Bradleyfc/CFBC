"""
Comando para crear los grupos del sistema manualmente
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from principal.config_grupos import GRUPOS_SISTEMA, configurar_permisos_grupo

class Command(BaseCommand):
    help = 'Crea los grupos del sistema manualmente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recrear grupos incluso si ya existen'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Creando Grupos del Sistema ===')
        )
        
        force = options['force']
        grupos_creados = 0
        grupos_existentes = 0
        grupos_actualizados = 0

        for config_grupo in GRUPOS_SISTEMA:
            nombre_grupo = config_grupo['nombre']
            
            # Verificar si ya existe
            grupo_existe = Group.objects.filter(name=nombre_grupo).exists()
            
            if grupo_existe and not force:
                grupos_existentes += 1
                self.stdout.write(f'○ Grupo "{nombre_grupo}" ya existe')
                continue
            
            if grupo_existe and force:
                # Eliminar y recrear
                Group.objects.filter(name=nombre_grupo).delete()
                grupos_actualizados += 1
                self.stdout.write(f'⟳ Recreando grupo "{nombre_grupo}"')
            
            # Crear el grupo
            try:
                grupo = Group.objects.create(name=nombre_grupo)
                if not grupo_existe:
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

        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN:')
        self.stdout.write(f'Grupos creados: {grupos_creados}')
        self.stdout.write(f'Grupos recreados: {grupos_actualizados}')
        self.stdout.write(f'Grupos que ya existían: {grupos_existentes}')
        self.stdout.write(f'Total de grupos: {len(GRUPOS_SISTEMA)}')
        
        if grupos_creados > 0 or grupos_actualizados > 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 ¡Grupos configurados exitosamente!')
            )
            self.stdout.write('\nPuedes verificar los grupos en:')
            self.stdout.write('http://localhost:8000/admin/auth/group/')
        else:
            self.stdout.write(
                self.style.WARNING('\nTodos los grupos ya estaban configurados.')
            )
            self.stdout.write('Usa --force para recrearlos si es necesario.')