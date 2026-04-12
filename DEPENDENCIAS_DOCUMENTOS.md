# 📦 Dependencias del Sistema de Documentos

## 🎯 Resumen
Este documento detalla todas las dependencias necesarias y opcionales para el sistema de gestión de documentos del CFBC.

## 🔧 Dependencias Principales (requirements.txt)

### 📁 Gestión de Archivos y Documentos
```
python-magic==0.4.27          # Detección automática de tipos MIME
python-magic-bin==0.4.14      # Binarios para Windows
django-storages==1.14.4       # Almacenamiento flexible (local/nube)
filetype==1.2.0               # Validación de tipos de archivo
python-mimetypes==1.1.0       # Manejo avanzado de MIME types
```

### 📄 Procesamiento de Documentos Office
```
python-docx==1.1.2            # Lectura/escritura de archivos DOCX
xlsxwriter==3.2.0             # Creación de archivos Excel avanzados
```

### 🗜️ Soporte para Archivos Comprimidos
```
py7zr==0.22.0                 # Archivos 7z
rarfile==4.2                  # Archivos RAR
zipfile36==0.1.3              # Soporte extendido para ZIP
```

### 🖼️ Procesamiento de Imágenes Avanzado
```
Wand==0.6.13                  # ImageMagick binding para thumbnails
```

### 📧 Notificaciones y Emails
```
django-email-extras==0.3.0    # Funcionalidades extra para emails
premailer==3.10.0             # Conversión de CSS inline para emails
```

### 🚀 Performance y Caching
```
django-redis==5.4.0           # Cache con Redis
redis==5.2.1                  # Cliente Redis
```

### 🛠️ Herramientas de Desarrollo
```
django-extensions==3.2.3      # Comandos útiles para Django
django-debug-toolbar==4.4.6   # Toolbar de debugging
```

### 📊 Utilidades
```
humanize==4.11.0              # Formateo legible de tamaños de archivo
```

## 🌟 Dependencias Opcionales (requirements-optional.txt)

### ☁️ Almacenamiento en la Nube
- **AWS S3**: `boto3`, `botocore`
- **Google Cloud**: `google-cloud-storage`

### 🔍 Procesamiento Avanzado de Documentos
- **Thumbnails**: `pdf2image`, `Wand`
- **Extracción de texto**: `PyPDF2`, `pdfplumber`, `textract`
- **Conversión**: `pandoc`, `pypandoc`

### 🔒 Seguridad Avanzada
- **Escaneo de virus**: `pyclamd` (requiere ClamAV)
- **Firmas digitales**: `pyOpenSSL`

### 📈 Monitoreo y Métricas
- **Logging estructurado**: `structlog`, `django-structlog`
- **Métricas**: `django-prometheus`, `prometheus-client`

## 🚀 Instalación

### Método 1: Script Automático (Recomendado)
```bash
python install_requirements.py
```

### Método 2: Manual
```bash
# Dependencias principales
pip install -r requirements.txt

# Dependencias opcionales (opcional)
pip install -r requirements-optional.txt
```

### Método 3: Solo lo esencial
```bash
# Solo las dependencias mínimas para funcionar
pip install Django==5.2.7 django-tailwind-cli==4.4.2 psycopg2==2.9.11 pillow==12.0.0
```

## 📋 Configuración Post-Instalación

### 1. Migraciones de Base de Datos
```bash
python manage.py makemigrations course_documents
python manage.py migrate
```

### 2. Compilar Tailwind CSS
```bash
python manage.py tailwind build
```

### 3. Configurar Almacenamiento (Opcional)
```python
# En settings.py para almacenamiento local
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Para AWS S3 (opcional)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'tu-bucket'
```

### 4. Configurar Redis (Opcional)
```python
# En settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 🔧 Funcionalidades por Dependencia

### Tipos de Archivo Soportados
| Extensión | Dependencia | Funcionalidad |
|-----------|-------------|---------------|
| PDF | `pypdf` | Lectura y procesamiento |
| DOCX | `python-docx` | Lectura de documentos Word |
| XLSX | `openpyxl`, `xlsxwriter` | Excel completo |
| PPT/PPTX | Nativo Django | Subida básica |
| ZIP | `zipfile36` | Extracción y validación |
| RAR | `rarfile` | Lectura de archivos RAR |
| 7Z | `py7zr` | Soporte completo 7-Zip |
| Imágenes | `pillow`, `Wand` | Procesamiento y thumbnails |

### Validaciones Implementadas
- ✅ **Tamaño máximo**: 10MB por archivo
- ✅ **Tipos permitidos**: Lista blanca de extensiones
- ✅ **Detección MIME**: Validación real del contenido
- ✅ **Nombres seguros**: Sanitización de nombres de archivo
- ✅ **Estructura de carpetas**: Organización automática

### Características de Seguridad
- 🔒 **Control de acceso**: Por rol (profesor/estudiante)
- 📊 **Auditoría completa**: Log de todas las acciones
- 🚫 **Validación estricta**: Múltiples capas de validación
- 🔍 **Detección de contenido**: Verificación real de archivos

## 🐛 Solución de Problemas

### Error: "No module named 'magic'"
```bash
# Windows
pip install python-magic-bin

# Linux/Mac
sudo apt-get install libmagic1  # Ubuntu/Debian
brew install libmagic           # macOS
```

### Error: "Wand not found"
```bash
# Instalar ImageMagick primero
# Windows: Descargar desde https://imagemagick.org/
# Linux: sudo apt-get install imagemagick
# Mac: brew install imagemagick
```

### Error: "Redis connection failed"
```bash
# Instalar y ejecutar Redis
# Windows: Usar Docker o WSL
# Linux: sudo apt-get install redis-server
# Mac: brew install redis
```

## 📈 Optimizaciones de Performance

### Caching Recomendado
```python
# Cache de vistas
@cache_page(60 * 15)  # 15 minutos
def document_list_view(request):
    pass

# Cache de templates
{% load cache %}
{% cache 500 document_list %}
    <!-- contenido -->
{% endcache %}
```

### Configuración de Producción
```python
# settings.py para producción
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com']

# Compresión de archivos estáticos
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Configuración de base de datos optimizada
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'conn_max_age': 600,
        }
    }
}
```

## 🎯 Próximas Mejoras

### Funcionalidades Planificadas
- [ ] **Previsualización de documentos**: Viewer integrado
- [ ] **Versionado de archivos**: Control de versiones
- [ ] **Colaboración**: Comentarios y anotaciones
- [ ] **Búsqueda full-text**: Indexación de contenido
- [ ] **API REST**: Acceso programático
- [ ] **Integración con Office 365**: Edición online
- [ ] **Firma digital**: Documentos firmados
- [ ] **Workflow de aprobación**: Proceso de revisión

### Dependencias Futuras
```
# Para búsqueda full-text
elasticsearch-dsl==8.15.0
django-elasticsearch-dsl==8.0

# Para previsualización
pdf.js  # Integración JavaScript
mammoth==1.8.0  # Conversión DOCX a HTML

# Para colaboración
django-channels==4.1.0  # WebSockets
channels-redis==4.2.0   # Backend para channels
```

---

**Nota**: Este sistema está diseñado para ser modular. Puedes instalar solo las dependencias que necesites según las funcionalidades que quieras usar.