# Guía Completa: Cómo Desplegar tu Aplicación en Internet

## 🎯 **¿Qué Pasará Cuando Subas a Internet?**

Cuando despliegues tu aplicación, **NO todo se activa automáticamente**. Tienes que configurar servicios específicos. Te explico qué se activa solo y qué necesitas configurar:

---

## 📊 **Resumen: Qué se Activa SOLO vs Qué Configuras TÚ**

### **Se Activa SOLO (Automático)**
1. **Redis Cache** - Funciona igual que en local
2. **Celery Workers** - Si los configuras, procesan tareas
3. **Django Admin** - Monitorización sigue igual
4. **Tareas programadas** - Si configuras Celery Beat

### **Necesitas Configurar TÚ**
1. **Servidor web** (Gunicorn/Nginx) - NO usa `runserver`
2. **Base de datos en la nube** - NO usa PostgreSQL local
3. **Variables de entorno** - Secretos, claves, configs
4. **Dominio y SSL** - HTTPS, nombre de dominio
5. **Servicios background** - Celery como servicio

---

## 🚀 **4 Opciones de Despliegue (de Simple a Avanzado)**

### **Opción 1: Despliegue Simple (VPS Básico)**
```
[Usuarios] → [Nginx] → [Gunicorn + Django] → [PostgreSQL]
                         ↑
                  [Celery Worker]
```

### **Opción 2: Despliegue con Docker (Recomendado)**
```
[Usuarios] → [Nginx] → [Contenedores Django] → [PostgreSQL Cloud]
                              ↑
                       [Contenedor Celery]
```

### **Opción 3: Plataforma como Servicio (PaaS)**
```
[Usuarios] → [Railway/Heroku/Render] → [Base de datos]
                  (Todo gestionado)
```

### **Opción 4: Escalable (Cloud Avanzado)**
```
[Usuarios] → [Load Balancer] → [Auto-Scaling] → [Contenedores] → [BD Cluster]
```

---

## 📋 **Checklist PREVIO al Despliegue**

### **1. Preparar el Código**
```python
# settings.py - Asegurar estas configuraciones:
DEBUG = False  # ✅ CRÍTICO: En producción FALSE
ALLOWED_HOSTS = ['tudominio.com', 'www.tudominio.com']  # ✅ Tu dominio
SECRET_KEY = os.getenv('SECRET_KEY')  # ✅ Desde variables env

# Base de datos para producción:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),  # Ej: 'aws-us-east-1.rds.amazonaws.com'
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

### **2. Variables de Entorno (.env.production)**
```bash
# Crear archivo .env.production:
SECRET_KEY=tu_clave_secreta_larga_y_compleja
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# Base de datos
DB_NAME=cfbc_production
DB_USER=cfbc_user
DB_PASSWORD=contraseña_fuerte
DB_HOST=postgres-host.com
DB_PORT=5432

# Email (opcional pero recomendado)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=contraseña_app_gmail
DEFAULT_FROM_EMAIL=noreply@tudominio.com

# Redis (puede ser cloud o en el mismo VPS)
REDIS_URL=redis://localhost:6379
```

### **3. Archivos Estáticos y Media**
```bash
# Asegurar que collectstatic funcione:
python manage.py collectstatic --noinput

# Configurar servicio de almacenamiento:
# Opción A: Mismo servidor (simple)
MEDIA_ROOT = '/var/www/cfbc/media'
STATIC_ROOT = '/var/www/cfbc/staticfiles'

# Opción B: Cloud Storage (recomendado para producción)
# AWS S3, Google Cloud Storage, etc.
```

---

## 🛠️ **Paso a Paso: Despliegue en VPS (Opción Recomendada)**

### **Paso 1: Elegir y Configurar VPS**
```bash
# Servidores recomendados:
- DigitalOcean: $5-10/mes (Droplet)
- Linode: $5-10/mes
- Vultr: $5-10/mes
- AWS Lightsail: $3.50/mes

# Características mínimas:
- 1-2 GB RAM
- 1-2 vCPUs
- 25-50 GB SSD
- Ubuntu 22.04 LTS
```

### **Paso 2: Conectar y Configurar Servidor**
```bash
# 1. Conectar por SSH
ssh root@tu-ip-server

# 2. Actualizar sistema
apt update && apt upgrade -y

