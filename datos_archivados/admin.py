from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    CursoAcademicoArchivado, UsuarioArchivado, CursoArchivado, 
    MatriculaArchivada, CalificacionArchivada, NotaIndividualArchivada,
    AsistenciaArchivada, MigracionLog, DatoArchivadoDinamico
)

@admin.register(CursoAcademicoArchivado)
class CursoAcademicoArchivadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'id_original', 'activo', 'archivado', 'fecha_creacion', 'fecha_migracion']
    list_filter = ['activo', 'archivado', 'fecha_creacion', 'fecha_migracion']
    search_fields = ['nombre', 'id_original']
    readonly_fields = ['fecha_migracion']
    ordering = ['-fecha_creacion']

@admin.register(UsuarioArchivado)
class UsuarioArchivadoAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'first_name', 'last_name', 'email', 'carnet', 
        'grupo', 'usuario_vinculado', 'fecha_migracion'
    ]
    list_filter = [
        'sexo', 'grado', 'ocupacion', 'grupo', 'is_active', 
        'fecha_migracion'
    ]
    search_fields = [
        'username', 'first_name', 'last_name', 'email', 'carnet',
        'usuario_actual__username', 'usuario_actual__email'
    ]
    readonly_fields = ['fecha_migracion']
    raw_id_fields = ['usuario_actual']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id_original', 'username', 'first_name', 'last_name', 'email', 'date_joined', 'is_active')
        }),
        ('Datos Personales', {
            'fields': ('nacionalidad', 'carnet', 'sexo', 'address', 'location', 'provincia')
        }),
        ('Contacto', {
            'fields': ('telephone', 'movil')
        }),
        ('Información Académica/Laboral', {
            'fields': ('grado', 'ocupacion', 'titulo')
        }),
        ('Sistema', {
            'fields': ('grupo', 'usuario_actual', 'fecha_migracion')
        }),
    )
    
    def usuario_vinculado(self, obj):
        if obj.usuario_actual:
            url = reverse('admin:auth_user_change', args=[obj.usuario_actual.pk])
            return format_html('<a href="{}">{}</a>', url, obj.usuario_actual.username)
        return "No vinculado"
    usuario_vinculado.short_description = 'Usuario Actual'

@admin.register(CursoArchivado)
class CursoArchivadoAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'area', 'tipo', 'teacher_name', 'curso_academico', 
        'status', 'class_quantity', 'profesor_vinculado', 'fecha_migracion'
    ]
    list_filter = [
        'area', 'tipo', 'status', 'curso_academico', 
        'fecha_migracion'
    ]
    search_fields = [
        'name', 'teacher_name', 'description', 
        'teacher_actual__username', 'teacher_actual__first_name', 'teacher_actual__last_name'
    ]
    readonly_fields = ['fecha_migracion']
    raw_id_fields = ['teacher_actual']
    
    fieldsets = (
        ('Información del Curso', {
            'fields': ('id_original', 'name', 'description', 'area', 'tipo', 'class_quantity', 'status')
        }),
        ('Profesor Original', {
            'fields': ('teacher_id_original', 'teacher_name')
        }),
        ('Fechas', {
            'fields': ('enrollment_deadline', 'start_date')
        }),
        ('Sistema', {
            'fields': ('curso_academico', 'teacher_actual', 'fecha_migracion')
        }),
    )
    
    def profesor_vinculado(self, obj):
        if obj.teacher_actual:
            url = reverse('admin:auth_user_change', args=[obj.teacher_actual.pk])
            return format_html('<a href="{}">{}</a>', url, obj.teacher_actual.get_full_name())
        return "No vinculado"
    profesor_vinculado.short_description = 'Profesor Actual'

@admin.register(MatriculaArchivada)
class MatriculaArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'id_original', 'student', 'course', 'estado', 'activo', 
        'fecha_matricula', 'fecha_migracion'
    ]
    list_filter = [
        'estado', 'activo', 'fecha_matricula', 'course__area', 
        'course__curso_academico', 'fecha_migracion'
    ]
    search_fields = [
        'student__username', 'student__first_name', 'student__last_name',
        'course__name', 'matricula_actual__id'
    ]
    readonly_fields = ['fecha_migracion']
    # raw_id_fields = ['matricula_actual']
    
    # def matricula_vinculada(self, obj):
    #     if obj.matricula_actual:
    #         return format_html('Matrícula #{} vinculada', obj.matricula_actual.id)
    #     return "No vinculada"
    # matricula_vinculada.short_description = 'Matrícula Actual'

