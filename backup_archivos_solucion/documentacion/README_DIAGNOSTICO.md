# Diagnóstico del Problema de Guardado en Historial

## 📋 Resumen del Problema

Cuando el usuario hace clic en "Combinar Tablas" después de seleccionar las tablas de docencia, **no se guardan los registros en los modelos históricos**.

## ✅ Verificación del Código

Se realizó un análisis automático del código y se confirmó que:

- ✅ El import está correcto (línea 3768 de `datos_archivados/views.py`)
- ✅ La función `guardar_datos_docencia_en_historial` se llama en 2 lugares
- ✅ La lógica de separación de tablas funciona correctamente
- ✅ Hay manejo de errores con try/except
- ✅ La función `es_tabla_docencia` está implementada
- ✅ El mapeo `DOCENCIA_TABLES_MAPPING` tiene las 11 tablas de docencia

**Conclusión**: El código está bien estructurado. El problema probablemente está en los datos.

## 🎯 Causa Más Probable

**No hay datos en `DatoArchivadoDinamico` para las tablas de docencia.**

El código ejecuta:
```python
datos_tabla = DatoArchivadoDinamico.objects.filter(tabla_origen='Docencia_area')
```

Si este query retorna 0 registros, no hay nada que guardar.

## 🚀 Inicio Rápido

### Opción 1: Diagnóstico Rápido (Recomendado)

```bash
python diagnostico_rapido.py
```

Este script ejecuta todas las verificaciones básicas y te dice exactamente cuál es el problema.

### Opción 2: Verificación Manual

```bash
python manage.py shell
```

```python
from datos_archivados.models import DatoArchivadoDinamico

# Ver si hay datos
print(f"Total registros: {DatoArchivadoDinamico.objects.count()}")

# Ver tablas disponibles
tablas = DatoArchivadoDinamico.objects.values_list('tabla_origen', flat=True).distinct()
print(f"Tablas: {list(tablas)}")

# Verificar tabla específica
count = DatoArchivadoDinamico.objects.filter(tabla_origen='Docencia_area').count()
print(f"Docencia_area: {count} registros")
```

## 📁 Archivos Creados

### Scripts de Diagnóstico

| Archivo | Propósito | Uso |
|---------|-----------|-----|
| **diagnostico_rapido.py** | Diagnóstico completo en un comando | `python diagnostico_rapido.py` |
| **test_guardado_historial_debug.py** | Simula el proceso completo con logging detallado | `python test_guardado_historial_debug.py` |
| **verificar_logs_django.py** | Busca y analiza logs de Django | `python verificar_logs_django.py` |
| **verificar_llamada_views.py** | Verifica que la función se llama correctamente | `python verificar_llamada_views.py` |
| **patch_logging_historial.py** | Agrega logging DEBUG adicional | `python patch_logging_historial.py` |
| **test_deteccion_tablas.py** | Prueba la detección de tablas de docencia | `python manage.py shell < test_deteccion_tablas.py` |

### Documentación

| Archivo | Contenido |
|---------|-----------|
| **DIAGNOSTICO_PROBLEMA_GUARDADO_HISTORIAL.md** | Análisis detallado del problema y soluciones |
| **INSTRUCCIONES_DIAGNOSTICO.md** | Guía paso a paso para diagnosticar |
| **README_DIAGNOSTICO.md** | Este archivo - resumen general |

## 🔍 Proceso de Diagnóstico

### Paso 1: Ejecutar Diagnóstico Rápido

```bash
python diagnostico_rapido.py
```

Este script te dirá inmediatamente:
- ✅ Si hay datos en DatoArchivadoDinamico
- ✅ Si hay datos para las tablas de docencia
- ✅ El estado de los modelos históricos
- ✅ Si la función de detección funciona

### Paso 2: Según el Resultado

#### Si NO hay datos en DatoArchivadoDinamico:
```
❌ PROBLEMA: No hay datos para migrar
✅ SOLUCIÓN: Ejecutar el proceso de migración/importación desde MariaDB
```

#### Si los nombres de tabla son diferentes:
```
❌ PROBLEMA: Las tablas tienen nombres diferentes (ej: 'docencia_area' vs 'Docencia_area')
✅ SOLUCIÓN: Actualizar DOCENCIA_TABLES_MAPPING en historical_data_saver.py
```

