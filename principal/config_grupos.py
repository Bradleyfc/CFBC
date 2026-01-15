"""
Configuración centralizada de grupos y permisos del sistema
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)

# Grupos por defecto que se crearán automáticamente
GRUPOS_SISTEMA = [
    {
        'nombre': 'Administración',
        'descripcion': 'Administradores del sistema de blog con acceso completo',
        'permisos_modelos': {
            'blog': ['noticia', 'categoria', 'comentario'],
        },
        'acciones': ['add', 'change', 'delete', 'view']
    },
    {
        'nombre': 'Blog Autor',
        'descripcion': 'Autores que pueden crear y editar sus propias noticias',
        'permisos_modelos': {
            'blog': ['noticia', 'categoria'],
        },
        'acciones': ['add', 'change', 'view']
    },
    {
        'nombre': 'Blog Moderador',
        'descripcion': 'Moderadores del blog con permisos de moderación',
        'permisos_modelos': {
            'blog': ['noticia', 'comentario'],
        },
        'acciones': ['add', 'change', 'delete', 'view']
    },
    {
        'nombre': 'Editor',
        'descripcion': 'Editor con permisos de edición de contenido',
        'permisos_modelos': {
            'blog': ['noticia', 'comentario'],
        },
        'acciones': ['add', 'change', 'delete', 'view']
    },
    {
        'nombre': 'Estudiantes',
        'descripcion': 'Estudiantes del sistema educativo',
        'permisos_modelos': {
            'principal': ['curso', 'matriculas'],
        },
        'acciones': ['view']
    },
    {
        'nombre': 'Profesores',
        'descripcion': 'Profesores con acceso a gestión de cursos',
        'permisos_modelos': {
            'principal': ['curso', 'matriculas', 'calificaciones', 'asistencia'],
        },
        'acciones': ['add', 'change', 'view']
    },
    {
        'nombre': 'Secretaría',
        'descripcion': 'Personal de secretaría con acceso administrativo',
        'permisos_modelos': {
            'principal': ['matriculas'],
            'accounts': ['registro'],
        },
        'acciones': ['add', 'change', 'view']
    }
]

def obtener_nombres_grupos():
    """Retorna solo los nombres de los grupos"""
    return [grupo['nombre'] for grupo in GRUPOS_SISTEMA]

def obtener_config_grupo(nombre_grupo):
    """Obtiene la configuración de un grupo específico"""
    for grupo in GRUPOS_SISTEMA:
        if grupo['nombre'] == nombre_grupo:
            return grupo
    return None

def configurar_permisos_grupo(grupo, config_grupo):
    """
    Configura los permisos para un grupo específico
    """
    try:
        permisos_asignados = 0
        
        # Iterar por cada app y sus modelos
        for app_label, modelos in config_grupo.get('permisos_modelos', {}).items():
            for modelo in modelos:
                try:
                    content_type = ContentType.objects.get(app_label=app_label, model=modelo)
                    
                    # Asignar cada acción permitida
                    for accion in config_grupo.get('acciones', []):
                        codename = f"{accion}_{modelo}"
                        try:
                            permiso = Permission.objects.get(
                                content_type=content_type,
                                codename=codename
                            )
                            grupo.permissions.add(permiso)
                            permisos_asignados += 1
                        except Permission.DoesNotExist:
                            # No mostrar warning para evitar spam en logs
                            pass
                            
                except ContentType.DoesNotExist:
                    # No mostrar warning para evitar spam en logs
                    pass
        
        if permisos_asignados > 0:
            logger.info(f"  → {permisos_asignados} permisos asignados al grupo {grupo.name}")
            
    except Exception as e:
        logger.error(f"Error configurando permisos para grupo {grupo.name}: {e}")

def obtener_info_grupos():
    """
    Función utilitaria para obtener información de los grupos configurados
    """
    info_grupos = {}
    nombres_grupos = [g['nombre'] for g in GRUPOS_SISTEMA]
    
    for grupo in Group.objects.filter(name__in=nombres_grupos):
        # Buscar la configuración del grupo
        config = next((g for g in GRUPOS_SISTEMA if g['nombre'] == grupo.name), {})
        
        info_grupos[grupo.name] = {
            'id': grupo.id,
            'usuarios_count': grupo.user_set.count(),
            'permisos_count': grupo.permissions.count(),
            'descripcion': config.get('descripcion', 'Sin descripción')
        }
    
    return info_grupos