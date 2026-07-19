"""
URL configuration for security app.
"""

from django.urls import path, include
from . import views_dashboard

urlpatterns = [
    # Authentication URLs
    path('auth/', include('security.auth.urls')),
    # Authorization URLs
    path('authorization/', include('security.authorization.urls')),
    # API Security URLs
    path('api/', include('security.api_security.urls')),
    # Hardening URLs (security.txt, etc.)
    path('', include('security.hardening.urls')),
    # Security Dashboard
    path('dashboard/', views_dashboard.security_dashboard, name='security_dashboard'),
    path('dashboard/data/', views_dashboard.security_dashboard_data, name='security_dashboard_data'),
]
