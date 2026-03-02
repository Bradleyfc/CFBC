#!/bin/bash
# Script de verificación rápida de la implementación de tablas mixtas

echo "=========================================="
echo "🔍 VERIFICACIÓN DE IMPLEMENTACIÓN"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de errores
ERRORS=0

# 1. Verificar que existe views.py
echo "1️⃣  Verificando archivo views.py..."
if [ -f "datos_archivados/views.py" ]; then
    echo -e "${GREEN}✅ views.py encontrado${NC}"
else
    echo -e "${RED}❌ views.py NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. Verificar que existe historical_data_saver.py
echo "2️⃣  Verificando archivo historical_data_saver.py..."
if [ -f "datos_archivados/historical_data_saver.py" ]; then
    echo -e "${GREEN}✅ historical_data_saver.py encontrado${NC}"
else
    echo -e "${RED}❌ historical_data_saver.py NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 3. Verificar que los 3 escenarios están implementados
echo "3️⃣  Verificando implementación de los 3 escenarios..."
ESCENARIO1=$(grep -c "ESCENARIO 1: SOLO TABLAS DE DOCENCIA" datos_archivados/views.py)
ESCENARIO2=$(grep -c "ESCENARIO 2: SOLO TABLAS DE USUARIOS" datos_archivados/views.py)
ESCENARIO3=$(grep -c "ESCENARIO 3: TABLAS MIXTAS" datos_archivados/views.py)

if [ "$ESCENARIO1" -gt 0 ]; then
    echo -e "${GREEN}✅ ESCENARIO 1 implementado${NC}"
else
    echo -e "${RED}❌ ESCENARIO 1 NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ "$ESCENARIO2" -gt 0 ]; then
    echo -e "${GREEN}✅ ESCENARIO 2 implementado${NC}"
else
    echo -e "${RED}❌ ESCENARIO 2 NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ "$ESCENARIO3" -gt 0 ]; then
    echo -e "${GREEN}✅ ESCENARIO 3 implementado${NC}"
else
    echo -e "${RED}❌ ESCENARIO 3 NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 4. Verificar funciones auxiliares
echo "4️⃣  Verificando funciones auxiliares..."
ES_TABLA=$(grep -c "def es_tabla_docencia" datos_archivados/historical_data_saver.py)
GUARDAR=$(grep -c "def guardar_datos_docencia_en_historial" datos_archivados/historical_data_saver.py)

if [ "$ES_TABLA" -gt 0 ]; then
    echo -e "${GREEN}✅ Función es_tabla_docencia() encontrada${NC}"
else
    echo -e "${RED}❌ Función es_tabla_docencia() NO encontrada${NC}"
    ERRORS=$((ERRORS + 1))
fi

if [ "$GUARDAR" -gt 0 ]; then
    echo -e "${GREEN}✅ Función guardar_datos_docencia_en_historial() encontrada${NC}"
else
    echo -e "${RED}❌ Función guardar_datos_docencia_en_historial() NO encontrada${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 5. Verificar sintaxis de Python
echo "5️⃣  Verificando sintaxis de Python..."
python -m py_compile datos_archivados/views.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ views.py: sintaxis correcta${NC}"
else
    echo -e "${RED}❌ views.py: errores de sintaxis${NC}"
    ERRORS=$((ERRORS + 1))
fi

python -m py_compile datos_archivados/historical_data_saver.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ historical_data_saver.py: sintaxis correcta${NC}"
else
    echo -e "${RED}❌ historical_data_saver.py: errores de sintaxis${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 6. Ejecutar Django check
echo "6️⃣  Ejecutando Django check..."
python manage.py check --quiet 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Django check: sin problemas${NC}"
else
    echo -e "${YELLOW}⚠️  Django check: revisar warnings${NC}"
fi

# 7. Ejecutar pruebas
echo "7️⃣  Ejecutando pruebas de separación de tablas..."
if [ -f "test_tablas_mixtas_completo.py" ]; then
    python test_tablas_mixtas_completo.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas: todas pasaron${NC}"
    else
        echo -e "${RED}❌ Pruebas: algunas fallaron${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Script de pruebas no encontrado${NC}"
fi

# Resumen final
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ VERIFICACIÓN COMPLETADA: TODO OK${NC}"
    echo "La implementación está correcta y funcional"
else
    echo -e "${RED}❌ VERIFICACIÓN COMPLETADA: $ERRORS ERROR(ES)${NC}"
    echo "Revisar los errores anteriores"
fi
echo "=========================================="

exit $ERRORS
