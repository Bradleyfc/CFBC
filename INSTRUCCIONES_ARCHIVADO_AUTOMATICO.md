# 📖 Instrucciones: Archivado Automático de Cursos Académicos

## 🎯 ¿Qué hace el sistema?

Cuando creas un nuevo curso académico y lo activas, el sistema **automáticamente archiva el curso académico anterior** y **copia todos sus datos** (cursos, matrículas, asistencias, calificaciones) a la aplicación `datos_archivados`.

## 🚀 Uso Normal (Automático)

### Paso 1: Crear un nuevo curso académico

Desde el panel de administración de Django:

1. Ve a **Principal → Cursos Académicos**
2. Haz clic en **Agregar Curso Académico**
3. Ingresa el nombre (ej: `2026-2027`)
4. Marca la casilla **Activo**
5. Guarda

### Paso 2: El sistema archiva automáticamente

Cuando guardas el nuevo curso académico como activo:

1. ✅ El curso académico anterior se marca como `archivado=True`
2. ✅ Se copian automáticamente todos los datos a `datos_archivados`:
   - Cursos
   - Matrículas
   - Asistencias
   - Calificaciones
   - Notas individuales
   - Usuarios (profesores y estudiantes)

### Paso 3: Verificar el archivado

Puedes verificar que el archivado funcionó:

**Opción 1: Desde el Admin de Django**
1. Ve a **Datos Archivados → Cursos Académicos Archivados**
2. Deberías ver el curso académico anterior
3. Explora los cursos archivados, matrículas, etc.

**Opción 2: Usando el script de prueba**
```bash
venv/bin/python probar_archivado_automatico.py
```

Selecciona la opción `2. Ver datos archivados` para ver las estadísticas.

## 🧪 Prueba Manual (Opcional)

Si quieres probar el archivado sin crear un nuevo curso académico:

### Usando el script de prueba:

```bash
venv/bin/python probar_archivado_automatico.py
```

1. Selecciona `3. Archivar un curso académico`
2. Elige el curso académico que deseas archivar
3. Confirma la operación
4. El script te mostrará:
   - Cuántos datos se archivaron
   - Comparación entre datos originales y archivados
   - Verificación de que todo se copió correctamente

### Usando el shell de Django:

```bash
venv/bin/python manage.py shell
```

```python
from principal.models import CursoAcademico

# Obtener un curso académico
ca = CursoAcademico.objects.get(nombre='2025-2026')

# Archivarlo manualmente
ca.archivado = True
ca.activo = False
ca.save()

# El sistema automáticamente copiará todos los datos a datos_archivados
```

## 📊 Ver Datos Archivados

### Desde el Admin de Django:

1. **Cursos Académicos Archivados**
   - Ruta: `Datos Archivados → Cursos Académicos Archivados`
   - Muestra todos los cursos académicos archivados

2. **Cursos Archivados**
   - Ruta: `Datos Archivados → Cursos Archivados`
   - Muestra todos los cursos de cursos académicos archivados

3. **Matrículas Archivadas**
   - Ruta: `Datos Archivados → Matrículas Archivadas`
   - Muestra todas las matrículas archivadas

4. **Calificaciones Archivadas**
   - Ruta: `Datos Archivados → Calificaciones Archivadas`
   - Muestra todas las calificaciones archivadas

5. **Asistencias Archivadas**
   - Ruta: `Datos Archivados → Asistencias Archivadas`
   - Muestra todas las asistencias archivadas

### Desde el script de prueba:

```bash
venv/bin/python probar_archivado_automatico.py
```

Selecciona `2. Ver datos archivados` para ver estadísticas completas.

## 🔍 Consultas Útiles

### Ver todos los cursos académicos archivados:

```python
from datos_archivados.models import CursoAcademicoArchivado

archivados = CursoAcademicoArchivado.objects.all()
for ca in archivados:
    print(f"{ca.nombre} - Archivado el {ca.fecha_migracion}")
```

### Ver cursos de un curso académico archivado:

