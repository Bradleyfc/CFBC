# 🔐 Manejo Inteligente de Contraseñas

## ✅ Cambios Implementados

### 1. **Eliminación de Sufijos Numéricos**

**ANTES:**
```python
# Si el usuario "juan.perez" ya existía, se creaba:
# - juan.perez0
# - juan.perez1
# - juan.perez2
# etc.
```

**AHORA:**
```python
# Si el usuario "juan.perez" ya existe:
# - Se ACTUALIZA el usuario existente
# - Se mapea para mantener relaciones
# - NO se crean usuarios duplicados
```

### 2. **Soporte para Contraseñas en Texto Plano**

**ANTES:**
- Solo se copiaban contraseñas hasheadas
- Contraseñas en texto plano causaban problemas

**AHORA:**
- ✅ Detecta automáticamente el formato de la contraseña
- ✅ Hashea contraseñas en texto plano antes de guardar
- ✅ Copia directamente contraseñas ya hasheadas

---

## 🔍 Detección Automática de Formato

### Algoritmo de Detección:

```python
password_original = datos.get('password')

# Verificar si está hasheada
if password_original.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2$', 'sha1$', 'md5$')):
    # Ya está hasheada → Copiar directamente
    usuario.password = password_original
else:
    # Está en texto plano → Hashear
    usuario.set_password(password_original)
```

### Formatos Soportados:

| Formato | Prefijo | Acción | Ejemplo |
|---------|---------|--------|---------|
| PBKDF2 SHA256 | `pbkdf2_sha256$` | Copia directa | `pbkdf2_sha256$260000$abc...` |
| BCrypt | `bcrypt$` | Copia directa | `bcrypt$2b$12$xyz...` |
| Argon2 | `argon2$` | Copia directa | `argon2$argon2id$v=19$m=...` |
| SHA1 | `sha1$` | Copia directa | `sha1$salt$hash...` |
| MD5 | `md5$` | Copia directa | `md5$salt$hash...` |
| Texto plano | (ninguno) | Hashea con `set_password()` | `mipassword123` |

---

## 📊 Flujo de Procesamiento

### Caso 1: Contraseña Hasheada

```
Tabla archivada:
password: "pbkdf2_sha256$260000$abc123..."
    ↓
Detección: Empieza con "pbkdf2_sha256$"
    ↓
Acción: Copia directa
    ↓
usuario.password = "pbkdf2_sha256$260000$abc123..."
    ↓
usuario.save()
    ↓
✅ Usuario puede hacer login con su contraseña original
```

### Caso 2: Contraseña en Texto Plano

```
Tabla archivada:
password: "mipassword123"
    ↓
Detección: NO empieza con prefijo conocido
    ↓
Acción: Hashear con set_password()
    ↓
usuario.set_password("mipassword123")
    ↓
usuario.password = "pbkdf2_sha256$260000$xyz789..." (hasheada)
    ↓
usuario.save()
    ↓
✅ Usuario puede hacer login con "mipassword123"
```

### Caso 3: Sin Contraseña

```
Tabla archivada:
password: null o ""
    ↓
Detección: No hay contraseña
    ↓
Acción: Establecer contraseña no utilizable
    ↓
usuario.set_unusable_password()
    ↓
usuario.save()
    ↓
❌ Usuario NO puede hacer login (necesita resetear contraseña)
```

---

## 🎯 Manejo de Usuarios Duplicados

### Escenario: Usuario ya existe

```python
# Usuario en tabla archivada:
username: "juan.perez"
password: "mipassword123"

# Usuario ya existe en base de datos actual:
username: "juan.perez"
password: "pbkdf2_sha256$old_hash..."

# ACCIÓN:
# 1. Detectar que ya existe
usuario_existente = User.objects.filter(username="juan.perez").first()

# 2. ACTUALIZAR (no crear duplicado)
usuario_existente.password = nueva_password_procesada
usuario_existente.save()

# 3. Mapear para relaciones
mapeo_usuarios[id_original] = usuario_existente

# RESULTADO:
# ✅ Usuario actualizado con nueva contraseña
# ✅ NO se crea "juan.perez0"
# ✅ Relaciones se mantienen correctamente
```

---

## 🧪 Ejemplos de Prueba

### Ejemplo 1: Contraseña Hasheada

**Datos archivados:**
```json
{
  "username": "maria.lopez",
  "password": "pbkdf2_sha256$260000$abc123def456...",
  "email": "maria@example.com"
}
```

