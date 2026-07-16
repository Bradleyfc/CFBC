"""
Django admin interface for Celery task management.
Provides monitoring views for task results, queues, and workers.
"""

from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
from django_celery_results.models import TaskResult
from django_celery_results.admin import TaskResultAdmin as BaseTaskResultAdmin
import json
from .models import TaskQueue, TaskWorker


class TaskResultAdmin(BaseTaskResultAdmin):
    """Custom admin interface for Celery task results."""

    list_display = (
        'task_id', 'status_colored', 'task_name', 'date_created',
        'date_done', 'worker', 'task_args_preview'
    )

    list_filter = ('status', 'task_name', 'date_created', 'date_done')

    search_fields = ('task_id', 'task_name', 'result', 'traceback')

    readonly_fields = (
        'task_id', 'status', 'task_name', 'worker', 'date_created',
        'date_done', 'meta', 'result', 'traceback', 'task_args_display',
        'task_kwargs_display', 'task_result_display'
    )

    fieldsets = (
        ('Información de la Tarea', {
            'fields': ('task_id', 'task_name', 'status', 'worker', 'date_created', 'date_done')
        }),
        ('Parámetros de la Tarea', {
            'fields': ('task_args_display', 'task_kwargs_display'),
            'classes': ('collapse',)
        }),
        ('Resultado de la Tarea', {
            'fields': ('task_result_display', 'traceback'),
            'classes': ('wide',)
        }),
    )

    def status_colored(self, obj):
        colors = {
            'SUCCESS': 'green',
            'FAILURE': 'red',
            'PENDING': 'orange',
            'STARTED': 'blue',
            'RETRY': 'purple',
            'REVOKED': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status
        )
    status_colored.short_description = 'Estado'
    status_colored.admin_order_field = 'status'

    def task_args_preview(self, obj):
        if obj.task_args:
            try:
                args = json.loads(obj.task_args)
                text = str(args)
                return text[:60] + '...' if len(text) > 60 else text
            except (json.JSONDecodeError, TypeError):
                raw = str(obj.task_args)
                return raw[:60] + '...' if len(raw) > 60 else raw
        return '-'
    task_args_preview.short_description = 'Args'

    def task_args_display(self, obj):
        if obj.task_args:
            try:
                args = json.loads(obj.task_args)
                return format_html('<pre style="max-height:200px;overflow:auto;">{}</pre>',
                                   json.dumps(args, indent=2, ensure_ascii=False))
            except (json.JSONDecodeError, TypeError):
                return str(obj.task_args)
        return '-'
    task_args_display.short_description = 'Argumentos de la Tarea'

    def task_kwargs_display(self, obj):
        if obj.task_kwargs:
            try:
                kwargs = json.loads(obj.task_kwargs)
                return format_html('<pre style="max-height:200px;overflow:auto;">{}</pre>',
                                   json.dumps(kwargs, indent=2, ensure_ascii=False))
            except (json.JSONDecodeError, TypeError):
                return str(obj.task_kwargs)
        return '-'
    task_kwargs_display.short_description = 'Argumentos Keywords'

    def task_result_display(self, obj):
        if obj.result:
            try:
                result = json.loads(obj.result)
                return format_html('<pre style="max-height:200px;overflow:auto;">{}</pre>',
                                   json.dumps(result, indent=2, ensure_ascii=False))
            except (json.JSONDecodeError, TypeError):
                return str(obj.result)
        return '-'
    task_result_display.short_description = 'Resultado de la Tarea'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class TaskQueueAdmin(admin.ModelAdmin):
    """Admin interface for task queue monitoring."""
    model = TaskQueue
    change_list_template = 'admin/task_management/queue_list.html'

    def get_queryset(self, request):
        return TaskQueue.objects.none()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        queues = self._get_queue_data()
        extra_context['queues'] = queues
        extra_context['total_queues'] = len(queues)
        extra_context['total_pending'] = sum(q['length'] for q in queues)
        extra_context['title'] = 'Estado de las Colas de Tareas'
        return super().changelist_view(request, extra_context=extra_context)

    def _get_queue_data(self):
        import redis as redis_module
        configured_queues = {
            'default': {'priority': 5, 'description': 'Tareas por defecto'},
            'email': {'priority': 1, 'description': 'Envío de correos electrónicos'},
            'file_processing': {'priority': 2, 'description': 'Procesamiento de archivos'},
            'reports': {'priority': 3, 'description': 'Generación de reportes'},
            'backup': {'priority': 4, 'description': 'Copias de seguridad'},
            'maintenance': {'priority': 6, 'description': 'Tareas de mantenimiento'},
        }
        broker_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://127.0.0.1:6379/3')
        queues_data = {}
        for name, info in configured_queues.items():
            queues_data[name] = {
                'name': name, 'length': 0, 'priority': info['priority'],
                'description': info['description'],
                'status': 'vacía', 'status_class': 'vacía',
            }
        try:
            r = redis_module.Redis.from_url(broker_url)
            for queue_name in configured_queues:
                try:
                    queue_len = r.llen(queue_name)
                    queues_data[queue_name]['length'] = queue_len
                    if queue_len == 0:
                        queues_data[queue_name]['status'] = 'vacía'
                    elif queue_len < 10:
                        queues_data[queue_name]['status'] = 'normal'
                    elif queue_len < 50:
                        queues_data[queue_name]['status'] = 'ocupada'
                    else:
                        queues_data[queue_name]['status'] = 'congestionada'
                except Exception:
                    queues_data[queue_name]['status'] = 'error'
        except Exception:
            for name in configured_queues:
                queues_data[name]['status'] = 'Redis no disponible'
                queues_data[name]['status_class'] = 'error'
        return [queues_data[n] for n in sorted(queues_data.keys(), key=lambda n: queues_data[n]['priority'])]


