"""
Custom template tags for security admin integration.
"""

from django import template
from django.urls import reverse
from django.contrib.auth import get_user_model

register = template.Library()


@register.inclusion_tag('security/admin/security_button.html', takes_context=True)
def security_admin_button(context):
    """
    Template tag that renders the security button in admin.
    """
    request = context.get('request')
    
    if not request or not request.user.is_authenticated or not request.user.is_staff:
        return {}
    
    return {
        'security_dashboard_url': reverse('security_dashboard'),
        'user': request.user,
    }


@register.simple_tag(takes_context=True)
def has_security_permission(context):
    """
    Check if user has permission to access security dashboard.
    """
    request = context.get('request')
    
    if not request or not request.user.is_authenticated:
        return False
    
    # Check if user is staff (admin)
    if not request.user.is_staff:
        return False
    
    # Additional permission checks can be added here
    # For example: request.user.has_perm('security.view_securityreport')
    
    return True