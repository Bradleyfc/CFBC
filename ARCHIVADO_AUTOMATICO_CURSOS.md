# Archivado Automático de Cursos Académicos

## 📋 Descripción del Problema

Cuando se creaba un nuevo curso académico, el curso académico anterior se archivaba automáticamente (marcando `archivado=True`), pero **los datos asociados** (cursos, matrículas, asistencias, calificaciones) **permanecían en la aplicación de Gestión Académica**.

Esto causaba que:
- Los datos del curso académico archivado seguían mezclados con los del curso activo
- No había separación clara entre datos históricos y datos actuales
- La app `datos_archivados` tenía modelos preparados pero no se usaban para archivar datos del sistema actual

## ✅ Solución Implementada

Se implementó un **sistema de archivado automático** que copia todos los datos de un curso académico a los modelos de `datos_archivados` cuando este se marca como archivado.

### Componentes Creados

#### 1. **Servicio de Archivado** (`datos_archivados/archivado_service.py`)

Función principal: `archivar_datos_curso_academico(curso_academico)`

**Proceso de archivado:**

1. **Verifica duplicados**: Si el curso académico ya fue archivado previamente, no lo vuelve a archivar
2. **Crea CursoAcademicoArchivado**: Copia el curso académico a `datos_archivados`
3. **Archiva Cursos**: Copia todos los cursos del curso académico
4. **Archiva Usuarios**: Crea `UsuarioArchivado` para profesores y estudiantes (sin duplicar)
5. **Archiva Matrículas**: Copia todas las matrículas del curso académico
6. **Archiva Calificaciones y Notas**: Copia calificaciones y sus notas individuales
7. **Archiva Asistencias**: Copia todas las asistencias de los cursos del curso académico

**Características:**
- ✅ Usa transacciones atómicas (todo o nada)
- ✅ Evita duplicar usuarios archivados
- ✅ Vincula usuarios archivados con usuarios actuales (`usuario_actual`)
- ✅ Vincula profesores archivados con profesores actuales (`teacher_actual`)
- ✅ Maneja casos donde faltan relaciones (crea matrículas mínimas si es necesario)
- ✅ Registra logs detallados del proceso

#### 2. **Señales en `principal/models.py`**

Se agregaron dos señales para detectar cuando un `CursoAcademico` se archiva:

**`pre_save`**: Captura el estado anterior de `archivado`
```python
@receiver(pre_save, sender=CursoAcademico)
def _capturar_estado_anterior_curso_academico(sender, instance, **kwargs):
    # Guarda el estado anterior para detectar el cambio
```

**`post_save`**: Ejecuta el archivado cuando cambia a `archivado=True`
```python
@receiver(post_save, sender=CursoAcademico)
def _archivar_datos_al_archivar_curso_academico(sender, instance, **kwargs):
    # Llama al servicio de archivado si recién se archivó
```

#### 3. **Migración de Base de Datos**

Se actualizó el modelo `NotaIndividualArchivada` para que el campo `valor` sea `DecimalField` (igual que en `principal`):

```python
# Antes:
valor = models.PositiveIntegerField(verbose_name='Valor de la Nota')

# Después:
valor = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Valor de la Nota')
```

**Migración aplicada:**
- `datos_archivados/migrations/0006_alter_notaindividualarchivada_valor_decimal.py`

## 🔄 Flujo de Archivado

```
┌─────────────────────────────────────────────────────────────┐
│  1. Usuario crea nuevo CursoAcademico y lo marca como activo│
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CursoAcademico.save() archiva automáticamente los demás │
│     (archivado=True, activo=False)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Señal pre_save captura estado anterior                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Señal post_save detecta cambio a archivado=True         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Llama a archivar_datos_curso_academico()                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Copia todos los datos a modelos de datos_archivados:    │
│     - CursoAcademicoArchivado                               │
│     - CursoArchivado                                        │
│     - UsuarioArchivado (profesores y estudiantes)           │
│     - MatriculaArchivada                                    │
│     - CalificacionArchivada                                 │
│     - NotaIndividualArchivada                               │
│     - AsistenciaArchivada                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Datos archivados disponibles en datos_archivados        │
│     Datos originales permanecen en principal (opcional)     │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Modelos de Datos Archivados

### Estructura de Relaciones

```
CursoAcademicoArchivado (2024-2025)
    │
    ├── CursoArchivado (Inglés Básico)
    │       ├── teacher_actual → User (profesor actual)
    │       └── teacher_id_original (ID del profesor)
    │
    ├── MatriculaArchivada
    │       ├── course → CursoArchivado
    │       └── student → UsuarioArchivado
    │
    ├── CalificacionArchivada
    │       ├── course → CursoArchivado
    │       ├── student → UsuarioArchivado
    │       ├── matricula → MatriculaArchivada
    │       └── NotaIndividualArchivada (múltiples)
    │
    └── AsistenciaArchivada
            ├── course → CursoArchivado
            └── student → UsuarioArchivado

UsuarioArchivado
    ├── usuario_actual → User (vinculación con usuario actual)
    ├── id_original (ID del usuario en principal)
    └── datos del perfil (carnet, dirección, etc.)
```

## 🧪 Pruebas

### Script de Prueba: `probar_archivado_automatico.py`

Script interactivo para probar el archivado automático:

```bash
venv/bin/python probar_archivado_automatico.py
```

**Funciones:**
1. **Ver cursos académicos**: Lista todos los cursos académicos con sus datos
2. **Ver datos archivados**: Muestra estadísticas de datos en `datos_archivados`
3. **Archivar un curso académico**: Archiva un curso y verifica que los datos se copiaron correctamente

### Verificación Manual

```python
from principal.models import CursoAcademico
from datos_archivados.models import CursoAcademicoArchivado, CursoArchivado

