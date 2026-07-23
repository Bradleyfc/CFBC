#!/bin/bash

echo "========================================"
echo "    LIMPIEZA DE TAILWIND MULTIPLATAFORMA"
echo "========================================"
echo

echo "Eliminando archivos de Tailwind anteriores..."

# Eliminar CLI anterior
python manage.py tailwind remove_cli 2>/dev/null || true

# Eliminar archivos temporales
rm -rf .django_tailwind_cli/tailwindcss-*
rm -rf .django_tailwind_cli/*.exe

# Crear directorio si no existe
mkdir -p .django_tailwind_cli

# Crear archivo source.css si no existe
if [ ! -f ".django_tailwind_cli/source.css" ]; then
    echo "Creando archivo source.css..."
    cat > .django_tailwind_cli/source.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Estilos personalizados aquí */
EOF
fi

# Crear directorio para CSS compilado
mkdir -p static/css

echo "Limpieza completada!"
echo "Ahora ejecuta: ./setup_proyecto.sh"