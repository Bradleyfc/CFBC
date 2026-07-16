"""
================================================================================
  Gunicorn Configuration
  =======================
  
  Configuration file for Gunicorn WSGI server running the CFBC Django app.
  
  Usage:
      gunicorn -c deploy/gunicorn/gunicorn.conf.py cfbc.wsgi:application
  
  With multiple instances (for load balancing):
      gunicorn -c deploy/gunicorn/gunicorn.conf.py cfbc.wsgi:application \\
               --bind 0.0.0.0:8001
  
  Systemd Service:
      See deploy/gunicorn/cfbc.service for production service definition.
================================================================================
"""

import os
import multiprocessing
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Server Socket
# ─────────────────────────────────────────────────────────────────────────────
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048  # Max pending connections

# ─────────────────────────────────────────────────────────────────────────────
# Worker Processes
# ─────────────────────────────────────────────────────────────────────────────
# Formula: 2 * CPU cores + 1 (for I/O bound apps)
# For CPU-bound: CPU cores + 1
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'  # Sync workers are sufficient for Django

# Threads per worker (only for gthread worker class)
# threads = 4

# Max requests before worker restart (prevent memory leaks)
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '10000'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '2000'))

# Worker timeouts
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))        # seconds
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '5'))      # seconds

# ─────────────────────────────────────────────────────────────────────────────
# Process Management
# ─────────────────────────────────────────────────────────────────────────────
pidfile = None                       # Managed by systemd
umask = 0o027                        # Secure file creation mask
user = os.getenv('GUNICORN_USER', 'www-data')
group = os.getenv('GUNICORN_GROUP', 'www-data')

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')    # stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')      # stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

# ─────────────────────────────────────────────────────────────────────────────
# Hooks
# ─────────────────────────────────────────────────────────────────────────────

def on_starting(server):
    """Log when server starts."""
    server.log.info("Gunicorn server starting...")


def on_reload(server):
    """Log when server reloads."""
    server.log.info("Gunicorn server reloading...")


def when_ready(server):
    """Log when server is ready to accept connections."""
    server.log.info(
        f"Gunicorn ready: {server.cfg.workers} workers, "
        f"listening on {server.cfg.bind}"
    )


def on_exit(server):
    """Log when server exits."""
    server.log.info("Gunicorn server shutting down...")


def worker_abort(worker):
    """Log when worker is aborted."""
    worker.log.warning(
        f"Worker {worker.pid} aborted after "
        f"{worker.age} seconds"
    )


def post_worker_init(worker):
    """Initialize worker after fork."""
    worker.log.info(f"Worker {worker.pid} initialized")


def worker_int(worker):
    """Log when worker receives INT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGINT")


def pre_fork(server, worker):
    """Log before forking a worker."""
    pass


def post_fork(server, worker):
    """Log after forking a worker."""
    server.log.debug(f"Worker {worker.pid} forked")


# ─────────────────────────────────────────────────────────────────────────────
# SSL (if not using Nginx for termination)
# ─────────────────────────────────────────────────────────────────────────────
# keyfile = None
# certfile = None
# ssl_version = 3
# ca_certs = None
# Suppress SSL when Nginx handles it

# ─────────────────────────────────────────────────────────────────────────────
# Monitoring
# ─────────────────────────────────────────────────────────────────────────────
# Enable prometheus metrics if using django-prometheus
# statsd_host = os.getenv('STATSD_HOST')
# statsd_port = os.getenv('STATSD_PORT', 8125)
# statsd_prefix = 'cfbc.gunicorn'

# ─────────────────────────────────────────────────────────────────────────────
# Production Checklist
# ─────────────────────────────────────────────────────────────────────────────
# [ ] Set GUNICORN_WORKERS environment variable (auto-detects if not set)
# [ ] Verify Nginx is running in front of Gunicorn
# [ ] Set GUNICORN_BIND=0.0.0.0:8001 (or different port per instance)
# [ ] Configure logging to centralized log aggregator
# [ ] Set GUNICORN_TIMEOUT based on slowest expected request
# [ ] Monitor worker restarts via max_requests
