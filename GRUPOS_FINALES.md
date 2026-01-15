# 📋 Grupos Configurados Automáticamente

## ✅ Lista Final de Grupos

Los siguientes **6 grupos** se crean automáticamente al iniciar el servidor:

### 1. **Administración**
- **Descripción**: Administradores del sistema con acceso completo
- **Permisos**: Crear, editar, eliminar y ver todo el contenido del blog
- **Modelos**: blog.noticia, blog.categoria, blog.comentario

### 2. **Blog Autor**
- **Descripción**: Autores que pueden crear y editar noticias
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

## 🚀 Configuración Automática

### Al iniciar el servidor:
```bash
python manage.py runserver
```

### Verificar que funciona:
```bash
python test_grupos.py
```

### Ver en el admin:
```
http://localhost:8000/admin/auth/group/
```

## 🎯 Asignación de Usuarios

Para asignar usuarios a grupos, ve al admin de Django:
1. `Usuarios` → Selecciona un usuario
2. En "Permisos" → Marca los grupos apropiados
3. Guarda

---

**¡Los grupos se configuran automáticamente!** 🎉