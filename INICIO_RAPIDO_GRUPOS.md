# 🚀 Inicio Rápido - Configuración de Grupos

## ✅ Configuración Automática (Recomendado)

Los grupos se configuran **automáticamente** cuando ejecutas las migraciones:

```bash
python manage.py migrate
```

¡Eso es todo! Los grupos ya están listos.

## 🔧 Configuración Manual (Si es necesario)

### Opción 1: Script Python
```bash
python configurar_grupos_sistema.py
```

### Opción 2: Comando Django
```bash
python manage.py configurar_grupos
```

### Opción 3: Setup Completo (Incluye usuario admin)
```bash
python manage.py setup_inicial
```

## 📋 Grupos Configurados

Se crean automáticamente estos 6 grupos:

1. **Administración** - Administradores del blog
2. **Blog Autor** - Autores de noticias  
3. **Blog Moderador** - Moderadores del blog
4. **Editor** - Editor de contenido
5. **Estudiantes** - Estudiantes del sistema
6. **Profesores** - Profesores con gestión de cursos
7. **Secretaría** - Personal administrativo

## 🔍 Verificar Configuración

### Ver grupos en Admin Django
```
http://localhost:8000/admin/auth/group/
```

### Ver información por comando
```bash
python manage.py configurar_grupos --info
```

## 👥 Asignar Usuarios a Grupos

### En el Admin Django
1. Ve a `Usuarios` → Selecciona un usuario
2. En "Permisos" → Selecciona los grupos
3. Guarda

### Por código Python
```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='nombre_usuario')
grupo = Group.objects.get(name='Estudiantes')
user.groups.add(grupo)
```

## 🆘 Solución de Problemas

### Los grupos no aparecen
```bash
# Forzar creación
python manage.py configurar_grupos --force
```

### Error en migraciones
```bash
# Aplicar migraciones primero
python manage.py migrate
# Luego configurar grupos
python configurar_grupos_sistema.py
```

### Verificar que todo funciona
```bash
python manage.py configurar_grupos --info
```

## 📁 Archivos Importantes

- `principal/config_grupos.py` - Configuración de grupos
- `principal/signals.py` - Creación automática
- `configurar_grupos_sistema.py` - Script manual

---

**¿Necesitas ayuda?** Ejecuta: `python manage.py configurar_grupos --info`