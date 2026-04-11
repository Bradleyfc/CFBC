# Configuración Automática de Grupos

Este sistema configura automáticamente los grupos por defecto del sistema con sus permisos correspondientes.

## Grupos Configurados Automáticamente

Los siguientes grupos se crean automáticamente cuando se ejecutan las migraciones:

### 1. **Administración**
- **Descripción**: Administradores del sistema de blog con acceso completo
- **Permisos**: Crear, editar, eliminar y ver noticias, categorías y comentarios
- **Modelos**: blog.noticia, blog.categoria, blog.comentario

### 2. **Blog Autor** 
- **Descripción**: Autores que pueden crear y editar sus propias noticias
- **Permisos**: Crear, editar y ver noticias y categorías
- **Modelos**: blog.noticia, blog.categoria

### 3. **Blog Moderador**
- **Descripción**: Moderadores del blog con permisos de moderación
- **Permisos**: Crear, editar, eliminar y ver noticias y comentarios
- **Modelos**: blog.noticia, blog.comentario

### 4. **Editor**
- **Descripción**: Editor con permisos de edición de contenido
- **Permisos**: Crear, editar, eliminar y ver noticias y comentarios
- **Modelos**: blog.noticia, blog.comentario

### 5. **Estudiantes**
- **Descripción**: Estudiantes del sistema educativo
- **Permisos**: Solo visualización de cursos y matrículas
- **Modelos**: principal.curso, principal.matriculas

### 5. **Profesores**
- **Descripción**: Profesores con acceso a gestión de cursos
- **Permisos**: Crear, editar y ver cursos, matrículas, calificaciones y asistencias
- **Modelos**: principal.curso, principal.matriculas, principal.calificaciones, principal.asistencia

### 6. **Secretaría**
- **Descripción**: Personal de secretaría con acceso administrativo
- **Permisos**: Crear, editar y ver matrículas y registros de usuarios
- **Modelos**: principal.matriculas, accounts.registro

## Configuración Automática

### Método 1: Automático (Recomendado)
Los grupos se crean automáticamente cuando ejecutas las migraciones:

```bash
python manage.py migrate
```

### Método 2: Script Manual
Si necesitas configurar los grupos manualmente:

```bash
python configurar_grupos_sistema.py
```

### Método 3: Comando de Django
Para configurar o reconfigurar los grupos:

```bash
# Configurar grupos
python manage.py configurar_grupos

# Forzar reconfiguración de permisos
python manage.py configurar_grupos --force

# Ver información de grupos configurados
python manage.py configurar_grupos --info
```

## Verificación

### En el Administrador de Django
1. Ve a: `http://localhost:8000/admin/auth/group/`
2. Verifica que todos los grupos estén creados
3. Revisa los permisos asignados a cada grupo

### Por Comando
```bash
python manage.py configurar_grupos --info
```

## Personalización

### Agregar Nuevos Grupos
Edita el archivo `principal/config_grupos.py` y agrega la configuración del nuevo grupo:

```python
{
    'nombre': 'NuevoGrupo',
    'descripcion': 'Descripción del nuevo grupo',
    'permisos_modelos': {
        'app_name': ['modelo1', 'modelo2'],
    },
    'acciones': ['add', 'change', 'view']
}
```

### Modificar Permisos
1. Edita `principal/config_grupos.py`
2. Ejecuta: `python manage.py configurar_grupos --force`

## Asignación de Usuarios a Grupos

### En el Admin de Django
1. Ve a `Usuarios` en el admin
2. Edita un usuario
3. En la sección "Permisos", selecciona los grupos apropiados

### Por Código
```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='nombre_usuario')
grupo = Group.objects.get(name='Estudiantes')
user.groups.add(grupo)
```

## Troubleshooting

### Los grupos no se crean automáticamente
1. Verifica que `principal.signals` esté importado en `principal/apps.py`
2. Ejecuta las migraciones: `python manage.py migrate`
3. Si persiste, ejecuta manualmente: `python manage.py configurar_grupos`

### Faltan permisos en un grupo
1. Ejecuta: `python manage.py configurar_grupos --force`
2. Verifica que los modelos existan en la base de datos
3. Revisa los logs para errores específicos

### Error de permisos no encontrados
Algunos permisos pueden no existir si:
- Los modelos no están migrados
- Los nombres de modelos en la configuración son incorrectos
- Las apps no están instaladas

## Logs

Los logs de configuración se guardan en el logger de Django. Para ver los logs:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Archivos Relacionados

- `principal/config_grupos.py` - Configuración de grupos
- `principal/signals.py` - Signals para creación automática
- `principal/management/commands/configurar_grupos.py` - Comando de Django
- `configurar_grupos_sistema.py` - Script independiente