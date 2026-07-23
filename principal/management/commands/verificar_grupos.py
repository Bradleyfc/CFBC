"""
Comando simple para verificar el estado de los grupos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from principal.signals import GRUPOS_SISTEMA

class Command(BaseCommand):
    help = 'Verifica el estado de los grupos del sistema'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Estado de Grupos del Sistema ===')
        )
        
        nombres_grupos = [g['nombre'] for g in GRUPOS_SISTEMA]
        grupos_existentes = Group.objects.filter(name__in=nombres_grupos)
        
        self.stdout.write(f'\nGrupos definidos: {len(nombres_grupos)}')
        self.stdout.write(f'Grupos configurados: {grupos_existentes.count()}')
        
        self.stdout.write('\nEstado por grupo:')
        for config_grupo in GRUPOS_SISTEMA:
            nombre = config_grupo['nombre']
            existe = Group.objects.filter(name=nombre).exists()
            
            if existe:
                grupo = Group.objects.get(name=nombre)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {nombre} - Configurado ({grupo.permissions.count()} permisos)')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {nombre} - NO configurado')
                )
        
        if grupos_existentes.count() == len(nombres_grupos):
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Todos los grupos están configurados correctamente')
            )
        else:
            faltantes = len(nombres_grupos) - grupos_existentes.count()
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  Faltan {faltantes} grupos por configurar')
            )
            self.stdout.write('Ejecuta: python manage.py migrate')
            self.stdout.write('O reinicia el servidor para configurarlos automáticamente')