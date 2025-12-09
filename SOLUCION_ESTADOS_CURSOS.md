# Solución para Estados Dinámicos de Cursos

## Problema Identificado

El sistema mostraba la etiqueta "En etapa de inscripción" para cursos cuya fecha límite de inscripción ya había pasado (mes 10 vs mes 11 actual). Esto ocurría porque:

1. **Estado Manual**: El campo `status` en el modelo `Curso` se almacena manualmente y no se actualiza automáticamente
2. **Sin Validación de Fechas**: No había lógica que comparara la fecha actual con `enrollment_deadline`
3. **Fecha del Servidor**: El sistema usa la fecha del servidor donde está ejecutándose Django (tu laptop)

## Solución Implementada

### 1. Métodos Dinámicos en el Modelo

Se agregaron dos nuevos métodos al modelo `Curso`:

```python
def get_dynamic_status(self):
    """Obtiene el estado dinámico basado en la fecha límite de inscripción"""
    
def get_dynamic_status_display(self):
    """Obtiene la descripción del estado dinámico"""
```

**Lógica implementada:**
- Si `enrollment_deadline` es None → usa el estado manual
- Si la fecha actual > fecha límite → cambia 'I' (En inscripción) a 'IT' (Plazo Terminado)
- Si la fecha actual ≤ fecha límite → cambia 'IT' a 'I' si corresponde
- Para otros estados (P, F) → mantiene el estado actual

### 2. Actualización de Templates

Se modificó `templates/cursos.html` para usar:
- `course.get_dynamic_status` en lugar de `course.status`
- `course.get_dynamic_status_display` en lugar de `course.get_status_display`

### 3. Comando de Gestión

Se creó el comando `actualizar_estados_cursos.py` que permite:

```bash
# Ver qué cambios se harían (sin aplicar)
python manage.py actualizar_estados_cursos --dry-run

# Aplicar los cambios realmente
python manage.py actualizar_estados_cursos
```

## Fecha de Referencia

**El sistema usa la fecha del servidor donde está ejecutándose Django**:

- **En desarrollo**: Fecha de tu laptop
- **En producción**: Fecha del servidor del hosting

### Zona Horaria Configurada
- **TIME_ZONE**: `America/Managua` (Nicaragua)
- **USE_TZ**: `True` (fechas conscientes de zona horaria)

Para verificar la fecha que está usando el sistema:
```python
from datetime import date
from django.utils import timezone
print(f"Fecha actual del servidor: {date.today()}")
print(f"Zona horaria: {timezone.get_current_timezone()}")
```

## Uso y Mantenimiento

### Opción 1: Estados Dinámicos (Recomendado)
Los templates ahora muestran automáticamente el estado correcto basándose en la fecha actual vs fecha límite.

### Opción 2: Actualización Manual
Ejecutar periódicamente el comando de gestión para actualizar los estados en la base de datos:
```bash
python manage.py actualizar_estados_cursos
```

### Opción 3: Automatización
Configurar un cron job o tarea programada para ejecutar el comando diariamente.

## Verificación

Para verificar que funciona correctamente:

1. **Ver estado dinámico**: Los cursos con fecha límite pasada ahora muestran "PLAZO DE INSCRIPCIÓN TERMINADO"
2. **Ejecutar comando**: `python manage.py actualizar_estados_cursos --dry-run`
3. **Verificar fecha del servidor**: El comando muestra la fecha y zona horaria actual

## Archivos Modificados

- `principal/models.py` - Agregados métodos dinámicos
- `templates/cursos.html` - Actualizado para usar estado dinámico  
- `principal/management/commands/actualizar_estados_cursos.py` - Nuevo comando
- `SOLUCION_ESTADOS_CURSOS.md` - Esta documentación