# Instrucciones para Aplicar Migraciones en el Hosting

## Problema Identificado
El error `column datos_archivados_migracionlog.tablas_inspeccionadas does not exist` indica que las migraciones más recientes no se han aplicado en el hosting.

## Solución

### Opción 1: Aplicar migraciones manualmente
```bash
# En el servidor de hosting, ejecutar:
python manage.py migrate datos_archivados
```

### Opción 2: Usar el script automatizado
```bash
# En el servidor de hosting, ejecutar:
python aplicar_migraciones_hosting.py
```

### Opción 3: Verificar y aplicar todas las migraciones
```bash
# Verificar estado actual
python manage.py showmigrations

# Aplicar todas las migraciones pendientes
python manage.py migrate

# Verificar que se aplicaron correctamente
python manage.py showmigrations datos_archivados
```

## Migraciones Requeridas
- `0001_initial.py` - Modelos iniciales
- `0002_datoarchivadodinamico.py` - Modelo dinámico
- `0003_migracionlog_tablas_con_datos_and_more.py` - **ESTA ES LA QUE FALTA**

## Campos Agregados en la Migración 0003
- `tablas_inspeccionadas` (IntegerField)
- `tablas_con_datos` (IntegerField) 
- `tablas_vacias` (IntegerField)

## Verificación Post-Migración
Después de aplicar las migraciones, el endpoint `/datos-archivados/migracion/estado/` debería funcionar sin errores.

## Código Actualizado
El código ya está preparado para manejar casos donde estos campos no existen (usando `safe_getattr`), pero es mejor aplicar las migraciones para tener la funcionalidad completa.

## Notas Importantes
- Las migraciones deben aplicarse en el mismo orden que se crearon
- Hacer backup de la base de datos antes de aplicar migraciones en producción
- Verificar que no hay usuarios activos durante la aplicación de migraciones