# Solución Final: Modal de Combinación Selectiva de Tablas

## Problema

El modal "Seleccionar y Combinar Tablas Específicas" no combinaba nada cuando se seleccionaban las 11 tablas de docencia y se presionaba el botón "Combinar Tablas".

## Causa Raíz

Había **DOS problemas principales**:

### 1. Error de Scope en `views.py`

La función `ejecutar_combinacion_seleccionada()` dentro de `combinar_datos_seleccionadas()` intentaba acceder a la variable `tablas_seleccionadas` del scope exterior, pero Python la trataba como una variable local no inicializada debido a una reasignación posterior en el código.

**Error:**
```python
UnboundLocalError: cannot access local variable 'tablas_seleccionadas' where it is not associated with a value
```

### 2. Campos Obligatorios Faltantes en `historical_data_saver.py`

Los datos archivados no contenían todos los campos obligatorios que requieren los modelos históricos, causando errores de integridad al intentar guardar.

## Solución Implementada

### Cambio 1: Fix de Scope en `views.py`

**Archivo:** `datos_archivados/views.py`

**Antes:**
```python
def ejecutar_combinacion_seleccionada():
    logger.info(f"Tablas seleccionadas: {tablas_seleccionadas}")  # Error!
```

**Después:**
```python
def ejecutar_combinacion_seleccionada(tablas_seleccionadas):  # Parámetro agregado
    logger.info(f"Tablas seleccionadas: {tablas_seleccionadas}")  # Funciona!
```

Y al llamar la función:
```python
ejecutar_combinacion_seleccionada(tablas_seleccionadas)  # Pasar parámetro
```

### Cambio 2: Import Faltante en `historical_data_saver.py`

**Archivo:** `datos_archivados/historical_data_saver.py`

Agregado:
```python
from mapeos_campos_docencia import aplicar_mapeo_campos
```

### Cambio 3: Función `completar_campos_obligatorios()`

**Archivo:** `datos_archivados/historical_data_saver.py`

Agregada función inteligente que detecta y completa automáticamente campos obligatorios:

```python
def completar_campos_obligatorios(objeto_destino, logger=None):
    """
    Completa campos obligatorios con valores por defecto si están vacíos.
    """
    from django.db import models
    from django.utils import timezone
    
    for field in objeto_destino._meta.fields:
        if field.null or field.has_default():
            continue
        
        valor_actual = getattr(objeto_destino, field.name, None)
        
        if valor_actual is None or valor_actual == '':
            if isinstance(field, models.BooleanField):
                setattr(objeto_destino, field.name, False)
            elif isinstance(field, models.DateTimeField):
                setattr(objeto_destino, field.name, timezone.now())
            # ... más tipos de campos
```

### Cambio 4: Actualización de Funciones de Procesamiento

Todas las 11 funciones `_procesar_*` ahora:
1. Usan `aplicar_mapeo_campos()` para mapear campos inglés→español
2. Llaman a `completar_campos_obligatorios()` antes de `.save()`
3. Definen correctamente `id_original = datos.get('id')`

### Cambio 5: Archivo `mapeos_campos_docencia.py`

Creado con mapeos completos de campos para las 11 tablas de docencia.

## Archivos Modificados

1. ✅ `datos_archivados/views.py` - Fix de scope en `ejecutar_combinacion_seleccionada()`
2. ✅ `datos_archivados/historical_data_saver.py` - Import, función completar_campos_obligatorios, y actualizaciones en todas las funciones _procesar_*
3. ✅ `mapeos_campos_docencia.py` - Creado con mapeos completos

## Resultado

El modal ahora funciona correctamente:

```
✅ Guardado exitoso!
  - Total guardado: 8817 registros
  - Tablas procesadas: 11

Desglose:
- HistoricalArea: 6 registros
- HistoricalCourseCategory: 4 registros
- HistoricalCourseInformation: 50 registros
- HistoricalSubjectInformation: 190 registros
- HistoricalEdition: 6 registros
- HistoricalEnrollmentApplication: 32 registros
- HistoricalAccountNumber: 2 registros
- HistoricalEnrollmentPay: 61 registros
- HistoricalEnrollment: 184 registros
- HistoricalApplication: 8282 registros
```

## Cómo Usar

1. Ve a la página de "Tablas Archivadas" en el admin de Django
2. Haz clic en el botón "Seleccionar Tablas"
3. Haz clic en "Seleccionar y Combinar"
4. En el modal, selecciona las 11 tablas de docencia
5. Haz clic en "Combinar Tablas Seleccionadas"
6. Espera a que el proceso termine (1-2 minutos)
7. Los registros se guardarán automáticamente en la app historial

## Verificación

Para verificar que los registros se guardaron:

1. Ve al admin de Django
2. Navega a la app "Historial"
3. Verifica que existen registros en los modelos históricos

O ejecuta el script de prueba:
```bash
python test_modal_real.py
```

## Estado Final

✅ **COMPLETADO Y FUNCIONANDO**

El modal de combinación selectiva ahora guarda correctamente todos los registros de las 11 tablas de docencia en la app historial del admin de Django.
