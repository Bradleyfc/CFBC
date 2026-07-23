"""
Views for Authentication Service.
"""

import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from security.models import UserSecurityProfile, SecurityAuditLog
from security.auth.services import (
    TOTPService, SessionSecurityService, AccountLockoutService,
)


@login_required
@require_http_methods(['GET', 'POST'])
def enable_2fa(request):
    """Activa 2FA para el usuario."""
    profile, _ = UserSecurityProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if profile.two_factor_enabled:
            return JsonResponse({'success': True, 'message': '2FA ya está activado.'})

        # Generar secreto y códigos de respaldo
        secret = TOTPService.generate_secret()
        backup_codes = TOTPService.generate_backup_codes()
        hashed_codes = TOTPService.hash_backup_codes(backup_codes)

        # Guardar en perfil
        profile.totp_secret = secret
        profile.backup_codes = hashed_codes
        profile.two_factor_enabled = True
        profile.save()

        # Generar URI para QR
        uri = TOTPService.get_totp_uri(secret, request.user.username)

        # Registrar evento
        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            user=request.user,
            action='2fa_enabled',
            resource='2fa',
            success=True,
        )

        return JsonResponse({
            'success': True,
            'secret': secret,
            'uri': uri,
            'backup_codes': backup_codes,
            'message': '2FA activado exitosamente. Guarda tus códigos de respaldo.',
        })

    # GET: Mostrar formulario
    return render(request, 'security/enable_2fa.html', {
        'already_enabled': profile.two_factor_enabled,
    })


@login_required
@require_http_methods(['POST'])
def disable_2fa(request):
    """Desactiva 2FA para el usuario."""
    profile, _ = UserSecurityProfile.objects.get_or_create(user=request.user)

    if not profile.two_factor_enabled:
        return JsonResponse({'success': False, 'error': '2FA no está activado.'})

    # Verificar código antes de desactivar
    code = request.POST.get('code', '')
    if not TOTPService.verify_code(profile.totp_secret, code):
        return JsonResponse({'success': False, 'error': 'Código TOTP inválido.'})

    profile.totp_secret = None
    profile.backup_codes = []
    profile.two_factor_enabled = False
    profile.last_2fa_verification = None
    profile.save()

    SecurityAuditLog.objects.create(
        event_type=SecurityAuditLog.EventTypes.AUTH,
        user=request.user,
        action='2fa_disabled',
        resource='2fa',
        success=True,
    )

    return JsonResponse({'success': True, 'message': '2FA desactivado exitosamente.'})


@login_required
@require_http_methods(['POST'])
def verify_2fa(request):
    """Verifica un código 2FA."""
    profile, _ = UserSecurityProfile.objects.get_or_create(user=request.user)
    code = request.POST.get('code', '')

    if not profile.two_factor_enabled:
        return JsonResponse({'success': False, 'error': '2FA no está activado.'})

    # Intentar verificación TOTP
    if TOTPService.verify_code(profile.totp_secret, code):
        profile.last_2fa_verification = timezone.now()
        profile.save(update_fields=['last_2fa_verification'])

        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            user=request.user,
            action='2fa_verified',
            resource='2fa',
            success=True,
        )

        return JsonResponse({'success': True, 'message': 'Código verificado exitosamente.'})

    # Intentar verificación con código de respaldo
    if TOTPService.verify_backup_code(profile.backup_codes, code):
        profile.last_2fa_verification = timezone.now()
        profile.save(update_fields=['last_2fa_verification'])

        SecurityAuditLog.objects.create(
            event_type=SecurityAuditLog.EventTypes.AUTH,
            user=request.user,
            action='2fa_verified_backup',
            resource='2fa',
            success=True,
        )

        return JsonResponse({'success': True, 'message': 'Código de respaldo válido.'})

    SecurityAuditLog.objects.create(
        event_type=SecurityAuditLog.EventTypes.AUTH,
        user=request.user,
        action='2fa_verification_failed',
        resource='2fa',
        success=False,
    )

    return JsonResponse({'success': False, 'error': 'Código inválido.'})


@login_required
@require_http_methods(['GET'])
def get_backup_codes(request):
    """Obtiene los códigos de respaldo del usuario."""
    profile, _ = UserSecurityProfile.objects.get_or_create(user=request.user)

    if not profile.two_factor_enabled:
        return JsonResponse({'success': False, 'error': '2FA no está activado.'})

    # Verificar contraseña para mostrar códigos
    return JsonResponse({
        'success': True,
        'backup_codes_count': len(profile.backup_codes),
        'message': 'Los códigos de respaldo se muestran en la página de configuración.',
    })


@login_required
@require_http_methods(['GET'])
def list_sessions(request):
    """Lista las sesiones activas del usuario."""
    active_count = SessionSecurityService.get_active_session_count(request.user)
    exceeded = SessionSecurityService.check_concurrent_sessions(request.user)

    return JsonResponse({
        'active_sessions': active_count,
        'max_sessions': 3,
        'limit_exceeded': exceeded,
    })


@login_required
@require_http_methods(['POST'])
def invalidate_all_sessions(request):
    """Invalida todas las sesiones del usuario."""
    count = SessionSecurityService.invalidate_all_sessions(request.user)

    return JsonResponse({
        'success': True,
        'invalidated_count': count,
        'message': f'{count} sesión(es) invalidadas.',
    })
