"""
Django REST Framework API views for Evaluaciones app.

Provides:
- Student evaluations list (published evaluations for enrolled courses with attempt status)
- Academic history (past completed/archived enrollments with grades)

Validates Requirements: 6.11, 6.12, 10.16, 10.17
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Evaluacion, IntentoEvaluacion
from .serializers import StudentEvaluationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_evaluations_view(request):
    """
    GET endpoint returning published evaluations for the authenticated student's
    enrolled courses, including their attempt status and grades.

    The response includes:
    - Evaluation metadata (title, description, type, deadline)
    - Course context (course_id, course_name)
    - Student's attempt status (pendiente, enviado, calificado)
    - Grade details if the attempt has been graded

    Validates Requirements: 6.11, 10.16
    """
    from principal.models import Matriculas

    # Get courses where the student has active enrollments
    enrolled_course_ids = Matriculas.objects.filter(
        student=request.user,
        activo=True,
    ).values_list('course_id', flat=True).distinct()

    # Get published evaluations for those courses
    evaluations = Evaluacion.objects.filter(
        curso_id__in=enrolled_course_ids,
        estado='publicada',
    ).select_related('curso').order_by('-fecha_creacion')

    serializer = StudentEvaluationSerializer(
        evaluations,
        many=True,
        context={'request': request},
    )
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_history_view(request):
    """
    GET endpoint returning the authenticated student's academic history.

    Returns past enrollments (inactive/archived) with course details,
    grades, and academic year context.

    Response format:
    [
        {
            "id": 1,
            "course_id": 5,
            "course_name": "Inglés Básico",
            "course_area": "idiomas",
            "course_tipo": "curso",
            "curso_academico": "2025-2026",
            "estado": "A",
            "estado_display": "Aprobado",
            "fecha_matricula": "2025-01-15",
            "average": 8.5,
            "evaluaciones_count": 12
        }
    ]

    Validates Requirements: 6.12, 10.17
    """
    from principal.models import Matriculas, Calificaciones

    # Get past (inactive) enrollments with related data
    past_enrollments = Matriculas.objects.filter(
        student=request.user,
        activo=False,
    ).select_related(
        'course',
        'curso_academico',
    ).order_by('-fecha_matricula')

    # Enrich with grades data
    history = []
    for enrollment in past_enrollments:
        # Get the grade for this enrollment
        try:
            cal = Calificaciones.objects.get(
                course=enrollment.course,
                student=request.user,
                curso_academico=enrollment.curso_academico,
            )
            average = float(cal.average) if cal.average else None
            evaluaciones_count = cal.notas.count()
        except Calificaciones.DoesNotExist:
            average = None
            evaluaciones_count = 0

        history.append({
            'id': enrollment.id,
            'course_id': enrollment.course.id,
            'course_name': enrollment.course.name,
            'course_area': enrollment.course.area,
            'course_area_display': enrollment.course.get_area_display(),
            'course_tipo': enrollment.course.tipo,
            'curso_academico': enrollment.curso_academico.nombre if enrollment.curso_academico else None,
            'estado': enrollment.estado,
            'estado_display': enrollment.get_estado_display(),
            'fecha_matricula': enrollment.fecha_matricula.isoformat() if enrollment.fecha_matricula else None,
            'average': average,
            'evaluaciones_count': evaluaciones_count,
        })

    return Response(history)
