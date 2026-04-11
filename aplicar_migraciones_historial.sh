#!/bin/bash
# Script para aplicar las migraciones de la app historial

echo "============================================================"
echo "APLICANDO MIGRACIONES DE HISTORIAL"
echo "============================================================"

echo ""
echo "📋 Estado actual de migraciones:"
python manage.py showmigrations historial

echo ""
echo "🚀 Aplicando migraciones..."
python manage.py migrate historial

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migraciones aplicadas exitosamente!"
    echo ""
    echo "📋 Estado final:"
    python manage.py showmigrations historial
else
    echo ""
    echo "❌ Error al aplicar migraciones"
    exit 1
fi

echo ""
echo "============================================================"
echo "PROCESO COMPLETADO"
echo "============================================================"
