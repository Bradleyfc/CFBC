"""
Django REST Framework API views for Principal app.

Provides public endpoints for courses and home page data.

Validates Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 10.3, 10.4
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from accounts.models import Registro
from .models import Curso, Matriculas, CourseApplication, Calificaciones, Asistencia
from .serializers import (
    CourseSerializer,
    HomePageDataSerializer,
    StudentProfileSerializer,
    EnrollmentSerializer,
    CourseApplicationSerializer,
    GradeSerializer,
    AttendanceSerializer,
)


# ===== Pagination =====

class CoursePagination(PageNumberPagination):
    """Pagination for courses - 20 items per page."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ===== Public Course Endpoints =====
# Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 10.3

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only ViewSet for available courses.
    
    Features:
    - Pagination (20 courses per page)
    - Filtering by area and tipo
    - Ordering by start_date (descending)
    - Only shows courses open for enrollment
    
    Validates Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 10.3
    """
    
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    pagination_class = CoursePagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['area', 'tipo']
    ordering = ['-start_date']
    
    def get_queryset(self):
        """
        Return courses with status indicating open for enrollment.
        Status 'I' = En etapa de inscripción.
        Orders by start_date descending (most recent first).
        """
        return Curso.objects.filter(
            status='I'
        ).select_related('teacher', 'curso_academico').order_by('-start_date')
    
    def list(self, request, *args, **kwargs):
        """
        List available courses with pagination and filtering.
        
        Query parameters:
        - area: Filter by course area (idiomas, humanidades, computacion, etc.)
        - tipo: Filter by course type (curso, diplomado, grado, taller)
        - page: Page number for pagination
        - page_size: Number of items per page (max 100)
        
        Validates Requirements: 2.2, 2.3, 2.4
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single course by ID.
        
        Validates Requirements: 2.1, 2.5
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# ===== Home Page Endpoint =====
# Requirements: 10.4

