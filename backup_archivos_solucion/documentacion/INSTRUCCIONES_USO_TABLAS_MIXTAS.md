# 📖 Instrucciones de Uso: Manejo Inteligente de Tablas Mixtas

## 🎯 Descripción General

El sistema ahora puede manejar inteligentemente tres tipos de selecciones de tablas en el modal "Seleccionar y Combinar Tablas Específicas":

1. **Solo tablas de docencia** → Se guardan en historial
2. **Solo tablas de usuarios** → Se combinan normalmente
3. **Tablas mixtas** → Se procesan ambos grupos independientemente

## 🚀 Cómo Usar

### Paso 1: Acceder al Modal
1. Ir a la sección de "Datos Archivados"
2. Hacer clic en "Seleccionar y Combinar Tablas Específicas"

### Paso 2: Seleccionar Tablas
Puedes seleccionar cualquier combinación de tablas:

#### Opción A: Solo Tablas de Docencia
Selecciona una o más de estas 11 tablas:
- ✅ Docencia_area
- ✅ Docencia_coursecategory
- ✅ Docencia_courseinformation_adminteachers
- ✅ Docencia_courseinformation
- ✅ Docencia_enrollmentapplication
- ✅ Docencia_enrollmentpay
- ✅ Docencia_accountnumber
- ✅ Docencia_enrollment
- ✅ Docencia_subjectinformation
- ✅ Docencia_edition
- ✅ Docencia_application

**Resultado:** Los datos se guardarán en los modelos históricos de la app `historial`.

#### Opción B: Solo Tablas de Usuarios
Selecciona una o más de estas tablas:
- ✅ auth_user
- ✅ auth_group
- ✅ auth_user_groups
- ✅ accounts_registro
- ✅ Docencia_teacherpersonalinformation
- ✅ Docencia_studentpersonalinformation

**Resultado:** Los datos se combinarán usando el proceso normal de combinación de usuarios.

#### Opción C: Tablas Mixtas (Docencia + Usuarios)
Selecciona tablas de ambos grupos, por ejemplo:
- ✅ Docencia_area
- ✅ Docencia_enrollment
- ✅ auth_user
- ✅ auth_group
- ✅ accounts_registro

**Resultado:** 
1. Las tablas de docencia se guardarán en historial
2. Las tablas de usuarios se combinarán normalmente
3. Recibirás estadísticas de ambos procesos

### Paso 3: Confirmar y Ejecutar
1. Hacer clic en "Combinar Tablas Seleccionadas"
2. El sistema detectará automáticamente el tipo de selección
3. Procesará las tablas según corresponda

## 📊 Interpretando los Resultados

### Escenario 1: Solo Docencia
```
======================================================================
✅ GUARDADO EN HISTORIAL COMPLETADO EXITOSAMENTE
======================================================================
Total de registros guardados: 150
```

### Escenario 2: Solo Usuarios
```
======================================================================
✅ COMBINACIÓN SELECTIVA COMPLETADA EXITOSAMENTE
======================================================================
Tipo de procesamiento: solo_usuarios
👥 Usuarios combinados: 25
📝 Registros combinados: 25
```

### Escenario 3: Tablas Mixtas
```
======================================================================
📊 RESUMEN DE PROCESAMIENTO MIXTO
======================================================================
Tablas de docencia guardadas en historial: 150 registros
Tablas de usuarios combinadas: 25 usuarios

======================================================================
✅ COMBINACIÓN SELECTIVA COMPLETADA EXITOSAMENTE
======================================================================
Tipo de procesamiento: mixto
📚 Registros de docencia guardados en historial: 150
👥 Usuarios combinados: 25
📝 Registros combinados: 25
```

## 🔍 Verificando los Resultados

### Para Tablas de Docencia (Historial)
1. Ir a la app `historial` en el admin de Django
2. Buscar los modelos históricos correspondientes:
   - HistoricalArea
   - HistoricalCourseCategory
   - HistoricalCourseInformation
   - etc.
3. Verificar que los registros se hayan guardado

### Para Tablas de Usuarios (Combinación)
1. Ir a la sección de Usuarios en el admin
2. Verificar que los usuarios se hayan combinado
3. Revisar los grupos y registros asociados

## ⚠️ Consideraciones Importantes

### 1. Orden de Procesamiento
En el escenario mixto:
- **Primero** se guardan las tablas de docencia en historial
- **Después** se combinan las tablas de usuarios
- Si falla el guardado de docencia, el sistema continúa con usuarios

### 2. Dependencias
El sistema maneja automáticamente las dependencias:
- Si seleccionas tablas que dependen de usuarios, el sistema agregará `auth_user` automáticamente
- Si seleccionas `auth_user_groups`, el sistema agregará `auth_group` automáticamente

### 3. Logs Detallados
Revisa los logs de Django para ver el progreso detallado:
```bash
tail -f logs/django.log
```

## 🐛 Solución de Problemas

### Problema: No se guardan las tablas de docencia
**Solución:** Verificar que los modelos históricos existan en la app `historial`

### Problema: No se combinan los usuarios
**Solución:** Verificar que las tablas de usuarios existan en los datos archivados

### Problema: Error en escenario mixto
**Solución:** 
1. Revisar los logs de Django
2. Verificar que ambos procesos (historial y combinación) funcionen independientemente
3. Si falla uno, el otro debería continuar

## 📝 Ejemplos de Uso Común

### Ejemplo 1: Migrar Solo Cursos
```
Seleccionar:
- Docencia_area
- Docencia_coursecategory
- Docencia_courseinformation

Resultado: Se guardan en historial
```

### Ejemplo 2: Migrar Solo Usuarios
```
Seleccionar:
- auth_user
- auth_group
- accounts_registro

Resultado: Se combinan normalmente
```

### Ejemplo 3: Migración Completa
```
Seleccionar:
- Todas las 11 tablas de docencia
- auth_user
- auth_group
- accounts_registro

Resultado: 
- Docencia → historial
- Usuarios → combinación
```

## 🎓 Mejores Prácticas

1. **Prueba Primero con Pocas Tablas:** Empieza con 1-2 tablas para verificar que funcione
2. **Revisa los Logs:** Siempre revisa los logs para entender qué está pasando
3. **Verifica los Resultados:** Después de cada operación, verifica que los datos estén donde esperas
4. **Backup:** Siempre ten un backup antes de hacer operaciones masivas

## 📞 Soporte

Si tienes problemas o preguntas:
1. Revisa los logs de Django
2. Consulta `IMPLEMENTACION_TABLAS_MIXTAS.md` para detalles técnicos
3. Ejecuta `test_separacion_tablas.py` para verificar la lógica

---

**Última Actualización:** 2024
**Versión:** 1.0
