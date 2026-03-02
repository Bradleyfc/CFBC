# Implementación de Manejo Inteligente de Tablas Mixtas

## 📋 Resumen

Se ha implementado la funcionalidad para que el sistema maneje inteligentemente diferentes tipos de tablas cuando se seleccionan en el modal "Seleccionar y Combinar Tablas Específicas".

## 🎯 Escenarios Implementados

### Escenario 1: Solo Tablas de Docencia (las 11)
**Acción:** Guardar en modelos históricos de la app `historial`

Cuando se seleccionan únicamente tablas de docencia, el sistema:
- Detecta automáticamente que todas son tablas de docencia
- Guarda los datos en los modelos históricos correspondientes
- No ejecuta el proceso de combinación de usuarios
- Retorna estadísticas específicas del guardado en historial

**Tablas de docencia:**
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

### Escenario 2: Solo Tablas de Usuarios
**Acción:** Usar el proceso de combinación existente para usuarios de Django

Cuando se seleccionan únicamente tablas de usuarios (auth_user, auth_group, etc.):
- Ejecuta el proceso de combinación normal
- Combina usuarios, grupos, registros, etc.
- Mantiene toda la funcionalidad existente

**Tablas de usuarios comunes:**
- `auth_user`
- `auth_group`
- `auth_user_groups`
- `accounts_registro`
- `Docencia_teacherpersonalinformation`
- `Docencia_studentpersonalinformation`

### Escenario 3: Tablas Mixtas (Docencia + Usuarios) ⭐ NUEVO
**Acción:** Procesar ambos grupos de forma independiente

Cuando se seleccionan tablas de ambos tipos:

#### Paso 1: Guardar Tablas de Docencia
- Separa las tablas de docencia del conjunto seleccionado
- Las guarda en los modelos históricos de la app `historial`
- Registra estadísticas del guardado

#### Paso 2: Combinar Tablas de Usuarios
- Separa las tablas de usuarios del conjunto seleccionado
- Ejecuta el proceso de combinación normal para estas tablas
- Registra estadísticas de la combinación

#### Resultado Final
- Retorna estadísticas combinadas de ambos procesos
- Muestra un resumen detallado con:
  - Registros de docencia guardados en historial
  - Usuarios combinados
  - Registros combinados
  - Cursos académicos combinados
  - Cursos combinados

## 🔧 Cambios Técnicos Implementados

### 1. Separación de Tablas
```python
# Separar tablas en dos grupos
tablas_docencia = [tabla for tabla in tablas_seleccionadas if es_tabla_docencia(tabla)]
tablas_usuarios = [tabla for tabla in tablas_seleccionadas if not es_tabla_docencia(tabla)]
```

### 2. Detección de Escenarios
```python
if tablas_docencia and not tablas_usuarios:
    # ESCENARIO 1: Solo docencia
elif tablas_usuarios and not tablas_docencia:
    # ESCENARIO 2: Solo usuarios
elif tablas_docencia and tablas_usuarios:
    # ESCENARIO 3: Mixto
```

### 3. Estadísticas Combinadas
```python
estadisticas_totales = {
    'docencia_guardadas': 0,
    'usuarios_combinados': 0,
    'tipo_procesamiento': None  # 'solo_docencia', 'solo_usuarios', 'mixto'
}
```

### 4. Logs Mejorados
El sistema ahora muestra logs detallados con:
- Análisis de tablas seleccionadas
- Separación por tipo (docencia vs usuarios)
- Progreso de cada fase en el escenario mixto
- Resumen final con estadísticas consolidadas

## 📊 Ejemplo de Logs

```
======================================================================
📊 ANÁLISIS DE TABLAS SELECCIONADAS
======================================================================
Total de tablas seleccionadas: 5
Tablas de docencia (→ historial): 2
Tablas de usuarios (→ combinación): 3

📚 Tablas de docencia detectadas:
  • Docencia_area
  • Docencia_coursecategory

👥 Tablas de usuarios detectadas:
  • auth_user
  • auth_group
  • accounts_registro
======================================================================

🔀 ESCENARIO 3: Tablas mixtas (docencia + usuarios)
Acción: Procesar ambos grupos de forma independiente

----------------------------------------------------------------------
PASO 1/2: Guardando tablas de docencia en historial...
----------------------------------------------------------------------
✅ Tablas de docencia guardadas: 150 registros

----------------------------------------------------------------------
PASO 2/2: Procesando tablas de usuarios con combinación...
----------------------------------------------------------------------
Tablas de usuarios a combinar: ['auth_user', 'auth_group', 'accounts_registro']

======================================================================
📊 RESUMEN DE PROCESAMIENTO MIXTO
======================================================================
Tablas de docencia guardadas en historial: 150 registros
Tablas de usuarios combinadas: 25 usuarios
```

## ✅ Compatibilidad

- ✅ Mantiene compatibilidad total con funcionalidad existente
- ✅ No afecta el proceso de combinación normal
- ✅ No requiere cambios en la interfaz de usuario
- ✅ Funciona con el sistema de progreso en tiempo real existente
- ✅ Compatible con el sistema de interrupción de combinación

## 🧪 Pruebas Recomendadas

1. **Prueba Escenario 1:** Seleccionar solo tablas de docencia
   - Verificar que se guarden en historial
   - Verificar que no se ejecute combinación

2. **Prueba Escenario 2:** Seleccionar solo tablas de usuarios
   - Verificar que se ejecute combinación normal
   - Verificar estadísticas de usuarios combinados

3. **Prueba Escenario 3:** Seleccionar tablas mixtas
   - Verificar que se procesen ambos grupos
   - Verificar estadísticas combinadas
   - Verificar logs detallados

## 📝 Notas Adicionales

- El sistema usa la función `es_tabla_docencia()` de `historical_data_saver.py` para detectar tablas de docencia
- En el escenario mixto, si falla el guardado de docencia, el sistema continúa con la combinación de usuarios
- Las estadísticas finales incluyen información de ambos procesos en el escenario mixto
- El tipo de procesamiento se registra en el cache para referencia futura

## 🔗 Archivos Modificados

- `datos_archivados/views.py` - Función `combinar_datos_seleccionadas()`
  - Líneas ~3765-3890: Separación de tablas y detección de escenarios
  - Líneas ~4915-4945: Consolidación de estadísticas finales

## 👨‍💻 Autor

Implementado según especificaciones del usuario para manejo inteligente de tablas mixtas.
