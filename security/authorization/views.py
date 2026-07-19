"""
Views for Authorization Service.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404

from security.models import Role, UserRoleAssignment, TimeBasedAccessPolicy
from security.authorization.services import (
    RBACService, TimeBasedAccessService,
)


@staff_member_required
@require_http_methods(['GET'])
def list_roles(request):
    """Lista todos los roles del sistema."""
    roles = Role.objects.all().values('id', 'name', 'description', 'parent__name', 'is_system_role')
    return JsonResponse({'roles': list(roles)})


@staff_member_required
@require_http_methods(['POST'])
def create_role(request):
    """Crea un nuevo rol."""
    import json
    data = json.loads(request.body)

    role = RBACService.create_role(
        name=data.get('name', ''),
        permissions=data.get('permissions', []),
        description=data.get('description', ''),
        is_system_role=data.get('is_system_role', False),
    )

    return JsonResponse({
        'success': True,
        'role': {
            'id': role.id,
            'name': role.name,
            'description': role.description,
        }
    })


@staff_member_required
@require_http_methods(['POST'])
def assign_role(request, role_id):
    """Asigna un rol a un usuario."""
    data = json.loads(request.body)
    role = get_object_or_404(Role, id=role_id)
    user = get_object_or_404(User, id=data.get('user_id'))

    RBACService.assign_role(user=user, role=role, assigned_by=request.user)

    return JsonResponse({
        'success': True,
        'message': f'Rol "{role.name}" asignado a "{user.username}".'
    })


@staff_member_required
@require_http_methods(['POST'])
def remove_role(request, role_id):
    """Remueve un rol de un usuario."""
    data = json.loads(request.body)
    role = get_object_or_404(Role, id=role_id)
    user = get_object_or_404(User, id=data.get('user_id'))

    RBACService.remove_role(user=user, role=role)

    return JsonResponse({
        'success': True,
        'message': f'Rol "{role.name}" removido de "{user.username}".'
    })


@login_required
@require_http_methods(['POST'])
def check_permission(request):
    """Verifica si el usuario actual tiene un permiso."""
    data = json.loads(request.body)
    codename = data.get('permission', '')
    user = request.user

    has_perm = RBACService.check_permission(user, codename)
    time_ok = RBACService.check_time_based_access(user)

    return JsonResponse({
        'has_permission': has_perm,
        'time_access_allowed': time_ok,
        'can_proceed': has_perm and time_ok,
    })


@staff_member_required
@require_http_methods(['GET'])
def list_time_policies(request):
    """Lista las políticas de acceso por tiempo."""
    policies = TimeBasedAccessPolicy.objects.filter(is_active=True).values(
        'id', 'name', 'start_hour', 'end_hour', 'allowed_days', 'timezone'
    )
    return JsonResponse({'policies': list(policies)})
