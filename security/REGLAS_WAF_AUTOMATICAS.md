# 🔥 Reglas WAF - Creación Automática

## ❓ Pregunta Original
> "Las reglas WAF que están creadas, ¿se crean solas con la migración?"

## ✅ Respuesta: SÍ, ahora sí

### Antes (Problema)
- ❌ Las reglas WAF **NO** se creaban automáticamente
- ❌ Había que ejecutar manualmente: `python manage.py create_default_waf_rules`
- ❌ Si no se ejecutaba el comando, el WAF no tenía reglas y no funcionaba
- ❌ Riesgo: En producción, olvidar este paso dejaba el sistema sin protección

### Ahora (Solución)
- ✅ Las reglas WAF **SÍ** se crean automáticamente
- ✅ Se crean al ejecutar: `python manage.py migrate`
- ✅ No requiere pasos manuales adicionales
- ✅ El sistema queda protegido desde el primer despliegue

---

## 🔧 Implementación Técnica

### Data Migration Creada
**Archivo:** `security/migrations/0003_create_default_waf_rules.py`

### ¿Qué hace esta migración?
1. Se ejecuta automáticamente después de `0001_initial.py`
2. Verifica si las reglas WAF ya existen (por nombre)
3. Si no existen, crea 5 reglas por defecto
4. Si ya existen, las deja intactas (no duplica)
5. Es **idempotente**: puedes ejecutarla múltiples veces sin problemas

### Reglas creadas automáticamente:

| # | Nombre | Categoría | Severity | Pattern Preview |
|---|--------|-----------|----------|----------------|
| 1 | SQL Injection - Basic | `sql_injection` | **CRITICAL** | `union.*select`, `drop.*table` |
| 2 | XSS - Script Tags | `xss` | **HIGH** | `<script>`, `javascript:`, `onclick=` |
| 3 | Path Traversal - Basic | `path_traversal` | **HIGH** | `../`, `/etc/passwd`, `C:\Windows\` |
| 4 | Command Injection - Basic | `command_injection` | **CRITICAL** | `\|\|`, `&&`, `;`, `cat /etc/passwd` |
| 5 | Sensitive Data Exposure | `custom` | **HIGH** | `password=`, `secret=`, `api_key=` |

---

## 📋 ¿Cómo usar?

### Para nuevas instalaciones:
```bash
# 1. Ejecuta las migraciones (como siempre)
python manage.py migrate

# 2. Listo! Las reglas WAF ya están creadas ✅
```

### Para instalaciones existentes:
```bash
# 1. Aplica la nueva migración
python manage.py migrate security

# 2. Verifica que las reglas existan
python manage.py shell
>>> from security.models import WAFRule
>>> WAFRule.objects.count()
5  # Deberías ver 5 reglas
```

### ¿Qué pasa si ya tenías reglas creadas?
- No hay problema ✅
- La migración verifica si existen por nombre
- Si ya existen, no las duplica
- Solo crea las que falten

---

## 🎯 Ventajas de esta solución

### 1. **Cero configuración manual**
- No tienes que recordar ejecutar comandos adicionales
- El sistema queda protegido automáticamente

### 2. **Idempotente**
- Puedes ejecutar `migrate` múltiples veces sin riesgo
- No crea reglas duplicadas

### 3. **Estándar de Django**
- Usa el mecanismo oficial de Django para datos iniciales
- Se integra perfectamente con el flujo de despliegue

### 4. **Reversible**
```bash
# Si quieres revertir la migración:
python manage.py migrate security 0001_initial

# Y luego volver a aplicarla:
python manage.py migrate security
```

### 5. **Fácil de mantener**
- El código está en un archivo de migración estándar
- Se versiona junto con el código
- Puedes modificar las reglas editando la migración

---

## 🔄 Comando Manual (Opcional)

El comando `create_default_waf_rules` **todavía existe** pero ahora es opcional:

```bash
python manage.py create_default_waf_rules
```

**¿Cuándo usarlo?**
- Si quieres **recrear** las reglas después de haberlas eliminado
- Si quieres **actualizar** las reglas con nuevos patterns
- Si estás probando diferentes configuraciones

**Nota:** Este comando usa `update_or_create`, así que también es idempotente.

---

## 📚 Documentación Actualizada

La guía `GUIA_USO_SEGURIDAD.md` ha sido actualizada con:

### Sección "Tabla Resumen Completa"
```markdown
| **WAFRule** | ✅ Auto | Con migraciones (`migrate`) | Ninguna - 5 reglas por defecto |
```

### Sección "SE LLENAN AUTOMÁTICAMENTE"
```markdown
3. ✅ **WAFRule** - Se crean automáticamente con las migraciones (5 reglas por defecto)
```

### Nueva sección "0. Reglas WAF - Creación Automática"
- Explica cómo se crean las reglas
- Lista las 5 reglas por defecto con detalles
- Muestra cómo agregar reglas personalizadas

---

## 🚀 Despliegue en Producción

### Flujo normal de despliegue:
```bash
# 1. Pull del código
git pull origin seguridad