#### Si hay datos pero no se guardan:
```
❌ PROBLEMA: Los datos existen pero no se guardan
✅ SOLUCIÓN: Ejecutar test_guardado_historial_debug.py para ver el error exacto
```

### Paso 3: Diagnóstico Detallado (si es necesario)

```bash
python test_guardado_historial_debug.py
```

Este script:
1. Verifica datos disponibles
2. Muestra estado de modelos históricos ANTES
3. Ejecuta el guardado con logging detallado
4. Muestra estado de modelos históricos DESPUÉS
5. Identifica exactamente dónde falla

### Paso 4: Revisar Logs en Tiempo Real

1. Terminal 1:
```bash
python manage.py runserver
```

2. Terminal 2 (si hay archivo de log):
```bash
tail -f logs/django.log
```

3. Navegador: Hacer clic en "Combinar Tablas"

4. Buscar en logs:
   - ✅ "INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL"
   - ✅ "Procesando tabla: Docencia_area"
   - ✅ "Encontrados X registros"
   - ❌ Cualquier ERROR o Exception

### Paso 5: Agregar Logging Adicional (opcional)

Si necesitas más detalles:

```bash
python patch_logging_historial.py
```

**NOTA**: Este script modifica `historical_data_saver.py`. Haz backup antes.

## 🛠️ Soluciones Comunes

### Solución 1: No hay datos

**Problema**: `DatoArchivadoDinamico` está vacío.

**Solución**:
1. Verificar que los datos existen en MariaDB
2. Ejecutar el proceso de migración/importación
3. Verificar que los datos llegaron a PostgreSQL

### Solución 2: Nombres de tabla incorrectos

**Problema**: Los datos existen pero con nombres diferentes.

**Solución**: Actualizar el mapeo en `datos_archivados/historical_data_saver.py`:

```python
DOCENCIA_TABLES_MAPPING = {
    'nombre_correcto_encontrado': 'HistoricalArea',
    # Usar los nombres exactos que aparecen en la base de datos
}
```

### Solución 3: Error en transacciones

**Problema**: Los logs muestran excepciones durante el guardado.

**Solución**:
1. Revisar el error específico en los logs
2. Verificar que los modelos históricos están correctamente definidos
3. Verificar que las relaciones FK existen
4. Verificar que los campos son compatibles

### Solución 4: Problemas con relaciones FK

**Problema**: Errores de IntegrityError o DoesNotExist.

**Solución**:
- Las tablas ya se procesan en el orden correcto
- Verificar que los IDs de las relaciones FK existen en los datos
- Verificar que los usuarios/profesores existen en la tabla User

## ✅ Verificación Final

Después de aplicar la solución:

```python
# En Django shell
from historial.models import HistoricalArea, HistoricalCourseCategory

print(f"Áreas: {HistoricalArea.objects.count()}")
print(f"Categorías: {HistoricalCourseCategory.objects.count()}")

# Debe mostrar > 0 si funcionó
```

## 📊 Información para Soporte

Si el problema persiste, proporciona:

1. **Salida de**: `python diagnostico_rapido.py`
2. **Salida de**: `python test_guardado_historial_debug.py`
3. **Logs de Django** cuando ejecutas "Combinar Tablas"
4. **Mensajes de error** específicos

## 📚 Documentación Adicional

- **DIAGNOSTICO_PROBLEMA_GUARDADO_HISTORIAL.md**: Análisis técnico detallado
- **INSTRUCCIONES_DIAGNOSTICO.md**: Guía paso a paso completa

## 🎯 Resumen Ejecutivo

1. **Ejecuta**: `python diagnostico_rapido.py`
2. **Lee** el resultado y sigue las recomendaciones
3. **Si no hay datos**: Migra desde MariaDB primero
4. **Si hay datos pero no se guardan**: Ejecuta `python test_guardado_historial_debug.py`
5. **Revisa logs** en tiempo real cuando haces clic en "Combinar Tablas"

---

**Nota**: Todos los scripts están listos para usar. Simplemente ejecuta el comando correspondiente.
