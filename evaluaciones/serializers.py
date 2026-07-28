"""
Django REST Framework serializers for Evaluaciones app.

Provides serializers for student-facing evaluation data:
- Published evaluations with attempt status
- Student attempt results and grades
- Academic history (past enrollments)

Validates Requirements: 6.11, 10.16
"""
from rest_framework import serializers
from .models import Evaluacion, IntentoEvaluacion, CalificacionEvaluacion


class EvaluationGradeSerializer(serializers.ModelSerializer):
    """Serializer for evaluation grades visible to students."""

    class Meta:
        model = CalificacionEvaluacion
        fields = [
            'puntaje',
            'comentario',
            'es_automatica',
            'fecha_calificacion',
        ]


class AttemptSerializer(serializers.ModelSerializer):
    """Serializer for student's evaluation attempts."""

    calificacion = EvaluationGradeSerializer(source='*', read_only=True)

    class Meta:
        model = IntentoEvaluacion
        fields = [
            'id',
            'evaluacion',
            'estado',
            'fecha_envio',
            'calificacion',
        ]

    def get_calificacion(self, obj):
        """Get the related grade if it exists."""
        cal = getattr(obj, 'calificacion', None)
        if cal:
            return EvaluationGradeSerializer(cal).data
        return None


class StudentEvaluationSerializer(serializers.ModelSerializer):
    """
    Serializer for evaluations visible to a specific student.
    Shows the evaluation metadata plus the student's attempt status.
    """

    course_name = serializers.CharField(source='curso.name', read_only=True)
    course_id = serializers.IntegerField(source='curso.id', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    attempt_status = serializers.SerializerMethodField()
    attempt_id = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()

    class Meta:
        model = Evaluacion
        fields = [
            'id',
            'titulo',
            'descripcion',
            'course_id',
            'course_name',
            'tipo',
            'tipo_display',
            'estado',
            'fecha_limite',
            'fecha_creacion',
            'attempt_status',
            'attempt_id',
            'grade',
        ]

    def get_attempt_status(self, obj):
        """Get the requesting student's attempt status for this evaluation."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            intento = IntentoEvaluacion.objects.get(
                evaluacion=obj,
                estudiante=request.user,
            )
            return intento.estado  # 'enviado' or 'calificado'
        except IntentoEvaluacion.DoesNotExist:
            return 'pendiente'

    def get_attempt_id(self, obj):
        """Get the ID of the student's attempt if it exists."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            intento = IntentoEvaluacion.objects.get(
                evaluacion=obj,
                estudiante=request.user,
            )
            return intento.id
        except IntentoEvaluacion.DoesNotExist:
            return None

    def get_grade(self, obj):
        """Get the student's grade for this evaluation if graded."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            intento = IntentoEvaluacion.objects.get(
                evaluacion=obj,
                estudiante=request.user,
            )
            cal = getattr(intento, 'calificacion', None)
            if cal:
                return EvaluationGradeSerializer(cal).data
        except (IntentoEvaluacion.DoesNotExist, AttributeError):
            pass
        return None
