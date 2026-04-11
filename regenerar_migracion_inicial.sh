#!/bin/bash
# Script para regenerar la migración inicial de historial con TODOS los campos

echo "=========================================="
echo "Regenerar Migración Inicial de Historial"
echo "=========================================="
echo ""

# 1. Backup de la migración actual
echo "1. Haciendo backup de migración actual..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_migracion_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"
cp historial/migrations/0001_initial.py "$BACKUP_DIR/"
echo "   ✓ Backup guardado en: $BACKUP_DIR/"

# 2. Eliminar registro de django_migrations
echo ""
echo "2. Limpiando registros de migraciones..."
python3 << 'EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'historial'")
    print("   ✓ Registros eliminados de django_migrations")
EOF

# 3. Eliminar archivo de migración
echo ""
echo "3. Eliminando archivo de migración antiguo..."
rm historial/migrations/0001_initial.py
echo "   ✓ Archivo eliminado"

# 4. Generar nueva migración
echo ""
echo "4. Generando nueva migración con TODOS los campos..."
python3 manage.py makemigrations historial
echo "   ✓ Nueva migración generada"

# 5. Aplicar con --fake (los campos ya existen)
echo ""
echo "5. Aplicando migración con --fake..."
python3 manage.py migrate historial --fake
echo "   ✓ Migración aplicada (fake)"

# 6. Verificar
echo ""
echo "6. Verificando..."
python3 manage.py makemigrations historial --dry-run --check
if [ $? -eq 0 ]; then
    echo "   ✓ No hay migraciones pendientes"
else
    echo "   ⚠ Hay migraciones pendientes"
fi

echo ""
echo "=========================================="
echo "✓ Migración regenerada exitosamente"
echo "=========================================="
echo ""
echo "Ahora historial/migrations/0001_initial.py incluye TODOS los campos."
echo "Tu amigo puede usar esta migración y funcionará desde cero."
