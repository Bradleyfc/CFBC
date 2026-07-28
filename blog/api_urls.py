"""
Django REST Framework URL routing for Blog app.

Provides API endpoints for:
- Public blog posts and categories
- Author post management
- Moderator reports and sanctions
- Editor post review and publishing

Validates Requirements: 10.11-10.22
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    BlogPostViewSet,
    CategoryViewSet,
    AuthorPostViewSet,
    ModeratorReportViewSet,
    ModeratorSanctionViewSet,
    moderator_metrics_view,
    EditorPostViewSet,
)

# ===== Router Configuration =====

# Public endpoints router
public_router = DefaultRouter()
public_router.register(r'posts', BlogPostViewSet, basename='blog-post')
public_router.register(r'categories', CategoryViewSet, basename='blog-category')

# Author endpoints router
author_router = DefaultRouter()
author_router.register(r'posts', AuthorPostViewSet, basename='author-post')

# Moderator endpoints router
moderator_router = DefaultRouter()
moderator_router.register(r'reports', ModeratorReportViewSet, basename='moderator-report')
moderator_router.register(r'sanctions', ModeratorSanctionViewSet, basename='moderator-sanction')

# Editor endpoints router
editor_router = DefaultRouter()
editor_router.register(r'posts', EditorPostViewSet, basename='editor-post')

# ===== URL Patterns =====

urlpatterns = [
    # Public blog endpoints
    path('', include(public_router.urls)),
    
    # Author endpoints
    path('author/', include(author_router.urls)),
    
    # Moderator endpoints
    path('moderator/', include(moderator_router.urls)),
    path('moderator/metrics/', moderator_metrics_view, name='moderator-metrics'),
    
    # Editor endpoints
    path('editor/', include(editor_router.urls)),
]
