# Solución: Problemas con la Barra de Progreso de Migración

## Problemas Identificados

### 1. **Progreso Artificial Basado en Tiempo**
- **Problema**: El progreso se calculaba como `15% por minuto, máximo 90%`
- **Ubicación**: `templates/datos_archivados/dashboard.html` línea 708
- **Impacto**: El progreso no reflejaba el trabajo real completado

### 2. **Limitación Artificial al 95%**
- **Problema**: El progreso se limitaba artificialmente al 95% durante el proceso
- **Ubicación**: `datos_archivados/views.py` función `actualizar_progreso`
- **Impacto**: La barra nunca llegaba al 100% hasta el final

### 3. **Timeout Muy Corto**
- **Problema**: Timeout de 5 minutos para procesos que pueden tardar más
- **Ubicación**: `templates/datos_archivados/tablas_list.html`
- **Impacto**: Procesos largos se marcaban como "trabados" prematuramente

### 4. **Cache Perdido**
- **Problema**: El cache de progreso se perdía o no se actualizaba correctamente
- **Ubicación**: Sistema de cache de Django
- **Impacto**: El progreso se "trababa" en un porcentaje y no avanzaba

## Soluciones Implementadas

### 1. **Progreso Real Basado en Trabajo Completado**

**Archivo**: `templates/datos_archivados/dashboard.html`
```javascript
// ANTES (artificial):
let progreso = Math.min(minutos * 15, 90); // 15% por minuto, máximo 90%

// DESPUÉS (real):
let progreso = 0;
if (data.tablas_inspeccionadas > 0) {
    const tablasProcessadas = (data.tablas_con_datos || 0) + (data.tablas_vacias || 0);
    progreso = Math.min(Math.round((tablasProcessadas / data.tablas_inspeccionadas) * 100), 100);
}
```

### 2. **Eliminación de Limitación Artificial**

**Archivo**: `datos_archivados/views.py`
```python
# ANTES:
porcentaje_progreso = min(int((pasos_completados / pasos_totales) * 100), 95)

# DESPUÉS:
porcentaje_progreso = min(int((pasos_completados / pasos_totales) * 100), 100)
```

### 3. **Timeout Extendido**

**Archivo**: `templates/datos_archivados/tablas_list.html`
```javascript
// ANTES: 5 minutos (300 segundos)
if (tiempoTranscurrido > 300000) {

// DESPUÉS: 15 minutos (900 segundos)
if (tiempoTranscurrido > 900000) {
```

### 4. **Sistema de Progreso Mejorado con Cache**

**Archivo**: `datos_archivados/services.py`
- Agregado sistema de cache en tiempo real para migración
- Actualización de progreso después de cada tabla procesada
- Limpieza automática del cache al completar o fallar

```python
def actualizar_progreso_migracion(tabla_actual, tabla_num, total_tablas, registros_migrados=0):
    progreso_porcentaje = int((tabla_num / total_tablas) * 100) if total_tablas > 0 else 0
    progreso_info = {
        'en_progreso': True,
        'tabla_actual': tabla_actual,
        'tabla_numero': tabla_num,
        'total_tablas': total_tablas,
        'progreso_porcentaje': progreso_porcentaje,
        # ... más datos
    }
    cache.set('migracion_progreso', progreso_info, timeout=1800)  # 30 minutos
```

### 5. **Detección de Procesos Trabados**

**Archivo**: `datos_archivados/views.py`
- Agregado mecanismo para detectar procesos trabados (más de 20 minutos sin cambios)
- Limpieza automática del cache cuando se detecta un proceso trabado
- Mensaje de error informativo para el usuario

### 6. **Cache Extendido**

- **Migración**: Cache extendido a 30 minutos (antes 10 minutos)
- **Combinación**: Cache extendido a 30 minutos (antes 10 minutos)
- Timeout más realista para procesos largos

## Mejoras Adicionales

### 1. **Logging Mejorado**
- Logs más detallados del progreso de migración
- Información de diagnóstico para debugging
- Timestamps precisos para cada paso

### 2. **Información Más Detallada**
- Nombre de la tabla actual siendo procesada
- Número de tabla actual vs total
- Registros migrados en tiempo real
- Tablas con datos vs tablas vacías

### 3. **Recuperación de Errores**
- Mejor manejo de errores durante la migración
- Continuación del proceso aunque falle una tabla
- Limpieza automática del estado en caso de error

## Archivos Modificados

1. `templates/datos_archivados/dashboard.html` - Progreso real en dashboard
2. `datos_archivados/views.py` - Eliminación de limitaciones artificiales
3. `templates/datos_archivados/tablas_list.html` - Timeout extendido
4. `datos_archivados/services.py` - Sistema de progreso mejorado
5. `templates/datos_archivados/tablas_list.html` - Clase CSS hidden agregada

## Resultado Esperado

### ✅ **Migración Normal**
- Progreso refleja el trabajo real completado
- Barra llega al 100% cuando termina realmente
- Información detallada del proceso en tiempo real

### ✅ **Migración con Muchos Datos**
- Timeout extendido permite procesos de hasta 15 minutos
- Progreso se actualiza correctamente tabla por tabla
- No se "traba" en porcentajes intermedios

### ✅ **Detección de Problemas**
- Procesos realmente trabados se detectan después de 20 minutos
- Mensaje de error informativo para el usuario
- Limpieza automática del estado para permitir reintentos

## Pruebas

Se incluye un script de prueba `test_progreso_migracion.py` para verificar el funcionamiento:

```bash
# Probar migración
python test_progreso_migracion.py

# Probar combinación
python test_progreso_migracion.py combinacion
```

## Notas Importantes

1. **Backup**: Se recomienda hacer backup antes de aplicar estos cambios
2. **Cache**: El sistema usa cache de Django - asegurar que esté configurado correctamente
3. **Logs**: Revisar logs de Django para diagnóstico en caso de problemas
4. **Timeout**: Los timeouts pueden ajustarse según las necesidades específicas del servidor