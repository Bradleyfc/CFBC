# Guía Completa: Cómo Funciona la Activación Automática del Sistema

## 🎯 **Respuesta Clara: ¿Qué se Activa Solo y Qué No?**

### **LO QUE SÍ SE ACTIVA SOLO** (Sin que hagas nada extra)
1. ✅ **Redis Cache** - Si Redis está instalado, Django lo usa automáticamente
2. ✅ **Sesiones en Redis** - Configurado en `settings.py`, funciona solo
3. ✅ **Celery Workers** - Si están corriendo, procesan tareas automáticamente
4. ✅ **Monitorización Django Admin** - Siempre disponible en `/admin/`
5. ✅ **Health Checks** - Verifican que los servicios estén vivos

### **LO QUE NO SE ACTIVA SOLO** (Tú debes activarlo/configurarlo)
1. ❌ **Auto-Scaling** - NO se activa automáticamente
2. ❌ **Múltiples instancias** - NO se crean solas
3. ❌ **Load Balancing** - NO se configura solo
4. ❌ **Docker/Contenedores** - NO se levantan solos
5. ❌ **Servicios del sistema** - NO arrancan solos al inicio

---

## 🔄 **CÓMO FUNCIONA REALMENTE LA "ACTIVACIÓN AUTOMÁTICA"**

### **Escenario 1: Sin Docker (VPS Tradicional)**
```
Tú activas manualmente → [Gunicorn + Django] → Funciona
                          ↑
                   [Celery Worker] (tú activas)
```

**Tú activas manualmente:**
- Gunicorn (servidor Django)
- Celery Worker
- Redis
- PostgreSQL
- Nginx

**Se activa automáticamente DESPUÉS:**
- Cache Redis (una vez Redis está corriendo)
- Sesiones Redis (una vez Redis está corriendo)
- Procesamiento de tareas (una vez Celery está corriendo)

### **Escenario 2: Con Docker Compose**
```bash
# Tú ejecutas MANUALMENTE:
docker-compose up -d  # ← TÚ ACTIVAS

# Se levantan AUTOMÁTICAMENTE:
- Contenedor Django (app)
- Contenedor Celery (worker) 
- Contenedor Redis
- Contenedor PostgreSQL
- Contenedor Nginx
```

**Tú activas:** El comando `docker-compose up` (una vez)

**Luego es automático:**
- Si un contenedor se cae, se reinicia solo (con `restart: always`)
- Health checks verifican estado
- Los contenedores se comunican automáticamente

### **Escenario 3: Con Auto-Scaling (cuando se necesita)**
```bash
# El auto-scaling NO se activa solo inicialmente
# Tú DEBES ejecutar UNA VEZ:
python manage.py autoscale --interval 60  # ← TÚ ACTIVAS

# Luego él monitorea AUTOMÁTICAMENTE y SI detecta carga alta:
if cpu > 70% and memory > 75%:
    crear_nueva_instancia()  # ← ESTO SÍ es automático (después de activado)
```

---

## 🛠️ **CONFIGURACIÓN PARA QUE "SE ACTIVE CUANDO HAGA FALTA"**

### **La CLAVE: Systemd Services (Inicio Automático)**

**Esto SÍ se puede configurar para que inicie automáticamente al prender el servidor:**

### **Paso 1: Crear Servicios Systemd**

