"""
Comando para activar/desactivar la creación automática de grupos
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Activa o desactiva la creación automática de grupos al crear superusuario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--activar',
            action='store_true',
            help='Activa la creación automática de grupos',
        )
        parser.add_argument(
            '--desactivar', 
            action='store_true',
            help='Desactiva la creación automática de grupos',
        )

    def handle(self, *args, **options):
        if options['activar'] and options['desactivar']:
            self.stdout.write(
                self.style.ERROR('No puedes usar --activar y --desactivar al mismo tiempo')
            )
            return
        
        if not options['activar'] and not options['desactivar']:
            self.stdout.write(
                self.style.WARNING('Debes usar --activar o --desactivar')
            )
            return
        
        signals_file = os.path.join(settings.BASE_DIR, 'principal', 'signals.py')
        
        try:
            with open(signals_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if options['activar']:
                # Activar: remover el return temprano
                new_content = content.replace(
                    '    # DESACTIVADO: No crear grupos automáticamente para evitar conflictos con migración\n    return\n    \n    if not created or not instance.is_superuser:\n        return',
                    '    if not created or not instance.is_superuser:\n        return'
                )
                
                if new_content != content:
                    with open(signals_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    self.stdout.write(
                        self.style.SUCCESS('✓ Creación automática de grupos ACTIVADA')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('La creación automática ya estaba activada')
                    )
            
            elif options['desactivar']:
                # Desactivar: agregar el return temprano
                new_content = content.replace(
                    '    if not created or not instance.is_superuser:\n        return',
                    '    # DESACTIVADO: No crear grupos automáticamente para evitar conflictos con migración\n    return\n    \n    if not created or not instance.is_superuser:\n        return'
                )
                
                if new_content != content:
                    with open(signals_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    self.stdout.write(
                        self.style.SUCCESS('✓ Creación automática de grupos DESACTIVADA')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('La creación automática ya estaba desactivada')
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error modificando signals.py: {e}')
            )