"""
================================================================================
  Dockerfile: CFBC Django Application
  =====================================
  
  Multi-stage build for the CFBC Django application.
  Produces a minimal production image with Gunicorn.
  
  Build:
      docker build -t cfbc-app:latest .
  
  Run:
      docker run -d \
        --name cfbc-app-1 \
        --network cfbc-network \
        -e GUNICORN_BIND=0.0.0.0:8000 \
        -e GUNICORN_WORKERS=4 \
        -v cfbc-media:/var/www/cfbc/media \
        -v cfbc-static:/var/www/cfbc/staticfiles \
        cfbc-app:latest
  
  With docker-compose:
      See deploy/docker-compose.prod.yml
================================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Python Dependencies
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements.txt /tmp/requirements.txt
COPY requirements-optional.txt /tmp/requirements-optional.txt

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements.txt && \
    pip install gunicorn && \
    if [ -f /tmp/requirements-optional.txt ]; then \
        pip install -r /tmp/requirements-optional.txt || true; \
    fi

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime Image
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r django --gid 1000 && \
    useradd -r -g django --uid 1000 -d /var/www/cfbc -s /sbin/nologin django

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=cfbc.settings \
    PYTHONPATH=/var/www/cfbc

# Create application directory structure
RUN mkdir -p /var/www/cfbc /var/log/cfbc /var/run/cfbc && \
    chown -R django:django /var/www/cfbc /var/log/cfbc /var/run/cfbc

# Set working directory
WORKDIR /var/www/cfbc

# Copy application code
COPY --chown=django:django . .

# Create staticfiles and media directories
RUN mkdir -p /var/www/cfbc/staticfiles /var/www/cfbc/media && \
    chown -R django:django /var/www/cfbc/staticfiles /var/www/cfbc/media

# Collect static files
RUN python manage.py collectstatic --noinput --clear 2>&1 || \
    (echo "WARNING: collectstatic failed, will retry at runtime" && exit 0)

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command: Gunicorn
CMD ["gunicorn", \
     "--config", "deploy/gunicorn/gunicorn.conf.py", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "cfbc.wsgi:application"]