# Obtener un curso académico
ca = CursoAcademico.objects.get(nombre='2024-2025')

# Archivarlo
ca.archivado = True
ca.activo = False
ca.save()

# Verificar que se archivó
ca_archivado = CursoAcademicoArchivado.objects.get(id_original=ca.pk)
print(f"Archivado: {ca_archivado}")

# Ver cursos archivados
cursos = CursoArchivado.objects.filter(curso_academico=ca_archivado)
print(f"Cursos archivados: {cursos.count()}")
```

## 🔍 Campos Importantes

### `id_original`
Todos los modelos archivados tienen un campo `id_original` que almacena el ID del registro original en `principal`. Esto permite:
- Evitar duplicados al archivar
- Vincular datos archivados con datos actuales
- Rastrear el origen de cada registro archivado

### Vinculaciones con Datos Actuales

Los modelos archivados mantienen referencias a los datos actuales:

- `UsuarioArchivado.usuario_actual` → `User`
- `CursoArchivado.teacher_actual` → `User`

Esto permite:
- Saber qué usuario actual corresponde a un usuario archivado
- Filtrar datos archivados por usuario actual
- Mantener la trazabilidad entre sistemas

## ⚠️ Consideraciones

### 1. **Los datos NO se eliminan de `principal`**

El archivado **copia** los datos a `datos_archivados` pero **NO los elimina** de `principal`. Esto es intencional para:
- Mantener integridad referencial
- Permitir auditorías
- Facilitar recuperación de datos

Si deseas eliminar los datos originales después de archivar, deberás implementar esa lógica por separado.

### 2. **Archivado es idempotente**

Si intentas archivar un curso académico que ya fue archivado, el sistema:
- Detecta que ya existe en `datos_archivados`
- No duplica los datos
- Registra un log informativo

### 3. **Transacciones atómicas**

Todo el proceso de archivado ocurre en una transacción atómica. Si algo falla:
- Se revierte toda la operación
- No quedan datos parcialmente archivados
- Se registra el error en los logs

### 4. **Usuarios sin duplicar**

El sistema evita crear múltiples `UsuarioArchivado` para el mismo usuario:
- Usa un mapa en memoria durante el archivado
- Busca usuarios archivados existentes antes de crear nuevos
- Vincula con `usuario_actual` para evitar duplicados entre archivados

## 📝 Logs

El sistema registra logs detallados del proceso de archivado:

```python
import logging
logger = logging.getLogger(__name__)

# Logs informativos
logger.info(f"CursoAcademicoArchivado creado: {curso_academico_archivado}")
logger.info(f"Archivado completado: {contadores}")

# Logs de advertencia
logger.warning(f"No se encontró CursoArchivado para curso.pk={curso.pk}")

# Logs de error
logger.error(f"Error al archivar: {e}", exc_info=True)
```

**Ver logs:**
```bash
# En desarrollo
tail -f logs/django.log

# En producción
journalctl -u gunicorn -f
```

## 🚀 Próximos Pasos (Opcional)

### 1. **Eliminar datos originales después de archivar**

Si deseas eliminar los datos de `principal` después de archivarlos:

```python
def eliminar_datos_archivados(curso_academico):
    """Elimina los datos de principal después de archivar."""
    # Verificar que se archivó correctamente
    if not CursoAcademicoArchivado.objects.filter(id_original=curso_academico.pk).exists():
        raise ValueError("El curso académico no ha sido archivado")
    
    # Eliminar en orden inverso a las dependencias
    Asistencia.objects.filter(course__curso_academico=curso_academico).delete()
    NotaIndividual.objects.filter(calificacion__curso_academico=curso_academico).delete()
    Calificaciones.objects.filter(curso_academico=curso_academico).delete()
    Matriculas.objects.filter(curso_academico=curso_academico).delete()
    Curso.objects.filter(curso_academico=curso_academico).delete()
```

### 2. **Interfaz de administración para datos archivados**

Crear vistas en el admin de Django para:
- Ver cursos académicos archivados
- Buscar y filtrar datos archivados
- Exportar datos archivados a Excel/PDF
- Restaurar datos archivados (si es necesario)

### 3. **Reportes de datos archivados**

Generar reportes automáticos:
- Certificados de estudiantes de cursos archivados
- Historial académico completo
- Estadísticas por curso académico

## 📚 Archivos Modificados/Creados

### Archivos Creados
- ✅ `datos_archivados/archivado_service.py` - Servicio de archivado
- ✅ `probar_archivado_automatico.py` - Script de prueba
- ✅ `ARCHIVADO_AUTOMATICO_CURSOS.md` - Esta documentación

### Archivos Modificados
- ✅ `principal/models.py` - Agregadas señales de archivado
- ✅ `datos_archivados/models.py` - Actualizado campo `valor` en `NotaIndividualArchivada`

### Migraciones Creadas
- ✅ `datos_archivados/migrations/0006_alter_notaindividualarchivada_valor_decimal.py`

## ✅ Resumen

El sistema ahora archiva automáticamente todos los datos de un curso académico cuando este se marca como archivado:

1. ✅ **Automático**: Se ejecuta mediante señales de Django
2. ✅ **Completo**: Archiva cursos, matrículas, asistencias, calificaciones y notas
3. ✅ **Seguro**: Usa transacciones atómicas y evita duplicados
4. ✅ **Trazable**: Mantiene vinculaciones con datos actuales
5. ✅ **Idempotente**: No duplica datos si se ejecuta múltiples veces
6. ✅ **Probado**: Incluye script de prueba interactivo

Los datos archivados están disponibles en la app `datos_archivados` y pueden ser consultados, exportados o utilizados para generar reportes históricos.
