"""
Chatbot URL Configuration
"""
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # API endpoints
    path('ask/', views.chatbot_ask, name='ask'),
    path('feedback/', views.chatbot_feedback, name='feedback'),
    path('status/', views.chatbot_status, name='status'),
    path('stats/', views.chatbot_stats, name='stats'),
    path('history/', views.chatbot_history, name='history'),
    path('clear-history/', views.chatbot_clear_history, name='clear_history'),
    
    # Widget view
    path('widget/', views.chatbot_widget, name='widget'),
]