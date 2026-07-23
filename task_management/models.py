"""
Proxy models for Celery task monitoring in Django admin.
These models don't create database tables - they're used solely
to register admin views for real-time Celery monitoring.
"""

from django.db import models


class TaskQueue(models.Model):
    """
    Proxy model for displaying Celery queue statistics in the admin.
    
    Uses managed=False so Django doesn't create a database table.
    The admin changelist_view is overridden to inject real-time data from Redis.
    """
    name = models.CharField(
        max_length=255, 
        primary_key=True, 
        verbose_name='Nombre de la cola',
        help_text='Nombre de la cola Celery'
    )

    class Meta:
        managed = False
        verbose_name = '🐍 Cola de Tareas'
        verbose_name_plural = '🐍 Colas de Tareas'
        ordering = ['name']

    def __str__(self):
        return self.name


class TaskWorker(models.Model):
    """
    Proxy model for displaying Celery worker status in the admin.
    
    Uses managed=False so Django doesn't create a database table.
    The admin changelist_view is overridden to inject real-time data from Celery inspect.
    """
    name = models.CharField(
        max_length=255, 
        primary_key=True, 
        verbose_name='Nombre del worker',
        help_text='Nombre del worker Celery'
    )

    class Meta:
        managed = False
        verbose_name = '⚙️ Trabajador Celery'
        verbose_name_plural = '⚙️ Trabajadores Celery'
        ordering = ['name']

    def __str__(self):
        return self.name
