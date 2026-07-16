"""
Celery configuration for CFBC project.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cfbc.settings')

app = Celery('cfbc')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# ─────────────────────────────────────────────────────────────────────────────
# Register periodic cache tasks on Celery beat
# ─────────────────────────────────────────────────────────────────────────────

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Setup periodic tasks for cache warming and health checks.
    This is called after the Celery app is fully configured.
    """
    from cfbc.cache_signals import register_warm_cache_task, register_health_check_task
    register_warm_cache_task(sender)
    register_health_check_task(sender)