# Instrucciones para Completar la Actualización

## Estado Actual

✓ Modelos históricos actualizados con campos de auditoría (11/11)
✓ Mapeos de campos creados en `mapeos_campos_docencia.py`
✓ Import agregado en `historical_data_saver.py`
✓ Función `_procesar_areas` actualizada y funcionando correctamente
✓ Función `_procesar_categorias` actualizada y funcionando correctamente

⚠ Faltan actualizar 9 funciones más

## Funciones que Faltan Actualizar

Las siguientes funciones en `datos_archivados/historical_data_saver.py` necesitan ser actualizadas:

1. `_procesar_cursos` (línea ~380)
2. `_procesar_admin_teachers` (línea ~425)
3. `_procesar_asignaturas` (línea ~479)
4. `_procesar_ediciones` (línea ~520)
5. `_procesar_solicitudes` (línea ~571)
6. `_procesar_cuentas` (línea ~620)
7. `_procesar_pagos` (línea ~667)
8. `_procesar_inscripciones` (línea ~708)
9. `_procesar_aplicaciones` (línea ~759)

## Patrón de Actualización

Para cada función, necesitas hacer 3 cambios:

### 1. Agregar mapeo de campos

ANTES de crear el objeto, agregar:
```python
# Aplicar mapeo de campos
datos_mapeados = aplicar_mapeo_campos(datos, 'Nombre_Tabla')
```

### 2. Actualizar creación del objeto

CAMBIAR:
```python
objeto = ModeloHistorico()
```

POR:
```python
objeto = ModeloHistorico(
    id_original=id_original,
    tabla_origen='Nombre_Tabla',
    dato_archivado=dato
)
```

### 3. Actualizar llamada a copiar_campos

CAMBIAR:
```python
copiar_campos_a_modelo_historico(objeto, datos, ...)
```

POR:
```python
copiar_campos_a_modelo_historico(objeto, datos_mapeados, ...)
```

## Mapeo de Tablas

- `_procesar_cursos` → `'Docencia_courseinformation'`
- `_procesar_admin_teachers` → `'Docencia_courseinformation_adminteachers'`
- `_procesar_asignaturas` → `'Docencia_subjectinformation'`
- `_procesar_ediciones` → `'Docencia_edition'`
- `_procesar_solicitudes` → `'Docencia_enrollmentapplication'`
- `_procesar_cuentas` → `'Docencia_accountnumber'`
- `_procesar_pagos` → `'Docencia_enrollmentpay'`
- `_procesar_inscripciones` → `'Docencia_enrollment'`
- `_procesar_aplicaciones` → `'Docencia_application'`

## Ejemplo Completo

ANTES:
```python
def _procesar_cursos(...):
    for dato in datos_tabla:
        datos = dato.datos_originales
        id_original = datos.get('id')
        
        # Crear curso
        curso = ModeloHistorico()
        copiar_campos_a_modelo_historico(curso, datos, ...)
        curso.save()
```

DESPUÉS:
```python
def _procesar_cursos(...):
    for dato in datos_tabla:
        datos = dato.datos_originales
        id_original = datos.get('id')
        
        # Aplicar mapeo de campos
        datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_courseinformation')
        
        # Crear curso
        curso = ModeloHistorico(
            id_original=id_original,
            tabla_origen='Docencia_courseinformation',
            dato_archivado=dato
        )
        copiar_campos_a_modelo_historico(curso, datos_mapeados, ...)
        curso.save()
```

## Cómo Probar

Después de actualizar todas las funciones:

```bash
source venv/bin/activate
python diagnostico_modal_combinar.py
```

Debe mostrar:
- ✓ Todos los pasos exitosos
- Campos copiados > 0 para cada tabla
- Total de registros guardados: 8966

## Nota Especial: _procesar_admin_teachers

Esta función usa `get_or_create` en lugar de crear directamente. El patrón es ligeramente diferente:

```python
# Aplicar mapeo de campos
datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_courseinformation_adminteachers')

# Crear relación
relacion, created = ModeloHistorico.objects.get_or_create(
    id_original=id_original,
    tabla_origen='Docencia_courseinformation_adminteachers',
    dato_archivado=dato,
    curso=curso,
    profesor=profesor
)
```