#### **1. Servicio Django (Gunicorn)**
```bash
# /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for CFBC Django
After=network.target postgresql.service redis.service

[Service]
User=django
Group=www-data
WorkingDirectory=/var/www/cfbc
Environment="PATH=/var/www/cfbc/venv/bin"
ExecStart=/var/www/cfbc/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/var/www/cfbc/cfbc.sock \
          cfbc.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### **2. Servicio Celery Worker**
```bash
# /etc/systemd/system/celery.service
[Unit]
Description=Celery Service for CFBC
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=django
Group=www-data
WorkingDirectory=/var/www/cfbc
Environment="PATH=/var/www/cfbc/venv/bin"
ExecStart=/var/www/cfbc/venv/bin/celery -A cfbc worker -l info --concurrency=2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### **3. Servicio Celery Beat (Tareas Programadas)**
```bash
# /etc/systemd/system/celery-beat.service
[Unit]
Description=Celery Beat Service for CFBC
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=django
Group=www-data
WorkingDirectory=/var/www/cfbc
Environment="PATH=/var/www/cfbc/venv/bin"
ExecStart=/var/www/cfbc/venv/bin/celery -A cfbc beat -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### **4. Servicio Auto-Scaling (CRÍTICO)**
```bash
# /etc/systemd/system/autoscale.service
[Unit]
Description=Auto-Scaling Service for CFBC
After=network.target gunicorn.service docker.service

[Service]
Type=simple
User=django
WorkingDirectory=/var/www/cfbc
Environment="PATH=/var/www/cfbc/venv/bin"
ExecStart=/var/www/cfbc/venv/bin/python manage.py autoscale --interval 60
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **Paso 2: Habilitar Servicios al Inicio**
```bash
# Estos comandos hacen que SE ACTIVEN SOLOS al prender el servidor:
sudo systemctl enable gunicorn      # Django
sudo systemctl enable celery        # Celery Worker  
sudo systemctl enable celery-beat   # Tareas programadas
sudo systemctl enable autoscale     # Auto-scaling
sudo systemctl enable redis         # Redis
sudo systemctl enable postgresql    # PostgreSQL
sudo systemctl enable nginx         # Web server
sudo systemctl enable docker        # Docker (si lo usas)
```

### **Paso 3: Iniciar Servicios Ahora**
```bash
# Iniciar todo ahora (no esperar a reiniciar):
sudo systemctl start gunicorn celery celery-beat autoscale
```

---

## 🐳 **OPCIÓN DOCKER: Configuración con Auto-Restart**

### **docker-compose.prod.yml con Configuración Automática**
```yaml
version: '3.8'

services:
  app:
    build: .
    image: cfbc-app:latest
    restart: always  # ← SE REINICIA SOLO si se cae
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  celery:
    build: .
    image: cfbc-app:latest
    command: celery -A cfbc worker -l info --concurrency=2
    restart: always  # ← SE REINICIA SOLO
    depends_on:
      - app
  
  celery-beat:
    build: .
    image: cfbc-app:latest
    command: celery -A cfbc beat -l info
    restart: always  # ← SE REINICIA SOLO
    depends_on:
      - app
  
  autoscale:
    build: .
    image: cfbc-app:latest
    command: python manage.py autoscale --interval 60
    restart: always  # ← SE REINICIA SOLO
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Para crear instancias
    depends_on:
      - app
  
  nginx:
    image: nginx:alpine
    restart: always  # ← SE REINICIA SOLO
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
```

### **Iniciar Todo con Docker Compose**
```bash
# Esto activa TODO de una vez:
docker-compose -f docker-compose.prod.yml up -d

# Con esto:
# - Todos los servicios arrancan
# - Si algo se cae, se reinicia automáticamente
# - Health checks verifican estado
# - Auto-scaler monitorea constantemente
```

---

## ⚡ **CÓMO FUNCIONA EL AUTO-SCALING "CUANDO HACE FALTA"**

### **Flujo Completo del Auto-Scaling:**

```python
# 1. Tú activas el auto-scaler (una vez)
# python manage.py autoscale --interval 60

# 2. Cada 60 segundos, él AUTOMÁTICAMENTE:
while True:
    # a. Recolecta métricas
    cpu = get_cpu_usage()      # Ej: 85%
    memory = get_memory_usage() # Ej: 78%
    requests = get_request_rate() # Ej: 120 req/min
    
    # b. Decide si hacer algo
    if cpu > 70 and memory > 75:
        # ¡HAY CARGA ALTA! Necesita más capacidad
        scale_up()  # ← Esto SÍ es automático
        
    elif cpu < 30 and memory < 40:
        # SOBRA CAPACIDAD
        scale_down()  # ← Esto SÍ es automático
    
    # c. Espera 60 segundos y repite
    sleep(60)
```

