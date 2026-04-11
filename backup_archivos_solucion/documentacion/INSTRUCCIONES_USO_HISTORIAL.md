# Instrucciones de Uso - Guardado de Datos de Docencia en Historial

## 🎯 Objetivo

Guardar los datos de las 11 tablas de docencia en los modelos históricos de la app `historial`.

## 📋 Pasos para Usar

### 1. Acceder al Admin

```
http://tu-dominio/admin/
```

### 2. Navegar a Datos Archivados

```
Admin → Datos Archivados → Tablas Archivadas
```

### 3. Abrir el Modal de Selección

Hacer clic en el botón:
```
"Seleccionar y Combinar Tablas Específicas"
```

### 4. Seleccionar las 11 Tablas de Docencia

Marcar las siguientes tablas en el modal:

- ☑️ Docencia_area
- ☑️ Docencia_coursecategory
- ☑️ Docencia_courseinformation_adminteachers
- ☑️ Docencia_courseinformation
- ☑️ Docencia_enrollmentapplication
- ☑️ Docencia_enrollmentpay
- ☑️ Docencia_accountnumber
- ☑️ Docencia_enrollment
- ☑️ Docencia_subjectinformation
- ☑️ Docencia_edition
- ☑️ Docencia_application

### 5. Iniciar el Proceso

Hacer clic en:
```
"Combinar Tablas"
```

### 6. Observar el Progreso

El sistema mostrará:
- ✅ Mensaje de inicio
- 📊 Progreso en tiempo real
- ✅ Mensaje de éxito con estadísticas

## 🔍 Verificar los Resultados

### Opción 1: Desde el Admin

```
Admin → Historial → [Seleccionar modelo histórico]
```

Por ejemplo:
- Historical Areas
- Historical Course Categories
- Historical Course Information
- etc.

### Opción 2: Desde Django Shell

```bash
python3 manage.py shell
```

```python
from historial.models import *

# Verificar áreas guardadas
print(f"Áreas: {HistoricalArea.objects.count()}")

# Verificar categorías guardadas
print(f"Categorías: {HistoricalCourseCategory.objects.count()}")

# Verificar cursos guardados
print(f"Cursos: {HistoricalCourseInformation.objects.count()}")

# Ver algunos registros
for area in HistoricalArea.objects.all()[:5]:
    print(f"  - {area.nombre}")
```

### Opción 3: Revisar los Logs

```bash
# Ver logs del servidor
tail -f logs/django.log

# O en la consola donde corre el servidor
# Buscar líneas como:
# === INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL ===
# ✅ Docencia_area: 10 registros guardados en historial
# === GUARDADO EN HISTORIAL COMPLETADO EXITOSAMENTE ===
```

## 📊 Ejemplo de Salida Esperada

### Mensaje de Inicio
```json
{
  "success": true,
  "message": "Combinación selectiva iniciada para 11 tablas. Puede seguir el progreso en tiempo real.",
  "tablas_seleccionadas": [
    "Docencia_area",
    "Docencia_coursecategory",
    ...
  ]
}
```

### Logs Durante el Proceso
```
=== INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL ===
Tablas a procesar: ['Docencia_area', 'Docencia_coursecategory', ...]

--- Procesando tabla: Docencia_area ---
Encontrados 10 registros en Docencia_area
Área guardada: Matemáticas (ID original: 1)
Área guardada: Ciencias (ID original: 2)
...
✅ Docencia_area: 10 registros guardados en historial

--- Procesando tabla: Docencia_coursecategory ---
Encontrados 25 registros en Docencia_coursecategory
Categoría guardada: Básico (ID original: 1)
...
✅ Docencia_coursecategory: 25 registros guardados en historial

...

=== GUARDADO EN HISTORIAL COMPLETADO EXITOSAMENTE ===
Total de registros guardados: 1234
Tablas procesadas: 11
```

### Resultado Final (en cache)
```python
{
  'fecha_inicio': '2024-03-01T10:30:00',
  'fecha_fin': '2024-03-01T10:35:00',
  'tipo_combinacion': 'guardar_historial_docencia',
  'tablas_procesadas': [
    'Docencia_area',
    'Docencia_coursecategory',
    ...
  ],
  'total_registros_guardados': 1234,
  'tablas_procesadas': 11,
  'Docencia_area_guardados': 10,
  'Docencia_coursecategory_guardados': 25,
  'Docencia_courseinformation_guardados': 50,
  ...
}
```

## ⚠️ Notas Importantes

### ✅ Qué Hace el Sistema

- Detecta automáticamente que son tablas de docencia
- Guarda TODOS los datos en los modelos históricos
- Mantiene TODAS las relaciones foreign key
- Procesa las tablas en el orden correcto
- Muestra progreso en tiempo real
- Registra todo en logs

### ❌ Qué NO Hace el Sistema

- NO combina con tablas activas (ese es el comportamiento normal)
- NO modifica los datos originales en DatoArchivadoDinamico
- NO elimina los datos después de guardar
- NO sobrescribe registros existentes (crea nuevos)

### 🔄 Si Algo Sale Mal

1. **Revisar los logs** para ver el error específico
2. **Verificar que los modelos históricos existen** en `historial/models.py`
3. **Verificar que las tablas tienen datos** en DatoArchivadoDinamico
4. **Verificar las relaciones FK** (usuarios, etc.)

### 🧪 Probar Primero

Antes de procesar todas las tablas, puedes probar con una sola:

1. Seleccionar solo `Docencia_area`
2. Hacer clic en "Combinar Tablas"
3. Verificar que se guardó correctamente
4. Luego procesar todas las 11 tablas

## 🆘 Solución de Problemas

### Problema: "No se seleccionaron tablas para combinar"
**Solución:** Asegúrate de marcar las casillas de las 11 tablas antes de hacer clic en "Combinar Tablas"

### Problema: "La tabla X no existe en los datos archivados"
**Solución:** Verifica que la tabla tenga datos en DatoArchivadoDinamico

### Problema: "Error guardando en historial"
**Solución:** Revisa los logs para ver el error específico. Puede ser:
- Falta un modelo histórico
- Error en una relación FK
- Problema con los datos

### Problema: No veo progreso
**Solución:** 
- Refresca la página
- Revisa los logs del servidor
- Verifica que el proceso no haya terminado ya

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs: `tail -f logs/django.log`
2. Ejecuta los tests: `python3 test_historial_saver.py`
3. Verifica la configuración: `python3 manage.py check`
4. Consulta la documentación completa: `GUARDADO_HISTORIAL_DOCENCIA.md`

## ✨ Resumen Rápido

```
1. Admin → Datos Archivados → Tablas Archivadas
2. Clic en "Seleccionar y Combinar Tablas Específicas"
3. Marcar las 11 tablas de docencia
4. Clic en "Combinar Tablas"
5. Esperar a que termine
6. Verificar en Admin → Historial
```

¡Listo! 🎉
