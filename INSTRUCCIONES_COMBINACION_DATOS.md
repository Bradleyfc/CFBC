# 📋 Instrucciones para Combinar Datos Archivados

## ✅ ¿Qué hace la función "Combinar Datos"?

Esta función combina **TODA LA INFORMACIÓN** de las tablas archivadas con las tablas activas de tu base de datos PostgreSQL, permitiendo que los usuarios y datos archivados estén disponibles en tu proyecto actual.

### 🌟 Características Principales:

1. **Copia TODOS los campos** de cada registro automáticamente
2. **Crea campos faltantes** dinámicamente si no existen en las tablas actuales
3. **Preserva contraseñas hasheadas** para que los usuarios puedan iniciar sesión
4. **Mantiene relaciones** entre tablas (usuarios, cursos, matrículas, etc.)
5. **Proceso seguro** con transacciones atómicas

---

## 🔧 Creación Automática de Campos

### ✨ Detección y Creación Dinámica

**El sistema detecta automáticamente campos que no existen en tus tablas actuales y los crea.**

#### Cómo funciona:

1. **Análisis**: El sistema analiza los datos archivados y detecta todos los campos
2. **Comparación**: Compara con los campos existentes en las tablas actuales
3. **Creación**: Ejecuta `ALTER TABLE` para agregar campos faltantes
4. **Tipo de dato**: Determina automáticamente el tipo de dato basándose en el valor:
   - `BOOLEAN` para valores true/false
   - `INTEGER` para números enteros
   - `DOUBLE PRECISION` para números decimales
   - `TIMESTAMP` para fechas
   - `TEXT` para texto (por defecto)

#### Ejemplo:

```
Tabla archivada tiene:
- username
- email
- telefono_celular  ← Este campo no existe en tu tabla actual
- direccion_completa ← Este campo tampoco existe

El sistema automáticamente:
✅ Ejecuta: ALTER TABLE auth_user ADD COLUMN telefono_celular TEXT NULL
✅ Ejecuta: ALTER TABLE auth_user ADD COLUMN direccion_completa TEXT NULL
✅ Copia los valores de estos campos
```

### 🎯 Ventajas:

- ✅ No pierdes información
- ✅ No necesitas modificar manualmente los modelos
- ✅ Los campos se agregan de forma segura
- ✅ Puedes acceder a los nuevos campos inmediatamente

---

## 🔐 Manejo de Contraseñas

### ✨ Característica Principal: Contraseñas Preservadas

**Las contraseñas se copian y procesan automáticamente desde la base de datos archivada.**

Esto significa que:
- ✅ Los usuarios podrán iniciar sesión con sus **contraseñas originales**
- ✅ No necesitas resetear contraseñas
- ✅ No necesitas notificar a los usuarios sobre cambios de contraseña
- ✅ La seguridad se mantiene (las contraseñas se hashean si es necesario)

### 🔍 Cómo funciona:

1. El sistema lee el campo `password` de la tabla `auth_user` archivada
2. **Detecta automáticamente** si la contraseña está hasheada o en texto plano:
   - **Si está hasheada** (ej: `pbkdf2_sha256$...`): Se copia directamente
   - **Si está en texto plano** (ej: `mipassword123`): Se hashea automáticamente con `set_password()`
3. Se guarda en el nuevo usuario en la base de datos actual
4. Django reconoce automáticamente el formato y permite el login

### 🔐 Soporte para Contraseñas:

| Formato | Acción | Resultado |
|---------|--------|-----------|
| `pbkdf2_sha256$...` | Copia directa | ✅ Login funciona |
| `bcrypt$...` | Copia directa | ✅ Login funciona |
| `argon2$...` | Copia directa | ✅ Login funciona |
| `texto_plano` | Hashea con `set_password()` | ✅ Login funciona |
| `vacío/null` | Contraseña no utilizable | ❌ No puede hacer login |

---

## 📊 Tablas que se Combinan

### 1. **auth_user** → `auth_user` (actual)
- Crea nuevos usuarios o actualiza existentes
- **Copia contraseñas hasheadas directamente**
- Mantiene fechas de registro (`date_joined`)
- Mantiene último login (`last_login`)
- Preserva estados: `is_active`, `is_staff`, `is_superuser`

### 2. **auth_user_groups** → Asignación de grupos
- Crea grupos si no existen (Estudiantes, Profesores, etc.)
- Asigna usuarios a sus grupos correspondientes
- Mantiene permisos y roles

### 3. **Docencia_studentpersonalinformation** → `accounts_registro`
- Combina información personal de estudiantes
- **Asigna automáticamente al grupo "Estudiantes"** (si aplica)
- Campos que se copian:
  - Nacionalidad
  - Carnet
  - Sexo
  - Dirección, municipio, provincia
  - Teléfono, móvil
  - Grado académico
  - Ocupación
  - Título

### 4. **Docencia_teacherpersonalinformation** → `accounts_registro`
- Combina información personal de profesores
- **Asigna automáticamente al grupo "Profesores"** ✅
- Campos que se copian:
  - Nacionalidad
  - Carnet
  - Sexo
  - Dirección, municipio, provincia
  - Teléfono, móvil
  - Grado académico
  - Ocupación
  - Título
  - Cualquier campo adicional

### 5. **principal_cursoacademico** → `CursoAcademico`
- Combina cursos académicos (ej: "2023-2024")
- Mantiene estado activo/archivado

### 6. **principal_curso** → `Curso`
- Combina cursos con sus profesores
- Vincula con cursos académicos
- Mantiene descripciones, áreas, tipos

### 7. **principal_matriculas** → `Matriculas`
- Combina matrículas de estudiantes
- Mantiene estados y fechas

