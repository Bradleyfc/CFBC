# Instrucciones para Diagnosticar el Problema de Guardado en Historial

## Resumen del Problema
Los registros no se guardan en los modelos históricos cuando se hace clic en "Combinar Tablas" con tablas de docencia seleccionadas.

## Verificación del Código ✅

El análisis automático confirma que:
- ✅ El import está correcto (línea 3768 de views.py)
- ✅ La función se llama en 2 lugares (líneas 3809 y 3866)
- ✅ La lógica de separación de tablas funciona (línea 3771)
- ✅ Hay manejo de errores con try/except
- ✅ La función es_tabla_docencia está implementada
- ✅ El mapeo DOCENCIA_TABLES_MAPPING tiene 11 tablas

## Causa Más Probable

**El problema más probable es que NO HAY DATOS en DatoArchivadoDinamico para las tablas de docencia.**

Cuando el código ejecuta:
```python
datos_tabla = DatoArchivadoDinamico.objects.filter(tabla_origen='Docencia_area')
```

Si este query retorna 0 registros, entonces no hay nada que guardar.

## Pasos para Diagnosticar

### Paso 1: Verificar si hay datos (MÁS IMPORTANTE)

Ejecuta en Django shell:
```bash
python manage.py shell
```

```python
from datos_archivados.models import DatoArchivadoDinamico

# Ver todas las tablas disponibles
tablas = DatoArchivadoDinamico.objects.values_list('tabla_origen', flat=True).distinct()
print(f"Tablas disponibles: {list(tablas)}")
print(f"Total de registros: {DatoArchivadoDinamico.objects.count()}")

# Verificar tablas de docencia específicas
tablas_docencia = [
    'Docencia_area',
    'Docencia_coursecategory',
    'Docencia_courseinformation',
    'Docencia_courseinformation_adminteachers',
    'Docencia_enrollmentapplication',
    'Docencia_enrollmentpay',
    'Docencia_accountnumber',
    'Docencia_enrollment',
    'Docencia_subjectinformation',
    'Docencia_edition',
    'Docencia_application',
]

for tabla in tablas_docencia:
    count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
    print(f"{tabla}: {count} registros")
```

**Resultado esperado:**
- Si todos muestran 0 registros → **El problema es que no hay datos para migrar**
- Si algunos muestran > 0 → Continuar con el diagnóstico

### Paso 2: Ejecutar script de diagnóstico completo

```bash
python test_guardado_historial_debug.py
```

Este script:
1. Verifica datos en DatoArchivadoDinamico
2. Muestra el estado de los modelos históricos antes
3. Ejecuta el guardado con logging detallado
4. Compara el estado después
5. Identifica exactamente dónde falla

### Paso 3: Revisar logs en tiempo real

1. Abre una terminal y ejecuta:
```bash
python manage.py runserver
```

2. En otra terminal, monitorea los logs (si hay archivo de log):
```bash
tail -f logs/django.log
```

3. En el navegador, ve a la interfaz y haz clic en "Combinar Tablas"

4. Busca en los logs:
   - ✅ "INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL"
   - ✅ "Procesando tabla: Docencia_area"
   - ✅ "Encontrados X registros en Docencia_area"
   - ❌ Cualquier mensaje de ERROR o Exception

### Paso 4: Agregar logging adicional (si es necesario)

Si los logs no son suficientemente detallados:

```bash
python patch_logging_historial.py
```

Esto agregará logging DEBUG adicional. Luego repite el Paso 3.

## Soluciones Según el Diagnóstico

### Solución 1: No hay datos en DatoArchivadoDinamico

**Síntoma**: Todos los conteos son 0 en el Paso 1.

**Causa**: Los datos no se han migrado desde MariaDB a PostgreSQL.

**Solución**: Primero debes importar/migrar los datos:
1. Verifica que los datos existen en MariaDB
2. Ejecuta el proceso de migración/importación
3. Verifica que los datos llegaron a DatoArchivadoDinamico

### Solución 2: Nombre de tabla incorrecto

**Síntoma**: En el Paso 1, las tablas tienen nombres diferentes (ej: 'docencia_area' en lugar de 'Docencia_area').

**Solución**: Actualizar el mapeo en `datos_archivados/historical_data_saver.py`:

```python
DOCENCIA_TABLES_MAPPING = {
    'nombre_correcto_encontrado': 'HistoricalArea',
    # ... resto
}
```

### Solución 3: Error en las transacciones

**Síntoma**: Los logs muestran excepciones o errores durante el guardado.

**Solución**: Revisar el error específico y:
- Verificar que los modelos históricos están correctamente definidos
- Verificar que las relaciones FK existen
- Verificar que los campos son compatibles

### Solución 4: Problema con relaciones FK

**Síntoma**: Errores de IntegrityError o DoesNotExist en los logs.

**Solución**: 
- Verificar que las tablas se procesan en el orden correcto (ya está implementado)
- Verificar que los IDs de las relaciones FK existen en los datos

## Scripts Creados

### 1. test_guardado_historial_debug.py
**Propósito**: Diagnóstico completo del proceso de guardado.
**Uso**: `python test_guardado_historial_debug.py`

### 2. verificar_logs_django.py
**Propósito**: Buscar y analizar logs de Django.
**Uso**: `python verificar_logs_django.py`

### 3. patch_logging_historial.py
**Propósito**: Agregar logging DEBUG adicional.
**Uso**: `python patch_logging_historial.py`
**NOTA**: Modifica el archivo historical_data_saver.py

### 4. verificar_llamada_views.py
**Propósito**: Verificar que la función se llama correctamente.
**Uso**: `python verificar_llamada_views.py`

### 5. test_deteccion_tablas.py
**Propósito**: Probar la detección de tablas de docencia.
**Uso**: `python manage.py shell < test_deteccion_tablas.py`

## Verificación Final

Después de aplicar la solución, verifica que funciona:

```python
# En Django shell
from historial.models import HistoricalArea, HistoricalCourseCategory

print(f"Áreas históricas: {HistoricalArea.objects.count()}")
print(f"Categorías históricas: {HistoricalCourseCategory.objects.count()}")

# Debe mostrar > 0 si el guardado funcionó
```

## Información Adicional para Soporte

Si el problema persiste, proporciona:

1. **Salida del Paso 1** (conteo de registros en DatoArchivadoDinamico)
2. **Salida completa de**: `python test_guardado_historial_debug.py`
3. **Logs de Django** cuando ejecutas "Combinar Tablas"
4. **Mensajes de error** específicos si los hay

## Contacto

Para más ayuda, incluye toda la información anterior en tu reporte.
