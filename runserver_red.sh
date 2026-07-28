#!/bin/bash

# Script para iniciar Django accesible desde la red WiFi local
# Necesario para que la app Android en dispositivo físico pueda conectarse

echo "========================================="
echo "  Iniciando Django Server para Red WiFi"
echo "========================================="
echo ""

# Activar entorno virtual
if [ -d "venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source venv/bin/activate
    echo "✅ Entorno virtual activado"
elif [ -d ".venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source .venv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️  No se encontró entorno virtual (venv o .venv)"
    echo "   Usando Python del sistema"
fi

echo ""
echo "📡 Servidor accesible en:"
echo "   - http://127.0.0.1:8000 (local)"
echo "   - http://192.168.1.101:8000 (red WiFi)"
echo ""
echo "📱 Tu app Android debe usar:"
echo "   http://192.168.1.101:8000"
echo ""
echo "🔥 Firewall: Asegúrate que el puerto 8000 esté permitido"
echo ""
echo "========================================="
echo ""

# Iniciar Django escuchando en todas las interfaces de red
python manage.py runserver 0.0.0.0:8000
