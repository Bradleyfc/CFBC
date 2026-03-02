# Guardado de Datos de Docencia en Historial

## Descripción

Se ha implementado una funcionalidad para guardar automáticamente los datos de las 11 tablas de docencia en los modelos históricos correspondientes de la app `historial` cuando se seleccionan en el modal "Seleccionar y Combinar Tablas Específicas".

## Tablas de Docencia Soportadas

Las siguientes 11 tablas de docencia se guardan automáticamente en historial:

1. **Docencia_area** → HistoricalArea
2. **Docencia_coursecategory** → HistoricalCourseCategory
3. **Docencia_courseinformation_adminteachers** → HistoricalCourseInformationAdminTeachers
4. **Docencia_courseinformation** → HistoricalCourseInformation
5. **Docencia_enrollmentapplication** → HistoricalEnrollmentApplication
6. **Docencia_enrollmentpay** → HistoricalEnrollmentPay
7. **Docencia_accountnumber** → HistoricalAccountNumber
8. **Docencia_enrollment** → HistoricalEnrollment
9. **Docencia_subjectinformation** → HistoricalSubjectInformation
10. **Docencia_edition** → HistoricalEdition
11. **Docencia_application** → HistoricalApplication

## Archivos Modificados

### 1. `datos_archivados/historical_data_saver.py` (NUEVO)

Módulo auxiliar que contiene toda la lógica para:
- Detectar si las tablas seleccionadas son tablas de docencia
- Guardar los datos en los modelos históricos correspondientes
- Mantener las relaciones foreign key correctamente
- Procesar las tablas en el orden correcto para respetar dependencias

**Funciones principales:**
- `son_todas_tablas_docencia(tablas_seleccionadas)`: Verifica si todas las tablas son de docencia
- `guardar_datos_docencia_en_historial(tablas_seleccionadas, logger)`: Guarda los datos en historial
- Funciones auxiliares `_procesar_*()` para cada tipo de tabla

### 2. `datos_archivados/views.py` (MODIFICADO)

Se modificó la función `combinar_datos_seleccionadas()` para:
- Detectar cuando se seleccionan tablas de docencia
- Llamar a la lógica de guardado en historial en lugar de la combinación normal
- Retornar estadísticas del proceso

**Ubicación de la modificación:** Línea ~3764, dentro de la función interna `ejecutar_combinacion_seleccionada()`

## Funcionamiento

### Flujo de Ejecución

1. El usuario selecciona las 11 tablas de docencia en el modal
2. Hace clic en "Combinar Tablas"
3. La vista `combinar_datos_seleccionadas` detecta que son tablas de docencia
4. En lugar de combinar, ejecuta el guardado en historial:
   - Procesa las tablas en orden para respetar dependencias FK
   - Crea registros en los modelos históricos
   - Mantiene mapeos de IDs para relaciones
   - Actualiza progreso en cache
5. Retorna mensaje de éxito con estadísticas

### Orden de Procesamiento

Las tablas se procesan en este orden para respetar dependencias:

```
1. Docencia_area (sin dependencias)
2. Docencia_coursecategory (puede tener parent self-referential)
3. Docencia_courseinformation (depende de area y categoria)
4. Docencia_courseinformation_adminteachers (depende de courseinformation)
5. Docencia_subjectinformation (depende de courseinformation)
6. Docencia_edition (depende de courseinformation)
7. Docencia_enrollmentapplication (depende de courseinformation)
8. Docencia_accountnumber (sin dependencias de docencia)
9. Docencia_enrollmentpay (depende de enrollmentapplication y accountnumber)
10. Docencia_enrollment (depende de subjectinformation y edition)
11. Docencia_application (depende de courseinformation y edition)
```

### Manejo de Relaciones Foreign Key

- **Mapeos internos**: Se mantienen diccionarios de mapeo para cada tipo de entidad
- **IDs originales**: Se usan los IDs de `datos_originales` para mantener relaciones
- **Usuarios**: Las FK a `auth_user` se resuelven buscando el usuario por ID
- **Relaciones jerárquicas**: Las categorías con `parent` se procesan en dos pasos

## Características

### ✅ Implementado

- Detección automática de tablas de docencia
- Guardado en modelos históricos con todas las relaciones
- Procesamiento transaccional con savepoints
- Manejo de errores por registro
- Actualización de progreso en cache
- Logging detallado de operaciones
- Estadísticas completas del proceso

### 🔄 Progreso en Tiempo Real

El proceso actualiza el cache con:
- Tabla actual siendo procesada
- Registros guardados por tabla
- Total de registros guardados
- Errores encontrados

### 🛡️ Manejo de Errores

- Cada registro se procesa en un savepoint independiente
- Si un registro falla, se hace rollback y se continúa con el siguiente
- Los errores se registran en el log pero no detienen el proceso
- Al final se reportan estadísticas completas

## Uso

### Desde el Admin

1. Ir a "Datos Archivados" → "Tablas Archivadas"
2. Hacer clic en "Seleccionar y Combinar Tablas Específicas"
3. Seleccionar las 11 tablas de docencia
4. Hacer clic en "Combinar Tablas"
5. El sistema detectará automáticamente que son tablas de docencia
6. Los datos se guardarán en los modelos históricos
7. Se mostrará un mensaje de éxito con las estadísticas

### Mensaje de Respuesta

```json
{
  "success": true,
  "message": "Combinación selectiva iniciada para 11 tablas. Puede seguir el progreso en tiempo real.",
  "tablas_seleccionadas": [...]
}
```

### Resultado Final (en cache)

```python
{
  'fecha_inicio': '2024-03-01T...',
  'fecha_fin': '2024-03-01T...',
  'tipo_combinacion': 'guardar_historial_docencia',
  'tablas_procesadas': [...],
  'total_registros_guardados': 1234,
  'tablas_procesadas': 11,
  'Docencia_area_guardados': 10,
  'Docencia_coursecategory_guardados': 25,
  ...
}
```

## Logs

El proceso genera logs detallados:

```
=== INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL ===
Tablas a procesar: ['Docencia_area', ...]
--- Procesando tabla: Docencia_area ---
Encontrados 10 registros en Docencia_area
Área guardada: Matemáticas (ID original: 1)
✅ Docencia_area: 10 registros guardados en historial
...
=== GUARDADO EN HISTORIAL COMPLETADO EXITOSAMENTE ===
Total de registros guardados: 1234
```

## Validación

Para verificar que los datos se guardaron correctamente:

```python
from historial.models import *

# Verificar áreas
print(HistoricalArea.objects.count())

# Verificar categorías
print(HistoricalCourseCategory.objects.count())

# Verificar cursos
print(HistoricalCourseInformation.objects.count())

# etc...
```

## Notas Técnicas

- Los modelos históricos ya existían en `historial/models.py`
- No se modificaron los modelos históricos
- La lógica es completamente independiente de la combinación normal
- Si no son todas tablas de docencia, se ejecuta la combinación normal
- El proceso es transaccional y seguro

## Mantenimiento

Si se agregan nuevas tablas de docencia:

1. Agregar el mapeo en `DOCENCIA_TABLES_MAPPING` en `historical_data_saver.py`
2. Crear el modelo histórico correspondiente en `historial/models.py`
3. Agregar la función `_procesar_*()` correspondiente
4. Agregar el caso en `guardar_datos_docencia_en_historial()`
5. Actualizar el orden de procesamiento si hay dependencias FK
