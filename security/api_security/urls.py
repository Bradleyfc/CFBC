"""
URL configuration for API Security Service.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('keys/', views.list_api_keys, name='security_list_api_keys'),
    path('keys/create/', views.create_api_key, name='security_create_api_key'),
    path('keys/<int:key_id>/revoke/', views.revoke_api_key, name='security_revoke_api_key'),
    path('tokens/generate/', views.generate_tokens, name='security_generate_tokens'),
    path('tokens/refresh/', views.refresh_token, name='security_refresh_token'),
    path('rate-limit/status/', views.rate_limit_status, name='security_rate_limit_status'),
]
