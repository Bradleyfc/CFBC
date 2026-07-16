# Load Balancer Configuration

## Overview

This document describes the load balancer setup for the CFBC Django application
using Nginx as a reverse proxy and load balancer, with Gunicorn as the WSGI
application server.

## Architecture

### Request Flow

```
                    ┌──────────────────────────────────────┐
                    │          Internet / Users            │
                    └──────────────┬───────────────────────┘
                                   │
                          HTTPS :443
                                   │
                    ┌──────────────▼───────────────────────┐
                    │           Nginx (Load Balancer)      │
                    │                                      │
                    │  ● SSL Termination                   │
                    │  ● Rate Limiting                     │
                    │  ● Static Files Caching              │
                    │  ● Health Checks                     │
                    │  ● Sticky Sessions (Cookie-based)    │
                    │  ● Least Connections Algorithm       │
                    └──┬──────┬──────┬──────┬──────────────┘
                       │      │      │      │
                  :8001│  :8002│  :8003│  :8004│
             ┌─────────┐┌────────┐┌────────┐┌────────┐
             │Gunicorn ││Gunicorn││Gunicorn││Gunicorn│
             │App Inst1││App Inst2││App Inst3││App Inst4│
             └─────────┘└────────┘└────────┘└────────┘
                       │      │      │      │
                       └──────┴──────┴──────┘
                                  │
                    ┌─────────────▼───────────────────────┐
                    │       Shared Resources              │
                    │                                      │
                    │  ┌──────────┐  ┌─────────────┐     │
                    │  │PostgreSQL│  │    Redis    │      │
                    │  │(Primary) │  │(Cache/Sess) │      │
                    │  └──────────┘  └─────────────┘     │
                    └──────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|---|---|---|
| Load Balancer | Nginx 1.25 | Reverse proxy, SSL termination, load distribution |
| Application Server | Gunicorn 22+ | WSGI server running Django |
| Application | Django 5.2 | Web application framework |
| Database | PostgreSQL 16 | Primary data store |
| Cache/Sessions | Redis 7 | Session storage, cache, Celery broker |
| Background Tasks | Celery | Async task processing |

## Configuration Files

| File | Purpose |
|---|---|
| `deploy/nginx/nginx.conf` | Main Nginx load balancer configuration |
| `deploy/nginx/ssl.conf` | SSL/TLS settings (included by nginx.conf) |
| `deploy/gunicorn/gunicorn.conf.py` | Gunicorn WSGI server configuration |
| `deploy/gunicorn/cfbc.service` | Systemd service template for app instances |
| `Dockerfile` | Production Docker image for Django app |
| `deploy/docker-compose.prod.yml` | Full production stack with Docker |

## Load Balancing Algorithms

The current configuration uses **Least Connections** (`least_conn`), which
directs traffic to the server with the fewest active connections. This is
optimal for Django applications because:

1. Requests have variable processing times (some pages are heavier than others)
2. It naturally distributes load uneven workloads
3. It avoids the "herd effect" of round-robin on slow requests

### Available Algorithms

| Algorithm | Directive | Best For |
|---|---|---|
| Least Connections | `least_conn` | Variable request times (Django default) |
| Round Robin | (default) | Equal request times, simple setups |
| IP Hash | `ip_hash` | Sticky sessions by client IP |
| Generic Hash | `hash $request_uri` | Cache-aware routing |

## Session Persistence (Sticky Sessions)

Since the application uses **Redis-backed sessions** (`SESSION_ENGINE =
'django.contrib.sessions.backends.cache'`), the application is already
stateless and sticky sessions are **not strictly required**.

However, for **performance optimization**, cookie-based sticky sessions are
enabled via the `sticky` directive. This allows:

- Better cache locality (each instance warms its own caches)
- Reduced Redis session reads for the same user
- Consistent file upload experience for large uploads

The sticky session uses a cookie named `srv_id` that expires after 1 hour.
If a user's session becomes invalid (e.g., server goes down), Nginx will
automatically redirect them to a healthy instance.

## Health Checks

### Active Health Checks

Nginx performs health checks against each app instance:

```nginx
health_check interval=10s fails=3 passes=2 uri=/health/;
```

- **Interval**: Every 10 seconds
- **Fails**: Mark server down after 3 failures
- **Passes**: Mark server up after 2 successes
- **Endpoint**: `/health/` on the Django application

### Health Check Endpoint

The Django `/health/` endpoint returns:

```json
// Healthy instance (200 OK)
{
    "status": "healthy",
    "database": "ok",
    "cache": "ok",
    "celery": "ok",
    "instance_id": "app-1",
    "timestamp": "2026-07-13T10:00:00Z"
}

// Unhealthy instance (503 Service Unavailable)
{
    "status": "unhealthy",
    "database": "error: connection refused",
    "cache": "ok",
    "celery": "ok",
    "instance_id": "app-1",
    "timestamp": "2026-07-13T10:00:00Z"
}
```

### Nginx Health Monitoring

Check individual backend status:

```bash
# Check Nginx status (if status module is configured)
curl http://127.0.0.1:8080/health/

