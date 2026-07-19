# 🚀 Instrucciones para Aplicar la Migración de Reglas WAF

## ⚡ Comando Rápido

```bash
python manage.py migrate
```

**Eso es todo.** Las reglas WAF se crearán automáticamente.

---

## 📋 Instrucciones Paso a Paso

### 1. Verifica el estado actual de las migraciones
```bash
python manage.py showmigrations security
```

**Deberías ver:**
```
security
 [X] 0001_initial
 [X] 0002_enable_pgcrypto_rls
 [ ] 0003_create_default_waf_rules  ← Esta es la nueva
```

### 2. Aplica las migraciones pendientes
```bash
python manage.py migrate
```

**Resultado esperado:**
```
Running migrations:
  Applying security.0003_create_default_waf_rules... OK
✅ Created 5 default WAF rules
```

### 3. Verifica que las reglas fueron creadas
```bash
python manage.py shell
```

Dentro del shell:
```python
from security.models import WAFRule

# Contar reglas
print(f"Total reglas: {WAFRule.objects.count()}")
# Debería mostrar: Total reglas: 5

# Listar todas las reglas
for rule in WAFRule.objects.all():
    print(f"✅ {rule.name} - {rule.severity} - Active: {rule.is_active}")

# Resultado esperado:
# ✅ SQL Injection - Basic - critical - Active: True
# ✅ XSS - Script Tags - high - Active: True
# ✅ Path Traversal - Basic - high - Active: True
# ✅ Command Injection - Basic - critical - Active: True
# ✅ Sensitive Data Exposure - high - Active: True

# Salir del shell
exit()
```

---

## 🔍 Verificación en el Admin

1. Ve a: `http://localhost:8000/admin/security/wafrule/`
2. Deberías ver 5 reglas WAF listadas
3. Todas deberían tener `is_active = True` (checkbox marcado)

---

## 🛡️ Verificación en el Dashboard

1. Ve a tu perfil de Admin
2. Click en **"Dashboard de Seguridad"**
3. Busca la tarjeta **"Bloqueos WAF"**
4. Deberías ver el botón "?" que abre el modal de información WAF
5. Las estadísticas de WAF deberían estar funcionando

---

## ❓ ¿Qué pasa si ya tenía reglas WAF creadas?

**No hay problema.** La migración es **idempotente**:
- Si las reglas ya existen (por nombre), no las crea de nuevo
- Si faltan algunas reglas, solo crea las que falten
- No elimina ni modifica las reglas existentes

---

## 🔄 Si necesitas revertir la migración

```bash
# Revertir a la migración anterior
python manage.py migrate security 0002_enable_pgcrypto_rls

# Esto eliminará las 5 reglas WAF creadas por la migración
# (pero NO las reglas creadas manualmente)
```

**Para volver a aplicarla:**
```bash
python manage.py migrate security
```

---

## 🆘 Solución de Problemas

### Error: "Relation does not exist"
**Causa:** No has aplicado las migraciones anteriores.

**Solución:**
```bash
python manage.py migrate
```

### Error: "UNIQUE constraint failed"
**Causa:** Ya existen reglas con esos nombres.

**Solución:** No es realmente un error. La migración debería manejar esto. Si persiste:
```bash
python manage.py shell
```
```python
from security.models import WAFRule
# Ver qué reglas existen
for rule in WAFRule.objects.all():
    print(rule.name)
```

Si hay duplicados, elimina los duplicados manualmente desde el Admin.

### Las reglas se crearon pero no aparecen en el Admin
**Causa:** Posible problema de cache del navegador.

**Solución:**
1. Cierra sesión del Admin
2. Limpia la caché del navegador (Ctrl + Shift + Delete)
3. Vuelve a iniciar sesión
4. Ve a `/admin/security/wafrule/`

---

## 📊 Comandos Útiles Adicionales

### Ver detalles de una migración específica
```bash
python manage.py sqlmigrate security 0003
```

### Verificar si hay migraciones pendientes
```bash
python manage.py showmigrations --plan
```

### Ver el estado de todas las apps
```bash
python manage.py showmigrations
```

---

## ✅ Checklist Final

Después de aplicar la migración, verifica:

- [ ] ✅ La migración se aplicó sin errores
- [ ] ✅ Existen 5 reglas WAF en la base de datos
- [ ] ✅ Las reglas están activas (`is_active = True`)
- [ ] ✅ Las reglas aparecen en el Admin de Django
- [ ] ✅ El Dashboard de Seguridad muestra las estadísticas WAF
- [ ] ✅ El modal de información WAF funciona correctamente

---

## 🎯 Próximos Pasos

Una vez aplicada la migración:

1. **Monitorea el Dashboard** para ver bloqueos en tiempo real
2. **Revisa los logs de auditoría** en `/admin/security/securityauditlog/`
3. **Ajusta las reglas** si tienes falsos positivos
4. **Agrega reglas personalizadas** según tus necesidades

---

## 📞 Más Información

- **Guía completa:** `security/GUIA_USO_SEGURIDAD.md`
- **Detalles técnicos:** `security/REGLAS_WAF_AUTOMATICAS.md`
- **Resumen:** `RESUMEN_REGLAS_WAF_AUTOMATICAS.md`

---

## 🎓 Nota Final

Esta migración es **segura** y está diseñada para:
- ✅ No causar downtime
- ✅ No modificar datos existentes
- ✅ Ser completamente reversible
- ✅ Funcionar en producción sin problemas

**¡Listo para aplicar!** 🚀
