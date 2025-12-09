# 🔍 Diagnóstico: Por qué no se copian los campos

## 📋 Problema Reportado

Los campos como `nacionalidad`, `telefono`, `carnet`, etc. no se están copiando de las tablas archivadas a la tabla `accounts_registro` actual.

---

## 🔧 Mejoras Implementadas

### 1. **Función `copiar_todos_los_campos` Mejorada**

**ANTES:**
```python
# Usaba hasattr() que puede fallar con campos de Django
if hasattr(objeto_destino, campo_nombre):
    setattr(objeto_destino, campo_nombre, valor)
```

**AHORA:**
```python
# Obtiene los campos reales del modelo Django
campos_modelo = {f.name for f in objeto_destino._meta.get_fields()}

# Verifica si el campo existe en el modelo
if campo_nombre in campos_modelo:
    setattr(objeto_destino, campo_nombre, valor)
    logger.debug(f"✅ Campo copiado: {campo_nombre} = {valor}")
else:
    logger.debug(f"⚠️ Campo '{campo_nombre}' no existe en el modelo")
```

### 2. **Logging Detallado Agregado**

Ahora el sistema registra:
- ✅ Qué campos están disponibles en los datos archivados
- ✅ Qué campos se copiaron exitosamente
- ✅ Qué campos no existen en el modelo
- ✅ Los valores después de copiar

---

## 🧪 Cómo Diagnosticar el Problema

### Paso 1: Ejecutar la Combinación

1. Ve a **Datos Archivados** → **Ver Tablas Archivadas**
2. Haz clic en **"Combinar Datos"**
3. Espera a que termine el proceso

### Paso 2: Revisar los Logs

Los logs ahora mostrarán información detallada:

```
📝 Datos a copiar para usuario juan.perez:
   Campos disponibles: ['id', 'user_id', 'nacionalidad', 'carnet', 'sexo', 'address', 'location', 'telephone', 'movil', 'grado', 'ocupacion', 'titulo']

✅ Campo copiado: nacionalidad = Cubana
✅ Campo copiado: carnet = 12345678901
✅ Campo copiado: sexo = M
✅ Campo copiado: address = Calle 123
✅ Campo copiado: location = La Habana
✅ Campo copiado: telephone = 555-1234
✅ Campo copiado: movil = 555-5678
✅ Campo copiado: grado = grado3
✅ Campo copiado: ocupacion = ocupacion2
✅ Campo copiado: titulo = Bachiller

📊 Total campos copiados: 10

📊 Valores copiados al registro:
   nacionalidad: Cubana
   carnet: 12345678901
   telephone: 555-1234
   address: Calle 123

✅ Registro creado para usuario juan.perez (10 campos copiados)
```

### Paso 3: Verificar en la Base de Datos

```sql
-- Ver los datos copiados
SELECT 
    u.username,
    r.nacionalidad,
    r.carnet,
    r.telephone,
    r.address,
    r.location,
    r.provincia
FROM auth_user u
LEFT JOIN accounts_registro r ON u.id = r.user_id
WHERE u.username = 'juan.perez';
```

---

## 🔍 Posibles Causas del Problema

### Causa 1: Nombres de Campos No Coinciden

**Problema:**
```
Tabla archivada: Docencia_studentpersonalinformation
- Campo: "telefono"

Tabla actual: accounts_registro
- Campo: "telephone"
```

**Solución:**
Los nombres deben coincidir exactamente. Si en la tabla archivada el campo se llama `telefono` pero en el modelo actual se llama `telephone`, no se copiará.

**Verificar:**
```python
# En los logs, busca:
⚠️ Campo 'telefono' no existe en el modelo Registro
```

### Causa 2: Campos con Valores NULL o Vacíos

**Problema:**
```
Tabla archivada:
- nacionalidad: null
- carnet: ""
- telephone: null
```

**Solución:**
Los campos con valores `null` o vacíos se copian, pero aparecerán vacíos en la tabla destino.

**Verificar:**
```python
# En los logs, busca:
✅ Campo copiado: nacionalidad = None
✅ Campo copiado: carnet = 
```

### Causa 3: user_id No Coincide

**Problema:**
```
Tabla archivada:
- user_id: 5

Pero el usuario con id=5 no se migró o no existe
```

**Solución:**
El sistema debe primero migrar `auth_user` y luego los registros.

**Verificar:**
```python
# En los logs, busca:
⚠️ No se encontró usuario para registro 123
```

### Causa 4: Tabla Archivada Vacía

**Problema:**
```
No hay datos en Docencia_studentpersonalinformation
```

**Solución:**
Verificar que la tabla archivada tenga datos.

