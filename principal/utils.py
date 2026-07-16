"""
Utilidades para la gestión de grupos y permisos
"""
from django.contrib.auth.models import Group, User
from .config_grupos import GRUPOS_SISTEMA, obtener_nombres_grupos
import logging

logger = logging.getLogger(__name__)

def verificar_grupos_configurados():
    """
    Verifica si todos los grupos están configurados correctamente
    """
    nombres_grupos = obtener_nombres_grupos()
    grupos_existentes = Group.objects.filter(name__in=nombres_grupos)
    
    return {
        'total_definidos': len(nombres_grupos),
        'total_configurados': grupos_existentes.count(),
        'faltantes': set(nombres_grupos) - set(grupos_existentes.values_list('name', flat=True)),
        'configurados_correctamente': grupos_existentes.count() == len(nombres_grupos)
    }

def asignar_usuario_a_grupo(usuario, nombre_grupo):
    """
    Asigna un usuario a un grupo específico
    """
    try:
        if isinstance(usuario, str):
            usuario = User.objects.get(username=usuario)
        
        grupo = Group.objects.get(name=nombre_grupo)
        usuario.groups.add(grupo)
        
        logger.info(f"Usuario {usuario.username} asignado al grupo {nombre_grupo}")
        return True
        
    except (User.DoesNotExist, Group.DoesNotExist) as e:
        logger.error(f"Error asignando usuario a grupo: {e}")
        return False

def obtener_usuarios_por_grupo():
    """
    Obtiene estadísticas de usuarios por grupo
    """
    nombres_grupos = obtener_nombres_grupos()
    estadisticas = {}
    
    for grupo in Group.objects.filter(name__in=nombres_grupos):
        estadisticas[grupo.name] = {
            'total_usuarios': grupo.user_set.count(),
            'usuarios': list(grupo.user_set.values_list('username', flat=True))
        }
    
    return estadisticas

def es_miembro_de_grupo(usuario, nombre_grupo):
    """
    Verifica si un usuario pertenece a un grupo específico
    """
    if isinstance(usuario, str):
        try:
            usuario = User.objects.get(username=usuario)
        except User.DoesNotExist:
            return False
    
    return usuario.groups.filter(name=nombre_grupo).exists()

def obtener_grupos_usuario(usuario):
    """
    Obtiene todos los grupos de un usuario
    """
    if isinstance(usuario, str):
        try:
            usuario = User.objects.get(username=usuario)
        except User.DoesNotExist:
            return []
    
    return list(usuario.groups.values_list('name', flat=True))

def configurar_usuario_inicial(username, email, password, grupos=None):
    """
    Configura un usuario inicial con grupos específicos
    Útil para setup inicial del sistema
    """
    try:
        # Crear o obtener usuario
        usuario, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            usuario.set_password(password)
            usuario.save()
            logger.info(f"Usuario {username} creado")
        else:
            logger.info(f"Usuario {username} ya existe")
        
        # Asignar grupos si se especifican
        if grupos:
            for nombre_grupo in grupos:
                asignar_usuario_a_grupo(usuario, nombre_grupo)
        
        return usuario
        
    except Exception as e:
        logger.error(f"Error configurando usuario inicial: {e}")
        return None