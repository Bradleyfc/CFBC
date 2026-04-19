# 📦 Resumen: Solución de Archivado Automático

## ❌ Problema Original

Cuando creabas un nuevo curso académico, el curso académico anterior se archivaba (marcando `archivado=True`), pero **los cursos, matrículas, asistencias y calificaciones se quedaban en la aplicación de Gestión Académica** mezclados con los datos del curso activo.

## ✅ Solución Implementada

Ahora, cuando un curso académico se archiva, **automáticamente se copian todos sus datos** a la app `datos_archivados`:

### Datos que se archivan automáticamente:
- ✅ **Cursos** del curso académico
- ✅ **Matrículas** de estudiantes
- ✅ **Asistencias** de los cursos
- ✅ **Calificaciones** de estudiantes
- ✅ **Notas individuales** de cada calificación
- ✅ **Usuarios** (profesores y estudiantes) vinculados

### Cómo funciona:

```
1. Creas un nuevo CursoAcademico (ej: 2026-2027) y lo activas
   ↓
2. El sistema automáticamente archiva el curso anterior (ej: 2025-2026)
   ↓
3. Una señal detecta el archivado y ejecuta el servicio de archivado
   ↓
4. Todos los datos del curso 2025-2026 se copian a datos_archivados
   ↓
5. Los datos archivados quedan disponibles en la app datos_archivados
```

## 🔧 Archivos Creados

1. **`datos_archivados/archivado_service.py`**
   - Servicio que copia todos los datos a modelos archivados
   - Usa transacciones atómicas (todo o nada)
   - Evita duplicados

2. **`probar_archivado_automatico.py`**
   - Script para probar el archivado
   - Muestra estadísticas antes y después
   - Verifica que todo se archivó correctamente

3. **Señales en `principal/models.py`**
   - Detectan cuando un CursoAcademico se archiva
   - Ejecutan automáticamente el servicio de archivado

## 🧪 Cómo Probar

```bash
# Ejecutar el script de prueba
venv/bin/python probar_archivado_automatico.py
```

El script te permite:
1. Ver todos los cursos académicos y su estado
2. Ver estadísticas de datos archivados
3. Archivar un curso académico y verificar que funcionó

## 📊 Ejemplo de Uso

### Antes del archivado:
```
CursoAcademico: 2025-2026 (ACTIVO)
├── 15 Cursos
├── 120 Matrículas
├── 450 Asistencias
└── 100 Calificaciones

datos_archivados: vacío
```

### Después de crear curso 2026-2027:
```
CursoAcademico: 2026-2027 (ACTIVO)
└── (nuevo, sin datos aún)

CursoAcademico: 2025-2026 (ARCHIVADO)
├── 15 Cursos (permanecen en principal)
├── 120 Matrículas (permanecen en principal)
└── ...

datos_archivados:
├── CursoAcademicoArchivado: 2025-2026
├── 15 CursoArchivado
├── 120 MatriculaArchivada
├── 450 AsistenciaArchivada
└── 100 CalificacionArchivada
```

## ⚠️ Importante

- **Los datos NO se eliminan** de la app principal, solo se copian a `datos_archivados`
- **El archivado es automático**, no necesitas hacer nada manualmente
- **No se duplican datos** si intentas archivar el mismo curso dos veces
- **Todo ocurre en una transacción**, si algo falla se revierte todo

## 📝 Documentación Completa

Para más detalles técnicos, consulta:
- `ARCHIVADO_AUTOMATICO_CURSOS.md` - Documentación técnica completa

## ✅ Estado

- ✅ Servicio de archivado implementado
- ✅ Señales configuradas
- ✅ Migración de base de datos aplicada
- ✅ Script de prueba creado
- ✅ Documentación completa

**El sistema está listo para usar. La próxima vez que crees un nuevo curso académico, el anterior se archivará automáticamente con todos sus datos.**
