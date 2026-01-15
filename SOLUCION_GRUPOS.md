# 🔧 Solución - Configuración Automática de Grupos

## ✅ Problema Solucionado

El error de importación se ha corregido. Ahora los grupos se configuran automáticamente de **2 formas**:

### 1. **Al ejecutar migraciones** (post_migrate signal)
```bash
python manage.py migrate
```

### 2. **Al iniciar el servidor** (apps.py ready())
```bash
python manage.py runserver
```

## 🚀 Cómo Funciona Ahora

### Verificación Automática
- **Al iniciar el servidor**: Verifica si los grupos existen
- **Si no existen**: Los crea automáticamente
- **Si ya existen**: No hace nada (no duplica)

### Grupos que se Crean
1. **Administración**
2. **Blog Autor** 
3. **Blog Moderador**
4. **Editor**
5. **Estudiantes**
6. **Profesores**
7. **Secretaría**

## 🔍 Verificar que Funciona

### Opción 1: Script de Prueba
```bash
python test_grupos.py
```

### Opción 2: Comando Django
```bash
python manage.py verificar_grupos
```

### Opción 3: Admin Django
Ve a: `http://localhost:8000/admin/auth/group/`

## 🛠️ Si Hay Problemas

### 1. Reiniciar el Servidor
```bash
# Detener el servidor (Ctrl+C)
# Luego iniciar de nuevo
python manage.py runserver
```

### 2. Forzar Migración
```bash
python manage.py migrate --run-syncdb
```

### 3. Crear Manualmente
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import Group

grupos = ['Administración', 'Blog Autor', 'Blog Moderador', 'Editor', 'Estudiantes', 'Profesores', 'Secretaría']

for nombre in grupos:
    grupo, created = Group.objects.get_or_create(name=nombre)
    if created:
        print(f"✓ {nombre} creado")
    else:
        print(f"○ {nombre} ya existe")
```

## ✅ Confirmación

Después de iniciar el servidor, deberías ver en los logs:
```
✓ Grupo 'Administración' creado al iniciar servidor
✓ Grupo 'Blog Autor' creado al iniciar servidor
...
Servidor iniciado: 7 grupos configurados automáticamente
```

## 🎯 Asignar Usuarios a Grupos

### En el Admin Django
1. Ve a `Usuarios` → Selecciona un usuario
2. En "Permisos" → Marca los grupos deseados
3. Guarda

### Por Código
```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='tu_usuario')
grupo = Group.objects.get(name='Estudiantes')
user.groups.add(grupo)
```

---

**¡Listo!** Los grupos se configuran automáticamente al iniciar el servidor. 🎉