@admin.register(CalificacionArchivada)
class CalificacionArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'id_original', 'student', 'course', 'average', 'fecha_migracion'
    ]
    list_filter = [
        'course__area', 'course__curso_academico', 'fecha_migracion'
    ]
    search_fields = [
        'student__username', 'student__first_name', 'student__last_name',
        'course__name'
    ]
    readonly_fields = ['fecha_migracion']

class NotaIndividualArchivadaInline(admin.TabularInline):
    model = NotaIndividualArchivada
    extra = 0
    readonly_fields = ['fecha_migracion']

@admin.register(NotaIndividualArchivada)
class NotaIndividualArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'id_original', 'get_student', 'get_course', 'valor', 
        'fecha_creacion', 'fecha_migracion'
    ]
    list_filter = [
        'valor', 'fecha_creacion', 'calificacion__course__area', 
        'calificacion__course__curso_academico', 'fecha_migracion'
    ]
    search_fields = [
        'calificacion__student__username', 'calificacion__student__first_name',
        'calificacion__student__last_name', 'calificacion__course__name'
    ]
    readonly_fields = ['fecha_migracion']
    
    def get_student(self, obj):
        return obj.calificacion.student.get_full_name() or obj.calificacion.student.username
    get_student.short_description = 'Estudiante'
    
    def get_course(self, obj):
        return obj.calificacion.course.name
    get_course.short_description = 'Curso'

@admin.register(AsistenciaArchivada)
class AsistenciaArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'id_original', 'student', 'course', 'presente', 'date', 'fecha_migracion'
    ]
    list_filter = [
        'presente', 'date', 'course__area', 'course__curso_academico', 'fecha_migracion'
    ]
    search_fields = [
        'student__username', 'student__first_name', 'student__last_name',
        'course__name'
    ]
    readonly_fields = ['fecha_migracion']
    date_hierarchy = 'date'

@admin.register(MigracionLog)
class MigracionLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'estado', 'fecha_inicio', 'fecha_fin', 
        'total_migrados', 'host_origen', 'base_datos_origen'
    ]
    list_filter = ['estado', 'fecha_inicio', 'fecha_fin', 'host_origen']
    search_fields = ['usuario__username', 'host_origen', 'base_datos_origen']
    readonly_fields = [
        'fecha_inicio', 'fecha_fin', 'usuarios_migrados', 'cursos_academicos_migrados',
        'cursos_migrados', 'matriculas_migradas', 'calificaciones_migradas',
        'notas_migradas', 'asistencias_migradas'
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'estado', 'fecha_inicio', 'fecha_fin')
        }),
        ('Origen de Datos', {
            'fields': ('host_origen', 'base_datos_origen')
        }),
        ('Estadísticas de Migración', {
            'fields': (
                'usuarios_migrados', 'cursos_academicos_migrados', 'cursos_migrados',
                'matriculas_migradas', 'calificaciones_migradas', 'notas_migradas',
                'asistencias_migradas'
            )
        }),
        ('Errores', {
            'fields': ('errores',),
            'classes': ('collapse',)
        }),
    )
    
    def total_migrados(self, obj):
        total = (
            obj.usuarios_migrados + obj.cursos_academicos_migrados + 
            obj.cursos_migrados + obj.matriculas_migradas + 
            obj.calificaciones_migradas + obj.notas_migradas + 
            obj.asistencias_migradas
        )
        return format_html('<strong>{}</strong> registros', total)
    total_migrados.short_description = 'Total Migrado'
    
    def has_add_permission(self, request):
        # No permitir crear logs manualmente
        return False

# Personalizar el admin site
admin.site.site_header = "Administración - Datos Archivados"
admin.site.site_title = "Datos Archivados"
admin.site.index_title = "Gestión de Datos Archivados"

@admin.register(DatoArchivadoDinamico)
class DatoArchivadoDinamicoAdmin(admin.ModelAdmin):
    list_display = [
        'tabla_origen', 'id_original', 'obtener_nombre_legible', 
        'tipo_registro', 'fecha_migracion'
    ]
    list_filter = [
        'tabla_origen', 'tipo_registro', 'fecha_migracion'
    ]
    search_fields = [
        'tabla_origen', 'nombre_registro', 'tipo_registro'
    ]
    readonly_fields = ['fecha_migracion']
    
    fieldsets = (
        ('Información General', {
            'fields': ('tabla_origen', 'id_original', 'nombre_registro', 'tipo_registro')
        }),
        ('Datos', {
            'fields': ('datos_originales', 'estructura_tabla'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('fecha_migracion',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-fecha_migracion')
    
    def has_add_permission(self, request):
        # No permitir crear registros manualmente
        return False