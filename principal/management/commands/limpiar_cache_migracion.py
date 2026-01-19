from django.core.management.base import BaseCommand
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Limpia el cache de interrupción que puede estar bloqueando migraciones y combinaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verificar',
            action='store_true',
            help='Solo verificar el estado del cache sin limpiar',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔧 Herramienta de limpieza de cache de migración/combinación')
        self.stdout.write('='*60)
        
        # Lista de claves de cache que pueden causar problemas
        claves_problematicas = [
            'combinacion_interrumpida',
            'combinacion_estado_interrupcion', 
            'combinacion_interrumpida_info',
            'combinacion_estado',
            'combinacion_en_progreso',
            'combinacion_progreso',
            'combinacion_completada',
            'combinacion_error',
            'migracion_progreso',
            'migracion_en_progreso'
        ]
        
        # Verificar estado actual
        self.stdout.write('\n🔍 Estado actual del cache:')
        claves_activas = []
        
        for clave in claves_problematicas:
            valor = cache.get(clave)
            if valor is not None:
                claves_activas.append(clave)
                self.stdout.write(f'  ⚠️  {clave}: {valor}')
            else:
                self.stdout.write(f'  ✅ {clave}: No definida')
        
        if options['verificar']:
            if claves_activas:
                self.stdout.write(f'\n⚠️ Se encontraron {len(claves_activas)} claves activas que podrían causar problemas.')
                self.stdout.write('Ejecuta sin --verificar para limpiarlas.')
            else:
                self.stdout.write('\n✅ No hay claves problemáticas en el cache.')
            return
        
        # Limpiar cache
        if claves_activas:
            self.stdout.write(f'\n🧹 Limpiando {len(claves_activas)} claves problemáticas...')
            
            for clave in claves_activas:
                try:
                    cache.delete(clave)
                    self.stdout.write(f'  ✅ Eliminada: {clave}')
                except Exception as e:
                    self.stdout.write(f'  ❌ Error eliminando {clave}: {str(e)}')
            
            self.stdout.write('\n✅ Cache limpiado correctamente.')
            self.stdout.write('🚀 Las migraciones y combinaciones deberían funcionar ahora.')
        else:
            self.stdout.write('\n💡 No había claves problemáticas que limpiar.')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📋 Comandos útiles:')
        self.stdout.write('  • Verificar cache: python manage.py limpiar_cache_migracion --verificar')
        self.stdout.write('  • Limpiar cache: python manage.py limpiar_cache_migracion')
        self.stdout.write('  • Probar migración: Ve al admin → Datos Archivados → Configurar Migración')