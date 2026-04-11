# 📖 Cómo Usar la Verificación de Tablas Mixtas

Este documento explica cómo usar los scripts de verificación y prueba de la funcionalidad de tablas mixtas.

---

## 🚀 Verificación Rápida

Para verificar rápidamente que todo está funcionando correctamente:

```bash
bash verificar_implementacion.sh
```

Este script verifica:
- ✅ Existencia de archivos necesarios
- ✅ Implementación de los 3 escenarios
- ✅ Funciones auxiliares
- ✅ Sintaxis de Python
- ✅ Validación de Django
- ✅ Ejecución de pruebas

**Resultado esperado:**
```
✅ VERIFICACIÓN COMPLETADA: TODO OK
La implementación está correcta y funcional
```

---

## 🧪 Pruebas Detalladas

Para ejecutar las pruebas detalladas con output completo:

```bash
python test_tablas_mixtas_completo.py
```

Este script ejecuta **7 pruebas** que cubren:
1. Solo tablas de docencia
2. Solo tablas de usuarios
3. Tablas mixtas (varios casos)

**Resultado esperado:**
```
✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE
✅ La lógica de separación de tablas funciona correctamente
✅ Los 3 escenarios se detectan y procesan adecuadamente
```

---

## 🔍 Verificaciones Individuales

### 1. Verificar Sintaxis de Python

```bash
# Verificar views.py
python -m py_compile datos_archivados/views.py

# Verificar historical_data_saver.py
python -m py_compile datos_archivados/historical_data_saver.py
```

**Sin output = Sin errores** ✅

---

### 2. Verificar Django

```bash
python manage.py check
```

**Resultado esperado:**
```
System check identified no issues (0 silenced).
```

---

### 3. Verificar Implementación de Escenarios

```bash
# Verificar que los 3 escenarios están en el código
grep "ESCENARIO" datos_archivados/views.py
```

**Resultado esperado:**
```
# ESCENARIO 1: SOLO TABLAS DE DOCENCIA
# ESCENARIO 2: SOLO TABLAS DE USUARIOS
# ESCENARIO 3: TABLAS MIXTAS (DOCENCIA + USUARIOS)
```

---

### 4. Verificar Funciones Auxiliares

```bash
# Verificar funciones en historical_data_saver.py
grep "^def " datos_archivados/historical_data_saver.py
```

**Debe incluir:**
- `def es_tabla_docencia(...)`
- `def son_todas_tablas_docencia(...)`
- `def guardar_datos_docencia_en_historial(...)`

---

## 📊 Entender los Resultados de las Pruebas

Cada prueba muestra:

```
TEST: [Nombre del test]
ℹ️  Tablas seleccionadas: [lista de tablas]
📊 Análisis de separación:
  • Tablas de docencia: X
  • Tablas de usuarios: Y
🎯 [ESCENARIO DETECTADO]
📋 Acción: [Acción a realizar]
✅ Validación correcta: [Confirmación]
```

---

## 🎯 Los 3 Escenarios Explicados

### ESCENARIO 1: Solo Tablas de Docencia

**Cuándo se activa:**
- Todas las tablas seleccionadas son de docencia
- Ejemplos: `Docencia_area`, `Docencia_enrollment`, etc.

**Qué hace:**
- Guarda los datos en modelos históricos de la app `historial`
- NO ejecuta el proceso de combinación
- Retorna inmediatamente después de guardar

**Ejemplo de uso:**
```python
tablas = ['Docencia_area', 'Docencia_enrollment']
# → Se activa ESCENARIO 1
```

---

### ESCENARIO 2: Solo Tablas de Usuarios

**Cuándo se activa:**
- Todas las tablas seleccionadas son de usuarios (Django auth, accounts, etc.)
- Ejemplos: `auth_user`, `auth_group`, `accounts_registro`

**Qué hace:**
- Usa el proceso de combinación existente
- NO intenta guardar en historial

**Ejemplo de uso:**
```python
tablas = ['auth_user', 'auth_group', 'accounts_registro']
# → Se activa ESCENARIO 2
```

