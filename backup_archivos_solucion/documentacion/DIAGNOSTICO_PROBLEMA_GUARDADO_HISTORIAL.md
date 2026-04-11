# Diagnóstico: Problema con Guardado en Historial

## Problema Reportado
Cuando el usuario hace clic en "Combinar Tablas" después de seleccionar las tablas de docencia, no se guardan los registros en los modelos históricos.

## Análisis del Código

### 1. Flujo del Proceso

El flujo actual es:

```
Usuario hace clic en "Combinar Tablas"
    ↓
datos_archivados/views.py (línea ~3768)
    ↓
Detecta tablas de docencia usando es_tabla_docencia()
    ↓
Llama a guardar_datos_docencia_en_historial(tablas_docencia, logger)
    ↓
datos_archivados/historical_data_saver.py
    ↓
Para cada tabla:
    - Ejecuta: DatoArchivadoDinamico.objects.filter(tabla_origen=tabla)
    - Procesa los registros
    - Guarda en modelos históricos
```

### 2. Posibles Causas del Problema

#### Causa 1: No hay datos en DatoArchivadoDinamico
**Síntoma**: El query `DatoArchivadoDinamico.objects.filter(tabla_origen=tabla)` retorna 0 registros.

**Verificación**:
```python
# Ejecutar en Django shell
from datos_archivados.models import DatoArchivadoDinamico

# Verificar si hay datos
for tabla in ['Docencia_area', 'Docencia_coursecategory', 'Docencia_courseinformation']:
    count = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla).count()
    print(f"{tabla}: {count} registros")
```

**Solución**: Si no hay datos, primero hay que migrar/importar los datos a DatoArchivadoDinamico.

#### Causa 2: Nombre de tabla incorrecto
**Síntoma**: Los datos existen pero con un nombre de tabla diferente (ej: 'docencia_area' vs 'Docencia_area').

**Verificación**:
```python
# Ver todos los nombres de tabla únicos
tablas = DatoArchivadoDinamico.objects.values_list('tabla_origen', flat=True).distinct()
print(list(tablas))
```

**Solución**: Ajustar el mapeo DOCENCIA_TABLES_MAPPING para usar los nombres correctos.

#### Causa 3: Error silencioso en transaction.atomic()
**Síntoma**: Los datos se procesan pero hay un error dentro del `transaction.atomic()` que hace rollback silencioso.

**Verificación**: Revisar logs para ver si hay excepciones capturadas.

**Solución**: Agregar logging más detallado dentro de cada función _procesar_*.

#### Causa 4: Problema con relaciones FK
**Síntoma**: Los registros fallan al guardar porque las relaciones FK (area_id, categoria_id, etc.) no existen.

**Verificación**: Revisar logs para ver errores de IntegrityError o DoesNotExist.

**Solución**: Asegurar que las tablas se procesan en el orden correcto (ya está implementado).

#### Causa 5: La función no se está llamando
**Síntoma**: La función guardar_datos_docencia_en_historial nunca se ejecuta.

**Verificación**: Buscar en logs el mensaje "INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL".

**Solución**: Verificar la lógica de detección de tablas de docencia en views.py.

## Scripts de Diagnóstico Creados

### 1. test_guardado_historial_debug.py
**Propósito**: Simula el proceso completo de guardado en historial con logging detallado.

**Uso**:
```bash
python test_guardado_historial_debug.py
```

**Qué hace**:
- Verifica si hay datos en DatoArchivadoDinamico para cada tabla de docencia
- Muestra el estado de los modelos históricos antes del guardado
- Ejecuta guardar_datos_docencia_en_historial con logging detallado
- Compara el estado de los modelos históricos después del guardado
- Verifica que el query específico funciona correctamente

**Salida esperada**:
- Si hay datos: Debe mostrar registros guardados en los modelos históricos
- Si no hay datos: Debe indicar qué tablas no tienen datos

### 2. verificar_logs_django.py
**Propósito**: Busca y analiza los logs de Django para encontrar errores.

**Uso**:
```bash
python verificar_logs_django.py
```

**Qué hace**:
- Busca archivos de log en el proyecto
- Verifica la configuración de LOGGING en settings.py
- Busca errores recientes relacionados con historial
- Proporciona instrucciones para verificar logs en tiempo real

### 3. patch_logging_historial.py
**Propósito**: Agrega logging adicional al archivo historical_data_saver.py para debug.

**Uso**:
```bash
python patch_logging_historial.py
```

**Qué hace**:
- Agrega logging detallado después de cada query
- Agrega logging al inicio de cada función _procesar_*
- Verifica que los querysets no estén vacíos
- Muestra todas las tablas disponibles si no encuentra datos

