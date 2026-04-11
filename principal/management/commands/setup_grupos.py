"""
Comando para configurar grupos del sistema después de crear superusuario
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from principal.config_grupos import GRUPOS_SISTEMA, configurar_permisos_grupo

class Command(BaseCommand):
    help = 'Configura los grupos del sistema automáticamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reconfigura los grupos existentes',
        )

    def handle(self, *args, **options):
        """
        Crea y configura los grupos del sistema
        """
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('Configurando grupos del sistema automáticamente...')
        )
        
        grupos_creados = 0
        grupos_existentes = 0
        grupos_reconfigurados = 0
        
        try:
            for config_grupo in GRUPOS_SISTEMA:
                nombre_grupo = config_grupo['nombre']
                
                # Verificar si el grupo ya existe
                grupo_existente = Group.objects.filter(name=nombre_grupo).first()
                
                if grupo_existente:
                    grupos_existentes += 1
                    if options['force']:
                        # Reconfigurar permisos
                        grupo_existente.permissions.clear()
                        configurar_permisos_grupo(grupo_existente, config_grupo)
                        grupos_reconfigurados += 1
                        self.stdout.write(
                            self.style.WARNING(f'↻ Grupo "{nombre_grupo}" reconfigurado')
                        )
                    else:
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
            
            # Resumen
            self.stdout.write('\n' + '='*60)
            self.stdout.write('RESUMEN DE CONFIGURACIÓN:')
            self.stdout.write(f'✓ Grupos creados: {grupos_creados}')
            self.stdout.write(f'○ Grupos que ya existían: {grupos_existentes}')
            if grupos_reconfigurados > 0:
                self.stdout.write(f'↻ Grupos reconfigurados: {grupos_reconfigurados}')
            self.stdout.write(f'📊 Total de grupos: {len(GRUPOS_SISTEMA)}')
            
            if grupos_creados > 0 or grupos_reconfigurados > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 ¡Configuración completada exitosamente!')
                )
                
                # Mostrar lista de grupos
                self.stdout.write('\n📋 Grupos disponibles:')
                for config_grupo in GRUPOS_SISTEMA:
                    self.stdout.write(f'  • {config_grupo["nombre"]}: {config_grupo["descripcion"]}')
                
                self.stdout.write('\n🔗 Enlaces útiles:')
                self.stdout.write('  • Admin Django: http://localhost:8000/admin/auth/group/')
                self.stdout.write('  • Verificar grupos: python3 manage.py verificar_grupos')
                
            else:
                self.stdout.write(
                    self.style.WARNING('\nTodos los grupos ya estaban configurados.')
                )
                self.stdout.write('Usa --force para reconfigurar permisos.')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error general configurando grupos: {e}')
            )
            raise