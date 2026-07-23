# Celery Async Processing Setup

This document provides instructions for setting up and using Celery for asynchronous task processing in the CFBC Django application.

## Overview

Celery is a distributed task queue system that allows time-consuming tasks to be executed asynchronously, improving user experience by offloading heavy processing from web requests.

## Installation

Celery and related packages are already installed in the project. Required packages:

```bash
celery==5.4.0
django-celery-results==2.5.1
flower==2.0.1
redis==5.2.1
django-redis==5.4.0
```

## Configuration

### Redis Setup
Redis is used as both the message broker and result backend. It should be running on `localhost:6379`.

Check if Redis is running:
```bash
redis-cli ping
```

### Django Settings
Celery is configured in `cfbc/settings.py`:

```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/3'  # Database 3 for Celery broker
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/4'  # Database 4 for Celery results
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE  # Use Django's timezone
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_RESULT_EXPIRES = 24 * 60 * 60  # 24 hours
```

### Task Queues
Tasks are routed to different queues based on their type:

- **email**: Email notifications (welcome emails, comment notifications)
- **file_processing**: Document upload processing
- **reports**: Report generation tasks
- **backup**: Data backup tasks
- **maintenance**: System maintenance tasks
- **default**: Default queue for other tasks

## Running Celery

### Start Celery Worker
To process tasks, start a Celery worker:

```bash
# Basic worker (processes all queues)
celery -A cfbc worker -l info

# Worker with concurrency
celery -A cfbc worker -l info --concurrency=4

# Worker for specific queues
celery -A cfbc worker -l info -Q email,reports
```

### Start Flower (Monitoring)
Flower is a web-based tool for monitoring Celery workers and tasks:

```bash
celery -A cfbc flower
```

Access Flower at: http://localhost:5555

### Start Celery Beat (Periodic Tasks)
For scheduled tasks (cron jobs):

```bash
celery -A cfbc beat -l info
```

## Available Tasks

### Blog Tasks (`blog/tasks.py`)
- `send_welcome_email(user_id)`: Send welcome email to new users
- `send_comment_notification(comment_id)`: Notify authors of new comments
- `send_comment_reply_notification(comment_id, reply_comment_id)`: Notify users of comment replies
- `generate_blog_statistics_report(start_date, end_date)`: Generate blog statistics report
- `backup_blog_data()`: Create backup of blog data

### Course Documents Tasks (`course_documents/tasks.py`)
- `process_uploaded_document(document_id)`: Process uploaded documents (metadata extraction, thumbnails)
- `send_document_notification(document_id)`: Notify students of new documents
- `generate_folder_report(folder_id, report_type)`: Generate reports for document folders
- `generate_performance_report(start_date, end_date)`: Generate system performance report
- `backup_document_metadata()`: Create backup of document metadata
- `cleanup_old_documents(days_old)`: Clean up old document access records

## Using Tasks in Code

### Delaying Tasks
```python
from blog.tasks import send_welcome_email
from course_documents.tasks import process_uploaded_document

# Simple task delay
send_welcome_email.delay(user.id)

# Task with arguments
process_uploaded_document.delay(document_id)
```

### Task Results
```python
# Get task result
result = send_welcome_email.delay(user.id)
task_id = result.id

# Check if task is ready
if result.ready():
    print(result.result)
    
# Wait for result (blocking)
result.get(timeout=30)
```

### Error Handling
```python
from celery.exceptions import TimeoutError

try:
    result = send_welcome_email.delay(user.id)
    task_result = result.get(timeout=30)
except TimeoutError:
    print("Task timed out")
except Exception as e:
    print(f"Task failed: {e}")
```

## Task Monitoring

### Django Admin Interface
Task results can be monitored in Django Admin at `/admin/django_celery_results/taskresult/`.

Features:
- View task execution history
- See task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)
- View task arguments and results
- See error traces for failed tasks

### Command-Line Monitoring
```bash
# Check worker status
celery -A cfbc inspect active
celery -A cfbc inspect registered
celery -A cfbc inspect scheduled

# Check queue lengths
celery -A cfbc inspect stats

# Revoke a task
celery -A cfbc control revoke <task_id>
```

## Testing Tasks

### Management Command
```bash
python manage.py test_celery_tasks --task-type=email
python manage.py test_celery_tasks --task-type=report
python manage.py test_celery_tasks --task-type=backup
python manage.py test_celery_tasks --task-type=all
```

### Manual Testing
```python
# Test script
python test_celery_setup.py
```

## Scheduled Tasks

To schedule periodic tasks, configure Celery Beat in `cfbc/settings.py`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'backup-blog-data-nightly': {
        'task': 'blog.tasks.backup_blog_data',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'backup-documents-nightly': {
        'task': 'course_documents.tasks.backup_document_metadata',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
    'cleanup-old-documents-weekly': {
        'task': 'course_documents.tasks.cleanup_old_documents',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # 4 AM every Sunday
    },
}
```

## Best Practices

1. **Task Idempotency**: Design tasks to be safe to run multiple times
2. **Error Handling**: Implement proper retry logic with exponential backoff
3. **Resource Management**: Set appropriate time limits for different task types
4. **Queue Separation**: Route different task types to different queues
5. **Monitoring**: Regularly check task queues and worker health
6. **Logging**: Include detailed logging in all tasks
7. **Testing**: Test tasks thoroughly before deployment

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check if Redis is running: `redis-cli ping`
   - Verify Redis URL in settings

2. **Tasks Not Processing**
   - Check worker status: `celery -A cfbc inspect active`
   - Verify task registration: `celery -A cfbc inspect registered`

3. **Task Timeouts**
   - Increase `CELERY_TASK_TIME_LIMIT` for long-running tasks
   - Optimize task code for better performance

4. **Memory Issues**
   - Reduce worker concurrency
   - Implement task chunking for large datasets

### Debugging Tips

```bash
# Enable debug logging
celery -A cfbc worker -l debug

# Check task details
celery -A cfbc result <task_id>

# Purge all tasks from queues (use with caution)
celery -A cfbc purge
```

## Deployment Notes

For production deployment:

1. Use process supervision (systemd, supervisord)
2. Configure multiple workers with different queue assignments
3. Set up monitoring and alerting
4. Implement task result expiration
5. Configure appropriate concurrency levels
6. Set up centralized logging

Example systemd service file (`/etc/systemd/system/celery.service`):

```ini
[Unit]
Description=Celery Service
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/etc/default/celery
WorkingDirectory=/var/www/cfbc
ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PIDFILE} \
  --logfile=${CELERYD_LOGFILE} ${CELERYD_OPTS}'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PIDFILE}'
ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PIDFILE} \
  --logfile=${CELERYD_LOGFILE} ${CELERYD_OPTS}'

[Install]
WantedBy=multi-user.target
```