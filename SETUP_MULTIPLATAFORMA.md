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

### Problema con python-mimetypes
- **Problema**: La librería `python-mimetypes==1.1.0` no es compatible con Python 3.13+
- **Solución**: Se removió la dependencia ya que Python incluye el módulo `mimetypes` nativo
- **Alternativa**: Usar `import mimetypes` (módulo estándar de Python)

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

# En lugar de python-mimetypes
mime_type, encoding = mimetypes.guess_type('archivo.pdf')
print(mime_type)  # application/pdf
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