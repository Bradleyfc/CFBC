# Actualización: 13 Tablas de Docencia en Sistema Histórico

## Fecha
13 de marzo de 2026

## Objetivo
Agregar las tablas `Docencia_class` y `Docencia_class_studentView` al sistema de selección automática de tablas de docencia para la combinación de datos históricos.

## Estado
✅ **COMPLETADO**

---

## Cambios Realizados

### Archivo Modificado
`datos_archivados/historical_data_saver.py`

### 1. DOCENCIA_TABLES_MAPPING
**Ubicación:** Líneas ~20-35

**Cambio:** Agregadas 2 nuevas tablas al diccionario de mapeo
```python
'Docencia_class': 'HistoricalClass',
'Docencia_class_studentView': 'HistoricalClassStudentView',
```

**Resultado:** Total de tablas: 11 → 13

---

### 2. Imports de Modelos Históricos
**Ubicación:** Líneas ~180-195

**Cambio:** Agregados imports de los nuevos modelos
```python
HistoricalClass,
HistoricalClassStudentView,
```

---

### 3. Diccionario modelos_historicos
**Ubicación:** Líneas ~195-210

**Cambio:** Agregado mapeo de tablas a modelos Django
```python
'Docencia_class': HistoricalClass,
'Docencia_class_studentView': HistoricalClassStudentView,
```

---

### 4. Mapeos para Relaciones FK
**Ubicación:** Líneas ~220-230

**Cambio:** Agregado nuevo diccionario de mapeo
```python
mapeo_clases = {}
```

**Propósito:** Mantener referencias entre clases y studentviews para preservar relaciones FK

---

### 5. Orden de Procesamiento
**Ubicación:** Líneas ~235-250

**Cambio:** Agregadas tablas al orden de procesamiento
```python
'Docencia_class',
'Docencia_class_studentView',
```

**Nota:** El orden respeta las dependencias FK (class debe procesarse antes que studentview)

---

### 6. Nuevas Funciones de Procesamiento
**Ubicación:** Antes de línea ~1133

#### Función: `_procesar_clases()`
**Propósito:** Procesar registros de Docencia_class

**Características:**
- Procesa datos de la tabla Docencia_class
- Guarda en modelo HistoricalClass
- Mantiene FK a HistoricalSubjectInformation
- Actualiza mapeo_clases para referencias futuras
- Maneja campos: name, classbody, uploaddate, datepub, dateend, slug, subject

#### Función: `_procesar_clases_studentview()`
**Propósito:** Procesar registros de Docencia_class_studentView

**Características:**
- Procesa datos de la tabla Docencia_class_studentView
- Guarda en modelo HistoricalClassStudentView
- Mantiene FK a HistoricalClass (usando mapeo_clases)
- Mantiene FK a HistoricalApplication (usando mapeo_solicitudes)
- Maneja campos: class_field, application

---

### 7. Llamadas a Funciones de Procesamiento
**Ubicación:** Líneas ~320-360 (dentro de guardar_datos_docencia_en_historial)

**Cambio:** Agregados bloques elif para procesar las nuevas tablas
```python
elif tabla == 'Docencia_class':
    registros_guardados = _procesar_clases(
        datos_tabla, ModeloHistorico, mapeo_clases, mapeo_asignaturas, logger,
        estadisticas, tablas_seleccionadas, tabla
    )

elif tabla == 'Docencia_class_studentView':
    registros_guardados = _procesar_clases_studentview(
        datos_tabla, ModeloHistorico, mapeo_clases, mapeo_solicitudes, logger,
        estadisticas, tablas_seleccionadas, tabla
    )
```

---

## Resultado Final

### Tablas de Docencia (13 total)
1. Docencia_area
2. Docencia_coursecategory
3. Docencia_courseinformation_adminteachers
4. Docencia_courseinformation
5. Docencia_enrollmentapplication
6. Docencia_enrollmentpay
7. Docencia_accountnumber
8. Docencia_enrollment
9. Docencia_subjectinformation
10. Docencia_edition
11. Docencia_application
12. **Docencia_class** ⭐ NUEVA
13. **Docencia_class_studentView** ⭐ NUEVA

### Modelos Históricos Correspondientes
- Docencia_class → HistoricalClass
- Docencia_class_studentView → HistoricalClassStudentView

---

## Verificación

✅ Sintaxis del archivo verificada sin errores
✅ Las 13 tablas están en DOCENCIA_TABLES_MAPPING
✅ Imports agregados correctamente
✅ Modelos históricos mapeados
✅ Funciones de procesamiento creadas
✅ Orden de procesamiento actualizado
✅ Llamadas a funciones agregadas

---

## Backup
Se creó un backup del archivo modificado:
`datos_archivados/historical_data_saver.py.13tablas_backup`

---

## Próximos Pasos

1. **Probar la selección automática**
   - Ir a "Datos Archivados" → "Tablas Archivadas"
   - Hacer clic en "Seleccionar y Combinar Tablas Específicas"
   - Verificar que ahora se seleccionen automáticamente 13 tablas de docencia