class TaskWorkerAdmin(admin.ModelAdmin):
    """Admin interface for worker status monitoring."""
    model = TaskWorker
    change_list_template = 'admin/task_management/worker_list.html'

    def get_queryset(self, request):
        return TaskWorker.objects.none()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        workers = self._get_worker_data()
        extra_context['workers'] = workers
        extra_context['total_workers'] = len(workers)
        extra_context['total_active'] = sum(w['active_tasks'] for w in workers)
        extra_context['total_processed'] = sum(w['total_processed'] for w in workers)
        extra_context['title'] = 'Estado de los Workers Celery'
        return super().changelist_view(request, extra_context=extra_context)

    def _get_worker_data(self):
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            workers_data = []
            if inspect is None:
                return [self._offline_entry('Celery inspect no disponible')]
            active = inspect.active() or {}
            reserved = inspect.reserved() or {}
            scheduled = inspect.scheduled() or {}
            stats_data = inspect.stats() or {}
            registered = inspect.registered() or {}
            active_queues = inspect.active_queues() or {}
            all_worker_names = set()
            all_worker_names.update(active.keys())
            all_worker_names.update(reserved.keys())
            all_worker_names.update(scheduled.keys())
            all_worker_names.update(stats_data.keys())
            all_worker_names.update(registered.keys())
            all_worker_names.update(active_queues.keys())
            if not all_worker_names:
                return [self._offline_entry('No hay workers conectados')]
            for worker_name in sorted(all_worker_names):
                worker_active = active.get(worker_name, [])
                worker_reserved = reserved.get(worker_name, [])
                worker_scheduled = scheduled.get(worker_name, [])
                worker_stats = stats_data.get(worker_name, {})
                worker_registered = registered.get(worker_name, [])
                worker_queues = active_queues.get(worker_name, [])
                total = worker_stats.get('total', {})
                total_processed = sum(total.values()) if isinstance(total, dict) else 0
                pool = worker_stats.get('pool', {})
                pool_size = pool.get('max-concurrency', 'N/A') if isinstance(pool, dict) else 'N/A'
                loadavg = worker_stats.get('loadavg', None)
                pid = worker_stats.get('pid', 'N/A')
                workers_data.append({
                    'name': worker_name, 'status': 'Online', 'status_color': 'green',
                    'active_tasks': len(worker_active), 'reserved_tasks': len(worker_reserved),
                    'scheduled_tasks': len(worker_scheduled), 'total_processed': total_processed,
                    'registered_tasks': len(worker_registered), 'pool_size': pool_size,
                    'loadavg': loadavg,
                    'queues': [q.get('name', str(q)) for q in worker_queues] if worker_queues else [],
                    'pid': pid,
                    'active_task_names': [t.get('name', str(t)[:50]) for t in worker_active] if worker_active else [],
                })
            return workers_data
        except Exception as e:
            return [self._offline_entry(f'Error: {e}')]

    def _offline_entry(self, message):
        return {
            'name': message, 'status': 'Offline', 'status_color': 'gray',
            'active_tasks': 0, 'reserved_tasks': 0, 'scheduled_tasks': 0,
            'total_processed': 0, 'registered_tasks': 0, 'pool_size': 'N/A',
            'loadavg': None, 'queues': [], 'pid': 'N/A', 'active_task_names': [],
        }


admin.site.unregister(TaskResult)
admin.site.register(TaskResult, TaskResultAdmin)
admin.site.register(TaskQueue, TaskQueueAdmin)
admin.site.register(TaskWorker, TaskWorkerAdmin)