@api_view(['GET'])
@permission_classes([AllowAny])
def home_page_view(request):
    """
    GET endpoint returning available courses (limit 10) + latest news (limit 5).
    
    Returns:
    - available_courses: List of up to 10 courses open for enrollment
    - latest_news: List of up to 5 latest published blog posts
    
    Validates Requirements: 10.4
    """
    # Fetch available courses (status 'I' = En etapa de inscripción)
    # Limit to 10, order by start_date descending
    available_courses = Curso.objects.filter(
        status='I'
    ).select_related('teacher', 'curso_academico').order_by('-start_date')[:10]
    
    # Fetch latest published blog posts
    # Import here to avoid circular dependency
    from blog.models import Noticia
    
    latest_news = Noticia.objects.filter(
        estado='publicado',
        visibilidad__in=['publico', 'indexable']
    ).select_related('categoria', 'autor').order_by('-fecha_publicacion')[:5]
    
    # Prepare data for serializer
    data = {
        'available_courses': available_courses,
        'latest_news': latest_news
    }
    
    # Serialize the combined data
    serializer = HomePageDataSerializer(data, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


# ===== Authentication Endpoints =====
# Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 10.5

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST endpoint to authenticate user and return token + username + groups.
    
    Request body:
    {
        "username": "user123",
        "password": "password123"
    }
    
    Response (HTTP 200):
    {
        "token": "abc123...",
        "username": "user123",
        "groups": ["Estudiantes", "Blog Autor"]
    }
    
    Response (HTTP 401):
    {
        "detail": "Credenciales inválidas."
    }
    
    Validates Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 10.5
    """
    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Validate required fields
    if not username or not password:
        return Response(
            {'detail': 'Se requiere nombre de usuario y contraseña.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Credenciales inválidas.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Create or get token
    token, created = Token.objects.get_or_create(user=user)
    
    # Get user groups
    groups = list(user.groups.values_list('name', flat=True))
    
    # Return response
    return Response({
        'token': token.key,
        'username': user.username,
        'groups': groups
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    POST endpoint to invalidate authentication token.
    
    Deletes the user's authentication token.
    
    Response (HTTP 200):
    {
        "detail": "Sesión cerrada exitosamente."
    }
    
    Validates Requirements: 5.1, 5.2, 10.5
    """
    from rest_framework.authtoken.models import Token
    
    try:
        # Delete the user's token
        token = Token.objects.get(user=request.user)
        token.delete()
        
        return Response(
            {'detail': 'Sesión cerrada exitosamente.'},
            status=status.HTTP_200_OK
        )
    except Token.DoesNotExist:
        # Token doesn't exist, but logout is still successful
        return Response(
            {'detail': 'Sesión cerrada exitosamente.'},
            status=status.HTTP_200_OK
        )


# ===== Student Profile Endpoint =====
# Requirements: 4.1, 4.2, 4.3, 10.6

class StudentProfileView(APIView):
    """
    APIView for the authenticated student to view or update their profile.
    
    Uses APIView (not ViewSet) because the profile is a singleton resource
    tied to the authenticated user — no ID parameter is needed.
    
    Features:
    - GET: Retrieve own profile
    - PATCH: Update own profile fields
    - Creates a profile automatically if one doesn't exist yet
    - Only accessible to authenticated users
    
    Validates Requirements: 4.1, 4.2, 4.3, 10.6
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """
        Return the Registro profile for the authenticated user.
        Creates one if it doesn't exist yet.
        """
        user = self.request.user
        profile, created = Registro.objects.get_or_create(user=user)
        return profile
    
    def get(self, request):
        """
        GET endpoint to retrieve the authenticated user's profile.
        
        Response (HTTP 200):
        {
            "username": "user123",
            "email": "user@example.com",
            "first_name": "Juan",
            "last_name": "Pérez",
            "nacionalidad": "Nicaragüense",
            "carnet": "001-123456-7",
            "sexo": "M",
            "image_url": "http://...",
            "address": "Calle Principal",
            ...
        }
        
        Validates Requirements: 4.1, 10.6
        """
        profile = self.get_object()
        serializer = StudentProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        """
        PATCH endpoint to update the authenticated user's profile.
        
        Only the following fields can be updated:
        - nacionalidad, carnet, sexo, address, location, provincia,
          telephone, movil
        
        Fields like username, email, first_name, last_name are read-only.
        
        Request body (partial):
        {
            "nacionalidad": "Nicaragüense",
            "telephone": "505 8888-8888",
            "address": "Nueva Dirección"
        }
        
        Validates Requirements: 4.2, 4.3, 10.6
        """
        profile = self.get_object()
        serializer = StudentProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ===== Enrollment Endpoints =====
# Requirements: 4.4, 10.7

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for the authenticated student's enrollments.
    
    Features:
    - List own enrollments (ordered by fecha_matricula descending)
    - Filter by active status
    - Filter by course area
    - Only accessible to authenticated users
    
    Validates Requirements: 4.4, 10.7
    """
    
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CoursePagination
    
    def get_queryset(self):
        """
        Return enrollments for the authenticated user.
        Ordered by most recent enrollment date first.
        """
        return Matriculas.objects.filter(
            student=self.request.user
        ).select_related(
            'course', 'course__teacher', 'curso_academico', 'semestre'
        ).order_by('-fecha_matricula')
    
    def list(self, request, *args, **kwargs):
        """
        GET endpoint to list the authenticated user's enrollments.
        
        Query parameters:
        - activo: Filter by active status (1 or 0)
        
        Response (HTTP 200):
        [
            {
                "id": 1,
                "course_id": 5,
                "course_name": "Inglés Básico",
                "course_area": "idiomas",
                "course_area_display": "Idiomas",
                "course_tipo": "curso",
                "course_tipo_display": "Curso",
                "course_teacher_name": "Prof. María López",
                "student": 3,
                "student_username": "user123",
                "activo": true,
                "fecha_matricula": "2026-01-15",
                "estado": "P",
                "estado_display": "Activo"
            }
        ]
        
        Validates Requirements: 4.4, 10.7
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Optional filter by active status
        activo_filter = request.query_params.get('activo')
        if activo_filter is not None:
            if activo_filter.lower() in ['1', 'true']:
                queryset = queryset.filter(activo=True)
            elif activo_filter.lower() in ['0', 'false']:
                queryset = queryset.filter(activo=False)
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ===== Course Application Endpoints =====
# Requirements: 10.8, 4.2

class CourseApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for students to manage their course applications.
    
    Features:
    - POST: Apply to a course (creates pending application)
    - GET: List own applications
    - GET by ID: View application detail
    - POST cancel: Cancel a pending application
    
    The model's pre_save signal validates:
    - Student is not already enrolled
    - No duplicate pending applications
    
    Validates Requirements: 10.8, 4.2
    """
    
    serializer_class = CourseApplicationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CoursePagination
    
    def get_queryset(self):
        """
        Return applications for the authenticated user.
        Ordered by most recent submission first.
        """
        return CourseApplication.objects.filter(
            student=self.request.user
        ).select_related('course', 'course__teacher').order_by('-submission_date')
    
    def perform_create(self, serializer):
        """Set the student to the authenticated user when creating."""
        serializer.save(student=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        POST endpoint to apply to a course.
        
        Request body:
        {
            "course": 5
        }
        
        Response (HTTP 201):
        {
            "id": 1,
            "course": 5,
            "course_name": "Inglés Básico",
            "student": 3,
            "student_username": "user123",
            "status": "pending",
            "status_display": "Pendiente",
            "submission_date": "2026-07-26T10:30:00Z",
            "processed_date": null,
            "notes": ""
        }
        
        Validates Requirements: 10.8
        """
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        POST endpoint to cancel a pending application.

        Only pending applications can be cancelled.
        Only the application owner can cancel their application.

        Response (HTTP 200):
        {
            "detail": "Solicitud cancelada exitosamente."
        }

        Validates Requirements: 10.8
        """
        application = self.get_object()

        # Check ownership
        if application.student != request.user:
            return Response(
                {'detail': 'No puedes cancelar solicitudes de otros estudiantes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if cancellable
        if not application.can_be_cancelled():
            return Response(
                {'detail': 'Solo puedes cancelar solicitudes pendientes.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancel the application (delete it since it's student-initiated)
        application.delete()

        return Response(
            {'detail': 'Solicitud cancelada exitosamente.'},
            status=status.HTTP_200_OK
        )


# ===== Student Grades Endpoint =====
# Requirements: 6.9, 10.14

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_grades_view(request):
    """
    GET endpoint returning the authenticated student's grades.
    """
    grades = Calificaciones.objects.filter(
        student=request.user
    ).select_related('course', 'curso_academico', 'semestre').order_by('course__name')
    
    serializer = GradeSerializer(grades, many=True, context={'request': request})
    return Response(serializer.data)


# ===== Student Attendance Endpoint =====
# Requirements: 6.10, 10.15

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_view(request):
    """
    GET endpoint returning the authenticated student's attendance records.
    """
    course_id = request.query_params.get('course')
    
    query = Asistencia.objects.filter(
        student=request.user
    ).select_related('course', 'semestre').order_by('-date')
    
    if course_id:
        query = query.filter(course_id=course_id)
    
    serializer = AttendanceSerializer(query, many=True, context={'request': request})
    return Response(serializer.data)
