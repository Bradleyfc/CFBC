"""
Signals para configuración automática del sistema
"""
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, User
from principal.config_grupos import GRUPOS_SISTEMA, configurar_permisos_grupo
import logging

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def crear_grupos_por_defecto(sender, **kwargs):
    """
    Crea automáticamente los grupos por defecto después de las migraciones
    """
    # Solo ejecutar para la app principal para evitar duplicados
    if sender.name != 'principal':
        return
    
    try:
        # Verificar que las tablas necesarias existan
        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError
        
        try:
            table_names = connection.introspection.table_names()
            if 'auth_group' not in table_names:
                logger.info("Tabla auth_group no disponible, saltando creación de grupos")
                return
        except (OperationalError, ProgrammingError):
            logger.info("Base de datos no lista, saltando creación de grupos")
            return
        
        logger.info("Verificando y configurando grupos por defecto del sistema...")
        
        grupos_creados = 0
        grupos_existentes = 0
        
        for config_grupo in GRUPOS_SISTEMA:
            nombre_grupo = config_grupo['nombre']
            
            try:
                # Verificar si el grupo ya existe
                if Group.objects.filter(name=nombre_grupo).exists():
                    grupos_existentes += 1
                    logger.info(f"○ Grupo '{nombre_grupo}' ya existe")
                    continue
                
                # Crear el grupo
                grupo = Group.objects.create(name=nombre_grupo)
                grupos_creados += 1
                logger.info(f"✓ Grupo '{nombre_grupo}' creado")
                
                # Configurar permisos (con manejo de errores)
                try:
                    configurar_permisos_grupo(grupo, config_grupo)
                except Exception as e:
                    logger.warning(f"Error configurando permisos para {nombre_grupo}: {e}")
                    
            except Exception as e:
                logger.error(f"Error creando grupo '{nombre_grupo}': {e}")
        
        if grupos_creados > 0:
            logger.info(f"Post-migrate: {grupos_creados} grupos creados, {grupos_existentes} ya existían")
        elif grupos_existentes > 0:
            logger.info("Todos los grupos ya estaban configurados")
            
    except Exception as e:
        logger.error(f"Error general configurando grupos en post_migrate: {e}")

@receiver(post_save, sender=User)
def crear_grupos_al_crear_superusuario(sender, instance, created, **kwargs):
    """
    Crea grupos automáticamente cuando se crea un superusuario
    """
    if not created or not instance.is_superuser:
        return
    
    try:
        logger.info(f"Superusuario '{instance.username}' creado, verificando grupos...")
        
        grupos_creados = 0
        grupos_existentes = 0
        
        for config_grupo in GRUPOS_SISTEMA:
            nombre_grupo = config_grupo['nombre']
            
            try:
                # Verificar si el grupo ya existe
                grupo, created_grupo = Group.objects.get_or_create(name=nombre_grupo)
                
                if created_grupo:
                    grupos_creados += 1
                    logger.info(f"✓ Grupo '{nombre_grupo}' creado automáticamente")
                    
                    # Configurar permisos
                    try:
                        configurar_permisos_grupo(grupo, config_grupo)
                        logger.info(f"  → Permisos configurados para '{nombre_grupo}'")
                    except Exception as e:
                        logger.warning(f"Error configurando permisos para {nombre_grupo}: {e}")
                else:
                    grupos_existentes += 1
                    
            except Exception as e:
                logger.error(f"Error procesando grupo '{nombre_grupo}': {e}")
        
        if grupos_creados > 0:
            logger.info(f"🎉 Superusuario creado: {grupos_creados} grupos configurados automáticamente")
            print(f"\n{'='*60}")
            print("🎉 ¡GRUPOS CONFIGURADOS AUTOMÁTICAMENTE!")
            print(f"✓ {grupos_creados} grupos creados")
            print(f"○ {grupos_existentes} grupos ya existían")
            print(f"📊 Total: {len(GRUPOS_SISTEMA)} grupos disponibles")
            print("\n📋 Grupos configurados:")
            for config_grupo in GRUPOS_SISTEMA:
                print(f"  • {config_grupo['nombre']}: {config_grupo['descripcion']}")
            print(f"\n🔗 Admin: http://localhost:8000/admin/auth/group/")
            print(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"Error configurando grupos para superusuario: {e}")