---

### ESCENARIO 3: Tablas Mixtas

**Cuándo se activa:**
- Hay tablas de docencia Y tablas de usuarios mezcladas

**Qué hace:**
1. **PASO 1:** Guarda tablas de docencia en historial
2. **PASO 2:** Procesa tablas de usuarios con combinación

**Ejemplo de uso:**
```python
tablas = ['Docencia_area', 'auth_user', 'Docencia_enrollment', 'auth_group']
# → Se activa ESCENARIO 3
# → Docencia_area y Docencia_enrollment → historial
# → auth_user y auth_group → combinación
```

---

## 📚 Tablas de Docencia Reconocidas

El sistema reconoce estas **11 tablas** como tablas de docencia:

1. `Docencia_area`
2. `Docencia_coursecategory`
3. `Docencia_courseinformation_adminteachers`
4. `Docencia_courseinformation`
5. `Docencia_enrollmentapplication`
6. `Docencia_enrollmentpay`
7. `Docencia_accountnumber`
8. `Docencia_enrollment`
9. `Docencia_subjectinformation`
10. `Docencia_edition`
11. `Docencia_application`

**Cualquier otra tabla** se considera tabla de usuarios.

---

## 🔧 Solución de Problemas

### Problema: "ModuleNotFoundError: No module named 'cfbc'"

**Solución:**
```bash
# Asegúrate de estar en el directorio correcto
cd /home/bradley/CFBC

# Asegúrate de tener el entorno virtual activado
source venv/bin/activate
```

---

### Problema: "No such file or directory: views.py"

**Solución:**
```bash
# Verifica que estás en el directorio raíz del proyecto
pwd
# Debe mostrar: /home/bradley/CFBC

# Verifica que el archivo existe
ls -la datos_archivados/views.py
```

---

### Problema: Las pruebas fallan

**Solución:**
```bash
# Ejecuta las pruebas con más detalle para ver el error
python test_tablas_mixtas_completo.py

# Si hay un error específico, revisa:
# 1. Que Django esté configurado correctamente
# 2. Que el archivo historical_data_saver.py exista
# 3. Que las funciones estén importadas correctamente
```

---

## 📝 Archivos de Documentación

Después de la verificación, encontrarás estos archivos:

1. **`VERIFICACION_TABLAS_MIXTAS.md`**
   - Documentación detallada de la verificación
   - Resultados de todas las pruebas
   - Explicación de cada escenario

2. **`RESUMEN_VERIFICACION_FINAL.md`**
   - Resumen ejecutivo de la verificación
   - Estadísticas y conclusiones
   - Estado final del proyecto

3. **`COMO_USAR_VERIFICACION.md`** (este archivo)
   - Instrucciones de uso
   - Guía de solución de problemas
   - Explicación de los escenarios

4. **`test_tablas_mixtas_completo.py`**
   - Script de pruebas automatizadas
   - 7 casos de prueba

5. **`verificar_implementacion.sh`**
   - Script de verificación rápida
   - Verifica todos los aspectos de la implementación

---

## ✅ Checklist de Verificación Manual

Si prefieres verificar manualmente, usa este checklist:

- [ ] El archivo `datos_archivados/views.py` existe
- [ ] El archivo `datos_archivados/historical_data_saver.py` existe
- [ ] Los 3 escenarios están implementados en `views.py`
- [ ] La función `es_tabla_docencia()` existe
- [ ] La función `guardar_datos_docencia_en_historial()` existe
- [ ] No hay errores de sintaxis en `views.py`
- [ ] No hay errores de sintaxis en `historical_data_saver.py`
- [ ] `python manage.py check` no reporta errores
- [ ] Las pruebas pasan correctamente

---

## 🎉 Conclusión

Si todos los scripts se ejecutan sin errores, la implementación está **completamente funcional** y lista para usar en producción.

Para cualquier duda, revisa los archivos de documentación generados o ejecuta las pruebas para ver ejemplos concretos de cómo funciona cada escenario.

---

**Última actualización:** 1 de marzo de 2024
