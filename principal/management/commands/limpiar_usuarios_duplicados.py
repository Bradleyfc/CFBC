from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from accounts.models import Registro
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Limpia usuarios duplicados y problemáticos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duplicados-email',
            action='store_true',
            help='Eliminar usuarios con emails duplicados (mantiene el más reciente)',
        )
        parser.add_argument(
            '--duplicados-username',
            action='store_true',
            help='Eliminar usuarios con usernames duplicados (mantiene el más reciente)',
        )
        parser.add_argument(
            '--sin-registro',
            action='store_true',
            help='Eliminar usuarios sin registro asociado',
        )
        parser.add_argument(
            '--usuarios-vacios',
            action='store_true',
            help='Eliminar usuarios con datos incompletos',
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirmar la eliminación (requerido para ejecutar)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin hacer cambios',
        )

    def handle(self, *args, **options):
        if not options['confirmar'] and not options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    'ADVERTENCIA: Esta operación eliminará usuarios de forma permanente.\n'
                    'Usa --confirmar para ejecutar o --dry-run para simular.'
                )
            )
            return

        eliminados_total = 0
        
        # 1. Limpiar usuarios con emails duplicados
        if options['duplicados_email']:
            eliminados = self.limpiar_emails_duplicados(options['dry_run'])
            eliminados_total += eliminados

        # 2. Limpiar usuarios con usernames duplicados
        if options['duplicados_username']:
            eliminados = self.limpiar_usernames_duplicados(options['dry_run'])
            eliminados_total += eliminados

        # 3. Limpiar usuarios sin registro asociado
        if options['sin_registro']:
            eliminados = self.limpiar_usuarios_sin_registro(options['dry_run'])
            eliminados_total += eliminados

        # 4. Limpiar usuarios con datos incompletos
        if options['usuarios_vacios']:
            eliminados = self.limpiar_usuarios_vacios(options['dry_run'])
            eliminados_total += eliminados

        # Resumen final
        if options['dry_run']:
            self.stdout.write(
                self.style.SUCCESS(f'\n[DRY RUN] Se eliminarían {eliminados_total} usuarios en total.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nEliminación completada: {eliminados_total} usuarios eliminados.')
            )

    def limpiar_emails_duplicados(self, dry_run=False):
        """Elimina usuarios con emails duplicados, manteniendo el más reciente"""
        self.stdout.write('\n--- Limpiando emails duplicados ---')
        
        # Encontrar emails duplicados (excluyendo emails vacíos)
        emails_duplicados = (
            User.objects
            .exclude(email='')
            .exclude(email__isnull=True)
            .values('email')
            .annotate(count=Count('email'))
            .filter(count__gt=1)
        )

        eliminados = 0
        
        for email_data in emails_duplicados:
            email = email_data['email']
            usuarios = User.objects.filter(email=email).order_by('-date_joined')
            
            # Mantener el más reciente, eliminar los demás
            usuarios_a_eliminar = usuarios[1:]  # Todos excepto el primero (más reciente)
            
            self.stdout.write(f'Email duplicado: {email} ({len(usuarios_a_eliminar)} duplicados)')
            
            for usuario in usuarios_a_eliminar:
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] Eliminaría: {usuario.username} (ID: {usuario.id})')
                else:
                    try:
                        usuario.delete()
                        self.stdout.write(f'  Eliminado: {usuario.username} (ID: {usuario.id})')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error eliminando {usuario.username}: {str(e)}'))
                        continue
                
                eliminados += 1

        self.stdout.write(f'Emails duplicados procesados: {eliminados} usuarios')
        return eliminados

    def limpiar_usernames_duplicados(self, dry_run=False):
        """Elimina usuarios con usernames duplicados, manteniendo el más reciente"""
        self.stdout.write('\n--- Limpiando usernames duplicados ---')
        
        # Encontrar usernames duplicados
        usernames_duplicados = (
            User.objects
            .values('username')
            .annotate(count=Count('username'))
            .filter(count__gt=1)
        )

        eliminados = 0
        
        for username_data in usernames_duplicados:
            username = username_data['username']
            usuarios = User.objects.filter(username=username).order_by('-date_joined')
            
            # Mantener el más reciente, eliminar los demás
            usuarios_a_eliminar = usuarios[1:]
            
            self.stdout.write(f'Username duplicado: {username} ({len(usuarios_a_eliminar)} duplicados)')
            
            for usuario in usuarios_a_eliminar:
                if dry_run:
                    self.stdout.write(f'  [DRY RUN] Eliminaría: {usuario.username} (ID: {usuario.id})')
                else:
                    try:
                        usuario.delete()
                        self.stdout.write(f'  Eliminado: {usuario.username} (ID: {usuario.id})')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error eliminando {usuario.username}: {str(e)}'))
                        continue
                
                eliminados += 1

        self.stdout.write(f'Usernames duplicados procesados: {eliminados} usuarios')
        return eliminados

    def limpiar_usuarios_sin_registro(self, dry_run=False):
        """Elimina usuarios que no tienen registro asociado"""
        self.stdout.write('\n--- Limpiando usuarios sin registro ---')
        
        usuarios_sin_registro = User.objects.filter(
            is_superuser=False,
            registro__isnull=True
        )
        
        count = usuarios_sin_registro.count()
        self.stdout.write(f'Usuarios sin registro encontrados: {count}')
        
        if dry_run:
            for usuario in usuarios_sin_registro[:10]:  # Mostrar solo los primeros 10
                self.stdout.write(f'  [DRY RUN] Eliminaría: {usuario.username} (ID: {usuario.id})')
            if count > 10:
                self.stdout.write(f'  ... y {count - 10} más')
        else:
            try:
                eliminados, _ = usuarios_sin_registro.delete()
                self.stdout.write(f'Eliminados {eliminados} usuarios sin registro')
                return eliminados
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error eliminando usuarios sin registro: {str(e)}'))
                return 0
        
        return count if dry_run else 0

    def limpiar_usuarios_vacios(self, dry_run=False):
        """Elimina usuarios con datos incompletos o problemáticos"""
        self.stdout.write('\n--- Limpiando usuarios con datos incompletos ---')
        
        # Usuarios con datos problemáticos
        usuarios_vacios = User.objects.filter(
            is_superuser=False
        ).filter(
            # Sin email o email inválido
            Q(email='') | 
            Q(email__isnull=True) |
            # Sin nombre y apellido
            (Q(first_name='') & Q(last_name='')) |
            # Username muy corto o problemático
            Q(username__regex=r'^.{1,2}$')
        )
        
        count = usuarios_vacios.count()
        self.stdout.write(f'Usuarios con datos incompletos encontrados: {count}')
        
        if dry_run:
            for usuario in usuarios_vacios[:10]:
                self.stdout.write(f'  [DRY RUN] Eliminaría: {usuario.username} (email: {usuario.email})')
            if count > 10:
                self.stdout.write(f'  ... y {count - 10} más')
        else:
            eliminados = 0
            for usuario in usuarios_vacios:
                try:
                    usuario.delete()
                    eliminados += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error eliminando {usuario.username}: {str(e)}'))
            
            self.stdout.write(f'Eliminados {eliminados} usuarios con datos incompletos')
            return eliminados
        
        return count if dry_run else 0