### **Ejemplo Práctico de Activación Automática:**

#### **8:00 AM - Situación Normal**
```
Usuarios: 15
CPU: 35%
Memoria: 45%
Instancias: 1
Auto-Scaler: "Todo normal, sigo monitoreando"
```

#### **9:00 AM - Pico de Tráfico (muchos usuarios entran)**
```
Usuarios: 150  ← ¡AUMENTÓ!
CPU: 82%       ← ¡ALTO!
Memoria: 79%   ← ¡ALTO!
Instancias: 1
Auto-Scaler: "¡DETECTO CARGA ALTA!"
            → EJECUTA: crear_nueva_instancia()
            → RESULTADO: Ahora hay 2 instancias
```

#### **9:05 AM - Con Nueva Instancia**
```
Usuarios: 150
CPU: 45%       ← ¡MEJORÓ! (se reparte carga)
Memoria: 50%   ← ¡MEJORÓ!
Instancias: 2
Auto-Scaler: "Carga manejable, sigo monitoreando"
```

#### **11:00 AM - Tráfico Baja**
```
Usuarios: 30
CPU: 25%       ← MUY BAJO
Memoria: 35%   ← MUY BAJO  
Instancias: 2
Auto-Scaler: "SOBRA CAPACIDAD"
            → EJECUTA: eliminar_instancia()
            → RESULTADO: Vuelve a 1 instancia
```

---

## 🎮 **DEMOSTRACIÓN: Cómo se "Activa Cuando Hace Falta"**

### **Configuración Inicial (Tú haces esto UNA VEZ):**
```bash
# 1. Configurar servicios systemd
sudo cp *.service /etc/systemd/system/

# 2. Habilitar al inicio
sudo systemctl enable gunicorn celery celery-beat autoscale

# 3. Iniciar ahora
sudo systemctl start gunicorn celery celery-beat autoscale
```

### **Lo que Pasa DESPUÉS (Automáticamente):**

#### **Cuando se Prende el Servidor:**
1. ✅ **Systemd inicia automáticamente** todos los servicios habilitados
2. ✅ **Gunicorn arranca solo** - Aplicación Django lista
3. ✅ **Celery arranca solo** - Workers para tareas
4. ✅ **Auto-scaler arranca solo** - Comienza a monitorear
5. ✅ **Redis arranca solo** - Cache y sesiones funcionan

#### **Durante Operación Normal:**
1. ✅ **Auto-scaler monitorea constantemente** (cada 60s)
2. ✅ **Si un servicio se cae**, systemd lo reinicia automáticamente
3. ✅ **Health checks** verifican que todo esté bien
4. ✅ **Tareas programadas** se ejecutan a su hora

#### **Cuando hay Mucha Carga:**
1. ✅ **Auto-scaler detecta** CPU > 70%, memoria > 75%
2. ✅ **Crea nueva instancia automáticamente** usando Docker
3. ✅ **Configura load balancing** automáticamente
4. ✅ **Balancea tráfico** entre las instancias

#### **Cuando Carga Baja:**
1. ✅ **Auto-scaler detecta** CPU < 30%, memoria < 40%
2. ✅ **Elimina instancias sobrantes** automáticamente
3. ✅ **Ajusta configuración** del load balancer

---

## 📋 **CHECKLIST para Configurar la Activación Automática**

### **ANTES de Subir a Producción:**
- [ ] **Systemd services** creados y configurados
- [ ] **Servicios habilitados** al inicio (`systemctl enable`)
- [ ] **Auto-restart configurado** (`Restart=always`)
- [ ] **Health checks** implementados
- [ ] **Docker configurado** (si usas contenedores)
- [ ] **Variables de entorno** en lugar seguro

