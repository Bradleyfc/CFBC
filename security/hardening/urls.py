"""
URL configuration for Application Hardening Service.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('.well-known/security.txt', views.security_txt, name='security_txt'),
    path('.well-known/security-policy', views.security_policy, name='security_policy'),
    path('security/headers-check/', views.check_headers, name='security_headers_check'),
]