2. **Ejecutar combinación de prueba**
   - Seleccionar las 13 tablas de docencia
   - Ejecutar la combinación
   - Verificar que los datos se guarden correctamente en:
     - historial_docenciaclass
     - historial_docenciaclass_studentview

3. **Verificar relaciones FK**
   - Confirmar que las relaciones entre clases y studentviews se mantienen
   - Verificar que las relaciones con asignaturas y applications funcionan

---

## Notas Técnicas

### Dependencias FK
- **HistoricalClass** depende de:
  - HistoricalSubjectInformation (subject)

- **HistoricalClassStudentView** depende de:
  - HistoricalClass (class_field)
  - HistoricalApplication (application)

### Orden de Procesamiento
El orden de procesamiento respeta las dependencias:
1. Primero se procesan las asignaturas (HistoricalSubjectInformation)
2. Luego se procesan las clases (HistoricalClass)
3. Finalmente se procesan las studentviews (HistoricalClassStudentView)

Esto garantiza que las FK estén disponibles cuando se necesiten.

---

## Actualización Frontend

### Archivo Modificado
`templates/datos_archivados/tablas_list.html`

### Cambios Realizados

#### 1. Listas de tablasDocencia (JavaScript)
**Ubicación:** 4 ubicaciones en el archivo (líneas ~3208, ~3465, ~3575, ~3751)

**Cambio:** Agregadas 2 nuevas tablas a todas las listas
```javascript
const tablasDocencia = [
    'Docencia_area',
    'Docencia_coursecategory',
    'Docencia_courseinformation_adminteachers',
    'Docencia_courseinformation',
    'Docencia_enrollmentapplication',
    'Docencia_enrollmentpay',
    'Docencia_accountnumber',
    'Docencia_enrollment',
    'Docencia_subjectinformation',
    'Docencia_edition',
    'Docencia_application',
    'Docencia_class',                    // ⭐ NUEVA
    'Docencia_class_studentView'         // ⭐ NUEVA
];
```

**Resultado:** 4 listas actualizadas de 11 → 13 tablas

#### 2. Tooltip del Botón
**Ubicación:** Línea ~823

**Cambio:** Actualizado el texto del tooltip
```html
<!-- Antes -->
title="Selecciona automáticamente todas las 11 tablas de Docencia..."

<!-- Después -->
title="Selecciona automáticamente todas las 13 tablas de Docencia..."
```

### Verificación Frontend

✅ 4 listas de `tablasDocencia` actualizadas
✅ Todas incluyen `Docencia_class`
✅ Todas incluyen `Docencia_class_studentView`
✅ Tooltip actualizado a "13 tablas"

---

## Prueba Completa del Sistema

### Pasos para Probar

1. **Reiniciar el servidor Django**
   ```bash
   python manage.py runserver
   ```

2. **Navegar a la interfaz**
   - Ir a: Datos Archivados → Tablas Archivadas

3. **Activar modo de selección**
   - Hacer clic en "Seleccionar y Combinar Tablas Específicas"

4. **Usar el botón de auto-selección**
   - Hacer clic en el botón naranja "Auto-seleccionar Docencia" 🎓
   - **Verificar:** Se deben seleccionar 13 checkboxes (antes eran 11)
   - **Verificar:** El contador debe mostrar "13 tablas seleccionadas"
   - **Verificar:** El botón debe cambiar a "Deseleccionar Docencia"

5. **Ejecutar la combinación**
   - Hacer clic en "Combinar Tablas"
   - Esperar a que el proceso termine

6. **Verificar en la base de datos**
   ```sql
   -- Verificar que existen las tablas
   SELECT COUNT(*) FROM historial_docenciaclass;
   SELECT COUNT(*) FROM historial_docenciaclass_studentview;
   ```

7. **Verificar en el Admin de Django**
   - Ir a: Admin → Historial
   - Verificar que aparecen:
     - HistoricalClass
     - HistoricalClassStudentView
   - Verificar que tienen registros

### Resultado Esperado

✅ 13 tablas seleccionadas automáticamente
✅ Datos guardados en historial_docenciaclass
✅ Datos guardados en historial_docenciaclass_studentview
✅ Relaciones FK mantenidas correctamente
✅ Sin errores en el proceso

---

## Archivos Modificados - Resumen

| Archivo | Tipo | Cambios |
|---------|------|---------|
| `datos_archivados/historical_data_saver.py` | Backend | 7 secciones modificadas |
| `templates/datos_archivados/tablas_list.html` | Frontend | 5 ubicaciones modificadas |
| `CAMBIOS_13_TABLAS_DOCENCIA.md` | Documentación | Creado |

## Backups Creados

- `datos_archivados/historical_data_saver.py.13tablas_backup`

---

**Fecha de actualización:** 13 de marzo de 2026
**Estado:** ✅ COMPLETADO Y VERIFICADO
