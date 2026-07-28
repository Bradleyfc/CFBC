"""
Django REST Framework serializers for Principal app.

Validates: Requirements 11.3, 11.4, 10.6, 10.8, 10.9
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import Registro
from .models import Curso, CursoAcademico, Matriculas, CourseApplication, Calificaciones, Asistencia


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Curso model."""
    
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    dynamic_status = serializers.CharField(source='get_dynamic_status', read_only=True)
    dynamic_status_display = serializers.CharField(source='get_dynamic_status_display', read_only=True)
    area_display = serializers.CharField(source='get_area_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    curso_academico_nombre = serializers.CharField(source='curso_academico.nombre', read_only=True, allow_null=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Curso
        fields = [
            'id',
            'name',
            'description',
            'area',
            'area_display',
            'tipo',
            'tipo_display',
            'teacher',
            'teacher_name',
            'teacher_username',
            'class_quantity',
            'status',
            'status_display',
            'dynamic_status',
            'dynamic_status_display',
            'curso_academico',
            'curso_academico_nombre',
            'enrollment_deadline',
            'start_date',
            'image_url',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = [
            'id',
            'fecha_creacion',
            'fecha_actualizacion',
            'dynamic_status',
            'dynamic_status_display',
        ]
    
    def get_image_url(self, obj):
        """Build absolute URL for the course image."""
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for student profile (Registro model).
    Excludes sensitive data like password hashes.
    """
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Registro
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'nacionalidad',
            'carnet',
            'sexo',
            'image_url',
            'address',
            'location',
            'provincia',
            'telephone',
            'movil',
        ]
        # Exclude sensitive fields - password is never included
    
    def get_image_url(self, obj):
        """Build absolute URL for the profile image."""
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Matriculas model.
    Includes related course details.
    """
    
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_area = serializers.CharField(source='course.area', read_only=True)
    course_area_display = serializers.CharField(source='course.get_area_display', read_only=True)
    course_tipo = serializers.CharField(source='course.tipo', read_only=True)
    course_tipo_display = serializers.CharField(source='course.get_tipo_display', read_only=True)
    course_teacher_name = serializers.CharField(source='course.teacher.get_full_name', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    curso_academico_nombre = serializers.CharField(source='curso_academico.nombre', read_only=True, allow_null=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    
    class Meta:
        model = Matriculas
        fields = [
            'id',
            'course',
            'course_id',
            'course_name',
            'course_area',
            'course_area_display',
            'course_tipo',
            'course_tipo_display',
            'course_teacher_name',
            'student',
            'student_username',
            'activo',
            'curso_academico',
            'curso_academico_nombre',
            'semestre',
            'fecha_matricula',
            'estado',
            'estado_display',
        ]
        read_only_fields = ['id', 'fecha_matricula']


class CourseAcademicoSerializer(serializers.ModelSerializer):
    """Serializer for CursoAcademico model."""
    
    class Meta:
        model = CursoAcademico
        fields = ['id', 'nombre', 'activo', 'archivado', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


# ===== Course Application Serializers =====
# Android App: Student applies to courses

class CourseApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseApplication model.
    
    Students apply to courses before being enrolled.
    Admins/teachers can approve or reject applications.
    
    Validates Requirements: 10.8, 4.2
    """
    
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_area = serializers.CharField(source='course.area', read_only=True)
    course_area_display = serializers.CharField(source='course.get_area_display', read_only=True)
    course_teacher_name = serializers.CharField(source='course.teacher.get_full_name', read_only=True, allow_null=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseApplication
        fields = [
            'id',
            'course',
            'course_name',
            'course_area',
            'course_area_display',
            'course_teacher_name',
            'student',
            'student_username',
            'status',
            'status_display',
            'submission_date',
            'processed_date',
            'notes',
        ]
        read_only_fields = [
            'id',
            'student',
            'submission_date',
            'processed_date',
            'status',
        ]
    
    def get_status_display(self, obj):
        """Get human-readable status."""
        return obj.get_status_display()


class GradeSerializer(serializers.ModelSerializer):
    """
    Serializer for student grades (Calificaciones).
    Includes related course and enrollment details.
    """
    
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_area = serializers.CharField(source='course.area', read_only=True)
    course_tipo = serializers.CharField(source='course.tipo', read_only=True)
    average = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)
    curso_academico_nombre = serializers.CharField(source='curso_academico.nombre', read_only=True, allow_null=True)
    semestre_numero = serializers.IntegerField(source='semestre.numero_semestre', read_only=True, allow_null=True)
    notas_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Calificaciones
        fields = [
            'id',
            'course',
            'course_name',
            'course_area',
            'course_tipo',
            'average',
            'curso_academico',
            'curso_academico_nombre',
            'semestre',
            'semestre_numero',
            'notas_count',
        ]
    
    def get_notas_count(self, obj):
        return obj.notas.count()


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for student attendance (Asistencia).
    """
    
    course_name = serializers.CharField(source='course.name', read_only=True)
    
    class Meta:
        model = Asistencia
        fields = [
            'id',
            'course',
            'course_name',
            'date',
            'presente',
            'semestre',
        ]


class HomePageDataSerializer(serializers.Serializer):
    """
    Serializer combining courses and latest news for home page.
    Returns available courses (limit 10) + latest blog posts (limit 5).
    """
    
    available_courses = CourseSerializer(many=True, read_only=True)
    latest_news = serializers.SerializerMethodField()
    
    def get_latest_news(self, obj):
        """
        Get latest news from blog.
        This will be populated by the view using BlogPostListSerializer.
        """
        # Import here to avoid circular dependency
        from blog.serializers import BlogPostListSerializer
        
        if isinstance(obj, dict) and 'latest_news' in obj:
            return BlogPostListSerializer(obj['latest_news'], many=True, context=self.context).data
        return []