```python
from datos_archivados.models import CursoAcademicoArchivado, CursoArchivado

ca = CursoAcademicoArchivado.objects.get(nombre='2025-2026')
cursos = CursoArchivado.objects.filter(curso_academico=ca)

print(f"Cursos archivados de {ca.nombre}: {cursos.count()}")
for curso in cursos:
    print(f"  - {curso.name} ({curso.teacher_name})")
```

### Ver matrículas de un estudiante archivado:

```python
from datos_archivados.models import UsuarioArchivado, MatriculaArchivada

# Buscar por username
estudiante = UsuarioArchivado.objects.get(username='juan.perez')
matriculas = MatriculaArchivada.objects.filter(student=estudiante)

print(f"Matrículas archivadas de {estudiante.first_name} {estudiante.last_name}:")
for mat in matriculas:
    print(f"  - {mat.course.name} ({mat.course.curso_academico.nombre})")
```

## ⚠️ Preguntas Frecuentes

### ¿Los datos se eliminan de la aplicación principal?

**No.** El archivado **copia** los datos a `datos_archivados` pero **NO los elimina** de `principal`. Esto es intencional para mantener la integridad referencial y permitir auditorías.

### ¿Qué pasa si intento archivar el mismo curso dos veces?

El sistema detecta que el curso ya fue archivado y **no duplica los datos**. Simplemente registra un log informativo y continúa.

### ¿Puedo deshacer un archivado?

El archivado no se puede deshacer automáticamente, pero puedes:
1. Cambiar el estado del curso académico a `activo=True, archivado=False`
2. Los datos archivados permanecerán en `datos_archivados`
3. Los datos originales siguen en `principal`

### ¿Cómo sé si el archivado funcionó correctamente?

Usa el script de prueba:
```bash
venv/bin/python probar_archivado_automatico.py
```

O verifica en el admin de Django que existen registros en `Datos Archivados`.

### ¿Qué pasa si hay un error durante el archivado?

El sistema usa **transacciones atómicas**. Si algo falla:
- Se revierte toda la operación
- No quedan datos parcialmente archivados
- Se registra el error en los logs
- El curso académico sigue marcado como archivado, pero sin datos en `datos_archivados`

Puedes revisar los logs para ver el error:
```bash
# Ver logs recientes
tail -f logs/django.log
```

### ¿Puedo exportar los datos archivados?

Sí, desde el admin de Django puedes:
1. Seleccionar los registros que deseas exportar
2. Usar la acción "Exportar a CSV" (si está configurada)
3. O crear un script personalizado para exportar a Excel/PDF

## 🛠️ Solución de Problemas

### El archivado no se ejecuta automáticamente

1. Verifica que las señales estén configuradas en `principal/models.py`
2. Revisa los logs para ver si hay errores
3. Asegúrate de que el curso académico se está marcando como `archivado=True`

### Los datos no aparecen en datos_archivados

1. Ejecuta el script de prueba para verificar:
   ```bash
   venv/bin/python probar_archivado_automatico.py
   ```
2. Revisa los logs de Django para ver errores
3. Verifica que la migración se aplicó correctamente:
   ```bash
   venv/bin/python manage.py showmigrations datos_archivados
   ```

### Error: "No module named 'datos_archivados.archivado_service'"

Asegúrate de que el archivo `datos_archivados/archivado_service.py` existe y está en el lugar correcto.

## 📞 Soporte

Si tienes problemas:

1. **Revisa los logs**: `tail -f logs/django.log`
2. **Ejecuta el script de prueba**: `venv/bin/python probar_archivado_automatico.py`
3. **Consulta la documentación técnica**: `ARCHIVADO_AUTOMATICO_CURSOS.md`

## ✅ Checklist de Verificación

Después de implementar el sistema, verifica:

- [ ] Las migraciones están aplicadas: `venv/bin/python manage.py migrate`
- [ ] El script de prueba funciona: `venv/bin/python probar_archivado_automatico.py`
- [ ] Puedes ver los modelos en el admin: `Datos Archivados → Cursos Académicos Archivados`
- [ ] Al crear un nuevo curso académico, el anterior se archiva automáticamente
- [ ] Los datos archivados aparecen en `datos_archivados`

---

**¡El sistema está listo para usar!** 🎉

La próxima vez que crees un nuevo curso académico, el anterior se archivará automáticamente con todos sus datos.
