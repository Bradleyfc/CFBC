# 📦 Dependencias del Sistema de Datos Archivados

Este documento describe todas las dependencias necesarias para el sistema de migración y gestión de datos archivados.

## 🚀 Instalación Rápida

```bash
pip install -r requirements.txt
```

## 📋 Dependencias por Categoría

### 🎯 **Core Django y Framework Web**
- **Django==5.2.7**: Framework web principal
- **djangorestframework==3.16.1**: API REST (futuras extensiones)
- **djangorestframework_simplejwt==5.5.1**: Autenticación JWT
- **django-crispy-forms==2.4**: Formularios mejorados
- **crispy-bootstrap5==2025.6**: Integración Bootstrap 5

### 🗄️ **Conectores de Base de Datos**
- **psycopg2==2.9.11**: Conector PostgreSQL (BD principal)
- **mysql-connector-python==9.1.0**: Conector MySQL/MariaDB (migración)

### 📊 **Procesamiento de Excel y Documentos**
- **openpyxl==3.1.5**: Lectura/escritura de archivos Excel (.xlsx)
- **et_xmlfile==2.0.0**: Dependencia de openpyxl

### 📄 **Generación y Procesamiento de PDF**
- **reportlab==4.4.4**: Generación de PDFs
- **pypdf==6.1.3**: Manipulación de PDFs
- **xhtml2pdf==0.2.17**: Conversión HTML a PDF
- **pyHanko==0.31.0**: Firma digital de PDFs
- **pyhanko-certvalidator==0.29.0**: Validación de certificados

### 🖼️ **Procesamiento de Imágenes**
- **pillow==12.0.0**: Manipulación de imágenes
- **pycairo==1.28.0**: Gráficos vectoriales
- **rlPyCairo==0.4.0**: Integración Cairo con ReportLab
- **freetype-py==2.5.1**: Renderizado de fuentes

### 🔧 **Procesamiento XML y HTML**
- **lxml==6.0.2**: Parser XML/HTML de alto rendimiento
- **html5lib==1.1**: Parser HTML5
- **cssselect2==0.8.0**: Selectores CSS
- **svglib==1.6.0**: Procesamiento de SVG
- **tinycss2==1.4.0**: Parser CSS
- **webencodings==0.5.1**: Codificación web

### 🌍 **Procesamiento de Texto e Internacionalización**
- **arabic-reshaper==3.0.0**: Reformateado de texto árabe
- **python-bidi==0.6.7**: Algoritmo bidireccional Unicode

### ⚙️ **Configuración y Entorno**
- **python-dotenv==1.1.1**: Variables de entorno desde .env
- **PyYAML==6.0.3**: Procesamiento de archivos YAML

### 🌐 **HTTP y Red**
- **requests==2.32.5**: Cliente HTTP
- **urllib3==2.5.0**: Cliente HTTP de bajo nivel
- **certifi==2025.10.5**: Certificados CA
- **charset-normalizer==3.4.4**: Detección de codificación
- **idna==3.11**: Soporte para dominios internacionales

### 🔐 **Criptografía y Seguridad**
- **cryptography==46.0.3**: Primitivas criptográficas
- **cffi==2.0.0**: Interfaz de funciones foráneas
- **pycparser==2.23**: Parser C para Python
- **oscrypto==1.3.0**: Criptografía del sistema operativo
- **asn1crypto==1.5.1**: Codificación/decodificación ASN.1

### 🔑 **JWT y Autenticación**
- **PyJWT==2.10.1**: Implementación de JSON Web Tokens

### ⏰ **Manejo de Tiempo y Fechas**
- **tzdata==2025.2**: Base de datos de zonas horarias
- **tzlocal==5.3.1**: Detección de zona horaria local

### 🛠️ **Utilidades**
- **asgiref==3.10.0**: Utilidades ASGI
- **sqlparse==0.5.3**: Parser SQL
- **six==1.17.0**: Compatibilidad Python 2/3
- **uritools==5.0.0**: Manipulación de URIs

## 🎯 Funcionalidades por Dependencia

### 📊 **Sistema de Datos Archivados**
- **mysql-connector-python**: Conexión a MariaDB/MySQL para migración
- **openpyxl**: Exportación de datos a Excel
- **psycopg2**: Almacenamiento en PostgreSQL
- **django**: Framework web y ORM

### 📈 **Exportación y Reportes**
- **openpyxl**: Archivos Excel (.xlsx)
- **reportlab**: Reportes en PDF
- **pillow**: Procesamiento de imágenes en reportes

### 🔄 **Migración de Datos**
- **mysql-connector-python**: Lectura desde MariaDB
- **psycopg2**: Escritura a PostgreSQL
- **python-dotenv**: Configuración de conexiones

## 🐍 Requisitos del Sistema

- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows, macOS, Linux
- **Memoria RAM**: Mínimo 2GB (recomendado 4GB+)
- **Espacio en disco**: 500MB para dependencias

## 🔧 Comandos Útiles

### Verificar dependencias instaladas:
```bash
python verificar_dependencias.py
```

### Instalar dependencias específicas:
```bash
# Solo las críticas
pip install django psycopg2 mysql-connector-python openpyxl

# Para desarrollo
pip install -r requirements.txt
```

### Actualizar dependencias:
```bash
pip install --upgrade -r requirements.txt
```

### Generar requirements actualizado:
```bash
pip freeze > requirements_actual.txt
```

## 🚨 Solución de Problemas

### Error con psycopg2:
```bash
# Windows
pip install psycopg2-binary

# Linux/macOS
sudo apt-get install libpq-dev  # Ubuntu/Debian
brew install postgresql         # macOS
```

### Error con mysql-connector-python:
```bash
pip install --upgrade mysql-connector-python
```

### Error con openpyxl:
```bash
pip install --upgrade openpyxl et-xmlfile
```

## 📝 Notas de Desarrollo

- Las versiones están fijadas para garantizar compatibilidad
- Se recomienda usar un entorno virtual (venv)
- Actualizar dependencias con cuidado en producción
- Probar en entorno de desarrollo antes de desplegar

## 🔄 Actualización de Dependencias

Para actualizar a versiones más recientes:

1. Crear backup del requirements.txt actual
2. Actualizar versiones en requirements.txt
3. Probar en entorno de desarrollo
4. Ejecutar tests completos
5. Desplegar en producción

---

**Última actualización**: Noviembre 2025  
**Versión del sistema**: 1.0.0