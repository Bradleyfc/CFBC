# Documentación Completa: Sistema de Escalabilidad, Rendimiento y Tareas Asíncronas

## Índice
1. [Introducción](#introducción)
2. [Sistema de Escalabilidad Automática](#sistema-de-escalabilidad-automática)
3. [Sistema de Tareas Asíncronas (Celery)](#sistema-de-tareas-asíncronas-celery)
4. [Monitorización en Django Admin](#monitorización-en-django-admin)
5. [Configuración y Arquitectura](#configuración-y-arquitectura)
6. [Cómo Usar Cada Componente](#cómo-usar-cada-componente)
7. [Ejemplos de Uso](#ejemplos-de-uso)
8. [Mantenimiento y Monitoreo](#mantenimiento-y-monitoreo)
9. [Solución de Problemas](#solución-de-problemas)

---

## Introducción

Has implementado un sistema completo de **escalabilidad, rendimiento y procesamiento asíncrono** en tu aplicación Django CFBC. Este sistema está compuesto por:

### Componentes Principales

1. **Auto-Escalado Automático** - Ajusta dinámicamente el número de instancias según la carga
2. **Sistema de Tareas Asíncronas** - Procesa trabajos pesados fuera de las peticiones web
3. **Monitorización en Tiempo Real** - Interfaz visual en Django Admin para monitorear todo
4. **Balanceo de Carga** - Distribuye tráfico entre múltiples instancias
5. **Caché Distribuido** - Redis para sesiones y caché
6. **Programación de Tareas** - Ejecución automática de tareas periódicas

### ¿Por qué se Implementó Esto?

- **Mejorar la experiencia de usuario**: Las tareas largas no bloquean las peticiones web
- **Escalabilidad horizontal**: Puedes manejar miles de usuarios concurrentes
- **Alta disponibilidad**: El sistema se ajusta automáticamente a la carga
- **Monitorización proactiva**: Ves problemas antes de que afecten a los usuarios
- **Mantenimiento automatizado**: Tareas de limpieza, backups, etc. se ejecutan automáticamente

---

## Sistema de Escalabilidad Automática

### ¿Qué es?

Un sistema que **monitorea automáticamente** la carga de tu aplicación y **ajusta el número de instancias** (servidores) según sea necesario.

### ¿Cómo Funciona?

```
[Usuarios] → [Balanceador Nginx] → [Instancias Django (2-8)] → [Base de Datos]
                 ↑
       [Auto-Escalador] ← [Métricas en tiempo real]
```

### Métricas Monitoreadas

| Métrica | Umbral Escalar ↑ | Umbral Escalar ↓ | ¿Qué Mide? |
|---------|-----------------|-----------------|------------|
| **Uso de CPU** | > 70% | < 30% | Carga del procesador |
| **Uso de Memoria** | > 75% | < 40% | Consumo de RAM |
| **Tasa de Peticiones** | > 50 req/s | < 10 req/s | Peticiones por segundo |
| **Tiempo de Respuesta P95** | > 1 segundo | < 0.3 segundos | 95% de respuestas más rápidas |
| **Cola Nginx** | > 10 peticiones | < 3 peticiones | Peticiones esperando |

### Configuración Actual

```python
# En cfbc/settings.py
AUTOSCALER_CONFIG = {
    'min_instances': 2,      # Mínimo de instancias
    'max_instances': 8,      # Máximo de instancias
    'scale_up_threshold_cpu': 70.0,
    'scale_down_threshold_cpu': 30.0,
    # ... otros umbrales
}
```

### Comandos de Control

```bash
# Estado del auto-escalador
python manage.py autoscale --status

# Ejecutar una evaluación (sin cambios)
python manage.py autoscale --once --dry-run

# Ejecutar continuamente (cada 60s)
python manage.py autoscale --interval 60

# Control manual de instancias
./deploy/scripts/scale_instances.sh docker status
./deploy/scripts/scale_instances.sh docker set 4  # 4 instancias
```

---

## Sistema de Tareas Asíncronas (Celery)

### ¿Qué es Celery?

**Celery** es un sistema de **cola de tareas distribuido** que permite ejecutar trabajos pesados de forma asíncrona.

### Arquitectura

```
[Aplicación Django] → [Redis (Broker)] → [Workers Celery] → [Resultados]
       ↑                    ↑                    ↑
  Envía tareas          Mensajes de         Procesan tareas
                     cola (JSON/Redis)    en segundo plano
```

### Componentes de Celery

1. **Broker (Redis)**: Almacena las tareas en cola
2. **Workers**: Procesan las tareas
3. **Beat**: Programa tareas periódicas
4. **Flower**: Monitorización web
5. **Result Backend**: Almacena resultados

### Colas Implementadas

| Cola | Prioridad | Descripción | Ejemplos de Tareas |
|------|-----------|-------------|-------------------|
| **email** | 1 (Alta) | Envío de emails | Bienvenida, notificaciones |
| **file_processing** | 2 | Procesamiento de archivos | Subir documentos, extraer metadatos |
| **reports** | 3 | Generación de reportes | Estadísticas, reportes PDF |
| **default** | 5 | Tareas generales | Tareas varias |
| **backup** | 4 | Copias de seguridad | Backup de datos |
| **maintenance** | 6 (Baja) | Mantenimiento | Limpieza, optimización |

### Tareas Disponibles

#### Blog (`blog/tasks.py`)
- `send_welcome_email(user_id)` - Email de bienvenida
- `send_comment_notification(comment_id)` - Notificación de comentarios
- `generate_blog_statistics_report()` - Reporte de estadísticas

#### Documentos del Curso (`course_documents/tasks.py`)
- `process_uploaded_document(document_id)` - Procesar documentos subidos
- `send_document_notification(document_id)` - Notificar nuevo documento
- `generate_folder_report(folder_id)` - Generar reporte de carpeta
- `cleanup_old_documents(days_old)` - Limpiar documentos antiguos

---

## Monitorización en Django Admin

### Secciones Nuevas en el Admin

#### 1. 🐍 Colas de Tareas (`Task Management` → `Colas de Tareas`)

**¿Qué muestra?**
- Estado en tiempo real de todas las colas Celery
- Cantidad de tareas pendientes en cada cola
- Prioridad y descripción de cada cola

**Estados posibles:**
- ✅ **Vacía**: 0 tareas pendientes
- 🔵 **Normal**: 1-9 tareas pendientes
- 🟡 **Ocupada**: 10-49 tareas pendientes
- 🔴 **Congestionada**: 50+ tareas pendientes
- ⚫ **Error**: No se puede conectar a Redis

#### 2. ⚙️ Trabajadores Celery (`Task Management` → `Trabajadores Celery`)

**¿Qué muestra?**
- Estado de todos los workers Celery (Online/Offline)
- Tareas activas en cada worker
- Tareas reservadas y programadas
- Estadísticas de procesamiento (total procesado)
- Tamaño del pool de workers
- Carga del sistema (loadavg)

**Campos importantes:**
- `active_tasks`: Tareas ejecutándose ahora
- `total_processed`: Total de tareas completadas
- `pool_size`: Número máximo de tareas concurrentes
- `queues`: Colas que atiende este worker

#### 3. 📊 Celery Results (`Celery results` → `Task results`)

**¿Qué registra?**
- **Historial completo** de todas las tareas ejecutadas
- **Estado** de cada tarea (SUCCESS, FAILURE, PENDING, etc.)
- **Argumentos** y **resultados** de cada tarea
- **Trazas de error** si falló
- **Tiempos** de inicio y fin

**Estados de tareas:**
- 🟢 **SUCCESS**: Completada exitosamente
- 🔴 **FAILURE**: Falló con error
- 🟡 **PENDING**: Esperando en cola
- 🔵 **STARTED**: Ejecutándose ahora
- 🟣 **RETRY**: Reintentando después de fallo
- ⚫ **REVOKED**: Cancelada manualmente

#### 4. ⏰ Tareas Periódicas (`Django Celery Beat`)

**¿Qué permite hacer?**
- Programar tareas que se ejecuten automáticamente
- Diferentes tipos de programación:
  - **Cron**: Ejecutar en momentos específicos (ej: todos los días a las 2 AM)
  - **Intervalos**: Ejecutar cada X segundos/minutos/horas
  - **Crontabs**: Expresiones cron complejas
  - **Eventos Solares**: Ejecutar al amanecer/atardecer

**Modelos disponibles:**
- **Periodic tasks**: Tareas periódicas
- **Crontabs**: Programación tipo cron
- **Intervals**: Intervalos de tiempo
- **Solar events**: Eventos solares
- **Clocked**: Ejecutar en fecha/hora específica

---

## Configuración y Arquitectura

### Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    Usuarios / Clientes                       │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Balanceador de Carga (Nginx)                │
│                    • Distribuye tráfico                      │
│                    • Health checks                           │
│                    • SSL termination                         │
└──────────────┬──────────────┬──────────────┬────────────────┘
               ▼              ▼              ▼
┌──────────────┴─────┐┌──────┴──────┐┌──────┴──────┐
│  Instancia Django 1││ Instancia 2 ││ Instancia N │
│  • App Django      ││ • App Django││ • App Django│
│  • Gunicorn        ││ • Gunicorn  ││ • Gunicorn  │
└─────────┬──────────┘└──────┬──────┘└──────┬──────┘
          │                  │              │
          └──────────────────┼──────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis (Cache/Broker)                      │
│  • DB 1: Cache general        • DB 3: Celery broker         │
│  • DB 2: Sesiones             • DB 4: Celery results        │
└──────────────┬──────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Base de Datos (PostgreSQL)                   │
│  • Datos principales          • Réplica de lectura (opcional)│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Sistema de Monitoreo (Paralelo)               │
│  • Auto-Escalador             • Flower (monitor Celery)     │
│  • Métricas Redis             • Django Admin                │
└─────────────────────────────────────────────────────────────┘
```

### Configuración de Redis

```python
# En cfbc/settings.py
CACHES = {
    'default': {  # DB 1 - Cache general
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,  # 5 minutos
    },
    'session': {  # DB 2 - Sesiones
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 86400,  # 24 horas
    },
}

# Celery usa:
# DB 3: Broker (cola de mensajes)
# DB 4: Resultados de tareas
```

### Configuración de Celery

```python
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/3'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/4'
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos máximo
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutos límite suave
```

---

## Cómo Usar Cada Componente

### 1. Enviar Tareas Asíncronas

```python
# En cualquier vista o modelo de Django
from blog.tasks import send_welcome_email
from course_documents.tasks import process_uploaded_document

# Enviar email de bienvenida (se ejecuta en segundo plano)
send_welcome_email.delay(user.id)

# Procesar documento subido
process_uploaded_document.delay(document_id)

# Con seguimiento de resultado
result = send_welcome_email.delay(user.id)
task_id = result.id  # Guardar para monitorear

# Verificar si terminó
if result.ready():
    print(f"Resultado: {result.result}")
```

### 2. Programar Tareas Periódicas

**Desde Django Admin:**
1. Ir a `Django Celery Beat` → `Periodic tasks`
2. Click en `ADD PERIODIC TASK`
3. Configurar:
   - **Name**: Nombre descriptivo
   - **Task**: Seleccionar tarea (ej: `blog.tasks.send_welcome_email`)
   - **Schedule**: Tipo de programación (Crontab, Interval, etc.)
   - **Arguments**: Argumentos para la tarea (en formato JSON)
   - **Enabled**: Activar/desactivar

**Ejemplo de Crontab:** `0 2 * * *` = Todos los días a las 2 AM

### 3. Monitorear el Sistema

**Django Admin:**
- `/admin/task_management/taskqueue/` - Estado de colas
- `/admin/task_management/taskworker/` - Estado de workers
- `/admin/django_celery_results/taskresult/` - Historial de tareas
- `/admin/django_celery_beat/periodictask/` - Tareas programadas

**Flower (Monitor Celery):**
```bash
celery -A cfbc flower
```
Acceder en: http://localhost:5555

### 4. Controlar Auto-Escalado

**Modo Automático:**
```bash
# Iniciar auto-escalador
python manage.py autoscale --interval 60

# Ver logs
tail -f logs/autoscale.log
```

**Modo Manual:**
```bash
# Ver estado
python manage.py autoscale --status

# Escalar a 4 instancias
./deploy/scripts/scale_instances.sh docker set 4

# Verificar health
curl http://localhost:8001/health/
curl http://localhost:8002/health/
```

---

## Ejemplos de Uso

### Caso 1: Notificación Masiva de Nuevo Documento

```python
# En views.py de course_documents
def upload_document(request, folder_id):
    # 1. Guardar documento (sincrónico)
    document = CourseDocument.objects.create(...)
    
    # 2. Procesar en segundo plano (asíncrono)
    from course_documents.tasks import (
        process_uploaded_document,
        send_document_notification
    )
    
    # Procesar documento (extraer metadatos, crear thumbnail)
    process_uploaded_document.delay(document.id)
    
    # Notificar a todos los estudiantes
    send_document_notification.delay(document.id)
    
    # 3. Responder inmediatamente al usuario
    return HttpResponse("Documento subido. Se procesará en segundo plano.")
```

### Caso 2: Reporte Semanal Automático

**Configurar en Django Admin:**
- **Task**: `course_documents.tasks.generate_performance_report`
- **Schedule**: Crontab `0 8 * * 1` (Lunes a las 8 AM)
- **Arguments**: `{"start_date": "auto", "end_date": "auto"}`
- **Enabled**: Sí

**Resultado:** Todos los lunes a las 8 AM se generará y enviará automáticamente un reporte de desempeño.

### Caso 3: Escalado para Evento Especial

```bash
# 1. Antes del evento, escalar manualmente
./deploy/scripts/scale_instances.sh docker set 8

# 2. Durante el evento, monitorear
python manage.py autoscale --status

# 3. Después del evento, volver a automático
python manage.py autoscale --interval 60
```

---

## Mantenimiento y Monitoreo

### Chequeos Diarios

1. **Estado de Colas:**
   - Verificar que no haya colas congestionadas
   - Revisar tareas fallidas en `Task results`

2. **Estado de Workers:**
   - Confirmar que todos los workers están `Online`
   - Verificar carga de workers (`loadavg` < 2.0)

3. **Auto-Escalador:**
   - Revisar logs: `tail -f logs/autoscale.log`
   - Verificar métricas actuales

4. **Redis:**
   - Verificar conexión: `redis-cli ping`
   - Monitorear uso de memoria

### Tareas de Mantenimiento Programadas

| Tarea | Frecuencia | Qué Hace |
|-------|------------|----------|
| **Limpieza de documentos antiguos** | Semanal | Elimina registros de acceso > 90 días |
| **Backup de metadatos** | Diario | Copia de seguridad de documentos |
| **Optimización de base de datos** | Mensual | VACUUM, REINDEX |
| **Limpieza de resultados Celery** | Diario | Elimina resultados > 30 días |

### Alertas Recomendadas

Configurar alertas para:
- Colas con > 100 tareas pendientes
- Workers offline por > 5 minutos
- Uso de CPU > 80% por > 10 minutos
- Tareas fallidas consecutivas
- Redis sin conexión

---

## Solución de Problemas

### Problema Común 1: Tareas No se Ejecutan

**Síntomas:**
- Tareas quedan en estado `PENDING`
- Colas muestran tareas pero no se procesan

**Solución:**
```bash
# 1. Verificar workers
celery -A cfbc inspect active

# 2. Verificar conexión Redis
redis-cli ping
redis-cli -n 3 llen default  # Ver cola 'default'

# 3. Reiniciar workers
pkill -f "celery worker"
celery -A cfbc worker -l info --concurrency=4

# 4. Si persiste, purgar colas (cuidado!)
celery -A cfbc purge
```

### Problema Común 2: Auto-Escalador No Funciona

**Síntomas:**
- Alta carga pero no se crean nuevas instancias
- `python manage.py autoscale --status` muestra errores

**Solución:**
```bash
# 1. Verificar logs
tail -f logs/autoscale.log

# 2. Verificar métricas
python manage.py shell -c "
from cfbc.autoscaler import create_default_scaler
scaler = create_default_scaler()
print(scaler.metrics_collector.collect_all_metrics())
"

# 3. Ejecutar manualmente
python manage.py autoscale --once --dry-run
```

### Problema Común 3: Redis con Alta Memoria

**Síntomas:**
- Redis usa > 80% de memoria
- Lentitud en cache y tareas

**Solución:**
```bash
# 1. Verificar uso
redis-cli info memory

# 2. Limpiar resultados viejos de Celery
python manage.py shell -c "
from django_celery_results.models import TaskResult
from datetime import datetime, timedelta
old_date = datetime.now() - timedelta(days=30)
TaskResult.objects.filter(date_done__lt=old_date).delete()
print('Resultados antiguos eliminados')
"

# 3. Limpiar cache
redis-cli -n 1 FLUSHDB  # CUIDADO: Borra todo el cache
```

### Problema Común 4: Workers Mueren Frecuentemente

**Síntomas:**
- Workers aparecen y desaparecen
- Tareas se pierden o fallan

**Solución:**
```bash
# 1. Reducir concurrencia
celery -A cfbc worker -l info --concurrency=2

# 2. Aumentar límites de memoria
# En settings.py:
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100  # Reiniciar después de 100 tareas
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 200000  # 200MB

# 3. Usar supervisord para reinicio automático
```

---

## Glosario de Términos

| Término | Significado |
|---------|-------------|
| **Broker** | Sistema de mensajería (Redis) que maneja las colas |
| **Worker** | Proceso que ejecuta tareas de la cola |
| **Queue** | Cola de tareas pendientes |
| **Task** | Unidad de trabajo asíncrono |
| **Beat** | Programador de tareas periódicas |
| **Concurrency** | Número de tareas que un worker puede ejecutar simultáneamente |
| **Auto-scaling** | Ajuste automático de instancias según carga |
| **Load balancing** | Distribución de tráfico entre múltiples instancias |
| **Health check** | Verificación de que un servicio está funcionando |
| **P95 response time** | Tiempo en que el 95% de las peticiones son más rápidas |

---

## Recursos y Enlaces

### Documentación del Proyecto
- `docs/auto_scaling.md` - Sistema de auto-escalado
- `docs/celery_setup.md` - Configuración de Celery
- `docs/database_scaling.md` - Escalado de base de datos
- `docs/load_balancer.md` - Balanceador de carga

### Comandos Útiles
```bash
# Monitoreo general
./deploy/scripts/scale_instances.sh docker status
celery -A cfbc inspect stats

# Logs
tail -f logs/autoscale.log
tail -f logs/celery.log

# Pruebas
python manage.py test_celery_tasks --task-type=all
python manage.py autoscale --once --dry-run
```

### Enlaces Externos
- [Documentación Celery](https://docs.celeryq.dev/)
- [Documentación django-celery-beat](https://django-celery-beat.readthedocs.io/)
- [Documentación django-celery-results](https://django-celery-results.readthedocs.io/)
- [Documentación Redis](https://redis.io/documentation)

---

## Conclusión

Has implementado un sistema **profesional y escalable** que incluye:

✅ **Procesamiento asíncrono** para tareas pesadas  
✅ **Auto-escalado automático** según la carga  
✅ **Monitorización en tiempo real** desde Django Admin  
✅ **Programación de tareas** periódicas automáticas  
✅ **Alta disponibilidad** con múltiples instancias  
✅ **Balanceo de carga** inteligente  

Este sistema te permite:
- Manejar **miles de usuarios concurrentes**
- Procesar **tareas largas sin bloquear la app**
- **Escalar automáticamente** durante picos de tráfico
- **Monitorear todo** desde una interfaz familiar (Django Admin)
- **Automatizar mantenimiento** y reportes

**¡Tu aplicación está lista para producción a gran escala!** 🚀