### 8. **principal_asistencia** → `Asistencia`
- Combina registros de asistencia
- Mantiene fechas y estados de presencia

### 9. **principal_calificaciones** → `Calificaciones`
- Combina calificaciones con matrículas
- Mantiene promedios

### 10. **principal_notaindividual** → `NotaIndividual`
- Combina notas individuales
- Mantiene valores y fechas

---

## 🚀 Cómo Usar

### Paso 1: Acceder a Datos Archivados
1. Inicia sesión como **Secretaria** o **Administrador**
2. Ve a **Datos Archivados** → **Ver Tablas Archivadas**

### Paso 2: Verificar Datos
- Revisa las tablas archivadas disponibles
- Verifica que tengas los datos que necesitas
- Especialmente verifica que exista la tabla `auth_user`

### Paso 3: Combinar Datos
1. Haz clic en el botón **"Combinar Datos"** (verde)
2. Lee la información del modal
3. Haz clic en **"Sí, Combinar Datos"**
4. Espera a que el proceso termine (puede tardar varios minutos)

### Paso 4: Verificar Resultados
El sistema mostrará estadísticas:
- ✅ Usuarios combinados
- ✅ Registros de estudiantes combinados
- ✅ Cursos académicos combinados
- ✅ Cursos combinados
- ✅ Matrículas combinadas
- ✅ Asistencias combinadas
- ✅ Calificaciones combinadas
- ✅ Notas individuales combinadas

---

## 🔒 Seguridad y Protección de Datos

### Transacciones Atómicas
- Si algo falla, **TODO** se revierte
- No quedarán datos a medias
- La base de datos permanece consistente

### No se Eliminan Datos
- Los datos archivados **NO** se eliminan
- Los datos actuales **NO** se sobrescriben (solo se actualizan campos vacíos)
- Puedes ejecutar el proceso múltiples veces de forma segura

### Detección de Duplicados
- El sistema detecta usuarios duplicados por `username` o `email`
- No crea registros duplicados
- Actualiza información existente

### Logging Completo
- Cada operación se registra en el log del sistema
- Puedes revisar qué se hizo exactamente
- Los errores se registran para debugging

---

## 🧪 Probar Login Después de Combinar

### Para Usuarios Combinados:

1. **Obtén el username del usuario archivado**
   - Ve a Datos Archivados → Tablas → `auth_user`
   - Busca el usuario que quieres probar
   - Anota su `username`

2. **Intenta iniciar sesión**
   - Ve a la página de login
   - Usa el `username` del usuario archivado
   - Usa la **contraseña original** que tenía en el sistema antiguo
   - ✅ Debería funcionar sin problemas

3. **Si no funciona:**
   - Verifica que el usuario tenga `is_active = True`
   - Verifica que la contraseña se haya copiado (debe empezar con `pbkdf2_sha256$` o similar)
   - Revisa los logs del sistema para errores

---

## 📝 Ejemplo de Uso

```
Usuario en tabla archivada:
- username: "juan.perez"
- password: "pbkdf2_sha256$260000$abc123..."
- email: "juan@example.com"
- first_name: "Juan"
- last_name: "Pérez"

Después de combinar:
✅ Usuario creado en base de datos actual
✅ Puede iniciar sesión con su contraseña original
✅ Tiene su perfil de estudiante completo
✅ Tiene sus matrículas, calificaciones y asistencias
```

---

## ⚠️ Consideraciones Importantes

### Antes de Combinar:
1. ✅ Haz un backup de tu base de datos actual
2. ✅ Verifica que tengas espacio suficiente
3. ✅ Asegúrate de tener permisos de Secretaria o Admin
4. ✅ Cierra otras operaciones que puedan estar en curso

### Durante el Proceso:
- ⏳ No cierres la ventana del navegador
- ⏳ No interrumpas el proceso
- ⏳ Espera a que aparezca el mensaje de éxito

### Después de Combinar:
- ✅ Verifica que los usuarios puedan iniciar sesión
- ✅ Revisa que los datos se hayan copiado correctamente
- ✅ Prueba con algunos usuarios de ejemplo
- ✅ Revisa los logs si hay errores

---

## 🆘 Solución de Problemas

### Problema: "No se pudo crear usuario"
**Causa:** El username ya existe
**Solución:** El sistema actualizará el usuario existente automáticamente

### Problema: "No se encontró usuario para registro"
**Causa:** El usuario no se migró correctamente
**Solución:** Verifica que la tabla `auth_user` se haya procesado primero

### Problema: "Error al combinar datos"
**Causa:** Error en la base de datos o permisos
**Solución:** 
1. Revisa los logs del sistema
2. Verifica permisos de base de datos
3. Contacta al administrador del sistema

### Problema: "Usuario no puede iniciar sesión"
**Causa:** Contraseña no se copió o usuario inactivo
**Solución:**
1. Verifica que `is_active = True`
2. Verifica que el campo `password` tenga un valor hasheado
3. Intenta resetear la contraseña desde el admin de Django

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs del sistema en `/var/log/` o en la consola de Django
2. Verifica la tabla `datos_archivados_migracionlog` para ver el historial
3. Contacta al administrador del sistema con los detalles del error

---

## ✨ Beneficios

- 🚀 **Rápido**: Procesa miles de registros en minutos
- 🔒 **Seguro**: Transacciones atómicas y sin pérdida de datos
- 🔐 **Contraseñas preservadas**: Los usuarios no necesitan resetear
- 📊 **Completo**: Combina todas las tablas automáticamente
- 🔄 **Reversible**: Los datos archivados permanecen intactos
- 📝 **Auditable**: Todo se registra en logs

---

**Última actualización:** Noviembre 2024
**Versión:** 2.0 - Con preservación de contraseñas hasheadas
