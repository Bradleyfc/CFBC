# 📚 Guía de Uso - Sistema de Seguridad Avanzada

## ❓ RESPUESTA RÁPIDA: ¿Por qué están vacías algunas secciones?

### Es **completamente normal**. Aquí está el desglose:

#### ✅ **SE LLENAN AUTOMÁTICAMENTE** (Ya funcionando)
1. ✅ **UserSecurityProfile** - Se crea con cada usuario nuevo
2. ✅ **SecurityAuditLog** - Se llena con logins, bloqueos WAF, etc.
3. ✅ **WAFRule** - Se crean automáticamente con las migraciones (5 reglas por defecto)

#### ⚠️ **VACÍAS PORQUE NO LAS USAS** (Normal)
4. ⚠️ **JWTSession** - Solo si usas autenticación JWT/API
5. ⚠️ **APIKey** - Solo si tienes APIs externas
6. ⚠️ **OAuth2 (Django OAuth Toolkit)** - Solo si implementas login con Google/Facebook

#### ⚙️ **VACÍAS PORQUE REQUIEREN ACCIÓN MANUAL**
7. ⚙️ **SecurityReport** - Ejecuta: `python manage.py generate_security_report`
8. ⚙️ **ComplianceCheck** - Ejecuta: `python manage.py run_compliance_checks`
9. ⚙️ **Role** - Crea roles personalizados si los necesitas
10. ⚙️ **ObjectPermission** - Asigna permisos específicos si los necesitas
11. ⚙️ **Otras tablas avanzadas** - Solo si implementas funcionalidades específicas

