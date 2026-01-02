# 🚀 Setup de Tailwind CSS para Colaboradores

## 📋 Instrucciones para configurar el proyecto después de clonar

### 1. Clonar el repositorio
```bash
git clone [URL_DEL_REPOSITORIO]
cd [NOMBRE_DEL_PROYECTO]
```

### 2. Crear y activar entorno virtual
```bash
python -m venv venv
venv\Scripts\activate  # En Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Tailwind CSS (AUTOMÁTICO)
El proyecto usa `django-tailwind-cli` con descarga automática del binario.

**Primera compilación:**
```bash
python manage.py tailwind
```

Esto automáticamente:
- Descarga el binario de Tailwind CSS para tu sistema operativo
- Compila el CSS usando el archivo `source.css` incluido
- Genera `static/css/tailwind.css`

### 5. Ejecutar el proyecto

**Terminal 1 - Servidor Django:**
```bash
python manage.py runserver
```

**Terminal 2 - Tailwind Watch (para desarrollo):**
```bash
python manage.py tailwind --watch
```

## 🔄 Flujo de trabajo diario

### Para desarrollo normal:
1. Activar entorno virtual: `venv\Scripts\activate`
2. Iniciar servidor: `python manage.py runserver`
3. En otra terminal: `python manage.py tailwind --watch`

### Para compilar CSS manualmente:
```bash
python manage.py tailwind          # Compilación normal
python manage.py tailwind --minify # Para producción
```

## 📁 Archivos importantes incluidos en el repo

✅ **Incluidos (no tocar):**
- `.django_tailwind_cli/source.css` - Archivo fuente de Tailwind
- `static/css/tailwind.css` - CSS compilado (funciona inmediatamente)

❌ **Excluidos (se descargan automáticamente):**
- `.django_tailwind_cli/tailwindcss-*.exe` - Binarios del sistema

## 🚨 Troubleshooting

### Problema: "tailwindcss binary not found"
**Solución:** Ejecutar `python manage.py tailwind` - descarga automáticamente

### Problema: CSS no se actualiza
**Solución:** Verificar que `--watch` esté corriendo en terminal separada

### Problema: Clases Tailwind no funcionan
**Solución:** Compilar manualmente con `python manage.py tailwind`

## 🎯 Configuración automática

El proyecto está configurado con:
```python
TAILWIND_CLI_PATH = "auto"  # Descarga automática
TAILWIND_CLI_SRC_CSS = ".django_tailwind_cli/source.css"
TAILWIND_CLI_DIST_CSS = "static/css/tailwind.css"
```

**¡No necesitas descargar nada manualmente!** 🎉

---

**Nota:** Si tienes problemas, revisa que tengas Python 3.8+ y conexión a internet para la descarga automática del binario.