# Check upstream status via stub_status
curl http://127.0.0.1:8080/nginx_status

# Check specific backend
curl http://127.0.0.1:8001/health/
curl http://127.0.0.1:8002/health/
```

## SSL/TLS Configuration

### Certificate Setup

**Production (Let's Encrypt):**
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d cfbc.edu.ni -d www.cfbc.edu.ni

# Auto-renewal (certbot adds this to crontab automatically)
sudo certbot renew --dry-run
```

**Development (Self-signed):**
```bash
# Generate self-signed certificate
sudo mkdir -p /etc/ssl/cfbc
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/cfbc/cfbc.key \
  -out /etc/ssl/cfbc/cfbc.crt \
  -subj "/C=NI/ST=Managua/L=Managua/O=CFBC/CN=cfbc.edu.ni"
```

### SSL Settings

- **Protocols**: TLSv1.2 and TLSv1.3 only (SSLv3, TLSv1.0, TLSv1.1 disabled)
- **Ciphers**: Modern, secure cipher suites only
- **HSTS**: Enabled with max-age=31536000 (1 year), include subdomains
- **OCSP Stapling**: Enabled for certificate status verification
- **DH Parameters**: 2048-bit Diffie-Hellman group for forward secrecy

## Monitoring and Metrics

### Nginx Stub Status

Enable the stub_status module for real-time metrics:

```nginx
server {
    listen 127.0.0.1:8080;
    
    location /nginx_status {
        stub_status on;
        allow 127.0.0.1;
        deny all;
    }
}
```

Available metrics:
- Active connections
- Accepted and handled connections
- Total requests
- Reading, writing, waiting connections

### Prometheus Metrics

For integration with Prometheus/Grafana:

1. Install `nginx-prometheus-exporter`:
   ```bash
   docker run -d --name nginx-exporter -p 9113:9113 \
     nginx/nginx-prometheus-exporter:latest \
     -nginx.scrape-uri http://nginx:8080/nginx_status
   ```

2. Metrics exposed:
   - `nginx_connections_active`
   - `nginx_connections_accepted`
   - `nginx_connections_handled`
   - `nginx_http_requests_total`
   - `nginx_upstream_server_response_time`

### Logging

Nginx logs are structured for analysis:

```bash
# Access log format includes backend info
tail -f /var/log/nginx/access.log

# Main fields captured:
#   $upstream_addr      - Which app instance handled the request
#   $upstream_response_time - Backend processing time
#   $request_time       - Total request time (including Nginx)
#   $status             - HTTP status code

# Error log
tail -f /var/log/nginx/error.log

# Health check log (separate)
tail -f /var/log/nginx/health.log
```

## Scaling

### Adding More Application Instances

**Docker deployment:**
```bash
# Scale to 6 instances
docker compose -f deploy/docker-compose.prod.yml up -d --scale app=6

# Update Nginx config to include new instances, then reload
docker compose -f deploy/docker-compose.prod.yml exec nginx nginx -s reload
```

**Systemd deployment:**
```bash
# Enable and start new instance
sudo systemctl enable cfbc@8005
sudo systemctl start cfbc@8005

# Update Nginx upstream block in nginx.conf, then reload
sudo nginx -t && sudo systemctl reload nginx
```

### Updating the Nginx Upstream

When adding/removing backend servers:

1. Edit `deploy/nginx/nginx.conf` upstream block
2. Test configuration: `nginx -t`
3. Reload gracefully: `nginx -s reload` (zero downtime)

## Rate Limiting

The Nginx configuration includes rate limiting for different endpoints:

| Zone | Rate | Limit | Burst | Applied To |
|---|---|---|---|---|
| `general` | 100 req/s | Per IP | 200 | All pages |
| `login` | 5 req/min | Per IP | 5 | `/admin/` login |
| `api` | 30 req/min | Per IP | - | API endpoints |

Rate limiting uses shared memory and works across all Nginx workers.

## Deployment

### Option 1: Docker Compose (Production)

```bash
# Clone repository
git clone <repo> /var/www/cfbc
cd /var/www/cfbc

# Copy environment file
cp .env.example .env
# Edit .env with production values

# Deploy
docker compose -f deploy/docker-compose.prod.yml up -d

# Run migrations
docker compose -f deploy/docker-compose.prod.yml exec app-1 python manage.py migrate

# Collect static files
docker compose -f deploy/docker-compose.prod.yml exec app-1 python manage.py collectstatic

# Create admin user
docker compose -f deploy/docker-compose.prod.yml exec app-1 python manage.py createsuperuser
```

### Option 2: Systemd (Bare Metal / VM)

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y nginx postgresql redis-server python3.11-venv

# Clone repository
sudo git clone <repo> /var/www/cfbc
sudo chown -R www-data:www-data /var/www/cfbc

# Setup Python environment
cd /var/www/cfbc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup Nginx
sudo ln -sf /var/www/cfbc/deploy/nginx/nginx.conf /etc/nginx/nginx.conf
sudo mkdir -p /etc/nginx/ssl.conf
sudo ln -sf /var/www/cfbc/deploy/nginx/ssl.conf /etc/nginx/ssl.conf

