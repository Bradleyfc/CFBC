# 🚀 Solución Rápida - Guardado en Historial

## ⚡ Inicio Rápido (30 segundos)

```bash
# Ejecuta este comando:
python diagnostico_rapido.py
```

Este script te dirá **exactamente** cuál es el problema y cómo solucionarlo.

---

## 🎯 Problemas Comunes y Soluciones

### Problema 1: No hay datos en DatoArchivadoDinamico ❌

**Síntoma**:
```
❌ Total de registros en DatoArchivadoDinamico: 0
```

**Causa**: Los datos no se han migrado desde MariaDB.

**Solución**:
1. Verificar que los datos existen en MariaDB
2. Ejecutar el proceso de migración/importación
3. Volver a intentar "Combinar Tablas"

---

### Problema 2: Nombres de tabla incorrectos ❌

**Síntoma**:
```
❌ Docencia_area: 0 registros
⚠️  Posibles variaciones: docencia_area (150 registros)
```

**Causa**: Los nombres de tabla en el código no coinciden con los de la base de datos.

**Solución**:

Editar `datos_archivados/historical_data_saver.py`:

```python
DOCENCIA_TABLES_MAPPING = {
    # Cambiar de:
    'Docencia_area': 'HistoricalArea',
    
    # A (usar el nombre correcto):
    'docencia_area': 'HistoricalArea',
    
    # Hacer lo mismo para todas las tablas
}
```

---

### Problema 3: Hay datos pero no se guardan ❌

**Síntoma**:
```
✅ Docencia_area: 150 registros
➖ HistoricalArea: 0 registros (después de combinar)
```

**Causa**: Error durante el proceso de guardado.

**Solución**:

1. Ejecutar diagnóstico detallado:
```bash
python test_guardado_historial_debug.py
```

2. Revisar logs en tiempo real:
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
tail -f logs/django.log  # o ver la consola del servidor

# Navegador: Hacer clic en "Combinar Tablas"
```

3. Buscar el error específico en los logs

---

## 🔍 Verificación Manual Rápida

```bash
python manage.py shell
```

```python
from datos_archivados.models import DatoArchivadoDinamico
from historial.models import HistoricalArea

# ¿Hay datos origen?
print(f"Datos origen: {DatoArchivadoDinamico.objects.filter(tabla_origen='Docencia_area').count()}")

# ¿Hay datos históricos?
print(f"Datos históricos: {HistoricalArea.objects.count()}")

# Si origen > 0 y históricos = 0 → hay un problema en el guardado
# Si origen = 0 → hay que migrar datos primero
```

---

## 📋 Checklist de Verificación

- [ ] Ejecuté `python diagnostico_rapido.py`
- [ ] Verifiqué que hay datos en DatoArchivadoDinamico
- [ ] Verifiqué que los nombres de tabla son correctos
- [ ] Revisé los logs de Django
- [ ] Ejecuté `python test_guardado_historial_debug.py`
- [ ] Verifiqué que los modelos históricos tienen datos después del guardado

---

## 🆘 Si Nada Funciona

1. **Recopila información**:
```bash
python diagnostico_rapido.py > diagnostico.txt
python test_guardado_historial_debug.py > test_detallado.txt
```

2. **Captura logs** cuando haces clic en "Combinar Tablas"

3. **Proporciona**:
   - `diagnostico.txt`
   - `test_detallado.txt`
   - Logs de Django
   - Descripción de lo que hiciste

---

## 📚 Más Información

- **README_DIAGNOSTICO.md**: Guía completa
- **INSTRUCCIONES_DIAGNOSTICO.md**: Pasos detallados
- **DIAGNOSTICO_PROBLEMA_GUARDADO_HISTORIAL.md**: Análisis técnico

---

## ✅ Verificación de Éxito

Después de aplicar la solución:

```python
# En Django shell
from historial.models import HistoricalArea

# Debe ser > 0
print(HistoricalArea.objects.count())
```

Si es > 0, ¡funcionó! 🎉

---

**Tiempo estimado**: 5-10 minutos para diagnosticar y solucionar.
