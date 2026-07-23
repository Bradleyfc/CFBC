# Dashboard de Seguridad - CFBC

## 🚀 Características Implementadas

### 1. **Panel de Control Principal**
- ✅ **Dashboard visual** con gráficos interactivos
- ✅ **Métricas en tiempo real** de seguridad
- ✅ **Gráficos Chart.js** para visualización de datos
- ✅ **Diseño responsive** para móviles y escritorio

### 2. **Métricas Disponibles**
- **Auditoría de Seguridad**: Eventos totales, críticos, fallidos
- **WAF (Web Application Firewall)**: Bloqueos, tipos de ataque, reglas activas
- **Autenticación**: Logins fallidos, bloqueos de cuenta, 2FA
- **Cumplimiento**: Score OWASP, checks de compliance
- **Sesiones**: Activas, expiradas, por usuario

### 3. **Gráficos Interactivos**
1. **Timeline de Eventos** - Tendencia de eventos de seguridad
2. **Tipos de Ataque WAF** - Distribución de ataques bloqueados
3. **Distribución de Severidad** - Eventos por nivel de severidad
4. **Eventos de Autenticación** - Logins exitosos/fallidos/logouts

### 4. **Funcionalidades Avanzadas**
- ✅ **Filtros de tiempo**: 24h, 7 días, 30 días
- ✅ **Actualización en tiempo real** con botón Refresh
- ✅ **Acceso rápido** a secciones del admin
- ✅ **Problemas críticos** destacados
- ✅ **Reportes recientes** visibles

## 🎯 Cómo Acceder

### 1. **Desde el Admin de Django**
1. Inicia sesión como usuario admin (`/admin/`)
2. Busca el botón **"Seguridad"** en la barra superior (color azul)
3. Haz clic para acceder al dashboard

### 2. **URL Directa**
- **Dashboard principal**: `/seguridad/dashboard/`
- **API de datos**: `/seguridad/dashboard/data/`

## 🛠️ Configuración Técnica

### Archivos Creados:

```
security/
├── views_dashboard.py          # Vistas del dashboard
├── templates/security/
│   └── dashboard.html          # Template HTML del dashboard
├── templatetags/
│   ├── __init__.py
│   └── security_admin.py       # Template tag para botón del admin
├── templates/security/admin/
│   └── security_button.html    # Template del botón
└── urls.py                     # URLs actualizadas
```

### Templates Modificados:
```
templates/admin/base_site.html  # Extensión del admin base
```

## 🔧 Personalización

### 1. **Modificar Colores**
Editar `dashboard.html` - sección CSS:
```css
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
    --info-color: #17a2b8;
}
```

### 2. **Agregar Métricas**
En `views_dashboard.py`:
```python
def get_new_metrics(start_date, end_date):
    # Tu lógica aquí
    return {'metric': value}
```

### 3. **Agregar Gráficos**
1. Añadir canvas HTML en `dashboard.html`:
```html
<canvas id="newChart"></canvas>
```
2. Crear función JavaScript en `dashboard.html`:
```javascript
function updateNewChart(data) {
    // Lógica del gráfico
}
```

## 📊 Requisitos de Datos

El dashboard utiliza los siguientes modelos:

### **Modelos de Seguridad Requeridos:**
- `SecurityAuditLog` - Eventos de auditoría
- `AuthorizationAuditLog` - Decisiones de autorización
- `WAFRule` - Reglas del firewall
- `SecurityReport` - Reportes de seguridad
- `ComplianceCheck` - Checks de cumplimiento
- `UserSecurityProfile` - Perfiles de seguridad
- `JWTSession` - Sesiones JWT

## 🚨 Solución de Problemas

### **Problema 1: Botón no aparece en admin**
- Verificar que el usuario sea `is_staff=True`
- Revisar `templates/admin/base_site.html`
- Verificar que `security_admin.py` esté cargado

### **Problema 2: Gráficos no cargan**
- Verificar conexión a internet (Chart.js CDN)
- Revisar consola del navegador para errores JavaScript
- Verificar que la API `/seguridad/dashboard/data/` retorne JSON

### **Problema 3: Datos vacíos**
- Verificar que haya datos en los modelos de seguridad
- Revisar las consultas en `views_dashboard.py`
- Verificar rangos de fechas

## 🔒 Permisos de Acceso

### **Requisitos:**
1. Usuario autenticado (`request.user.is_authenticated`)
2. Usuario staff (`request.user.is_staff`)
3. (Opcional) Permisos específicos

### **Personalizar permisos:**
En `views_dashboard.py` - decorador `admin_required`:
```python
def check_admin(user):
    return user.is_authenticated and user.is_staff and user.has_perm('security.view_dashboard')
```

## 📈 Próximas Mejoras (Opcionales)

### **Planeado:**
1. **Exportación de datos** - CSV, PDF, Excel
2. **Alertas configurables** - Email, notificaciones
3. **Dashboard en tiempo real** - WebSockets
4. **Comparativas históricas** - Año vs año, mes vs mes
5. **Mapa de amenazas** - Geolocalización de IPs

### **Integraciones:**
- **Slack/Teams** - Notificaciones
- **Grafana** - Dashboards avanzados
- **ELK Stack** - Logs centralizados

## 🎨 Personalización Visual

### **Temas disponibles:**
1. **Default** - Azul profesional (actual)
2. **Dark Mode** - Tema oscuro
3. **High Contrast** - Accesibilidad
4. **Brand Colors** - Colores de la organización

### **Cambiar tema:**
Editar `dashboard.html` - sección `<style>` o agregar clases CSS.

## 📱 Compatibilidad

### **Navegadores:**
- ✅ Chrome 60+
- ✅ Firefox 55+
- ✅ Safari 11+
- ✅ Edge 79+

### **Dispositivos:**
- ✅ Desktop
- ✅ Tablet
- ✅ Mobile

## 🔗 Enlaces Útiles

### **Admin Django:**
- Reportes: `/admin/security/securityreport/`
- Auditoría: `/admin/security/securityauditlog/`
- WAF: `/admin/security/wafrule/`
- Compliance: `/admin/security/compliancecheck/`

### **API Endpoints:**
- Dashboard: `/seguridad/dashboard/`
- Datos: `/seguridad/dashboard/data/?range=7d`

---

**Estado:** ✅ **Implementado y Funcional**
**Última Actualización:** Julio 2026
**Versión:** 1.0.0