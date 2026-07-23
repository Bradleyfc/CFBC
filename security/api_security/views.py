"""
Views for API Security Service.
"""

import json
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from security.models import APIKey
from security.api_security.services import (
    APIKeyService, JWTTokenService, PerUserRateLimitService,
)


@login_required
@require_http_methods(['GET'])
def list_api_keys(request):
    """Lista las API keys del usuario actual."""
    keys = APIKeyService.get_user_api_keys(request.user)
    data = [{
        'id': k.id,
        'name': k.name,
        'key_prefix': k.key_prefix,
        'created_at': k.created_at.isoformat(),
        'expires_at': k.expires_at.isoformat(),
        'daily_used': k.daily_used,
        'daily_limit': k.daily_limit,
        'is_active': k.is_active,
    } for k in keys]
    return JsonResponse({'api_keys': data})


@login_required
@require_http_methods(['POST'])
def create_api_key(request):
    """Crea una nueva API key."""
    data = json.loads(request.body)
    name = data.get('name', 'API Key')
    expires_in_days = data.get('expires_in_days', 90)
    daily_limit = data.get('daily_limit', 10000)

    api_key = APIKeyService.create_api_key(
        user=request.user,
        name=name,
        expires_in_days=expires_in_days,
        daily_limit=daily_limit,
    )

    return JsonResponse({
        'success': True,
        'api_key': {
            'id': api_key.id,
            'name': api_key.name,
            'key': api_key.key,
            'key_prefix': api_key.key_prefix,
            'expires_at': api_key.expires_at.isoformat(),
            'daily_limit': api_key.daily_limit,
        },
        'warning': 'Guarda esta clave ahora. No podrás verla nuevamente.',
    })


@login_required
@require_http_methods(['POST'])
def revoke_api_key(request, key_id):
    """Revoca una API key."""
    from django.shortcuts import get_object_or_404
    api_key = get_object_or_404(APIKey, id=key_id, user=request.user)
    APIKeyService.revoke_api_key(api_key)

    return JsonResponse({
        'success': True,
        'message': f'API Key "{api_key.name}" revocada exitosamente.'
    })


@login_required
@require_http_methods(['POST'])
def generate_tokens(request):
    """Genera un par de tokens JWT."""
    access_token, refresh_token = JWTTokenService.generate_tokens(request.user)

    return JsonResponse({
        'success': True,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': JWTTokenService.ACCESS_TOKEN_EXPIRY_MINUTES * 60,
    })


@require_http_methods(['POST'])
def refresh_token(request):
    """Refresca un access token."""
    data = json.loads(request.body)
    refresh_token_str = data.get('refresh_token', '')

    new_access_token = JWTTokenService.refresh_access_token(refresh_token_str)

    if new_access_token:
        return JsonResponse({
            'success': True,
            'access_token': new_access_token,
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Refresh token inválido o expirado.',
        }, status=401)


@login_required
@require_http_methods(['GET'])
def rate_limit_status(request):
    """Obtiene el estado del rate limit del usuario."""
    result = PerUserRateLimitService.check_rate_limit(request.user)

    return JsonResponse({
        'is_allowed': result.is_allowed,
        'remaining': result.remaining,
        'limit': result.limit,
        'retry_after': result.retry_after,
    })
