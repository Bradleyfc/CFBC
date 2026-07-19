"""
URL configuration for Authorization Service.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('roles/', views.list_roles, name='security_list_roles'),
    path('roles/create/', views.create_role, name='security_create_role'),
    path('roles/<int:role_id>/assign/', views.assign_role, name='security_assign_role'),
    path('roles/<int:role_id>/remove/', views.remove_role, name='security_remove_role'),
    path('permissions/check/', views.check_permission, name='security_check_permission'),
    path('policies/time-based/', views.list_time_policies, name='security_time_policies'),
]
