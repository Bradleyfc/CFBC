"""
Django REST Framework URL routing for Principal app.

Provides API endpoints for:
- Authentication (login/logout)
- Courses (list/detail with filtering)
- Home page data (courses + blog)

Validates Requirements: 10.1-10.10
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    CourseViewSet,
    StudentProfileView,
    EnrollmentViewSet,
    CourseApplicationViewSet,
    login_view,
    logout_view,
    home_page_view,
    student_grades_view,
    student_attendance_view,
)
from evaluaciones.api_views import (
    student_evaluations_view,
    student_history_view,
)

# ===== Router Configuration =====

# Courses - public read-only
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')

# Enrollments - authenticated user's own enrollments (GET)
enrollment_router = DefaultRouter()
enrollment_router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')

# Course Applications - student can create, list, cancel
application_router = DefaultRouter()
application_router.register(r'applications', CourseApplicationViewSet, basename='application')

# ===== URL Patterns =====

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login_view, name='api-login'),
    path('auth/logout/', logout_view, name='api-logout'),
    
    # Student profile - singleton resource (no ID), uses APIView
    path('profile/', StudentProfileView.as_view(), name='api-profile'),
    
    # Home page data
    path('home/', home_page_view, name='api-home'),
    
    # Student sub-features
    path('grades/', student_grades_view, name='api-grades'),
    path('attendance/', student_attendance_view, name='api-attendance'),
    path('evaluations/', student_evaluations_view, name='api-evaluations'),
    path('history/', student_history_view, name='api-history'),

    # Router URLs
    path('', include(router.urls)),
    path('', include(enrollment_router.urls)),
    path('', include(application_router.urls)),
]
