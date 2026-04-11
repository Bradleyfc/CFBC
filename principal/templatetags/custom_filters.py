from django import template

register = template.Library()

@register.filter
def filter_present_for_course(queryset, curso):
    return queryset.filter(presente=True, course=curso).count()

@register.filter
def filter_total_for_course(queryset, curso):
    return queryset.filter(course=curso).count()

@register.filter
def subtract(value, arg):
    return value - arg

from django.contrib.auth import get_user_model
from principal.models import Curso
from datetime import datetime

User = get_user_model()

@register.filter
def filter_asistencia(queryset, student_id):
    try:
        student = User.objects.get(id=student_id)
        return queryset.filter(student=student)
    except User.DoesNotExist:
        return queryset.none() # Return an empty queryset if student not found

@register.filter
def filter_by_date(queryset, date):
    return queryset.filter(date=date).first()

@register.filter
def join_strings(value, arg):
    return str(value) + str(arg)

@register.filter
def get_range(value, start=0):
    """
    Retorna un rango de números desde start hasta value
    Ejemplo: 5|get_range:1 retorna [1, 2, 3, 4, 5]
    """
    return range(start, int(value) + 1)

@register.filter
def map_max_notas(calificaciones):
    """
    Retorna el número máximo de notas entre todas las calificaciones
    """
    max_notas = 0
    for calificacion in calificaciones:
        num_notas = calificacion.notas.count()
        if num_notas > max_notas:
            max_notas = num_notas
    return max_notas

@register.filter
def get_item(dictionary, key):
    """Obtiene un valor de un diccionario usando una clave"""
    return dictionary.get(key, 0)