"""
Security Dashboard Views.

Provides dedicated security dashboard with charts and metrics.
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from security.models import (
    SecurityAuditLog, AuthorizationAuditLog, WAFRule,
    SecurityReport, ComplianceCheck, UserSecurityProfile,
    APIKey, JWTSession
)


def admin_required(view_func):
    """Decorator that requires user to be admin staff."""
    def check_admin(user):
        return user.is_authenticated and user.is_staff
    return user_passes_test(check_admin)(view_func)


@admin_required
def security_dashboard(request):
    """
    Main security dashboard view.
    """
    # Get time ranges
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Get pagination parameters
    issues_page = request.GET.get('issues_page', 1)
    issues_per_page = 2  # Mostrar 2 problemas por página
    
    # Get all critical issues
    all_critical_issues = get_critical_issues(month_ago, now)
    
    # Paginate critical issues
    paginator = Paginator(all_critical_issues, issues_per_page)
    try:
        critical_issues_page = paginator.page(issues_page)
    except PageNotAnInteger:
        critical_issues_page = paginator.page(1)
    except EmptyPage:
        critical_issues_page = paginator.page(paginator.num_pages)
    
    # Collect dashboard data
    context = {
        'page_title': 'Dashboard de Seguridad',
        'today': today,
        
        # Security Audit Metrics
        'audit_metrics': get_audit_metrics(week_ago, now),
        
        # WAF Statistics
        'waf_stats': get_waf_statistics(month_ago, now),
        
        # Authentication Metrics
        'auth_metrics': get_auth_metrics(week_ago, now),
        
        # Compliance Status
        'compliance_status': get_compliance_status(),
        
        # Recent Security Reports
        'recent_reports': SecurityReport.objects.filter(
            generated_at__gte=month_ago
        ).order_by('-generated_at')[:10],
        
        # Critical Issues (paginated)
        'critical_issues': critical_issues_page,
        'critical_issues_total': len(all_critical_issues),
        
        # Session Statistics
        'session_stats': get_session_statistics(),
    }
    
    return render(request, 'security/dashboard.html', context)


@admin_required
def security_dashboard_data(request):
    """
    API endpoint for dashboard chart data (AJAX).
    """
    time_range = request.GET.get('range', '7d')
    now = timezone.now()
    
    if time_range == '7d':
        start_date = now - timedelta(days=7)
    elif time_range == '30d':
        start_date = now - timedelta(days=30)
    else:  # 24h
        start_date = now - timedelta(hours=24)
    
    # Get data
    audit_timeline = get_audit_timeline(start_date, now)
    waf_attacks = get_waf_attack_types(start_date, now)
    auth_events = get_auth_events_timeline(start_date, now)
    severity_distribution = get_severity_distribution(start_date, now)
    
    data = {
        'audit_timeline': audit_timeline,
        'waf_attacks': waf_attacks,
        'auth_events': auth_events,
        'severity_distribution': severity_distribution,
        'compliance_chart': get_compliance_chart_data(),
    }
    
    # Debug: Log data to verify
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Dashboard data requested for range: {time_range}')
    logger.info(f'Audit timeline dates: {len(audit_timeline.get("dates", []))}')
    logger.info(f'Severity data: {severity_distribution.get("data", [])}')
    
    return JsonResponse(data)


# =============================================================================
# Data Collection Functions
# =============================================================================

def get_audit_metrics(start_date, end_date):
    """Get security audit metrics for the dashboard."""
    logs = SecurityAuditLog.objects.filter(
        timestamp__range=[start_date, end_date]
    )
    
    total_events = logs.count()
    failed_events = logs.filter(success=False).count()
    critical_events = logs.filter(severity='critical').count()
    
    # Group by event type
    event_types = logs.values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return {
        'total_events': total_events,
        'failed_events': failed_events,
        'critical_events': critical_events,
        'success_rate': ((total_events - failed_events) / total_events * 100) if total_events > 0 else 100,
        'top_event_types': list(event_types),
    }


def get_waf_statistics(start_date, end_date):
    """Get WAF statistics and attack patterns."""
    # Get active rules with hits
    active_rules = WAFRule.objects.filter(is_active=True)
    
    # Get recent WAF blocks from audit logs
    waf_blocks = SecurityAuditLog.objects.filter(
        event_type='waf_block',
        timestamp__range=[start_date, end_date]
    )
    
    total_blocks = waf_blocks.count()
    
    # Get attack categories
    attack_categories = defaultdict(int)
    for rule in active_rules:
        attack_categories[rule.category] += rule.hit_count
    
    # Top attacked paths (from WAF blocks)
    top_paths = waf_blocks.values('details__path').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return {
        'total_blocks': total_blocks,
        'active_rules': active_rules.count(),
        'attack_categories': dict(attack_categories),
        'top_attacked_paths': list(top_paths),
        'most_hit_rule': active_rules.order_by('-hit_count').first(),
    }


def get_auth_metrics(start_date, end_date):
    """Get authentication and authorization metrics."""
    # Authentication events
    auth_logs = SecurityAuditLog.objects.filter(
        event_type__in=['login', 'logout', '2fa_verification'],
        timestamp__range=[start_date, end_date]
    )
    
    # Failed logins
    failed_logins = SecurityAuditLog.objects.filter(
        event_type='login_failed',
        timestamp__range=[start_date, end_date]
    ).count()
    
    # Account lockouts - count from audit logs
    lockouts = SecurityAuditLog.objects.filter(
        event_type='account_lockout',
        timestamp__range=[start_date, end_date]
    ).count()
    
    # 2FA status
    users_with_2fa = UserSecurityProfile.objects.filter(
        two_factor_enabled=True
    ).count()
    total_users = UserSecurityProfile.objects.count()
    
    # Authorization decisions
    auth_decisions = AuthorizationAuditLog.objects.filter(
        timestamp__range=[start_date, end_date]
    )
    allowed_decisions = auth_decisions.filter(outcome='allowed').count()
    denied_decisions = auth_decisions.filter(outcome='denied').count()
    
    return {
        'total_auth_events': auth_logs.count(),
        'failed_logins': failed_logins,
        'account_lockouts': lockouts,
        'users_with_2fa': users_with_2fa,
        'total_users': total_users,
        'auth_decisions_total': auth_decisions.count(),
        'auth_allowed': allowed_decisions,
        'auth_denied': denied_decisions,
        'auth_denial_rate': (denied_decisions / auth_decisions.count() * 100) if auth_decisions.count() > 0 else 0,
    }


def get_compliance_status():
    """Get compliance status across different regulations."""
    # Get latest compliance checks
    compliance_checks = ComplianceCheck.objects.filter(
        checked_at__gte=timezone.now() - timedelta(days=7)
    )
    
    # Group by regulation
    regulations = {}
    for check in compliance_checks:
        reg = check.regulation
        if reg not in regulations:
            regulations[reg] = {'total': 0, 'passed': 0}
        regulations[reg]['total'] += 1
        if check.passed:
            regulations[reg]['passed'] += 1
    
    # Calculate percentages
    for reg, data in regulations.items():
        data['percentage'] = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
    
    # Get OWASP compliance specifically
    owasp_checks = compliance_checks.filter(regulation='owasp')
    owasp_passed = owasp_checks.filter(passed=True).count()
    owasp_total = owasp_checks.count()
    
    return {
        'regulations': regulations,
        'owasp_score': (owasp_passed / owasp_total * 100) if owasp_total > 0 else 0,
        'total_checks': compliance_checks.count(),
        'passed_checks': compliance_checks.filter(passed=True).count(),
    }


def get_critical_issues(start_date, end_date):
    """Get critical security issues from reports and audit logs."""
    # Get critical issues from security reports
    critical_reports = SecurityReport.objects.filter(
        generated_at__range=[start_date, end_date]
    )[:10]
    
    issues = []
    
    # Process reports
    for report in critical_reports:
        if report.findings and isinstance(report.findings, list):
            for finding in report.findings:
                if isinstance(finding, dict) and finding.get('severity') == 'critical':
                    issues.append({
                        'report_id': str(report.report_id),
                        'description': finding.get('description', 'Finding crítico'),
                        'generated_at': report.generated_at,
                        'scan_type': report.scan_type,
                        'source': 'report',
                        'origin': 'security',
                        'origin_label': 'Security Scan',
                        'origin_icon': 'fa-shield-alt',
                        'origin_color': 'red',
                        'should_display': True,
                        'reason': 'Vulnerability detectada en escaneo',
                        'attack_details': ''
                    })
    
    # Get critical issues from audit logs
    critical_logs = SecurityAuditLog.objects.filter(
        timestamp__range=[start_date, end_date],
        severity='critical'
    ).order_by('-timestamp')[:50]  # Obtener más para filtrar y paginar
    
    for log in critical_logs:
        # Determinar origen y si debe mostrarse
        origin_info = classify_event_origin(log)
        
        # SOLO agregar si should_display=True
        if not origin_info.get('should_display', True):
            continue
        
        issues.append({
            'report_id': f'AUDIT-{str(log.event_id)[:8]}',
            'description': f'{log.get_event_type_display()}: {log.action}',
            'generated_at': log.timestamp,
            'scan_type': log.event_type,
            'source': 'audit',
            'ip_address': log.ip_address,
            'event_type': log.event_type,
            'action': log.action,
            'details': log.details,
            **origin_info
        })
    
    # Ordenar por fecha (más recientes primero)
    issues.sort(key=lambda x: x['generated_at'], reverse=True)
    
    return issues  # Retornar todos para que el paginador los maneje


def classify_event_origin(log):
    """
    Classify the origin of a security event.
    Returns dict with origin, origin_label, origin_icon, origin_color, should_display.
    """
    # WAF blocks
    if log.action == 'waf_blocked':
        path = log.details.get('path', '') if log.details else ''
        rule_name = log.details.get('rule_name', '') if log.details else ''
        
        # Filtrar navegación normal y recursos estáticos
        NORMAL_PATHS = ['/', '/favicon.ico', '/static/', '/media/', '/admin/jsi18n/']
        is_normal_navigation = any(path.startswith(p) or path == p for p in NORMAL_PATHS)
        
        # Check if it's from localhost
        is_localhost = log.ip_address in ('127.0.0.1', '::1')
        
        # Si es navegación normal desde localhost, NO mostrar
        if is_localhost and is_normal_navigation:
            return {
                'origin': 'normal',
                'origin_label': 'Navegación Normal',
                'origin_icon': 'fa-browser',
                'origin_color': 'gray',
                'should_display': False,  # NO mostrar en dashboard
                'reason': f'Navegación normal a {path}'
            }
        
        # Si es localhost pero NO es navegación normal = test
        if is_localhost:
            return {
                'origin': 'test',
                'origin_label': 'Test/Desarrollo',
                'origin_icon': 'fa-flask',
                'origin_color': 'blue',
                'should_display': True,
                'reason': f'Patrón detectado: {rule_name}',
                'attack_details': f'Path: {path}'
            }
        
        # IP externa = ataque real
        return {
            'origin': 'attack',
            'origin_label': 'Ataque Real',
            'origin_icon': 'fa-exclamation-triangle',
            'origin_color': 'red',
            'should_display': True,
            'reason': f'Ataque desde IP externa: {log.ip_address}',
            'attack_details': f'Regla: {rule_name}, Path: {path}'
        }
    
    # Authentication failures from localhost = likely tests
    if log.event_type == 'auth' and not log.success:
        if log.ip_address in ('127.0.0.1', '::1'):
            return {
                'origin': 'test',
                'origin_label': 'Test/Desarrollo',
                'origin_icon': 'fa-flask',
                'origin_color': 'blue',
                'should_display': False,  # Tests no se muestran
                'reason': 'Test de autenticación'
            }
        # Fallo desde IP externa = posible ataque
        return {
            'origin': 'security',
            'origin_label': 'Intento de Acceso',
            'origin_icon': 'fa-user-lock',
            'origin_color': 'orange',
            'should_display': True,
            'reason': f'Intento fallido desde {log.ip_address}'
        }
    
    # File operations with errors
    if log.event_type == 'file_operation' and not log.success:
        return {
            'origin': 'test',
            'origin_label': 'Test/Desarrollo',
            'origin_icon': 'fa-flask',
            'origin_color': 'blue',
            'should_display': False,
            'reason': 'Test de operaciones de archivo'
        }
    
    # Security test events
    if 'test' in log.action.lower() or log.event_type == 'security_test':
        return {
            'origin': 'test',
            'origin_label': 'Test Automatizado',
            'origin_icon': 'fa-flask',
            'origin_color': 'blue',
            'should_display': False,
            'reason': 'Test automatizado del sistema'
        }
    
    # Default: security event real
    return {
        'origin': 'security',
        'origin_label': 'Evento de Seguridad',
        'origin_icon': 'fa-shield-alt',
        'origin_color': 'yellow',
        'should_display': True,
        'reason': 'Evento de seguridad detectado'
    }


def get_api_keys_status():
    """Get API keys statistics and status."""
    try:
        total_keys = APIKey.objects.count()
        active_keys = APIKey.objects.filter(is_active=True).count()
        expired_keys = APIKey.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        # Keys near expiration (within 7 days)
        week_from_now = timezone.now() + timedelta(days=7)
        expiring_soon = APIKey.objects.filter(
            expires_at__range=[timezone.now(), week_from_now],
            is_active=True
        ).count()
        
        # Daily usage stats
        high_usage_keys = APIKey.objects.filter(
            daily_used__gte=8000  # More than 80% of typical 10,000 limit
        ).count()
        
        return {
            'total_keys': total_keys,
            'active_keys': active_keys,
            'expired_keys': expired_keys,
            'expiring_soon': expiring_soon,
            'high_usage_keys': high_usage_keys,
            'active_percentage': (active_keys / total_keys * 100) if total_keys > 0 else 0,
        }
    except Exception:
        # Return default values if there's an issue
        return {
            'total_keys': 0,
            'active_keys': 0,
            'expired_keys': 0,
            'expiring_soon': 0,
            'high_usage_keys': 0,
            'active_percentage': 0,
        }


def get_session_statistics():
    """Get session and JWT statistics."""
    try:
        active_sessions = JWTSession.objects.filter(
            is_active=True,
            access_token_expires__gt=timezone.now()
        ).count()
        
        expired_sessions = JWTSession.objects.filter(
            access_token_expires__lte=timezone.now()
        ).count()
        
        # Sessions by user (top 5)
        sessions_by_user = JWTSession.objects.values(
            'user__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return {
            'active_sessions': active_sessions,
            'expired_sessions': expired_sessions,
            'sessions_by_user': list(sessions_by_user),
        }
    except Exception:
        # Return default values if there's an issue
        return {
            'active_sessions': 0,
            'expired_sessions': 0,
            'sessions_by_user': [],
        }


def get_audit_timeline(start_date, end_date):
    """
    Get timeline data for audit events chart.
    Genera SIEMPRE los últimos 7 días en el eje X, incluso si no hay datos.
    """
    # Obtener TODOS los logs sin filtrar
    logs = SecurityAuditLog.objects.filter(
        timestamp__range=[start_date, end_date]
    )
    
    # Generar todos los días en el rango (últimos 7 días)
    timeline = {}
    current_date = end_date.date()
    start = start_date.date()
    
    # Generar array con todos los días del rango
    while current_date >= start:
        date_str = current_date.strftime('%Y-%m-%d')
        timeline[date_str] = {'total': 0, 'critical': 0}
        current_date -= timedelta(days=1)
    
    # Llenar con datos reales si existen
    for log in logs:
        date_str = log.timestamp.strftime('%Y-%m-%d')
        if date_str in timeline:
            timeline[date_str]['total'] += 1
            # Check severity usando el campo directo
            if hasattr(log, 'severity') and log.severity == 'critical':
                timeline[date_str]['critical'] += 1
    
    # Ordenar las fechas cronológicamente (más antiguo a más reciente)
    dates = sorted(timeline.keys())
    
    # Formatear fechas para mostrar en el eje X (formato más legible)
    formatted_dates = []
    for date_str in dates:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Formato: "18 Jul" o "Lun 18" dependiendo de lo que prefieras
        formatted_dates.append(date_obj.strftime('%d %b'))
    
    result = {
        'dates': formatted_dates,
        'total_events': [timeline[d]['total'] for d in dates],
        'critical_events': [timeline[d]['critical'] for d in dates],
    }
    
    return result


def get_waf_attack_types(start_date, end_date):
    """Get WAF attack types distribution."""
    # Obtener todos los eventos WAF en el rango de fechas
    waf_blocks = SecurityAuditLog.objects.filter(
        event_type='waf_block',
        timestamp__range=[start_date, end_date]
    )
    
    # Contar por categoría desde los details de los logs
    categories = defaultdict(int)
    for block in waf_blocks:
        if block.details and isinstance(block.details, dict):
            category = block.details.get('category', 'unknown')
            categories[category] += 1
    
    # Si no hay datos de logs, obtener de las reglas WAF activas
    if not categories:
        waf_rules = WAFRule.objects.filter(is_active=True)
        for rule in waf_rules:
            if rule.hit_count > 0:
                categories[rule.category] += rule.hit_count
    
    # Si aún no hay datos, mostrar las categorías disponibles con 0
    if not categories:
        default_categories = ['sql_injection', 'xss', 'path_traversal', 'command_injection', 'sensitive_data']
        for cat in default_categories:
            categories[cat] = 0
    
    result = {
        'labels': list(categories.keys()),
        'data': list(categories.values()),
    }
    
    return result


def get_auth_events_timeline(start_date, end_date):
    """
    Get authentication events timeline.
    Genera SIEMPRE los últimos 7 días en el eje X, incluso si no hay datos.
    """
    auth_logs = SecurityAuditLog.objects.filter(
        event_type__in=['login', 'login_failed', 'logout'],
        timestamp__range=[start_date, end_date]
    )
    
    # Generar todos los días en el rango (últimos 7 días)
    timeline = {}
    current_date = end_date.date()
    start = start_date.date()
    
    # Generar array con todos los días del rango
    while current_date >= start:
        date_str = current_date.strftime('%Y-%m-%d')
        timeline[date_str] = {'login': 0, 'failed': 0, 'logout': 0}
        current_date -= timedelta(days=1)
    
    # Llenar con datos reales si existen
    for log in auth_logs:
        date_str = log.timestamp.strftime('%Y-%m-%d')
        if date_str in timeline:
            if log.event_type == 'login':
                timeline[date_str]['login'] += 1
            elif log.event_type == 'login_failed':
                timeline[date_str]['failed'] += 1
            elif log.event_type == 'logout':
                timeline[date_str]['logout'] += 1
    
    # Ordenar las fechas cronológicamente
    dates = sorted(timeline.keys())
    
    # Formatear fechas para mostrar en el eje X
    formatted_dates = []
    for date_str in dates:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_dates.append(date_obj.strftime('%d %b'))
    
    result = {
        'dates': formatted_dates,
        'logins': [timeline[d]['login'] for d in dates],
        'failed_logins': [timeline[d]['failed'] for d in dates],
        'logouts': [timeline[d]['logout'] for d in dates],
    }
    
    return result


def get_compliance_chart_data():
    """Get compliance data for radar chart."""
    checks = ComplianceCheck.objects.filter(
        checked_at__gte=timezone.now() - timedelta(days=30)
    )
    
    categories = defaultdict(lambda: {'total': 0, 'passed': 0})
    for check in checks:
        # Extract category from check_name
        category = check.check_name.split(':')[0] if ':' in check.check_name else 'General'
        categories[category]['total'] += 1
        if check.passed:
            categories[category]['passed'] += 1
    
    # Calculate percentages
    labels = []
    data = []
    for category, stats in categories.items():
        if stats['total'] > 0:
            labels.append(category)
            data.append((stats['passed'] / stats['total']) * 100)
    
    return {
        'labels': labels,
        'data': data,
    }


def get_severity_distribution(start_date, end_date):
    """
    Get severity distribution of security events.
    NO FILTRA eventos - muestra todos para estadísticas.
    """
    # Obtener TODOS los logs sin filtrar
    logs = SecurityAuditLog.objects.filter(
        timestamp__range=[start_date, end_date]
    )
    
    # Contar por severidad directamente
    severities = {
        'critical': 0,
        'error': 0,
        'warning': 0,
        'info': 0
    }
    
    for log in logs:
        severity_value = str(log.severity).lower()
        if severity_value in severities:
            severities[severity_value] += 1
    
    result = {
        'labels': ['Crítico', 'Error', 'Advertencia', 'Info'],
        'data': [
            severities['critical'],
            severities['error'],
            severities['warning'],
            severities['info']
        ],
        'colors': ['#dc3545', '#fd7e14', '#ffc107', '#17a2b8'],
    }
    
    return result