# 📚 DOCUMENTACIÓN DEL PROYECTO

## 📋 Índice de Documentación Disponible

Este proyecto cuenta con la siguiente documentación importante:

---

## 🔐 Sistema de Usuarios

### 1. SISTEMA_RECUPERACION_USUARIOS.md
**Descripción:** Documentación completa del sistema de recuperación de usuarios archivados.

**Contenido:**
- Las 3 opciones de recuperación de cuentas
- Backend de autenticación automático
- Sistema de reclamación manual
- Comando administrativo para migración masiva
- Asignación automática al grupo "Estudiantes"
- Ejemplos de uso y configuración

**Cuándo consultarlo:**
- Para entender cómo funciona la recuperación de usuarios
- Para configurar el sistema de autenticación
- Para migrar usuarios de años anteriores

---

### 2. MODAL_LOGIN_USUARIOS_ANTERIORES.md
**Descripción:** Documentación del modal informativo en la página de login.

**Contenido:**
- Diseño y funcionamiento del modal
- Explicación de las 3 opciones para usuarios
- Cómo probar el modal
- Características de accesibilidad

**Cuándo consultarlo:**
- Para entender el flujo de usuario en el login
- Para modificar el contenido del modal
- Para verificar que el modal funciona correctamente

---

## 🚀 Despliegue y Hosting

### 3. INSTRUCCIONES_HOSTING.md
**Descripción:** Guía completa para desplegar el proyecto en un servidor de producción.

**Contenido:**
- Configuración del servidor
- Variables de entorno
- Migraciones de base de datos
- Configuración de archivos estáticos
- Troubleshooting

**Cuándo consultarlo:**
- Al desplegar el proyecto por primera vez
- Al actualizar el proyecto en producción
- Al resolver problemas de despliegue

---

## 📦 Dependencias

### 4. DEPENDENCIAS.md
**Descripción:** Lista completa de dependencias del proyecto y su propósito.

**Contenido:**
- Paquetes de Python requeridos
- Versiones específicas
- Propósito de cada dependencia
- Cómo instalar las dependencias

**Cuándo consultarlo:**
- Al configurar un nuevo entorno de desarrollo
- Al actualizar dependencias
- Al resolver conflictos de versiones

---

## 👨‍💼 Administración

### 5. ADMIN_FORMULARIOS_GUIA.md
**Descripción:** Guía para administradores sobre el uso de formularios y gestión del sistema.

**Contenido:**
- Cómo usar el panel de administración
- Gestión de usuarios y permisos
- Configuración de formularios
- Mejores prácticas

**Cuándo consultarlo:**
- Para administradores nuevos
- Al configurar permisos
- Al gestionar usuarios

---

### 6. INSTRUCCIONES_PRUEBA_ADMIN.md
**Descripción:** Instrucciones para probar funcionalidades administrativas.

**Contenido:**
- Cómo probar el panel de administración
- Casos de prueba comunes
- Verificación de permisos

**Cuándo consultarlo:**
- Al probar nuevas funcionalidades
- Al verificar permisos
- Al hacer QA del sistema

---

## 🛠️ Scripts Útiles

### Scripts de Python en la raíz:

1. **aplicar_migraciones_hosting.py**
   - Aplica migraciones en el servidor de hosting
   - Uso: `python aplicar_migraciones_hosting.py`

2. **create_pending_course.py**
   - Crea cursos pendientes en el sistema
   - Uso: `python create_pending_course.py`

3. **setup_blog_data.py**
   - Configura datos iniciales del blog
   - Uso: `python setup_blog_data.py`

4. **setup_editores.py**
   - Configura editores del sistema
   - Uso: `python setup_editores.py`

5. **setup_test_data.py**
   - Crea datos de prueba
   - Uso: `python setup_test_data.py`

### Scripts Batch:

1. **aplicar_migraciones.bat**
   - Aplica migraciones en Windows
   - Uso: Doble clic o `aplicar_migraciones.bat`

2. **crear_nuevo_curso.bat**
   - Asistente para crear nuevos cursos
   - Uso: Doble clic o `crear_nuevo_curso.bat`

---

## 📁 Estructura de Archivos Importantes

```
proyecto/
├── manage.py                          # Comando principal de Django
├── requirements.txt                   # Dependencias del proyecto
├── db.sqlite3                        # Base de datos (desarrollo)
├── .env                              # Variables de entorno (no en git)
│
├── 📚 Documentación/
│   ├── SISTEMA_RECUPERACION_USUARIOS.md
│   ├── MODAL_LOGIN_USUARIOS_ANTERIORES.md
│   ├── INSTRUCCIONES_HOSTING.md
│   ├── DEPENDENCIAS.md
│   ├── ADMIN_FORMULARIOS_GUIA.md
│   └── INSTRUCCIONES_PRUEBA_ADMIN.md
│
├── 🔧 Scripts/
│   ├── aplicar_migraciones_hosting.py
│   ├── create_pending_course.py
│   ├── setup_blog_data.py
│   ├── setup_editores.py
│   └── setup_test_data.py
│
├── cfbc/                             # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── datos_archivados/                 # App de datos archivados
│   ├── models.py
│   ├── views.py
│   ├── backends.py                   # Backend de autenticación
│   └── management/commands/
│       └── migrar_usuarios_archivados.py
│
├── principal/                        # App principal
├── blog/                            # App de blog
├── accounts/                        # App de cuentas
│
├── templates/                       # Templates HTML
│   ├── base.html
│   ├── registration/
│   │   └── login.html              # Con modal de usuarios anteriores
│   └── datos_archivados/
│       ├── reclamar_usuario.html
│       └── buscar_usuario.html
│
└── static/                          # Archivos estáticos
    ├── css/
    ├── js/
    └── images/
```

---

## 🚀 Inicio Rápido

### Para Desarrollo:

```bash
# 1. Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones
python manage.py migrate

# 4. Crear superusuario (si es necesario)
python manage.py createsuperuser

# 5. Iniciar servidor
python manage.py runserver
```

### Para Producción:

Consulta `INSTRUCCIONES_HOSTING.md` para instrucciones detalladas.

---

## 📞 Soporte

Para problemas o dudas:
1. Consulta la documentación relevante arriba
2. Revisa los logs en `logs/` (si existen)
3. Verifica la configuración en `.env`
4. Consulta el panel de administración de Django

---

## 🔄 Actualizaciones

Este documento se actualiza cuando se agrega nueva documentación importante al proyecto.

**Última actualización:** Noviembre 2024

---

## ✅ Checklist de Documentación

- ✅ Sistema de recuperación de usuarios documentado
- ✅ Modal de login documentado
- ✅ Instrucciones de hosting disponibles
- ✅ Dependencias listadas
- ✅ Guías de administración creadas
- ✅ Scripts documentados

---

**Todos los archivos de test, debug y temporales han sido eliminados. Solo queda la documentación esencial y los archivos de producción.**