# Setup Gunicorn services
sudo cp deploy/gunicorn/cfbc.service /etc/systemd/system/cfbc@.service
sudo systemctl daemon-reload

# Start application instances
for port in 8001 8002 8003 8004; do
  sudo systemctl enable cfbc@$port
  sudo systemctl start cfbc@$port
done

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Testing

### Test Load Balancing

```bash
# Test that requests are distributed across backends
for i in {1..20}; do
  curl -s -I http://localhost/ | grep -i "x-instance"
done

# Check which backend handled each request
tail -f /var/log/nginx/access.log | grep "cfbc-app"
```

### Test Sticky Sessions

```bash
# Verify cookie is set
curl -v http://localhost/ 2>&1 | grep "Set-Cookie"

# Same client gets same backend
curl -b /tmp/cookies.txt -c /tmp/cookies.txt http://localhost/
```

### Test Health Checks

```bash
# Health endpoint
curl http://localhost/health/
curl http://127.0.0.1:8001/health/
curl http://127.0.0.1:8002/health/

# Take one instance down
sudo systemctl stop cfbc@8001

# Verify requests are redirected to remaining instances
while true; do
  curl -s http://localhost/health/ | python -m json.tool
  sleep 0.5
done

# Restart the instance
sudo systemctl start cfbc@8001
```

### Test SSL

```bash
# Test HTTPS
curl -I https://localhost/

# Check SSL certificate
openssl s_client -connect localhost:443 -servername cfbc.edu.ni

# Test HSTS
curl -s -D- https://localhost/ | grep -i "strict-transport-security"
```

### Load Test

```bash
# Using wrk (install: sudo apt-get install wrk)
wrk -t12 -c400 -d30s http://localhost/

# Using ab (install: sudo apt-get install apache2-utils)
ab -n 10000 -c 100 http://localhost/health/

# Using locust (Python-based)
locust -f locustfile.py --host=http://localhost
```

## Troubleshooting

### Backend Marked as Down

```bash
# Check why Nginx marked a backend as down
tail -f /var/log/nginx/error.log | grep "upstream"

# Force re-check
curl http://localhost:8001/health/

# Reload Nginx after fixes
sudo nginx -s reload
```

### High Response Times

```bash
# Check which backend is slow
tail -f /var/log/nginx/access.log | awk '{print $NF}' | sort | tail -20

# Check backend resources
ssh app-server-1 "top -bn1 | head -20"
ssh app-server-1 "free -m"
ssh app-server-1 "df -h"
```

### SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in /etc/ssl/cfbc/cfbc.crt -noout -dates

# Force renew
sudo certbot renew --force-renewal

# Check Nginx SSL config
nginx -t 2>&1
```

## Rollback Procedures

### Quick Rollback

```bash
# If new Nginx config fails
sudo cp /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf
sudo systemctl reload nginx

# If new app version fails (Docker)
docker compose -f deploy/docker-compose.prod.yml up -d --force-recreate app-1
```

### Full Rollback

```bash
# Revert to previous Docker image
docker compose -f deploy/docker-compose.prod.yml down
git checkout <previous-tag>
docker compose -f deploy/docker-compose.prod.yml up -d

# Revert to previous systemd version
cd /var/www/cfbc
git checkout <previous-tag>
sudo systemctl restart cfbc@8001 cfbc@8002 cfbc@8003 cfbc@8004
```

## Maintenance Procedures

### Graceful Nginx Reload

```bash
# Zero-downtime reload
sudo nginx -s reload

# Or with systemd
sudo systemctl reload nginx
```

### Rolling Restart of App Instances

```bash
# Restart one at a time to maintain availability
for port in 8001 8002 8003 8004; do
  echo "Restarting cfbc@$port..."
  sudo systemctl restart cfbc@$port
  sleep 10  # Wait for health check to pass
  echo "Instance $port restarted successfully"
done
```

### Graceful Shutdown

```bash
# Drain connections from Nginx first
sudo nginx -s quit

# Then stop app instances
for port in 8001 8002 8003 8004; do
  sudo systemctl stop cfbc@$port
done
```

## Verification Checklist

- [ ] Nginx configuration passes syntax check (`nginx -t`)
- [ ] All app instances are registered and healthy in the upstream
- [ ] Health checks pass for each instance (`curl /health/`)
- [ ] SSL certificate is valid and not expired
- [ ] HTTPS redirect works (HTTP→HTTPS)
- [ ] Static files are served directly by Nginx (not proxied to Django)
- [ ] Media files are served correctly
- [ ] Sticky sessions cookie is being set
- [ ] Rate limiting is active and working
- [ ] Load balancing distributes requests across instances
- [ ] Taking down one instance doesn't affect service availability
- [ ] Logs are being written to correct location
- [ ] Monitoring endpoints are accessible
- [ ] SSL test passes (SSL Labs or similar)
- [ ] Security headers are present (HSTS, X-Frame-Options, etc.)