### **DESPUÉS de Subir:**
- [ ] **Verificar que servicios arrancan** al reiniciar servidor
- [ ] **Probar auto-scaling** con carga simulada
- [ ] **Verificar health checks** funcionan
- [ ] **Monitorear logs** de auto-scaler
- [ ] **Configurar alertas** (opcional)

### **PARA PROBAR la Activación Automática:**
```bash
# 1. Reiniciar servidor
sudo reboot

# 2. Verificar que todo arrancó solo
sudo systemctl status gunicorn celery autoscale

# 3. Probar con carga (simular muchos usuarios)
# Usar herramienta como wrk o ab
wrk -t10 -c100 -d30s http://tudominio.com/

# 4. Verificar que auto-scaler creó instancias
docker ps  # Si usas Docker
sudo systemctl status autoscale
```

---

## 🔧 **ARCHIVOS DE CONFIGURACIÓN COMPLETOS**

### **1. Sistema Tradicional (Systemd)**

#### **Archivo: /etc/systemd/system/autoscale.service**
```ini
[Unit]
Description=CFBC Auto-Scaling Service
Description=Monitors system metrics and scales instances automatically
After=network.target gunicorn.service docker.service
Requires=gunicorn.service docker.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=django
Group=www-data
WorkingDirectory=/var/www/cfbc
Environment="PATH=/var/www/cfbc/venv/bin"
EnvironmentFile=/var/www/cfbc/.env
ExecStart=/var/www/cfbc/venv/bin/python manage.py autoscale \
    --interval 60 \
    --min-instances 1 \
    --max-instances 8 \
    --mode docker

# Auto-restart configuration
Restart=always
RestartSec=10
StartLimitIntervalSec=0
StartLimitBurst=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cfbc-autoscaler

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

#### **Archivo: /etc/systemd/system/gunicorn.service**
```ini
[Unit]
Description=Gunicorn Django Server for CFBC
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
User=django
Group=www-data
WorkingDirectory=/var/www/cfbc
Environment="PATH=/var/www/cfbc/venv/bin"
EnvironmentFile=/var/www/cfbc/.env

ExecStart=/var/www/cfbc/venv/bin/gunicorn \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --keep-alive 5 \
    --bind unix:/var/www/cfbc/cfbc.sock \
    --access-logfile /var/log/cfbc/gunicorn-access.log \
    --error-logfile /var/log/cfbc/gunicorn-error.log \
    --capture-output \
    --log-level info \
    cfbc.wsgi:application

# Auto-restart
Restart=always
RestartSec=3

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

# Resource limits
LimitNOFILE=65535
LimitNPROC=65535

[Install]
WantedBy=multi-user.target
```

### **2. Sistema Docker (Compose)**

#### **Archivo: docker-compose.autoscale.yml**
```yaml
version: '3.8'

services:
  # Aplicación principal
  cfbc-app:
    build: .
    image: cfbc-app:latest
    container_name: cfbc-app-1
    restart: unless-stopped
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DB_HOST=postgres
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - cfbc-network
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
      - "traefik.enable=true"
      - "traefik.http.routers.cfbc.rule=Host(`tudominio.com`)"
    
  # Auto-scaler (el que activa nuevas instancias)
  autoscaler:
    build: .
    image: cfbc-app:latest
    container_name: cfbc-autoscaler
    restart: unless-stopped
    command: python manage.py autoscale --interval 60
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./logs/autoscale:/var/www/cfbc/logs
    depends_on:
      - cfbc-app
    networks:
      - cfbc-network
    
  # Load balancer
  traefik:
    image: traefik:v2.10
    container_name: cfbc-traefik
    restart: unless-stopped
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=admin@tudominio.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    networks:
      - cfbc-network

networks:
  cfbc-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  letsencrypt:
```

#### **Script: deploy/auto-scaling-init.sh**
```bash
#!/bin/bash
# Script para inicializar auto-scaling automático
# Ejecutar UNA VEZ al desplegar

set -e

echo "🔧 Configurando activación automática del sistema..."

