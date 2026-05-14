from django.contrib import admin

from .models import (
    Evaluacion,
    PreguntaEvaluacion,
    OpcionEvaluacion,
    IntentoEvaluacion,
    RespuestaIntento,
    CalificacionEvaluacion,
)


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ["titulo", "curso", "tipo", "estado", "fecha_creacion"]
    list_filter = ["tipo", "estado", "curso"]
    search_fields = ["titulo"]


@admin.register(PreguntaEvaluacion)
class PreguntaEvaluacionAdmin(admin.ModelAdmin):
    list_display = ["texto", "evaluacion", "tipo", "requerida", "orden"]
    list_filter = ["tipo", "requerida"]
    search_fields = ["texto"]


@admin.register(OpcionEvaluacion)
class OpcionEvaluacionAdmin(admin.ModelAdmin):
    list_display = ["texto", "pregunta", "es_correcta", "orden"]
    list_filter = ["es_correcta"]
    search_fields = ["texto"]


@admin.register(IntentoEvaluacion)
class IntentoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ["evaluacion", "estudiante", "estado", "fecha_envio"]
    list_filter = ["estado"]
    search_fields = ["estudiante__username", "evaluacion__titulo"]


@admin.register(RespuestaIntento)
class RespuestaIntentoAdmin(admin.ModelAdmin):
    list_display = ["intento", "pregunta"]
    list_filter = ["pregunta__tipo"]
    search_fields = ["intento__estudiante__username"]


@admin.register(CalificacionEvaluacion)
class CalificacionEvaluacionAdmin(admin.ModelAdmin):
    list_display = ["intento", "puntaje", "es_automatica", "fecha_calificacion"]
    list_filter = ["es_automatica"]
    search_fields = ["intento__estudiante__username"]
