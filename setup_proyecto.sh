#!/bin/bash

echo "========================================"
echo "    SETUP AUTOMATICO DEL PROYECTO"
echo "========================================"
echo

# Función para manejar errores
handle_error() {
    echo "ERROR: $1"
    echo "Presiona Enter para salir..."
    read
    exit 1
}

echo "[1/5] Creando entorno virtual..."
python3 -m venv venv || handle_error "No se pudo crear el entorno virtual"

echo "[2/5] Activando entorno virtual..."
source venv/bin/activate || handle_error "No se pudo activar el entorno virtual"

echo "[3/5] Instalando dependencias..."
pip install -r requirements.txt || handle_error "No se pudieron instalar las dependencias"

#echo "[4/5] Configurando Tailwind CSS..."
#echo "  - Limpiando configuración anterior..."
#python manage.py tailwind remove_cli 2>/dev/null || true
#echo "  - Descargando Tailwind CLI para Linux..."
#python manage.py tailwind download_cli --cli-binary-path=/home/yssl/tailwindcss || handle_error "No se pudo descargar Tailwind CLI"
echo "  - Compilando CSS..."
python manage.py tailwind build || handle_error "No se pudo compilar Tailwind CSS"

echo "[5/5] Aplicando migraciones..."
python manage.py migrate || handle_error "No se pudieron aplicar las migraciones"

echo
echo "========================================"
echo "        SETUP COMPLETADO! 🎉"
echo "========================================"
echo
echo "Para ejecutar el proyecto:"
echo "1. Activar entorno: source venv/bin/activate"
echo "2. Servidor Django: python manage.py runserver"
echo "3. Tailwind Watch: python manage.py tailwind --watch"
echo
echo "Presiona Enter para continuar..."
read