# 1. Crear directorio de logs
mkdir -p /var/log/cfbc
chown -R django:django /var/log/cfbc

# 2. Copiar servicios systemd
cp deploy/systemd/*.service /etc/systemd/system/

# 3. Recargar systemd
systemctl daemon-reload

# 4. Habilitar servicios al inicio
echo "🔄 Habilitando servicios al inicio..."
systemctl enable cfbc-gunicorn
systemctl enable cfbc-celery
systemctl enable cfbc-celery-beat
systemctl enable cfbc-autoscale
systemctl enable postgresql redis nginx docker

# 5. Iniciar servicios ahora
echo "🚀 Iniciando servicios..."
systemctl start cfbc-gunicorn
systemctl start cfbc-celery
systemctl start cfbc-celery-beat
systemctl start cfbc-autoscale

# 6. Verificar estado
echo "✅ Verificando estado..."
systemctl status cfbc-gunicorn cfbc-celery cfbc-autoscale --no-pager

# 7. Configurar crontab para monitoreo
echo "📊 Configurando monitoreo automático..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/bin/curl -s http://localhost:8000/health/ > /dev/null") | crontab -

echo "🎉 Configuración completada!"
echo "El sistema se activará automáticamente:"
echo "- Al prender el servidor"
echo "- Cuando detecte carga alta"
echo "- Si un servicio se cae"
echo ""
echo "Comandos útiles:"
echo "  Ver logs: journalctl -u cfbc-autoscale -f"
echo "  Ver estado: systemctl status cfbc-*"
echo "  Ver contenedores: docker ps"
```

---

## 🚨 **SOLUCIÓN DE PROBLEMAS COMUNES**

### **Problema: "Los servicios no arrancan automáticamente"**
```bash
# Solución:
# 1. Verificar que están habilitados
systemctl list-unit-files | grep enabled | grep cfbc

# 2. Verificar dependencias
systemctl status postgresql redis docker

# 3. Verificar logs
journalctl -u cfbc-gunicorn --since "10 minutes ago"

# 4. Verificar permisos
ls -la /var/www/cfbc/cfbc.sock
```

### **Problema: "Auto-scaler no crea instancias cuando hay carga"**
```bash
# Solución:
# 1. Verificar que está corriendo
systemctl status cfbc-autoscale

# 2. Verificar métricas
curl http://localhost:8000/metrics/  # Si tienes endpoint

# 3. Verificar configuración
cat /var/www/cfbc/.env | grep SCALE

# 4. Probar manualmente
python manage.py autoscale --once --dry-run
```

### **Problema: "Instancias no se eliminan cuando sobra capacidad"**
```bash
# Solución:
# 1. Verificar umbrales de scale-down
# En settings.py o .env:
# SCALE_DOWN_THRESHOLD_CPU=30
# SCALE_DOWN_THRESHOLD_MEMORY=40

# 2. Verificar cooldown period
# COOLDOWN_PERIOD_SCALE_DOWN=300 (5 minutos)

# 3. Forzar scale-down
python manage.py autoscale --scale-down --force
```

### **Problema: "Health checks fallan"**
```bash
# Solución:
# 1. Verificar endpoint health
curl -f http://localhost:8000/health/

# 2. Verificar dependencias
curl http://localhost:8000/health/db/
curl http://localhost:8000/health/redis/

# 3. Ajustar timeout en healthcheck
# En docker-compose o systemd service
```

---

## 📊 **MONITOREO de la Activación Automática**

### **Comandos para Verificar que Todo es Automático:**
```bash
# 1. Ver estado de todos los servicios
systemctl list-units --type=service --state=running | grep cfbc

# 2. Ver logs del auto-scaler (en tiempo real)
journalctl -u cfbc-autoscale -f

# 3. Ver eventos de scaling
tail -f /var/log/cfbc/autoscale.log

# 4. Ver uso de recursos
htop
docker stats  # Si usas Docker

# 5. Ver métricas de la aplicación
curl http://localhost:8000/metrics/  # Si tienes endpoint
```

### **Dashboard Simple para Monitorear:**
```bash
# Crear script de monitoreo
cat > /usr/local/bin/monitor-cfbc.sh << 'EOF'
#!/bin/bash
echo "=== CFBC Auto-Scaling Monitor ==="
echo "Hora: $(date)"
echo ""
echo "1. Servicios Systemd:"
systemctl status cfbc-gunicorn cfbc-celery cfbc-autoscale --no-pager | grep -A1 "Active:"
echo ""
echo "2. Contenedores Docker:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep cfbc
echo ""
echo "3. Métricas del Sistema:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "Memoria: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo ""
echo "4. Últimos Eventos de Scaling:"
tail -5 /var/log/cfbc/autoscale.log 2>/dev/null || echo "No hay logs aún"
EOF

chmod +x /usr/local/bin/monitor-cfbc.sh

# Ejecutar cada 5 minutos
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-cfbc.sh >> /var/log/cfbc/monitor.log") | crontab -
```

---

## 🎯 **RESUMEN FINAL: Lo que es REALMENTE Automático**

### **Después de Configurar UNA VEZ:**

#### **Al Inicio del Servidor (Automático):**
1. ✅ **Systemd inicia** todos los servicios habilitados
2. ✅ **Django/Gunicorn** arranca solo
3. ✅ **Celery Workers** arrancan solos
4. ✅ **Auto-Scaler** arranca solo y comienza a monitorear
5. ✅ **Redis/PostgreSQL** arrancan solos

#### **Durante Operación (Automático):**
1. ✅ **Monitoreo constante** cada 60 segundos
2. ✅ **Creación de instancias** cuando CPU > 70%, memoria > 75%
3. ✅ **Eliminación de instancias** cuando CPU < 30%, memoria < 40%
4. ✅ **Reinicio de servicios** si se caen
5. ✅ **Health checks** constantes
6. ✅ **Balanceo de carga** entre instancias

#### **Lo que NO es Automático (Tú haces):**
1. ❌ **Configuración inicial** (una vez)
2. ❌ **Primer despliegue** (una vez)
3. ❌ **Actualizaciones de código** (pero puedes automatizar)
4. ❌ **Backups** (pero puedes programarlos)

### **Tu Ruta para Lograrlo:**

1. **Hoy:** Configurar servicios systemd con `Restart=always`
2. **Hoy:** Habilitar servicios al inicio (`systemctl enable`)
3. **Hoy:** Probar que todo arranca al reiniciar
4. **Mañana:** El sistema se activa solo cuando hace falta

### **Frase Clave para Recordar:**
**"Configuras UNA VEZ, funciona AUTOMÁTICAMENTE para SIEMPRE"**

El auto-scaling, los reinicios, la monitorización... todo funciona automáticamente **después de que tú hagas la configuración inicial**. Es como programar un robot: le das las instrucciones una vez, y luego él hace el trabajo automáticamente.

---

## 🆘 **Soporte Rápido**

### **Si algo NO se activa automáticamente:**
```bash
# 1. Verificar que el servicio está habilitado
systemctl is-enabled cfbc-autoscale

# 2. Verificar que está corriendo
systemctl is-active cfbc-autoscale

# 3. Verificar logs
journalctl -u cfbc-autoscale --since "today"

# 4. Reiniciar servicio
systemctl restart cfbc-autoscale

# 5. Si persiste, verificar configuración
cat /etc/systemd/system/cfbc-autoscale.service
```

### **Para probar QUE SÍ es automático:**
```bash
# 1. Detener servicio manualmente
systemctl stop cfbc-autoscale

# 2. Esperar 10 segundos (RestartSec=10)
sleep 10

# 3. Verificar que systemd lo reinició automáticamente
systemctl status cfbc-autoscale
# Debe decir: Active: active (running)
```

---

**Documentación práctica para activación automática**  
**CFBC - Centro Fray Bartolomé de las Casas**  
**Configuración: Una vez, funcionamiento: Automático para siempre**