**Verificar:**
```sql
SELECT COUNT(*) 
FROM datos_archivados_datoarchivadinamico 
WHERE tabla_origen = 'Docencia_studentpersonalinformation';
```

---

## 📊 Tabla de Mapeo de Campos

### Campos del Modelo `Registro` (accounts_registro):

| Campo en Modelo | Tipo | Descripción |
|----------------|------|-------------|
| `user` | ForeignKey | Usuario (relación) |
| `nacionalidad` | CharField(150) | Nacionalidad |
| `carnet` | CharField(11) | Número de carnet |
| `foto_carnet` | ImageField | Foto del carnet |
| `sexo` | CharField(1) | Sexo (M/F) |
| `image` | ImageField | Imagen de perfil |
| `address` | CharField(150) | Dirección |
| `location` | CharField(150) | Municipio |
| `provincia` | CharField(150) | Provincia |
| `telephone` | CharField(50) | Teléfono |
| `movil` | CharField(50) | Móvil |
| `grado` | CharField(50) | Grado académico |
| `ocupacion` | CharField(100) | Ocupación |
| `titulo` | CharField(150) | Título |
| `foto_titulo` | ImageField | Foto del título |

### Campos que DEBEN existir en la tabla archivada:

Para que se copien correctamente, los campos en `Docencia_studentpersonalinformation` deben llamarse **exactamente igual**:

- ✅ `nacionalidad` (no `Nacionalidad` ni `nacionality`)
- ✅ `carnet` (no `Carnet` ni `ci`)
- ✅ `telephone` (no `telefono` ni `phone`)
- ✅ `address` (no `direccion` ni `addr`)
- ✅ `location` (no `municipio` ni `ciudad`)
- ✅ `provincia` (no `Provincia` ni `state`)

---

## 🔧 Comandos de Verificación

### 1. Ver campos disponibles en tabla archivada:

```sql
SELECT datos_originales 
FROM datos_archivados_datoarchivadinamico 
WHERE tabla_origen = 'Docencia_studentpersonalinformation' 
LIMIT 1;
```

### 2. Ver si los datos se copiaron:

```sql
SELECT 
    u.username,
    r.nacionalidad,
    r.carnet,
    r.telephone,
    r.address
FROM auth_user u
LEFT JOIN accounts_registro r ON u.id = r.user_id
ORDER BY u.id DESC
LIMIT 10;
```

### 3. Contar registros con datos:

```sql
SELECT 
    COUNT(*) as total,
    COUNT(nacionalidad) as con_nacionalidad,
    COUNT(carnet) as con_carnet,
    COUNT(telephone) as con_telephone
FROM accounts_registro;
```

---

## ✅ Solución Paso a Paso

### Si los campos NO se están copiando:

1. **Ejecuta la combinación de nuevo** con el logging mejorado
2. **Revisa los logs** para ver:
   - ¿Qué campos están disponibles?
   - ¿Qué campos se copiaron?
   - ¿Hay errores?
3. **Verifica los nombres de campos** en la tabla archivada
4. **Verifica que los datos existan** en la tabla archivada
5. **Verifica que los usuarios se hayan migrado** primero

### Si los nombres de campos no coinciden:

**✅ SOLUCIÓN AUTOMÁTICA IMPLEMENTADA:**

El sistema ahora **crea automáticamente** los campos que no existen:

```python
# Si el campo 'telefono' no existe en el modelo:
# 1. Detecta que no existe
# 2. Ejecuta: ALTER TABLE accounts_registro ADD COLUMN "telefono" TEXT NULL
# 3. Copia el valor
# 4. ✅ Campo creado y copiado automáticamente
```

**Ejemplo de logs:**
```
⚠️ Campo 'telefono' no existe en Registro, creando...
✅ Campo CREADO: accounts_registro.telefono (TEXT NULL)
✅ Campo copiado: telefono = 555-1234
🆕 Campos CREADOS automáticamente: telefono, direccion_completa, fecha_nacimiento
```

**Ya NO necesitas:**
- ❌ Crear mapeo manual
- ❌ Renombrar columnas
- ❌ Modificar modelos Django

**El sistema lo hace TODO automáticamente** ✅

---

## 📞 Próximos Pasos

1. **Ejecuta la combinación** con el nuevo código
2. **Copia los logs** que aparecen en la consola
3. **Comparte los logs** para identificar el problema exacto
4. **Verifica la base de datos** con las consultas SQL

El nuevo logging te dirá exactamente qué está pasando con cada campo.

---

**Última actualización:** Noviembre 2024  
**Versión:** 4.0 - Diagnóstico mejorado
