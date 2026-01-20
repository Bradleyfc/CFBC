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
def agregar_superusuario_a_administracion(sender, instance, created, **kwargs):
    """
    Agrega automáticamente el superusuario al grupo Administración cuando se crea
    """
    if not created or not instance.is_superuser:
        return
    
    try:
        from django.db import transaction
        
        with transaction.atomic():
            # Crear o obtener el grupo Administración
            grupo_admin, created_grupo = Group.objects.get_or_create(name='Administración')
            
            if created_grupo:
                logger.info(f"✓ Grupo 'Administración' creado automáticamente")
                
                # Configurar permisos del grupo Administración
                try:
                    from principal.config_grupos import obtener_config_grupo, configurar_permisos_grupo
                    config_admin = obtener_config_grupo('Administración')
                    if config_admin:
                        configurar_permisos_grupo(grupo_admin, config_admin)
                        logger.info("  → Permisos del grupo Administración configurados")
                except Exception as e:
                    logger.warning(f"Error configurando permisos para Administración: {e}")
            
            # Verificar si el usuario ya está en el grupo
            if not instance.groups.filter(name='Administración').exists():
                # Agregar el superusuario al grupo Administración
                instance.groups.add(grupo_admin)
                logger.info(f"✓ Superusuario '{instance.username}' agregado al grupo Administración")
                
                # Mostrar mensaje de confirmación
                print(f"\n{'='*60}")
                print("🎉 ¡SUPERUSUARIO AGREGADO AL GRUPO ADMINISTRACIÓN!")
                print(f"👤 Usuario: {instance.username}")
                print(f"👥 Grupo: Administración")
                print(f"🔧 Permisos: Configurados automáticamente")
                print(f"\n🔗 Verificar en: http://localhost:8000/admin/auth/group/")
                print(f"{'='*60}\n")
            else:
                logger.info(f"○ Superusuario '{instance.username}' ya está en el grupo Administración")
        
    except Exception as e:
        logger.error(f"Error agregando superusuario al grupo Administración: {e}")
        import traceback
        logger.error(f"Detalles: {traceback.format_exc()}")