### 💡 ¿Qué hacer?
- **Opción 1 (Rápida):** Probar comandos → Ir a la sección [Comandos Útiles](#%EF%B8%8F-comandos-útiles-de-management)
- **Opción 2 (Completa):** Leer toda la guía para entender cada sección

---

## 🎯 ¿Qué se llena automáticamente y qué no?

### Tabla Resumen Completa

| Sección | Estado | Se llena... | Acción requerida |
|---------|--------|-------------|------------------|
| **UserSecurityProfile** | ✅ Auto | Al crear usuarios | Ninguna |
| **SecurityAuditLog** | ✅ Auto | Con cada evento de seguridad | Ninguna |
| **WAFRule** | ✅ Auto | Con migraciones (`migrate`) | Ninguna - 5 reglas por defecto |
| **JWTSession** | ⚠️ Vacío | Solo si usas JWT | No aplica |
| **SecurityReport** | ⚙️ Manual | Ejecutar comando | Ver comandos abajo |
| **ComplianceCheck** | ⚙️ Manual | Ejecutar comando | Ver comandos abajo |
| **AuthorizationAuditLog** | ⚠️ Vacío | Si usas sistema de autorización | No aplica aún |
| **Role** | ⚙️ Manual | Crear roles personalizados | Opcional |
| **UserRoleAssignment** | ⚙️ Manual | Asignar roles a usuarios | Opcional |
| **APIKey** | ⚠️ Vacío | Solo si usas APIs externas | No aplica |
| **OAuth2 Tables** | ⚠️ Vacío | Solo si implementas OAuth2 | No aplica |

---

## 🎯 DETALLES COMPLETOS: ¿Qué se llena automáticamente y qué no?

---

## ✅ **SE LLENAN AUTOMÁTICAMENTE** (Con el uso normal)

### 1. **Perfiles de Seguridad de Usuarios** (`UserSecurityProfile`)
- ✅ **Se crea automáticamente** cuando se registra un nuevo usuario
- **Qué registra:**
  - Intentos fallidos de login
  - Bloqueos de cuenta
  - Estado de 2FA
  - Sesiones concurrentes

**Acción requerida:** Ninguna, se gestiona solo.

---

### 2. **Registros de Auditoría de Seguridad** (`SecurityAuditLog`)
- ✅ **Se llena automáticamente** con eventos del sistema
- **Qué registra:**
  - Logins exitosos/fallidos (ahora con los signals)
  - Bloqueos WAF
  - Cambios de contraseña
  - Accesos denegados
  - Operaciones de archivos

**Acción requerida:** Ninguna, se registra automáticamente.

---

### 3. **Reglas WAF** (`WAFRule`)
- ✅ **Se crean automáticamente** al ejecutar las migraciones (`python manage.py migrate`)
- **Qué incluye por defecto:**
  - SQL Injection - Basic (severity: critical)
  - XSS - Script Tags (severity: high)
  - Path Traversal - Basic (severity: high)
  - Command Injection - Basic (severity: critical)
  - Sensitive Data Exposure (severity: high)

**Acción requerida:** Ninguna. Las reglas se crean automáticamente con la migración `0003_create_default_waf_rules.py`.

**Nota:** Si necesitas agregar más reglas, usa el comando:
```bash
python manage.py create_default_waf_rules
```
O créalas manualmente desde el Admin de Django en **Seguridad Avanzada > Reglas WAF**.

---

### 4. **Sesiones JWT** (`JWTSession`)
- ✅ **Se llena solo si usas autenticación JWT/API**
- **Cuándo se usa:**
  - Si tienes una API REST con tokens JWT
  - Si usas Django REST Framework con JWT
  - Si implementas autenticación de tokens

**Nota:** Si solo usas sesiones normales de Django (cookies), esta tabla estará vacía. **Es normal.**

---

### 4. **Logs de Auditoría de Autorización** (`AuthorizationAuditLog`)
- ✅ **Se llena si usas el sistema de autorización avanzado**
- **Qué registra:**
  - Decisiones de permisos (permitido/denegado)
  - Accesos a recursos
  - Uso de roles

**Acción requerida:** Se llena automáticamente si implementas el sistema de autorización basado en roles.

---

## ⚙️ **REQUIEREN CONFIGURACIÓN MANUAL**

### 5. **Reglas WAF** (`WAFRule`) ✅ YA CONFIGURADO
- ⚙️ **Requieren creación manual o mediante comando**
- **Estado actual:** Ya tienes reglas creadas
- **Cómo se usan:**
  - Las reglas se activan con `is_active=True`
  - Cada vez que bloquean un ataque, incrementan `hit_count`
  - Se registra un evento en `SecurityAuditLog`

**Acción requerida:** Ya está configurado, solo monitorear.

---

### 6. **Reportes de Seguridad** (`SecurityReport`)
- ⚙️ **Requieren generación manual o programada**
- **Cómo generarlos:**
  ```bash
  # Desde la terminal
  python manage.py generate_security_report
  ```
- **O desde el código:**
  ```python
  from security.testing.services import SecurityTestingService
  report = SecurityTestingService.run_security_scan('vulnerability')
  ```

**Acción requerida:** Ejecutar comando manualmente o programar con cron/celery.

---

### 7. **Checks de Cumplimiento** (`ComplianceCheck`)
- ⚙️ **Requieren ejecución manual**
- **Cómo ejecutarlos:**
  ```bash
  # Comando para ejecutar checks de compliance
  python manage.py run_compliance_checks
  ```

**Acción requerida:** Ejecutar manualmente o programar.

---

### 8. **Políticas de Seguridad a Nivel de Fila** (`RowLevelSecurityPolicy`)
- ⚙️ **Requieren creación manual**
- **Para qué sirve:**
  - Filtrar datos por usuario a nivel de base de datos
  - Ejemplo: "Los estudiantes solo ven sus propios cursos"
  
**Acción requerida:** Crear políticas específicas según necesidades.

---

### 9. **Claves de Cifrado** (`EncryptedDataKey`)
- ⚙️ **Se crean bajo demanda**
- **Cuándo se usan:**
  - Si implementas cifrado de datos sensibles
  - Se crean automáticamente al cifrar datos

**Acción requerida:** Se crean automáticamente al usar el servicio de cifrado.

---

### 10. **Roles** (`Role`)
- ⚙️ **Requieren creación manual**
- **Para qué sirven:**
  - Sistema de roles avanzado (más allá de grupos de Django)
  - Jerarquía de roles
  - Permisos temporales

**Acción requerida:** Crear roles según tu organización.

---

### 11. **Asignación de Roles** (`UserRoleAssignment`)
- ⚙️ **Se llenan al asignar roles manualmente**
- **Cómo asignar:**
  ```python
  from security.models import Role, UserRoleAssignment
  role = Role.objects.get(name='Editor')
  UserRoleAssignment.objects.create(user=usuario, role=role)
  ```

**Acción requerida:** Asignar roles a usuarios según necesidades.

---

### 12. **Permisos de Objeto** (`ObjectPermission`)
- ⚙️ **Se crean al asignar permisos específicos a objetos**
- **Ejemplo:**
  - "Usuario X puede editar la Noticia Y"
  - "Profesor Z puede ver Curso W"

**Acción requerida:** Asignar permisos específicos según necesidades.

---

### 13. **Políticas de Acceso Temporal** (`TimeBasedAccessPolicy`)
- ⚙️ **Requieren creación manual**
- **Para qué sirven:**
  - Restringir acceso por horario
  - Ejemplo: "Solo acceso de 8am a 6pm"

**Acción requerida:** Crear políticas según horarios.

---

### 14. **API Keys** (`APIKey`)
- ⚙️ **Se crean manualmente**
- **Cuándo usarlas:**
  - Si tienes APIs REST públicas
  - Si necesitas autenticación de servicios externos

**Nota:** Como NO usas APIs externas, esta tabla estará vacía. **Es normal.**

---

## 🔵 **DJANGO OAUTH TOOLKIT** (Vacío - Normal)

Las tablas de OAuth2 solo se llenan si implementas:

### **¿Cuándo se usa OAuth2?**
- ✅ Si permites login con Google/Facebook/GitHub
- ✅ Si tienes una app móvil que se conecta a tu API
- ✅ Si permites que aplicaciones de terceros se conecten

### **Tablas OAuth2:**
1. **Applications** - Aplicaciones registradas (ej: "Mi App Móvil")
2. **Access Tokens** - Tokens de acceso activos
3. **Refresh Tokens** - Tokens para renovar acceso
4. **Authorization Codes** - Códigos temporales de autorización
5. **ID Tokens** - Tokens de identidad (OpenID Connect)

**Si NO usas OAuth2, estas tablas estarán vacías. Es completamente normal.**

---

## 📊 Resumen Rápido

| Sección | Estado | Se llena... |
|---------|--------|-------------|
| **UserSecurityProfile** | ✅ Auto | Al crear usuarios |
| **SecurityAuditLog** | ✅ Auto | Con cada evento de seguridad |
| **WAFRule** | ✅ Configurado | Ya tienes reglas activas |
| **JWTSession** | ⚠️ Vacío | Solo si usas JWT (no aplica) |
| **SecurityReport** | ⚙️ Manual | Ejecutar comando |
| **ComplianceCheck** | ⚙️ Manual | Ejecutar comando |
| **AuthorizationAuditLog** | ⚠️ Vacío | Si usas sistema de autorización |
| **Role** | ⚙️ Manual | Crear roles personalizados |
| **UserRoleAssignment** | ⚙️ Manual | Asignar roles a usuarios |
| **APIKey** | ⚠️ Vacío | Solo si usas APIs externas |
| **OAuth2** | ⚠️ Vacío | Solo si implementas OAuth2 |

---

## 🚀 ¿Qué deberías hacer?

### **Para uso básico (lo que tienes ahora):**
✅ Todo está funcionando correctamente
✅ Los logs se llenan automáticamente
✅ El WAF está protegiendo tu sitio
✅ Las tablas vacías son normales si no usas esas funcionalidades

### **Para uso avanzado (opcional):**
1. **Generar reportes periódicos:**
   ```bash
   python manage.py generate_security_report
   ```

2. **Ejecutar checks de compliance:**
   ```bash
   python manage.py run_compliance_checks
   ```

3. **Crear roles personalizados:**
   - Ir a `/admin/security/role/`
   - Crear roles como "Editor", "Moderador", etc.

---

## ❓ ¿Tienes dudas?

### **"¿Por qué está vacía la tabla X?"**
Probablemente porque esa funcionalidad no la estás usando actualmente. Es completamente normal.

### **"¿Debería llenar todas las tablas?"**
No, solo usa lo que necesites. Las funcionalidades avanzadas están ahí por si las necesitas en el futuro.

### **"¿Cómo sé qué necesito?"**
- Si tienes una web normal con login de Django → Solo necesitas lo básico (ya lo tienes)
- Si agregas una API REST → Necesitarás API Keys o JWT
- Si quieres login con Google → Necesitarás OAuth2
- Si necesitas permisos muy granulares → Usa Roles y ObjectPermission

---

**Conclusión:** Tu sistema está funcionando correctamente. Las tablas vacías son normales si no usas esas funcionalidades específicas.

---

## 🛠️ **COMANDOS ÚTILES DE MANAGEMENT**

Django proporciona comandos de consola para gestionar el sistema de seguridad. Aquí están todos los disponibles:

---

### **0. Reglas WAF - Creación Automática** 🔥

#### **¿Cómo se crean las reglas WAF?**
Las reglas WAF se crean **automáticamente** al ejecutar las migraciones de Django. No necesitas hacer nada manualmente.

```bash
# Al ejecutar las migraciones, se crean automáticamente 5 reglas WAF:
python manage.py migrate
```

#### **Reglas WAF creadas automáticamente:**
1. 🛡️ **SQL Injection - Basic** (Severity: CRITICAL)
   - Detecta patrones de inyección SQL
   - Pattern: `union.*select`, `drop.*table`, etc.

2. 🛡️ **XSS - Script Tags** (Severity: HIGH)
   - Detecta scripts maliciosos y event handlers
   - Pattern: `<script>`, `javascript:`, `onclick=`, etc.

3. 🛡️ **Path Traversal - Basic** (Severity: HIGH)
   - Detecta intentos de acceder a archivos del sistema
   - Pattern: `../`, `/etc/passwd`, `C:\Windows\`, etc.

4. 🛡️ **Command Injection - Basic** (Severity: CRITICAL)
   - Detecta intentos de ejecutar comandos del sistema
   - Pattern: `||`, `&&`, `;`, `cat /etc/passwd`, etc.

5. 🛡️ **Sensitive Data Exposure** (Severity: HIGH)
   - Detecta datos sensibles en requests
   - Pattern: `password=`, `secret=`, `api_key=`, etc.

#### **¿Qué migración las crea?**
- **Archivo:** `security/migrations/0003_create_default_waf_rules.py`
- **Tipo:** Data migration (migración de datos)
- **Comportamiento:** Solo crea reglas si no existen (idempotente)

#### **Comando manual (opcional):**
Si necesitas recrear las reglas o agregar más, puedes usar:
```bash
python manage.py create_default_waf_rules
```

**Nota:** Este comando es **opcional**. Las reglas ya se crean con `python manage.py migrate`.

#### **¿Cómo agregar reglas personalizadas?**
Puedes agregar más reglas desde el Admin de Django:
- Ve a **Admin > Seguridad Avanzada > Reglas WAF**
- Click en **Agregar Regla WAF**
- Define tu regex pattern, categoría y severidad
- Guarda

---

### **1. Generar Reportes de Seguridad**

Este comando genera reportes automáticos de seguridad con hallazgos y recomendaciones.

#### **Uso básico:**
```bash
python manage.py generate_security_report
```

#### **Opciones disponibles:**
```bash
# Reporte de vulnerabilidades (por defecto)
python manage.py generate_security_report --scan-type vulnerability

# Reporte de cumplimiento normativo
python manage.py generate_security_report --scan-type compliance

# Simulación de test de penetración
python manage.py generate_security_report --scan-type penetration

# Análisis de configuración de seguridad
python manage.py generate_security_report --scan-type configuration
```

#### **¿Qué hace este comando?**
- ✅ Crea un nuevo registro en `SecurityReport`
- ✅ Genera hallazgos (findings) en formato JSON
- ✅ Clasifica hallazgos por severidad (critical, high, medium, low, info)
- ✅ Proporciona recomendaciones de remediación
- ✅ Aparece automáticamente en el Dashboard de Seguridad

#### **Ejemplo de salida:**
```
Generando reporte de seguridad: vulnerability...
✅ Reporte generado exitosamente: RPT-20260719-abcd1234
   Fecha: 2026-07-19 10:30:00
   Hallazgos: 5

✅ No se encontraron hallazgos críticos

Puedes ver el reporte completo en: /admin/security/securityreport/1/
```

#### **Tipos de hallazgos por scan-type:**

**Vulnerability:**
- Estado del sistema de autenticación
- Estado del WAF
- Recomendaciones de 2FA
- Validación de entradas
- Protección contra inyecciones

**Compliance:**
- Headers de seguridad HTTP
- Protección CSRF
- Política de contraseñas
- Configuración de sesiones

**Penetration:**
- Tests de inyección SQL
- Tests de XSS
- Tests de CSRF
- Rate limiting
- Path traversal

**Configuration:**
- DEBUG mode
- SECRET_KEY
- ALLOWED_HOSTS
- Configuración de middleware
- Headers de seguridad

---

### **2. Ejecutar Checks de Compliance**

Este comando verifica el cumplimiento de normativas de seguridad (OWASP, GDPR, PCI DSS, HIPAA).

#### **Uso básico:**
```bash
python manage.py run_compliance_checks
```

#### **Opciones disponibles:**
```bash
# Ejecutar TODOS los checks de todas las regulaciones
python manage.py run_compliance_checks --regulation all

# Solo checks de OWASP Top 10 2021
python manage.py run_compliance_checks --regulation owasp

# Solo checks de GDPR (protección de datos)
python manage.py run_compliance_checks --regulation gdpr

# Solo checks de PCI DSS (pagos con tarjeta)
python manage.py run_compliance_checks --regulation pci_dss

# Solo checks de HIPAA (datos de salud)
python manage.py run_compliance_checks --regulation hipaa
```

#### **¿Qué hace este comando?**
- ✅ Ejecuta checks específicos según la regulación
- ✅ Crea registros en `ComplianceCheck`
- ✅ Marca cada check como PASSED (✅) o FAILED (❌)
- ✅ Proporciona detalles de cada verificación
- ✅ Calcula porcentaje de cumplimiento
- ✅ Aparece en el Dashboard de Seguridad

#### **Ejemplo de salida:**
```
Ejecutando checks de compliance: owasp...

📋 Verificando OWASP...
  ✅ A01:2021 - Broken Access Control
  ✅ A02:2021 - Cryptographic Failures
  ✅ A03:2021 - Injection
  ✅ A04:2021 - Insecure Design
  ✅ A05:2021 - Security Misconfiguration
  ✅ A06:2021 - Vulnerable Components
  ✅ A07:2021 - Authentication Failures
  ✅ A08:2021 - Software Integrity Failures
  ✅ A09:2021 - Logging Failures
  ✅ A10:2021 - SSRF

============================================================

📊 Resumen: 10/10 checks pasados (100.0%)
🎉 ¡Excelente nivel de cumplimiento!

Puedes ver los detalles en: /admin/security/compliancecheck/
```

#### **Checks por regulación:**

**OWASP Top 10 2021:**
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Authentication Failures
- A08: Software Integrity Failures
- A09: Logging Failures
- A10: SSRF

**GDPR (Protección de Datos):**
- Derecho al olvido
- Consentimiento explícito
- Cifrado de datos personales
- Auditoría de accesos
- Notificación de brechas

**PCI DSS (Seguridad de Pagos):**
- Firewall activo
- No almacenar datos de tarjetas
- Cifrado en tránsito (HTTPS/TLS)
- Acceso restringido
- Monitoreo de accesos

**HIPAA (Datos de Salud):**
- Control de acceso
- Auditoría de accesos
- Cifrado de datos de salud
- Sistema de backup
- Autenticación fuerte (2FA)

---

### **3. Crear Reglas WAF por Defecto**

Este comando crea las reglas básicas del Web Application Firewall.

```bash
python manage.py create_default_waf_rules
```

**Nota:** Ya has ejecutado este comando, por eso tienes reglas WAF activas. Solo necesitas ejecutarlo de nuevo si borras las reglas.

---

### **4. Verificar Estado del Dashboard**

Verifica que el dashboard de seguridad esté configurado correctamente.

```bash
python manage.py check_security_dashboard
```

---

## 📅 **AUTOMATIZACIÓN CON CRON/CELERY**

Puedes programar estos comandos para ejecutarse automáticamente:

### **Opción 1: Cron (Linux/Mac)**

Edita el crontab:
```bash
crontab -e
```

Agrega estas líneas:
```bash
# Generar reporte de seguridad diario a las 2 AM
0 2 * * * cd /ruta/a/tu/proyecto && python manage.py generate_security_report --scan-type vulnerability

# Ejecutar checks de compliance semanal (lunes a las 3 AM)
0 3 * * 1 cd /ruta/a/tu/proyecto && python manage.py run_compliance_checks --regulation all
```

### **Opción 2: Celery Beat (Django)**

En `settings.py`:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-daily-security-report': {
        'task': 'security.tasks.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),
    },
    'run-weekly-compliance-checks': {
        'task': 'security.tasks.run_compliance_checks',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
    },
}
```

### **Opción 3: Windows Task Scheduler**

1. Abre "Programador de tareas" (Task Scheduler)
2. Crear tarea básica
3. Trigger: Diariamente a las 2:00 AM
4. Acción: Iniciar programa
5. Programa: `python.exe`
6. Argumentos: `manage.py generate_security_report`
7. Directorio: Ruta de tu proyecto

---

## 🎯 **¿QUÉ DEBERÍAS HACER AHORA?**

### **Nivel Básico (Recomendado para empezar):**

#### **1. Probar los comandos manualmente:**
```bash
# Paso 1: Generar un reporte de vulnerabilidades
python manage.py generate_security_report --scan-type vulnerability

# Paso 2: Ejecutar checks de OWASP
python manage.py run_compliance_checks --regulation owasp

# Paso 3: Ver resultados en el admin
# /admin/security/securityreport/
# /admin/security/compliancecheck/
```

#### **2. Revisar el Dashboard:**
```
Ir a: /seguridad/dashboard/
```
Verás los nuevos datos en:
- Sección "Métricas de Seguridad"
- Tarjeta "Compliance Status"
- Sección "Problemas Críticos" (si hay hallazgos críticos)

#### **3. Ejecutar manualmente cuando lo necesites:**
- Antes de un despliegue a producción
- Después de cambios importantes
- Mensualmente para auditoría
- Cuando necesites un reporte formal

---

### **Nivel Intermedio (Uso regular):**

#### **Programar ejecución automática:**

**Semanal (recomendado):**
```bash
# Cada lunes a las 8 AM
0 8 * * 1 python manage.py generate_security_report
0 8 * * 1 python manage.py run_compliance_checks
```

**Mensual (para auditorías):**
```bash
# Primer día del mes a las 2 AM
0 2 1 * * python manage.py generate_security_report --scan-type vulnerability
0 2 1 * * python manage.py generate_security_report --scan-type compliance
0 2 1 * * python manage.py run_compliance_checks --regulation all
```

---

### **Nivel Avanzado (Opcional):**

#### **Crear reportes personalizados:**
Puedes modificar los comandos en:
```
security/management/commands/generate_security_report.py
security/management/commands/run_compliance_checks.py
```

#### **Integrar con servicios externos:**
- Enviar reportes por email
- Enviar alertas a Slack/Teams
- Integrar con sistemas SIEM
- Exportar a formatos específicos (PDF, CSV)

---

## 📊 **INTERPRETACIÓN DE RESULTADOS**

### **SecurityReport - Niveles de Severidad:**

| Severidad | Significado | Acción |
|-----------|-------------|--------|
| **Critical** 🔴 | Vulnerabilidad explotable activamente | Corregir INMEDIATAMENTE |
| **High** 🟠 | Vulnerabilidad seria, alto riesgo | Corregir en 24-48 horas |
| **Medium** 🟡 | Vulnerabilidad moderada | Corregir en 1-2 semanas |
| **Low** 🟢 | Vulnerabilidad menor | Corregir cuando sea posible |
| **Info** ℹ️ | Información, buena práctica | No requiere acción urgente |

### **ComplianceCheck - Niveles de Cumplimiento:**

| Porcentaje | Calificación | Estado |
|------------|--------------|--------|
| **90-100%** | Excelente 🎉 | Cumplimiento óptimo |
| **70-89%** | Aceptable ⚠️ | Mejorable, revisar fallos |
| **50-69%** | Insuficiente 🚨 | Requiere mejoras urgentes |
| **< 50%** | Crítico ⛔ | Incumplimiento grave |

---

## 🔧 **SOLUCIÓN DE PROBLEMAS**

### **Problema: "No se generan reportes"**
```bash
# Verificar que el comando funciona
python manage.py generate_security_report --help

# Ver errores en detalle
python manage.py generate_security_report --verbosity 2
```

### **Problema: "Checks de compliance fallan"**
```bash
# Ejecutar con verbose para ver detalles
python manage.py run_compliance_checks --verbosity 2

# Revisar configuración de Django
python manage.py check --deploy
```

### **Problema: "No aparecen en el Dashboard"**
1. Verificar que los reportes se crearon: `/admin/security/securityreport/`
2. Refrescar el dashboard: Click en botón "Actualizar"
3. Verificar el rango de tiempo (últimos 7 días, 30 días)

---

## 📧 **NOTIFICACIONES POR EMAIL (Opcional)**

Si quieres recibir reportes por email, agrega esto en `settings.py`:

```python
# Configuración de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-contraseña-app'

# Destinatarios de reportes de seguridad
SECURITY_REPORT_EMAILS = ['admin@tudominio.com', 'security@tudominio.com']
```

Luego modifica el comando para enviar emails automáticamente.

---

## 🎓 **BUENAS PRÁCTICAS**

### **Frecuencia Recomendada:**

| Tipo de Check | Frecuencia | Cuándo |
|---------------|------------|--------|
| Vulnerability Scan | Semanal | Lunes por la mañana |
| Compliance Check | Mensual | Primer día del mes |
| Penetration Test | Trimestral | Antes de releases importantes |
| Configuration Audit | Después de cambios | Post-deployment |

### **Antes de Producción:**
```bash
# Checklist pre-deployment
python manage.py check --deploy
python manage.py generate_security_report --scan-type vulnerability
python manage.py generate_security_report --scan-type configuration
python manage.py run_compliance_checks --regulation owasp
```

### **Después de Incidentes:**
```bash
# Análisis post-incidente
python manage.py generate_security_report --scan-type penetration
python manage.py run_compliance_checks --regulation all
# Revisar SecurityAuditLog manualmente
```

---

## 📚 **RECURSOS ADICIONALES**

### **Documentación:**
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- GDPR: https://gdpr.eu/
- PCI DSS: https://www.pcisecuritystandards.org/
- HIPAA: https://www.hhs.gov/hipaa/

### **Archivos del Sistema:**
- Comandos: `security/management/commands/`
- Modelos: `security/models.py`
- Admin: `security/admin.py`
- Dashboard: `security/views_dashboard.py`
- Templates: `security/templates/security/`

### **URLs Útiles:**
- Dashboard: `/seguridad/dashboard/`
- Admin Security: `/admin/security/`
- Audit Logs: `/admin/security/securityauditlog/`
- Reports: `/admin/security/securityreport/`
- Compliance: `/admin/security/compliancecheck/`
- WAF Rules: `/admin/security/wafrule/`

---

**✅ RESUMEN FINAL:**

1. **Ejecuta los comandos manualmente** para ver cómo funcionan
2. **Revisa los resultados** en el admin y dashboard
3. **Si te parecen útiles**, programa su ejecución automática
4. **Si no los necesitas**, déjalos para uso ocasional

Tu sistema básico de seguridad (WAF, logs, autenticación) **ya está funcionando perfectamente** sin necesidad de estos comandos. Los comandos son herramientas adicionales para auditoría y compliance formal.
