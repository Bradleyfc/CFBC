# Solución al Problema del Modal de Combinación de Tablas

## Problema Identificado

Cuando se seleccionan las 11 tablas de docencia en el modal "Seleccionar y Combinar Tablas Específicas" y se presiona "Combinar tablas", no se guardan registros en la app historial.

## Causa Raíz

Se identificaron DOS problemas principales:

### 1. Campos de Auditoría Faltantes en los Modelos

Los modelos históricos en `historial/models.py` NO tenían definidos los campos de auditoría que SÍ existen en la base de datos:
- `id_original` (NOT NULL)
- `tabla_origen` (NOT NULL)
- `fecha_consolidacion` (NOT NULL)
- `dato_archivado_id` (nullable)

Esto causaba el error:
```
null value in column "id_original" of relation "historial_docenciaarea" violates not-null constraint
```

### 2. Mapeo de Campos Incorrecto

Los datos archivados tienen nombres de campos en INGLÉS (de la base de datos MariaDB original):
- `name` → debe mapearse a `nombre`
- `description` → debe mapearse a `descripcion`
- `typeOf` → debe mapearse a `codigo`

Pero la función `copiar_campos_a_modelo_historico` intentaba copiar directamente sin mapeo, resultando en "Campos copiados: 0".

## Solución Implementada

### Paso 1: Agregar Campos de Auditoría a Todos los Modelos Históricos ✓

Se agregaron los siguientes campos a TODOS los modelos históricos:

```python
# Campos de auditoría
id_original = models.IntegerField()
tabla_origen = models.CharField(max_length=255)
fecha_consolidacion = models.DateTimeField(auto_now_add=True)
dato_archivado = models.ForeignKey(
    'datos_archivados.DatoArchivadoDinamico',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='historical_xxx'
)
```

Modelos actualizados:
- ✓ HistoricalArea
- ✓ HistoricalCourseCategory
- ✓ HistoricalCourseInformation
- ✓ HistoricalCourseInformationAdminTeachers
- ✓ HistoricalEnrollmentApplication
- ✓ HistoricalEnrollmentPay
- ✓ HistoricalAccountNumber
- ✓ HistoricalEnrollment
- ✓ HistoricalSubjectInformation
- ✓ HistoricalEdition
- ✓ HistoricalApplication

### Paso 2: Crear Mapeos de Campos (PENDIENTE)

Necesitamos crear mapeos de campos inglés → español para cada tabla de docencia en `historical_data_saver.py`.

Ejemplo para Docencia_area:
```python
MAPEO_CAMPOS_AREA = {
    'name': 'nombre',
    'description': 'descripcion',
    'typeOf': 'codigo'
}
```

### Paso 3: Actualizar Funciones de Procesamiento (PENDIENTE)

Cada función `_procesar_xxx` debe:
1. Aplicar el mapeo de campos ANTES de copiar
2. Asignar correctamente `id_original`, `tabla_origen` y `dato_archivado`

## Próximos Pasos

1. Crear mapeos de campos para las 11 tablas de docencia
2. Actualizar todas las funciones `_procesar_xxx` para usar los mapeos
3. Probar el guardado completo con el script de diagnóstico
4. Probar desde el modal en el navegador

## Archivos Modificados

- `historial/models.py` - Agregados campos de auditoría a todos los modelos
- `datos_archivados/historical_data_saver.py` - Función `_procesar_areas` ya tiene la estructura correcta

## Scripts de Diagnóstico Creados

- `diagnostico_modal_combinar.py` - Script completo de diagnóstico
- `verificar_estructura_tabla.py` - Verifica estructura de tablas en BD
- `agregar_campos_auditoria_modelos.py` - Script para agregar campos automáticamente
- `completar_campos_auditoria.py` - Script para completar campos faltantes
