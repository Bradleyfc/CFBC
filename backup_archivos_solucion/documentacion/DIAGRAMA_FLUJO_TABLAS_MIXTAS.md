# 🔄 Diagrama de Flujo: Manejo Inteligente de Tablas Mixtas

## 📊 Flujo Principal

```
┌─────────────────────────────────────────────────────────────┐
│  Usuario selecciona tablas en el modal                      │
│  "Seleccionar y Combinar Tablas Específicas"                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Sistema recibe tablas_seleccionadas                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  SEPARAR TABLAS EN DOS GRUPOS                                │
│  • tablas_docencia = [tabla if es_tabla_docencia(tabla)]    │
│  • tablas_usuarios = [tabla if not es_tabla_docencia(tabla)]│
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  ANÁLISIS DE TABLAS SELECCIONADAS                            │
│  • Total: X tablas                                           │
│  • Docencia: Y tablas → historial                            │
│  • Usuarios: Z tablas → combinación                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
              ┌──────┴──────┐
              │  DECISIÓN   │
              └──────┬──────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │ CASO 1 │  │ CASO 2 │  │ CASO 3 │
   └────┬───┘  └────┬───┘  └────┬───┘
        │           │           │
        │           │           │
        ▼           ▼           ▼
```

## 🎯 Caso 1: Solo Tablas de Docencia

```
┌─────────────────────────────────────────────────────────────┐
│  ESCENARIO 1: Solo tablas de docencia                        │
│  Condición: tablas_docencia AND NOT tablas_usuarios          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Acción: Guardar en modelos históricos                       │
│  • guardar_datos_docencia_en_historial(tablas_docencia)     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Resultado:                                                   │
│  • X registros guardados en historial                        │
│  • tipo_procesamiento: 'solo_docencia'                       │
│  • NO se ejecuta combinación                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
                  [FIN]
```

## 👥 Caso 2: Solo Tablas de Usuarios

```
┌─────────────────────────────────────────────────────────────┐
│  ESCENARIO 2: Solo tablas de usuarios                        │
│  Condición: tablas_usuarios AND NOT tablas_docencia          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Acción: Usar proceso de combinación existente               │
│  • Continuar con código normal de combinación                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Proceso de Combinación Normal:                              │
│  1. Procesar auth_user                                       │
│  2. Procesar auth_group                                      │
│  3. Procesar auth_user_groups                                │
│  4. Procesar registros                                       │
│  5. Procesar otras tablas                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Resultado:                                                   │
│  • X usuarios combinados                                     │
│  • Y registros combinados                                    │
│  • tipo_procesamiento: 'solo_usuarios'                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
                  [FIN]
```

## 🔀 Caso 3: Tablas Mixtas (NUEVO)

```
┌─────────────────────────────────────────────────────────────┐
│  ESCENARIO 3: Tablas mixtas (docencia + usuarios)            │
│  Condición: tablas_docencia AND tablas_usuarios              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 1/2: Guardar tablas de docencia en historial           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  try:                                                         │
│    estadisticas_docencia =                                   │
│      guardar_datos_docencia_en_historial(tablas_docencia)   │
│    estadisticas_totales['docencia_guardadas'] = X            │
│  except Exception:                                           │
│    logger.error("Error guardando docencia")                  │
│    # Continuar con usuarios aunque falle                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PASO 2/2: Procesar tablas de usuarios con combinación       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Actualizar tablas_seleccionadas:                            │
│  • tablas_seleccionadas = tablas_usuarios                    │
│  • Continuar con proceso normal de combinación               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Proceso de Combinación Normal (solo usuarios):              │
│  1. Procesar auth_user                                       │
│  2. Procesar auth_group                                      │
│  3. Procesar auth_user_groups                                │
│  4. Procesar registros                                       │
│  5. Procesar otras tablas de usuarios                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  CONSOLIDAR ESTADÍSTICAS FINALES                             │
│  • docencia_guardadas: X registros                           │
│  • usuarios_combinados: Y usuarios                           │
│  • tipo_procesamiento: 'mixto'                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Resultado Final:                                             │
│  ✅ Tablas de docencia guardadas: X registros                │
│  ✅ Tablas de usuarios combinadas: Y usuarios                │
│  📊 Estadísticas consolidadas de ambos procesos              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
                  [FIN]
```

## 🔍 Detección de Tipo de Tabla

```
┌─────────────────────────────────────────────────────────────┐
│  Función: es_tabla_docencia(tabla_nombre)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  DOCENCIA_TABLES_MAPPING = {                                 │
│    'Docencia_area': 'HistoricalArea',                        │
│    'Docencia_coursecategory': 'HistoricalCourseCategory',    │
│    'Docencia_courseinformation': 'HistoricalCourseInfo',     │
│    'Docencia_courseinformation_adminteachers': ...,          │
│    'Docencia_enrollmentapplication': ...,                    │
│    'Docencia_enrollmentpay': ...,                            │
│    'Docencia_accountnumber': ...,                            │
│    'Docencia_enrollment': ...,                               │
│    'Docencia_subjectinformation': ...,                       │
│    'Docencia_edition': ...,                                  │
│    'Docencia_application': ...                               │
│  }                                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  return tabla_nombre in DOCENCIA_TABLES_MAPPING              │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Estadísticas Finales

```
┌─────────────────────────────────────────────────────────────┐
│  estadisticas_totales = {                                    │
│    'docencia_guardadas': 0,        # Solo escenario 1 y 3    │
│    'usuarios_combinados': 0,       # Solo escenario 2 y 3    │
│    'tipo_procesamiento': None      # Tipo de escenario       │
│  }                                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  tipo_procesamiento puede ser:                               │
│  • 'solo_docencia'  → Escenario 1                            │
│  • 'solo_usuarios'  → Escenario 2                            │
│  • 'mixto'          → Escenario 3                            │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 Leyenda

```
┌─────────┐
│ Proceso │  = Acción o proceso
└─────────┘

    │
    ▼        = Flujo de ejecución

┌──────┐
│ CASO │    = Punto de decisión
└──────┘

[FIN]        = Fin del proceso

✅           = Éxito
❌           = Error
📊           = Estadísticas
🔀           = Procesamiento paralelo/mixto
```

## 📝 Notas Importantes

1. **Independencia de Procesos:** En el escenario mixto, si falla el guardado de docencia, el sistema continúa con la combinación de usuarios.

2. **Orden de Procesamiento:** Siempre se procesan primero las tablas de docencia (historial) y luego las de usuarios (combinación).

3. **Estadísticas Consolidadas:** En el escenario mixto, las estadísticas finales incluyen información de ambos procesos.

4. **Compatibilidad:** Los escenarios 1 y 2 mantienen compatibilidad total con la funcionalidad existente.

---

**Versión:** 1.0
**Fecha:** 2024