**Resultado:**
```python
# Usuario creado/actualizado
username: "maria.lopez"
password: "pbkdf2_sha256$260000$abc123def456..." (copiada directamente)

# Login:
username: "maria.lopez"
password: [su contraseña original] ✅ FUNCIONA
```

### Ejemplo 2: Contraseña en Texto Plano

**Datos archivados:**
```json
{
  "username": "carlos.ruiz",
  "password": "carlos2024",
  "email": "carlos@example.com"
}
```

**Resultado:**
```python
# Usuario creado/actualizado
username: "carlos.ruiz"
password: "pbkdf2_sha256$260000$xyz789..." (hasheada automáticamente)

# Login:
username: "carlos.ruiz"
password: "carlos2024" ✅ FUNCIONA
```

### Ejemplo 3: Usuario Duplicado

**Datos archivados:**
```json
{
  "username": "admin",
  "password": "newpassword123",
  "email": "admin@example.com"
}
```

**Usuario actual existente:**
```python
username: "admin"
password: "pbkdf2_sha256$old_hash..."
```

**Resultado:**
```python
# Usuario ACTUALIZADO (no duplicado)
username: "admin" (mismo)
password: "pbkdf2_sha256$new_hash..." (actualizada)

# Login:
username: "admin"
password: "newpassword123" ✅ FUNCIONA con nueva contraseña
```

---

## 🔒 Seguridad

### Ventajas del Nuevo Sistema:

1. **Contraseñas Siempre Seguras:**
   - Texto plano se hashea automáticamente
   - Nunca se guardan contraseñas sin hashear
   - Usa el algoritmo de Django (PBKDF2 SHA256 por defecto)

2. **No Hay Duplicados:**
   - Usuarios existentes se actualizan
   - No se crean usernames con sufijos
   - Mantiene integridad de datos

3. **Compatibilidad Total:**
   - Funciona con cualquier formato de hash
   - Funciona con texto plano
   - Funciona con contraseñas vacías

4. **Logging Completo:**
   - Registra si la contraseña estaba hasheada
   - Registra si se hasheó texto plano
   - Registra si no había contraseña

---

## 📝 Logs de Ejemplo

### Contraseña Hasheada:
```
✅ Contraseña hasheada copiada para usuario: juan.perez
✅ Usuario creado: juan.perez (15 campos copiados)
```

### Contraseña en Texto Plano:
```
✅ Contraseña en texto plano hasheada para usuario: maria.lopez
✅ Usuario creado: maria.lopez (15 campos copiados)
```

### Usuario Duplicado:
```
⚠️ Usuario admin ya existe, buscando para actualizar...
✅ Usuario duplicado encontrado y mapeado: admin
✅ Usuario actualizado: admin (15 campos copiados)
```

### Sin Contraseña:
```
⚠️ No se encontró contraseña para usuario: invitado
✅ Usuario creado: invitado (14 campos copiados)
```

---

## ✅ Verificación

### Para verificar que funciona:

1. **Ejecutar combinación:**
   ```
   Ir a: Datos Archivados → Ver Tablas Archivadas
   Clic en: "Combinar Datos"
   Esperar: Proceso complete
   ```

2. **Revisar logs:**
   ```python
   # Buscar en logs:
   "Contraseña hasheada copiada"
   "Contraseña en texto plano hasheada"
   "Usuario duplicado encontrado"
   ```

3. **Probar login:**
   ```
   Username: [usuario de tabla archivada]
   Password: [contraseña original]
   Resultado: ✅ Debe funcionar
   ```

4. **Verificar en base de datos:**
   ```sql
   SELECT username, password 
   FROM auth_user 
   WHERE username = 'juan.perez';
   
   -- password debe empezar con "pbkdf2_sha256$" o similar
   ```

---

## 🎯 Resumen de Cambios

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| Usuarios duplicados | Se creaban con sufijos (0, 1, 2) | Se actualizan, no se duplican |
| Contraseñas hasheadas | Se copiaban | Se copian (igual) |
| Contraseñas texto plano | Causaban problemas | Se hashean automáticamente |
| Sin contraseña | Error | Contraseña no utilizable |
| Logging | Básico | Detallado con tipo de contraseña |

---

**Última actualización:** Noviembre 2024  
**Versión:** 3.0 - Manejo inteligente de contraseñas