# 3. Instalar dependencias básicas
apt install -y python3-pip python3-venv nginx postgresql redis-server
apt install -y git curl ufw

# 4. Configurar firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
```

### **Paso 3: Configurar PostgreSQL**
```bash
# 1. Acceder a PostgreSQL
sudo -u postgres psql

# 2. Crear base de datos y usuario
CREATE DATABASE cfbc_production;
CREATE USER cfbc_user WITH PASSWORD 'contraseña_fuerte';
ALTER ROLE cfbc_user SET client_encoding TO 'utf8';
ALTER ROLE cfbc_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cfbc_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE cfbc_production TO cfbc_user;
\q
```

### **Paso 4: Configurar Redis**
```bash
# Redis ya está instalado, solo verificar:
systemctl status redis

# Configurar si es necesario (opcional):
nano /etc/redis/redis.conf
# Buscar y modificar:
# bind 127.0.0.1  # Solo localhost por seguridad
# requirepass tu_contraseña_redis  # Contraseña opcional
```

### **Paso 5: Clonar y Configurar Tu Aplicación**
```bash
# 1. Crear usuario para la app
adduser django --disabled-password --gecos ""

# 2. Clonar repositorio
cd /var/www
git clone https://github.com/tu-usuario/cfbc.git
chown -R django:django /var/www/cfbc

# 3. Crear entorno virtual
cd /var/www/cfbc
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# 5. Configurar variables de entorno
cp .env.production .env
nano .env  # Editar con tus valores reales
```

### **Paso 6: Configurar Gunicorn (Servidor de Aplicación)**
```bash
# 1. Crear servicio systemd
nano /etc/systemd/system/gunicorn.service
```

```ini
# /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for CFBC Django
After=network.target postgresql.service redis.service

[Service]
User=django
Group=www-data
WorkingDirectory=/var/www/cfbc
Environment="PATH=/var/www/cfbc/venv/bin"
EnvironmentFile=/var/www/cfbc/.env
ExecStart=/var/www/cfbc/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/var/www/cfbc/cfbc.sock \
          cfbc.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Habilitar y iniciar
systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn
```

### **Paso 7: Configurar Nginx (Servidor Web)**
```bash
# 1. Crear configuración
nano /etc/nginx/sites-available/cfbc
```

```nginx
# /etc/nginx/sites-available/cfbc
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    # Archivos estáticos
    location /static/ {
        alias /var/www/cfbc/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Archivos media
    location /media/ {
        alias /var/www/cfbc/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Aplicación Django
    location / {
        proxy_pass http://unix:/var/www/cfbc/cfbc.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Denegar acceso a archivos sensibles
    location ~ /\. {
        deny all;
    }
    
    location ~ /(README\.md|requirements\.txt|\.env) {
        deny all;
    }
}
```

```bash
# 2. Habilitar sitio
ln -s /etc/nginx/sites-available/cfbc /etc/nginx/sites-enabled/
nginx -t  # Verificar sintaxis
systemctl reload nginx
```

### **Paso 8: Configurar Celery (Tareas Background)**
```bash
# 1. Crear servicio para Celery Worker
nano /etc/systemd/system/celery.service
```

```ini
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
EnvironmentFile=/var/www/cfbc/.env
ExecStart=/var/www/cfbc/venv/bin/celery -A cfbc worker -l info --concurrency=2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Crear servicio para Celery Beat (tareas programadas)
nano /etc/systemd/system/celery-beat.service
```

```ini
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
EnvironmentFile=/var/www/cfbc/.env
ExecStart=/var/www/cfbc/venv/bin/celery -A cfbc beat -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 3. Habilitar servicios
systemctl daemon-reload
systemctl start celery celery-beat
systemctl enable celery celery-beat
```

### **Paso 9: SSL (HTTPS) - OBLIGATORIO para Producción**
```bash
# Usar Certbot (Let's Encrypt - GRATIS)
apt install -y certbot python3-certbot-nginx
certbot --nginx -d tudominio.com -d www.tudominio.com

# Renovar automáticamente
certbot renew --dry-run  # Probar renovación
# Se renueva automáticamente cada 90 días
```

### **Paso 10: Configurar Dominio**
```
1. Comprar dominio: Namecheap, GoDaddy, Google Domains
2. Configurar DNS:
   - A Record: @ → IP de tu VPS
   - A Record: www → IP de tu VPS
3. Esperar 5-60 minutos para propagación
```

### **Paso 11: Migrar Datos y Primera Ejecución**
```bash
# Conectar como usuario django
sudo -u django bash
cd /var/www/cfbc
source venv/bin/activate

# 1. Migrar base de datos
python manage.py migrate

# 2. Crear superusuario
python manage.py createsuperuser

# 3. Colectar archivos estáticos
python manage.py collectstatic --noinput

# 4. Opcional: Cargar datos iniciales
python manage.py loaddata initial_data.json  # Si tienes
```

---

## 🐳 **Opción Alternativa: Despliegue con Docker (Más Simple)**

### **docker-compose.prod.yml** (adaptado)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cfbc_production
      POSTGRES_USER: cfbc_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  app:
    build: .
    image: cfbc-app:latest
    environment:
      DEBUG: 'False'
      SECRET_KEY: ${SECRET_KEY}
      DB_HOST: postgres
      DB_NAME: cfbc_production
      DB_USER: cfbc_user
      DB_PASSWORD: ${DB_PASSWORD}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    restart: always

  celery:
    build: .
    image: cfbc-app:latest
    command: celery -A cfbc worker -l info --concurrency=2
    environment:
      DEBUG: 'False'
      SECRET_KEY: ${SECRET_KEY}
      DB_HOST: postgres
      DB_NAME: cfbc_production
      DB_USER: cfbc_user
      DB_PASSWORD: ${DB_PASSWORD}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
      - app
    restart: always

  celery-beat:
    build: .
    image: cfbc-app:latest
    command: celery -A cfbc beat -l info
    environment:
      DEBUG: 'False'
      SECRET_KEY: ${SECRET_KEY}
      DB_HOST: postgres
      DB_NAME: cfbc_production
      DB_USER: cfbc_user
      DB_PASSWORD: ${DB_PASSWORD}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
      - app
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./deploy/nginx/ssl:/etc/nginx/ssl
      - static_volume:/var/www/cfbc/staticfiles
      - media_volume:/var/www/cfbc/media
    depends_on:
      - app
    restart: always

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### **Comandos para Despliegue Docker**
```bash
# 1. Construir imágenes
docker compose -f docker-compose.prod.yml build

# 2. Levantar servicios
docker compose -f docker-compose.prod.yml up -d

# 3. Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec app python manage.py migrate

# 4. Crear superusuario
docker compose -f docker-compose.prod.yml exec app python manage.py createsuperuser

# 5. Colectar estáticos
docker compose -f docker-compose.prod.yml exec app python manage.py collectstatic --noinput
```

---

## ☁️ **Opción SUPER Simple: Plataformas como Servicio (PaaS)**

### **Railway.app (Recomendado para empezar)**
```bash
# 1. Crear cuenta en railway.app
# 2. Conectar tu repositorio GitHub
# 3. Railway detecta automáticamente:
#    - requirements.txt → Instala Python
#    - runtime.txt → Versión Python
#    - Procfile → Comandos a ejecutar
```

**Procfile** (crear en raíz del proyecto):
```
web: gunicorn cfbc.wsgi --log-file -
worker: celery -A cfbc worker --loglevel=info
beat: celery -A cfbc beat --loglevel=info
```

**railway.toml** (configuración opcional):
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python manage.py migrate && gunicorn cfbc.wsgi --log-file -"

[variables]
DEBUG = "False"
SECRET_KEY = "generar-automaticamente"
```

**Ventajas de Railway:**
- Base de datos PostgreSQL incluida
- Redis incluido
- SSL automático
- Despliegue con git push
- Desde $5/mes

### **Render.com (Alternativa gratuita al inicio)**
```yaml
# render.yaml (en raíz)
services:
  - type: web
    name: cfbc-web
    env: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn cfbc.wsgi:application"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: cfbc-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: cfbc-redis
          property: connectionString

  - type: worker
    name: cfbc-celery
    env: python
    buildCommand: "./build.sh"
    startCommand: "celery -A cfbc worker -l info"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: cfbc-db
          property: connectionString

databases:
  - name: cfbc-db
    databaseName: cfbc
    user: cfbc_user

redis:
  - name: cfbc-redis
```
---

## 🔧 **Configuración Post-Despliegue**

### **1. Verificar que Todo Funciona**
```bash
# 1. Verificar servicios
systemctl status gunicorn celery celery-beat nginx postgresql redis

# 2. Verificar logs
journalctl -u gunicorn -f
journalctl -u celery -f
tail -f /var/log/nginx/error.log

# 3. Verificar endpoints
curl -I https://tudominio.com/health/  # Health check
curl -I https://tudominio.com/admin/   # Admin
```

### **2. Configurar Backups Automáticos**
```bash
# Crear script de backup
nano /usr/local/bin/backup-cfbc.sh
```

```bash
#!/bin/bash
# backup-cfbc.sh
BACKUP_DIR="/backups/cfbc"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="cfbc_production"

mkdir -p $BACKUP_DIR

# Backup base de datos
pg_dump -U cfbc_user $DB_NAME > $BACKUP_DIR/cfbc_db_$DATE.sql
gzip $BACKUP_DIR/cfbc_db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/cfbc_media_$DATE.tar.gz /var/www/cfbc/media

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
```

```bash
# Programar en crontab (diario a las 2 AM)
crontab -e
# Agregar:
0 2 * * * /usr/local/bin/backup-cfbc.sh
```

### **3. Configurar Monitoreo**
```bash
# Instalar y configurar monitoring básico
apt install -y htop nmon

# Ver recursos en tiempo real:
htop
nmon
```

### **4. Configurar Alertas (Opcional)**
```bash
# Monitoreo simple con logwatch
apt install -y logwatch
# Configura informes diarios por email
```

---

## 🚨 **Problemas Comunes y Soluciones**

### **Problema 1: "La app funciona pero las tareas no se ejecutan"**
```bash
# Solución:
# 1. Verificar Redis
redis-cli ping
# 2. Verificar Celery
systemctl status celery
# 3. Verificar logs
journalctl -u celery -f
# 4. Reiniciar si es necesario
systemctl restart celery celery-beat
```

### **Problema 2: "Error 502 Bad Gateway"**
```bash
# Solución:
# 1. Verificar Gunicorn
systemctl status gunicorn
# 2. Verificar socket
ls -la /var/www/cfbc/cfbc.sock
# 3. Verificar permisos
chown django:www-data /var/www/cfbc/cfbc.sock
# 4. Reiniciar
systemctl restart gunicorn nginx
```

### **Problema 3: "Base de datos no conecta"**
```bash
# Solución:
# 1. Verificar PostgreSQL
systemctl status postgresql
# 2. Verificar conexión
sudo -u postgres psql -c "\l"
# 3. Verificar usuario/contraseña
# 4. Revisar .env
cat /var/www/cfbc/.env | grep DB_
```

### **Problema 4: "Archivos estáticos no cargan"**
```bash
# Solución:
# 1. Verificar collectstatic
cd /var/www/cfbc && python manage.py collectstatic --noinput
# 2. Verificar permisos
chown -R django:www-data /var/www/cfbc/staticfiles
# 3. Verificar configuración Nginx
nginx -t
```

---

## 📈 **Escalando: Cuándo Activar el Auto-Scaling**

### **Señales de que Necesitas Auto-Scaling:**
```bash
# 1. Uso de CPU > 70% constantemente
top  # Ver carga CPU

# 2. Memoria > 80% constantemente
free -h

# 3. Tiempo de respuesta > 2 segundos
# Ver en Django Admin → Middleware metrics

# 4. Muchas tareas en cola
# Ver en Django Admin → Colas de Tareas
```

### **Activar Auto-Scaling (si usas Docker):**
```bash
# 1. Asegurar tener docker-compose.prod.yml
# 2. Configurar Nginx como load balancer
# 3. Usar el script de scaling:
./deploy/scripts/scale_instances.sh docker set 3  # 3 instancias

# 4. Activar auto-scaling (opcional):
python manage.py autoscale --interval 60
```

### **Si NO usas Docker pero necesitas escalar:**
```bash
# Opción A: Más workers Gunicorn
# Editar /etc/systemd/system/gunicorn.service
# Cambiar: --workers 3 → --workers 6

# Opción B: Servidor más grande
# Upgradear VPS: 2GB → 4GB RAM, más CPU

# Opción C: CDN para archivos estáticos
# Cloudflare, AWS CloudFront, etc.
```

---

## 🔒 **Seguridad Post-Despliegue (CRÍTICO)**

### **1. Firewall Configurado**
```bash
# Verificar:
ufw status
# Debe mostrar:
# 22/tcp (SSH) ALLOW
# 80/tcp (HTTP) ALLOW  
# 443/tcp (HTTPS) ALLOW
# El resto DENY
```

### **2. Actualizaciones Automáticas**
```bash
# Configurar actualizaciones de seguridad
apt install -y unattended-upgrades
dpkg-reconfigure unattended-upgrades  # Seleccionar Yes
```

### **3. Fail2ban (protege contra ataques)**
```bash
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### **4. Contraseñas Fuertes**
```bash
# Cambiar contraseñas por defecto:
passwd  # Contraseña root
sudo -u postgres psql -c "\password postgres"
redis-cli CONFIG SET requirepass "contraseña_fuerte_redis"
```

### **5. SSH Seguro**
```bash
# Editar /etc/ssh/sshd_config:
PermitRootLogin no
PasswordAuthentication no  # Usar solo keys SSH
AllowUsers django  # Solo usuario django
```

---

## 📝 **Checklist Final de Despliegue**

### **ANTES de Subir:**
- [ ] `DEBUG = False` en settings.py
- [ ] `ALLOWED_HOSTS` configurado con tu dominio
- [ ] `SECRET_KEY` en variables de entorno (NO en código)
- [ ] Base de datos de producción configurada
- [ ] `collectstatic` funciona
- [ ] Migraciones probadas

### **DESPUÉS de Subir:**
- [ ] Dominio apunta al servidor
- [ ] SSL/HTTPS funcionando
- [ ] Gunicorn/Nginx funcionando
- [ ] Base de datos conecta
- [ ] Redis funcionando
- [ ] Celery workers activos
- [ ] Admin accesible
- [ ] Archivos estáticos cargan
- [ ] Emails enviándose (si configuraste)

### **MONITOREO continuo:**
- [ ] Logs revisados regularmente
- [ ] Backups funcionando
- [ ] SSL renovándose automáticamente
- [ ] Actualizaciones de seguridad aplicadas
- [ ] Uso de recursos monitoreado

---

## 🆘 **Soporte Rápido: Comandos para Diagnóstico**

```bash
# 1. Ver todo en una pantalla
systemctl status gunicorn celery celery-beat nginx postgresql redis

# 2. Ver logs en tiempo real
journalctl -f -u gunicorn
tail -f /var/log/nginx/error.log

# 3. Ver recursos
htop
df -h  # Espacio disco
free -h  # Memoria

# 4. Ver conexiones de red
ss -tulpn | grep :80
ss -tulpn | grep :443

# 5. Probar endpoints
curl -I https://tudominio.com/health/
curl -I https://tudominio.com/admin/login/
```

---

## 🎯 **Recomendación Final**

### **Para empezar (menos complicado):**
1. **Railway.app** o **Render.com** - Todo gestionado
2. Conectar tu repositorio GitHub
3. Configurar variables de entorno
4. ¡Listo!

### **Para control total:**
1. **VPS de $5-10/mes** (DigitalOcean, Linode)
2. Seguir la guía de VPS paso a paso
3. Tú gestionas todo (más trabajo, más control)

### **Para escalar mucho:**
1. **Docker + Auto-scaling** (cuando tengas 500+ usuarios)
2. **Load balancer** (cuando un servidor no baste)
3. **CDN** para archivos estáticos

---

## 📞 **Qué Hacer si Algo Sale Mal**

1. **NO entrar en pánico** - Todo tiene solución
2. **Revisar logs** - 90% de problemas están en los logs
3. **Googlear el error** - Alguien más ya lo tuvo
4. **Hacer backup antes de cambios grandes**
5. **Pedir ayuda** - Comunidades, foros, contratar ayuda

**Recuerda:** Tu aplicación YA está diseñada para producción. Solo necesitas el entorno correcto. 🚀

---

*Documentación práctica para despliegue en internet*  
*CFBC - Centro Fray Bartolomé de las Casas*  
*Última actualización: Julio 2026*