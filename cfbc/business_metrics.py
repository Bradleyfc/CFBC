"""
Business Metrics Monitoring for CFBC.

Tracks domain-specific key performance indicators (KPIs):
- User registrations (by role, by day/week/month)
- Course activity (active courses, enrollments)
- Document management (uploads, downloads, storage usage)
- Blog activity (posts, comments)
- Evaluation activity (evaluations created, responses)

All metrics are stored in Redis for time-series aggregation
and exposed via the /metrics/ endpoint.

Usage:
    from cfbc.business_metrics import record_metric, get_business_metrics

    record_metric('user_registration', {'role': 'estudiante'})
    record_metric('document_upload', {'curso_id': 1, 'file_size': 1024})
"""

import json
import time
import logging
from datetime import datetime, date
from typing import Optional

from django.db.models import Count, Sum, Avg
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Metric Recording (Redis-backed)
# ─────────────────────────────────────────────────────────────────────────────


def record_metric(metric_name: str, tags: Optional[dict] = None,
                  value: float = 1.0) -> None:
    """
    Record a business metric event in Redis for aggregation.

    Args:
        metric_name: The metric name (e.g., 'user_registration', 'document_download')
        tags: Optional dict of tags/labels (e.g., {'role': 'estudiante'})
        value: Numeric value (default: 1 for counting events)
    """
    try:
        today = date.today().isoformat()
        now = datetime.now()
        hour_key = now.strftime('%Y-%m-%dT%H:00')
        minute_key = now.strftime('%Y-%m-%dT%H:%M')
        tags = tags or {}

        pipe = cache.client.get_client().pipeline() if hasattr(cache, 'client') else None
        if not pipe:
            return

        base_key = f'cfbc:biz:{metric_name}'

        # Daily total
        pipe.hincrbyfloat(f'{base_key}:daily:{today}', 'total', value)

        # Hourly breakdown
        pipe.hincrbyfloat(f'{base_key}:hourly:{hour_key}', 'total', value)

        # Per-minute (for real-time dashboards)
        pipe.hincrbyfloat(f'{base_key}:minutely:{minute_key}', 'total', value)

        # Tagged breakdown (e.g., by role)
        for tag_key, tag_value in tags.items():
            pipe.hincrbyfloat(f'{base_key}:daily:{today}', f'{tag_key}:{tag_value}', value)

        # Set TTLs for automatic cleanup
        pipe.expire(f'{base_key}:daily:{today}', 86400 * 90)     # 90 days
        pipe.expire(f'{base_key}:hourly:{hour_key}', 86400 * 7)  # 7 days
        pipe.expire(f'{base_key}:minutely:{minute_key}', 3600)   # 1 hour

        pipe.execute()

    except Exception as e:
        logger.debug(f"Failed to record business metric '{metric_name}': {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Data Aggregation Functions
# ─────────────────────────────────────────────────────────────────────────────


def get_business_metrics() -> dict:
    """
    Aggregate business metrics from Redis and database.

    Returns a complete snapshot of current business KPIs.
    """
    return {
        'users': _get_user_metrics(),
        'courses': _get_course_metrics(),
        'documents': _get_document_metrics(),
        'blog': _get_blog_metrics(),
        'evaluations': _get_evaluation_metrics(),
        'registrations': _get_registration_trends(),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }


def get_business_metrics_text() -> str:
    """
    Generate business metrics in Prometheus text format.
    Used by the /metrics/ endpoint.
    """
    from cfbc.views import _generate_text_metrics

    metrics = get_business_metrics()
    lines = []

    # User metrics
    user_data = metrics.get('users', {})
    for role, count in user_data.get('by_role', {}).items():
        lines.append(f'cfbc_users_total{{role="{role}"}} {count}')
    lines.append(f'cfbc_users_total{{role="all"}} {user_data.get("total", 0)}')
    lines.append(f'cfbc_users_active_today {user_data.get("active_today", 0)}')

    # Course metrics
    course_data = metrics.get('courses', {})
    lines.append(f'cfbc_courses_total{{status="active"}} {course_data.get("active", 0)}')
    lines.append(f'cfbc_courses_total{{status="all"}} {course_data.get("total", 0)}')
    lines.append(f'cfbc_courses_total{{status="archived"}} {course_data.get("archived", 0)}')
    lines.append(f'cfbc_enrollments_total {course_data.get("enrollments", 0)}')

    # Document metrics
    doc_data = metrics.get('documents', {})
    lines.append(f'cfbc_documents_total {doc_data.get("total", 0)}')
    lines.append(f'cfbc_documents_storage_bytes {doc_data.get("storage_bytes", 0)}')
    lines.append(f'cfbc_document_folders_total {doc_data.get("folders", 0)}')

    # Blog metrics
    blog_data = metrics.get('blog', {})
    lines.append(f'cfbc_blog_posts_total {blog_data.get("posts", 0)}')
    lines.append(f'cfbc_blog_comments_total {blog_data.get("comments", 0)}')
    lines.append(f'cfbc_blog_published_posts_total {blog_data.get("published_posts", 0)}')

    # Evaluation metrics
    eval_data = metrics.get('evaluations', {})
    lines.append(f'cfbc_evaluations_total {eval_data.get("total", 0)}')
    lines.append(f'cfbc_evaluations_questions_total {eval_data.get("questions", 0)}')

    # Registration trends (today, this week, this month)
    reg_data = metrics.get('registrations', {})
    lines.append(f'cfbc_registrations_today {reg_data.get("today", 0)}')
    lines.append(f'cfbc_registrations_this_week {reg_data.get("this_week", 0)}')
    lines.append(f'cfbc_registrations_this_month {reg_data.get("this_month", 0)}')

    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# User Metrics
# ─────────────────────────────────────────────────────────────────────────────


def _get_user_metrics() -> dict:
    """Get user-related KPIs from the database."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from accounts.models import Registro

        total_users = User.objects.count()
        today = date.today()
        active_today = User.objects.filter(
            last_login__date=today
        ).count()

        # Users by role (from Registro model)
        roles = {}
        try:
            role_counts = Registro.objects.values('rol').annotate(count=Count('id'))
            for rc in role_counts:
                roles[rc['rol']] = rc['count']
        except Exception:
            pass

        return {
            'total': total_users,
            'by_role': roles,
            'active_today': active_today,
        }
    except Exception as e:
        logger.warning(f"Failed to get user metrics: {e}")
        return {'total': 0, 'by_role': {}, 'active_today': 0}


# ─────────────────────────────────────────────────────────────────────────────
# Course Metrics
# ─────────────────────────────────────────────────────────────────────────────


def _get_course_metrics() -> dict:
    """Get course-related KPIs from the database."""
    try:
        from principal.models import Curso, Matriculas, CursoAcademico

        # Active courses (in current academic year)
        current_period = CursoAcademico.objects.filter(
            activo=True
        ).first() if CursoAcademico.objects.filter(activo=True).exists() else None

        active_courses = 0
        if current_period:
            active_courses = Curso.objects.filter(
                curso_academico=current_period
            ).count()

        total_courses = Curso.objects.count()
        archived_courses = 0
        try:
            archived_courses = Curso.objects.filter(
                archivado=True
            ).count()
        except Exception:
            pass

        # Enrollments
        total_enrollments = Matriculas.objects.count()
        current_enrollments = 0
        if current_period:
            current_enrollments = Matriculas.objects.filter(
                curso__curso_academico=current_period
            ).count()

        return {
            'active': active_courses,
            'total': total_courses,
            'archived': archived_courses,
            'enrollments': total_enrollments,
            'current_enrollments': current_enrollments,
        }
    except Exception as e:
        logger.warning(f"Failed to get course metrics: {e}")
        return {'active': 0, 'total': 0, 'archived': 0, 'enrollments': 0, 'current_enrollments': 0}


# ─────────────────────────────────────────────────────────────────────────────
# Document Metrics
# ─────────────────────────────────────────────────────────────────────────────


def _get_document_metrics() -> dict:
    """Get document-related KPIs from the database."""
    try:
        from course_documents.models import CourseDocument, DocumentFolder

        total_docs = CourseDocument.objects.count()
        total_folders = DocumentFolder.objects.count()

        # Calculate total storage
        storage_result = CourseDocument.objects.aggregate(
            total_bytes=Sum('file_size', default=0)
        )
        storage_bytes = storage_result['total_bytes'] or 0

        # Recent uploads (last 7 days)
        from django.utils import timezone
        week_ago = timezone.now() - timezone.timedelta(days=7)
        recent_uploads = CourseDocument.objects.filter(
            uploaded_at__gte=week_ago
        ).count()

        return {
            'total': total_docs,
            'folders': total_folders,
            'storage_bytes': storage_bytes,
            'storage_mb': round(storage_bytes / (1024 * 1024), 2),
            'recent_uploads_7d': recent_uploads,
        }
    except Exception as e:
        logger.warning(f"Failed to get document metrics: {e}")
        return {'total': 0, 'folders': 0, 'storage_bytes': 0, 'storage_mb': 0, 'recent_uploads_7d': 0}


# ─────────────────────────────────────────────────────────────────────────────
# Blog Metrics
# ─────────────────────────────────────────────────────────────────────────────


def _get_blog_metrics() -> dict:
    """Get blog-related KPIs from the database."""
    try:
        from blog.models import Noticia, Comentario

        total_posts = Noticia.objects.count()
        published_posts = Noticia.objects.filter(estado='publicado').count() if hasattr(Noticia, 'estado') else 0
        total_comments = Comentario.objects.count()

        return {
            'posts': total_posts,
            'published_posts': published_posts,
            'comments': total_comments,
        }
    except Exception as e:
        logger.warning(f"Failed to get blog metrics: {e}")
        return {'posts': 0, 'published_posts': 0, 'comments': 0}


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation Metrics
# ─────────────────────────────────────────────────────────────────────────────


def _get_evaluation_metrics() -> dict:
    """Get evaluation-related KPIs from the database."""
    try:
        from evaluaciones.models import Evaluacion

        total_evals = Evaluacion.objects.count()

        # Total questions across all evaluations
        total_questions = 0
        try:
            from evaluaciones.models import Pregunta
            total_questions = Pregunta.objects.count()
        except Exception:
            pass

        return {
            'total': total_evals,
            'questions': total_questions,
        }
    except Exception as e:
        logger.warning(f"Failed to get evaluation metrics: {e}")
        return {'total': 0, 'questions': 0}


# ─────────────────────────────────────────────────────────────────────────────
# Registration Trends (from Redis)
# ─────────────────────────────────────────────────────────────────────────────


def _get_registration_trends() -> dict:
    """Get registration trends from Redis metrics."""
    try:
        today = date.today().isoformat()
        from datetime import timedelta

        # Get counts from Redis business metrics
        reg_key = 'cfbc:biz:user_registration:daily'

        today_count = int(float(cache.hget(f'{reg_key}:{today}', 'total') or 0))

        # This week
        week_count = 0
        for i in range(7):
            day = (date.today() - timedelta(days=i)).isoformat()
            count = int(float(cache.hget(f'{reg_key}:{day}', 'total') or 0))
            week_count += count

        # This month
        month_count = 0
        for i in range(30):
            day = (date.today() - timedelta(days=i)).isoformat()
            count = int(float(cache.hget(f'{reg_key}:{day}', 'total') or 0))
            month_count += count

        return {
            'today': today_count,
            'this_week': week_count,
            'this_month': month_count,
        }
    except Exception as e:
        logger.debug(f"Failed to get registration trends: {e}")
        return {'today': 0, 'this_week': 0, 'this_month': 0}


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions for Views/Signals
# ─────────────────────────────────────────────────────────────────────────────


def record_user_registration(rol: str = 'estudiante') -> None:
    """Record a user registration event."""
    record_metric('user_registration', {'role': rol})


def record_document_upload(curso_id: int, file_size: int) -> None:
    """Record a document upload event."""
    record_metric('document_upload', {
        'curso_id': str(curso_id),
    }, value=file_size)


def record_document_download(curso_id: int, student_id: int) -> None:
    """Record a document download event."""
    record_metric('document_download', {
        'curso_id': str(curso_id),
    })


def record_evaluation_response(evaluacion_id: int) -> None:
    """Record an evaluation response."""
    record_metric('evaluation_response', {
        'evaluacion_id': str(evaluacion_id),
    })


def record_blog_comment(noticia_id: int) -> None:
    """Record a blog comment."""
    record_metric('blog_comment', {
        'noticia_id': str(noticia_id),
    })
