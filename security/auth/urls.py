"""
URL configuration for Authentication Service.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('2fa/enable/', views.enable_2fa, name='security_enable_2fa'),
    path('2fa/disable/', views.disable_2fa, name='security_disable_2fa'),
    path('2fa/verify/', views.verify_2fa, name='security_verify_2fa'),
    path('2fa/backup-codes/', views.get_backup_codes, name='security_backup_codes'),
    path('sessions/', views.list_sessions, name='security_list_sessions'),
    path('sessions/invalidate-all/', views.invalidate_all_sessions, name='security_invalidate_sessions'),
]