# 2. Activar entorno virtual (si aplica)
source venv/bin/activate

# 3. Instalar dependencias (si hay cambios)
pip install -r requirements.txt

# 4. Ejecutar migraciones (aquí se crean las reglas WAF)
python manage.py migrate

# 5. Recolectar archivos estáticos
python manage.py collectstatic --noinput

# 6. Reiniciar servidor
# (depende de tu configuración: gunicorn, uwsgi, etc.)
```

**Resultado:** Las reglas WAF están activas desde el primer request 🛡️

---

## ✅ Verificación

### Desde Django Shell:
```python
python manage.py shell

from security.models import WAFRule

# Ver todas las reglas
for rule in WAFRule.objects.all():
    print(f"{rule.name} - {rule.severity} - Active: {rule.is_active}")

# Resultado esperado:
# SQL Injection - Basic - critical - Active: True
# XSS - Script Tags - high - Active: True
# Path Traversal - Basic - high - Active: True
# Command Injection - Basic - critical - Active: True
# Sensitive Data Exposure - high - Active: True
```

### Desde Admin de Django:
1. Ve a: `/admin/security/wafrule/`
2. Deberías ver 5 reglas creadas
3. Todas con `is_active = True`

### Desde Dashboard de Seguridad:
1. Ve a tu perfil de Admin
2. Click en "Dashboard de Seguridad"
3. Tarjeta "Bloqueos WAF" debe mostrar estadísticas

---

## 🎓 ¿Cómo funciona una Data Migration?

### Estructura del archivo:
```python
# security/migrations/0003_create_default_waf_rules.py

def create_default_waf_rules(apps, schema_editor):
    """Función que corre al aplicar la migración"""
    WAFRule = apps.get_model('security', 'WAFRule')
    # ... crear reglas ...

def reverse_func(apps, schema_editor):
    """Función que corre al revertir la migración"""
    WAFRule = apps.get_model('security', 'WAFRule')
    # ... eliminar reglas ...

class Migration(migrations.Migration):
    dependencies = [
        ('security', '0001_initial'),  # Depende de la migración anterior
    ]
    
    operations = [
        migrations.RunPython(create_default_waf_rules, reverse_func),
    ]
```

### Orden de ejecución:
1. `0001_initial.py` → Crea las tablas de la BD
2. `0002_enable_pgcrypto_rls.py` → Habilita RLS (Row Level Security) en PostgreSQL
3. `0003_create_default_waf_rules.py` → Inserta reglas WAF por defecto
4. Futuras migraciones → Modificaciones adicionales

---

## 🆚 Comparación: Antes vs Ahora

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Comando para reglas** | `create_default_waf_rules` (manual) | Automático con `migrate` |
| **Riesgo de olvido** | Alto ⚠️ | Ninguno ✅ |
| **Pasos en producción** | 2 comandos | 1 comando |
| **Documentación** | "Recuerda ejecutar..." | "Se crea automáticamente" |
| **Idempotencia** | ✅ Sí | ✅ Sí |
| **Reversible** | ❌ No | ✅ Sí (con migrate) |

---

## 💡 Conclusión

**Respuesta final a tu pregunta:**
> "Las reglas WAF que están creadas, ¿se crean solas con la migración?"

✅ **SÍ**, ahora se crean automáticamente con `python manage.py migrate`.

**Lo que hicimos:**
1. ✅ Creada data migration `0003_create_default_waf_rules.py`
2. ✅ Actualizada documentación en `GUIA_USO_SEGURIDAD.md`
3. ✅ Sistema listo para producción sin pasos manuales adicionales

**Próximos pasos recomendados:**
1. Ejecutar `python manage.py migrate` para aplicar la nueva migración
2. Verificar que las 5 reglas WAF estén creadas
3. El sistema WAF ya está protegiendo tu aplicación 🛡️

---

## 📞 Soporte Adicional

Si necesitas:
- Agregar más reglas personalizadas
- Modificar los patterns de las reglas existentes
- Deshabilitar reglas específicas
- Crear reglas para casos de uso específicos

Usa el Admin de Django en **Seguridad Avanzada > Reglas WAF** o consulta la guía completa en `GUIA_USO_SEGURIDAD.md`.
