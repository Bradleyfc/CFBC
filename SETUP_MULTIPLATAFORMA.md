# Setup Multiplataforma del Proyecto

Este proyecto incluye scripts de setup automático para Windows y Linux.

## Para Windows
```bash
setup_proyecto.bat
```

## Para Linux/macOS
```bash
chmod +x setup_proyecto.sh
./setup_proyecto.sh
```

## Cambios Realizados

### Librerías Removidas por Incompatibilidad con Python 3.13+
- **python-mimetypes==1.1.0**: Incompatible con Python 3.13+
  - **Solución**: Usar `import mimetypes` (módulo nativo de Python)
- **python-magic==0.4.27**: No se usa en el código y causa problemas de compatibilidad
- **python-magic-bin==0.4.14**: Específico para Windows y no se usa en el código

### Librerías Actualizadas
- **psycopg2 → psycopg2-binary**: Mejor compatibilidad y más fácil instalación en diferentes sistemas

### Alternativas Nativas Disponibles

#### Para detección de tipos MIME:
```python
import mimetypes
mime_type, encoding = mimetypes.guess_type('archivo.pdf')
print(mime_type)  # application/pdf
```

#### Para validación de archivos:
Ya tienes `filetype==1.2.0` que es más preciso y compatible.

### Diferencias entre Scripts

| Característica | Windows (.bat) | Linux (.sh) |
|----------------|----------------|-------------|
| Entorno virtual | `python -m venv venv` | `python3 -m venv venv` |
| Activación | `call venv\Scripts\activate.bat` | `source venv/bin/activate` |
| Manejo de errores | `if errorlevel 1` | `|| handle_error` |
| Pausa | `pause` | `read` |

## Uso del módulo mimetypes nativo

Si necesitas detectar tipos MIME en tu código, usa:

```python
import mimetypes

# En lugar de python-mimetypes o python-magic
mime_type, encoding = mimetypes.guess_type('archivo.pdf')
print(mime_type)  # application/pdf

# Para validación más precisa, usa filetype (ya incluido)
import filetype

# Detectar tipo por contenido del archivo
kind = filetype.guess('archivo.pdf')
if kind is None:
    print('No se pudo determinar el tipo de archivo')
else:
    print(f'Tipo: {kind.extension}, MIME: {kind.mime}')
```

## Requisitos del Sistema

### Windows
- Python 3.8+
- pip

### Linux/macOS
- Python 3.8+
- pip
- Permisos de ejecución para el script

## Solución de Problemas

### Error de permisos en Linux
```bash
chmod +x setup_proyecto.sh
```

### Python no encontrado en Linux
```bash
# Instalar Python 3
sudo apt update
sudo apt install python3 python3-pip python3-venv

# O en macOS con Homebrew
brew install python3
```