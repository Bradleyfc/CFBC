# Sistema de Migración Automática de Datos

Este módulo proporciona un sistema completo para migrar automáticamente datos desde una base de datos MariaDB remota hacia PostgreSQL, inspeccionando automáticamente la estructura y creando modelos dinámicos.

## 🚀 Características Principales

### Inspección Automática
- **Detección automática de tablas**: Inspecciona todas las tablas de la base de datos remota
- **Análisis de estructura**: Detecta columnas, tipos de datos, claves foráneas y restricciones
- **Mapeo inteligente**: Convierte automáticamente tipos MySQL a campos Django
- **Sin configuración manual**: No requiere definir modelos previamente

### Migración Inteligente
- **Modelos dinámicos**: Crea modelos Django en tiempo de ejecución
- **Preservación de datos**: Mantiene toda la información original
- **Almacenamiento flexible**: Guarda datos en formato JSON para máxima flexibilidad
- **Trazabilidad completa**: Registra origen, estructura y fecha de migración

### Interfaz de Usuario
- **Dashboard intuitivo**: Visualización de estadísticas y progreso
- **Configuración simple**: Solo requiere datos de conexión
- **Monitoreo en tiempo real**: Seguimiento del progreso de migración
- **Búsqueda y filtrado**: Herramientas para explorar datos migrados

## 📋 Requisitos

- Django 4.0+
- PostgreSQL (base de datos local)
- MariaDB/MySQL (base de datos remota)
- Python 3.8+
- Paquetes: `mysql-connector-python`, `openpyxl`

## 🛠️ Instalación

1. **Agregar a INSTALLED_APPS**:
```python
INSTALLED_APPS = [
    # ... otras apps
    'datos_archivados.apps.DatosArchivadosConfig',
]
```

2. **Incluir URLs**:
```python
urlpatterns = [
    # ... otras URLs
    path('datos-archivados/', include('datos_archivados.urls')),
]
```

3. **Ejecutar migraciones**:
```bash
python manage.py migrate datos_archivados
```

## 🎯 Uso

### Desde la Interfaz Web

1. **Acceder al Dashboard**:
   - Ir a `/datos-archivados/`
   - Solo usuarios del grupo "Secretaria" tienen acceso

2. **Configurar Migración**:
   - Hacer clic en "Configurar Migración"
   - Ingresar datos de conexión de la base de datos remota:
     - Host/Servidor
     - Puerto (default: 3306)
     - Nombre de base de datos
     - Usuario
     - Contraseña

3. **Ejecutar Migración**:
   - El sistema automáticamente:
     - Inspecciona todas las tablas
     - Crea modelos dinámicos
     - Migra todos los datos
     - Proporciona seguimiento en tiempo real

4. **Explorar Datos**:
   - Ver estadísticas en el dashboard
   - Buscar y filtrar datos migrados
   - Exportar a Excel

### Desde Línea de Comandos

```bash
python manage.py migrar_datos_automatico \
    --host mysql.tuhosting.com \
    --database mi_base_datos \
    --user mi_usuario \
    --password mi_contraseña \
    --port 3306 \
    --usuario-django admin
```

## 📊 Modelos de Datos

### DatoArchivadoDinamico
Modelo principal que almacena todos los datos migrados:

- `tabla_origen`: Nombre de la tabla original
- `id_original`: ID del registro en la base de datos original
- `datos_originales`: Datos completos en formato JSON
- `estructura_tabla`: Estructura de la tabla original
- `fecha_migracion`: Timestamp de la migración

### MigracionLog
Registro de todas las migraciones ejecutadas:

- `fecha_inicio/fin`: Timestamps del proceso
- `estado`: Estado de la migración (iniciada, en_progreso, completada, error)
- `usuario`: Usuario que ejecutó la migración
- `host_origen/base_datos_origen`: Información de la fuente
- `usuarios_migrados`: Contador de registros migrados
- `errores`: Log de errores si los hay

## 🔧 Configuración Avanzada

### Personalizar Mapeo de Tipos
Editar `InspectorBaseDatos.mapear_tipo_campo()` para agregar tipos personalizados:

```python
def mapear_tipo_campo(self, tipo_mysql, es_nullable, es_clave_primaria, longitud_maxima=None):
    if 'mi_tipo_personalizado' in tipo_mysql:
        return models.CharField(max_length=100, null=es_nullable, blank=es_nullable)
    # ... resto del mapeo
```

### Filtrar Tablas
Modificar `InspectorBaseDatos.inspeccionar_base_datos_completa()` para excluir tablas específicas:

```python
tablas_interes = [t for t in tablas if not t.startswith('django_') 
                 and t not in ['tabla_a_excluir', 'otra_tabla']]
```

## 🚨 Consideraciones de Seguridad

- **Credenciales**: Nunca hardcodear credenciales en el código
- **Acceso**: Solo usuarios autorizados (grupo "Secretaria") pueden ejecutar migraciones
- **Logs**: Todas las migraciones quedan registradas con usuario y timestamp
- **Validación**: Se valida la conexión antes de iniciar la migración

## 🐛 Solución de Problemas

### Error de Conexión
- Verificar host, puerto y credenciales
- Comprobar conectividad de red
- Revisar configuración del firewall

### Error de Permisos
- Asegurar que el usuario tenga permisos de lectura en todas las tablas
- Verificar que el usuario Django pertenezca al grupo "Secretaria"

### Migración Incompleta
- Revisar logs en el modelo MigracionLog
- Verificar espacio en disco
- Comprobar límites de memoria

## 📈 Monitoreo y Mantenimiento

### Logs de Sistema
Los logs se almacenan en:
- Modelo `MigracionLog` para historial de migraciones
- Logs de Django para errores técnicos

### Limpieza de Datos
Para limpiar datos antiguos:
```python
# Eliminar migraciones anteriores a una fecha
MigracionLog.objects.filter(fecha_inicio__lt='2024-01-01').delete()

# Eliminar datos de tablas específicas
DatoArchivadoDinamico.objects.filter(tabla_origen='tabla_antigua').delete()
```

## 🤝 Contribución

Para contribuir al desarrollo:
1. Fork del repositorio
2. Crear rama para nueva funcionalidad
3. Implementar cambios con tests
4. Enviar pull request

## 📄 Licencia

Este módulo es parte del sistema de gestión académica y sigue la misma licencia del proyecto principal.