from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from principal.models import Curso

class Command(BaseCommand):
    help = 'Actualiza automáticamente los estados de los cursos basándose en las fechas límite de inscripción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué cambios se harían sin aplicarlos realmente',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = date.today()
        
        # Obtener cursos que tienen fecha límite de inscripción
        cursos_con_fecha = Curso.objects.filter(enrollment_deadline__isnull=False)
        
        cambios_realizados = 0
        
        for curso in cursos_con_fecha:
            estado_actual = curso.status
            estado_dinamico = curso.get_dynamic_status()
            
            # Si el estado dinámico es diferente al estado actual, actualizar
            if estado_actual != estado_dinamico:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY RUN] Curso "{curso.name}": '
                            f'{curso.get_status_display()} → {curso.get_dynamic_status_display()}'
                        )
                    )
                else:
                    curso.status = estado_dinamico
                    curso.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Actualizado curso "{curso.name}": '
                            f'{dict(curso.STATUS_CHOICES)[estado_actual]} → {curso.get_dynamic_status_display()}'
                        )
                    )
                cambios_realizados += 1
        
        if cambios_realizados == 0:
            self.stdout.write(
                self.style.SUCCESS('No se encontraron cursos que necesiten actualización de estado.')
            )
        else:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'Se encontraron {cambios_realizados} cursos que necesitan actualización.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Se actualizaron {cambios_realizados} cursos exitosamente.')
                )
        
        # Mostrar información adicional sobre fechas
        self.stdout.write(f'\nFecha actual del servidor: {today}')
        self.stdout.write(f'Zona horaria del servidor: {timezone.get_current_timezone()}')