**IMPORTANTE**: Este script modifica el archivo historical_data_saver.py. Se recomienda hacer backup antes.

## Pasos para Diagnosticar el Problema

### Paso 1: Verificar datos disponibles
```bash
python test_guardado_historial_debug.py
```

Esto te dirá inmediatamente si:
- Hay datos en DatoArchivadoDinamico
- Los datos se están guardando en los modelos históricos
- Hay algún error durante el proceso

### Paso 2: Revisar logs
```bash
python verificar_logs_django.py
```

Busca mensajes de error o excepciones.

### Paso 3: Agregar logging detallado (si es necesario)
```bash
python patch_logging_historial.py
```

Luego ejecuta el servidor y realiza la acción "Combinar Tablas" mientras observas los logs.

### Paso 4: Verificar en Django shell
```bash
python manage.py shell
```

```python
from datos_archivados.models import DatoArchivadoDinamico
from historial.models import HistoricalArea

# Verificar datos origen
print(f"Datos en DatoArchivadoDinamico: {DatoArchivadoDinamico.objects.count()}")
print(f"Tablas únicas: {list(DatoArchivadoDinamico.objects.values_list('tabla_origen', flat=True).distinct())}")

# Verificar datos históricos
print(f"Áreas históricas: {HistoricalArea.objects.count()}")

# Probar el query específico
datos = DatoArchivadoDinamico.objects.filter(tabla_origen='Docencia_area')
print(f"Registros de Docencia_area: {datos.count()}")
if datos.exists():
    print(f"Ejemplo: {datos.first().datos_originales}")
```

## Soluciones Propuestas

### Solución 1: Si no hay datos en DatoArchivadoDinamico
Primero hay que importar/migrar los datos desde MariaDB a PostgreSQL.

### Solución 2: Si el nombre de tabla es incorrecto
Modificar el mapeo en historical_data_saver.py:

```python
DOCENCIA_TABLES_MAPPING = {
    'nombre_correcto_tabla': 'HistoricalArea',
    # ... resto del mapeo
}
```

### Solución 3: Si hay errores en las transacciones
Agregar manejo de errores más robusto:

```python
def _procesar_areas(datos_tabla, ModeloHistorico, mapeo_areas, logger):
    """Procesa y guarda áreas en HistoricalArea."""
    registros_guardados = 0
    
    logger.info(f"🔧 Iniciando procesamiento de áreas")
    logger.info(f"🔧 Total de registros a procesar: {datos_tabla.count()}")
    
    with transaction.atomic():
        for dato in datos_tabla:
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                logger.debug(f"Procesando área con ID original: {id_original}")
                logger.debug(f"Datos: {datos}")
                
                # Crear nueva área histórica
                area = ModeloHistorico()
                copiar_campos_a_modelo_historico(area, datos, campos_excluir=['id', 'pk'], logger=logger)
                
                logger.debug(f"Guardando área: {area.nombre}")
                area.save()
                logger.debug(f"Área guardada exitosamente con ID: {area.id}")
                
                # Guardar mapeo
                mapeo_areas[id_original] = area
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"❌ Error procesando área con ID {id_original}: {str(e)}", exc_info=True)
                continue
    
    logger.info(f"✅ Total de áreas guardadas: {registros_guardados}")
    return registros_guardados
```

### Solución 4: Si la función no se está llamando
Verificar la lógica en views.py alrededor de la línea 3768:

```python
# Asegurar que esta condición se cumple
if tablas_docencia:
    logger.info(f"📚 Detectadas {len(tablas_docencia)} tablas de docencia")
    logger.info(f"Tablas: {tablas_docencia}")
    
    try:
        estadisticas_docencia = guardar_datos_docencia_en_historial(tablas_docencia, logger)
        logger.info(f"✅ Guardado completado: {estadisticas_docencia}")
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise
```

## Verificación Final

Después de aplicar las soluciones, verificar que:

1. Los logs muestran: "INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL"
2. Los logs muestran: "Encontrados X registros en Docencia_area"
3. Los logs muestran: "X registros guardados en historial"
4. Los modelos históricos tienen datos:
   ```python
   from historial.models import HistoricalArea
   print(HistoricalArea.objects.count())  # Debe ser > 0
   ```

## Contacto y Soporte

Si después de seguir estos pasos el problema persiste, proporciona:
1. La salida completa de test_guardado_historial_debug.py
2. Los logs relevantes de Django
3. La salida del comando en Django shell para verificar datos
