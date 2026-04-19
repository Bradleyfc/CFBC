from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    CursoAcademicoArchivado, UsuarioArchivado, CursoArchivado,
    MatriculaArchivada, CalificacionArchivada, NotaIndividualArchivada,
    AsistenciaArchivada, MigracionLog, DatoArchivadoDinamico,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers reutilizables
# ─────────────────────────────────────────────────────────────────────────────

def link_curso_academico(obj_curso_academico):
    """Devuelve un enlace HTML al CursoAcademicoArchivado dado."""
    if not obj_curso_academico:
        return "—"
    url = reverse('admin:datos_archivados_cursoacademicoarchivado_change',
                  args=[obj_curso_academico.pk])
    return format_html('<a href="{}">{}</a>', url, obj_curso_academico.nombre)


# ─────────────────────────────────────────────────────────────────────────────
# Inlines: permiten ver los datos relacionados dentro del CursoAcademicoArchivado
# ─────────────────────────────────────────────────────────────────────────────

class CursoArchivadoInline(admin.TabularInline):
    model = CursoArchivado
    extra = 0
    show_change_link = True
    fields = ('name', 'area', 'tipo', 'teacher_name', 'status', 'class_quantity')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CursoAcademicoArchivado
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(CursoAcademicoArchivado)
class CursoAcademicoArchivadoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'fecha_creacion', 'fecha_archivado',
        'total_cursos', 'total_matriculas', 'total_calificaciones',
        'total_asistencias', 'fecha_migracion',
    ]
    list_filter = ['fecha_creacion', 'fecha_migracion']
    search_fields = ['nombre']
    readonly_fields = ['fecha_migracion']
    ordering = ['-fecha_creacion']
    inlines = [CursoArchivadoInline]

    fieldsets = (
        ('Curso Académico', {
            'fields': ('id_original', 'nombre', 'activo', 'archivado', 'fecha_creacion'),
        }),
        ('Registro', {
            'fields': ('fecha_migracion',),
        }),
    )

    def fecha_archivado(self, obj):
        return obj.fecha_migracion.strftime('%d/%m/%Y %H:%M')
    fecha_archivado.short_description = 'Fecha de Archivado'
    fecha_archivado.admin_order_field = 'fecha_migracion'

    def total_cursos(self, obj):
        n = CursoArchivado.objects.filter(curso_academico=obj).count()
        if n:
            url = (reverse('admin:datos_archivados_cursoarchivado_changelist')
                   + f'?curso_academico__id__exact={obj.pk}')
            return format_html('<a href="{}">{} cursos</a>', url, n)
        return '0 cursos'
    total_cursos.short_description = 'Cursos'

    def total_matriculas(self, obj):
        n = MatriculaArchivada.objects.filter(course__curso_academico=obj).count()
        if n:
            url = (reverse('admin:datos_archivados_matriculaarchivada_changelist')
                   + f'?course__curso_academico__id__exact={obj.pk}')
            return format_html('<a href="{}">{} matrículas</a>', url, n)
        return '0 matrículas'
    total_matriculas.short_description = 'Matrículas'

    def total_calificaciones(self, obj):
        n = CalificacionArchivada.objects.filter(course__curso_academico=obj).count()
        if n:
            url = (reverse('admin:datos_archivados_calificacionarchivada_changelist')
                   + f'?course__curso_academico__id__exact={obj.pk}')
            return format_html('<a href="{}">{} calificaciones</a>', url, n)
        return '0 calificaciones'
    total_calificaciones.short_description = 'Calificaciones'

    def total_asistencias(self, obj):
        n = AsistenciaArchivada.objects.filter(course__curso_academico=obj).count()
        if n:
            url = (reverse('admin:datos_archivados_asistenciaarchivada_changelist')
                   + f'?course__curso_academico__id__exact={obj.pk}')
            return format_html('<a href="{}">{} asistencias</a>', url, n)
        return '0 asistencias'
    total_asistencias.short_description = 'Asistencias'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# UsuarioArchivado
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(UsuarioArchivado)
class UsuarioArchivadoAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'first_name', 'last_name', 'email', 'carnet',
        'grupo', 'cursos_academicos_participados', 'usuario_vinculado', 'fecha_migracion',
    ]
    list_filter = [
        'sexo', 'grado', 'ocupacion', 'grupo', 'is_active',
        # Filtrar por curso académico a través de matrículas
        'matriculas_archivadas__course__curso_academico',
    ]
    search_fields = [
        'username', 'first_name', 'last_name', 'email', 'carnet',
        'usuario_actual__username', 'usuario_actual__email',
    ]
    readonly_fields = ['fecha_migracion', 'cursos_academicos_participados']
    raw_id_fields = ['usuario_actual']

    fieldsets = (
        ('Información Básica', {
            'fields': ('id_original', 'username', 'first_name', 'last_name',
                       'email', 'date_joined', 'is_active'),
        }),
        ('Datos Personales', {
            'fields': ('nacionalidad', 'carnet', 'sexo', 'address', 'location', 'provincia'),
        }),
        ('Contacto', {
            'fields': ('telephone', 'movil'),
        }),
        ('Información Académica/Laboral', {
            'fields': ('grado', 'ocupacion', 'titulo'),
        }),
        ('Cursos Académicos', {
            'fields': ('cursos_academicos_participados',),
        }),
        ('Sistema', {
            'fields': ('grupo', 'usuario_actual', 'fecha_migracion'),
        }),
    )

    def usuario_vinculado(self, obj):
        if obj.usuario_actual:
            url = reverse('admin:auth_user_change', args=[obj.usuario_actual.pk])
            return format_html('<a href="{}">{}</a>', url, obj.usuario_actual.username)
        return "No vinculado"
    usuario_vinculado.short_description = 'Usuario Actual'

    def cursos_academicos_participados(self, obj):
        """Muestra los cursos académicos en los que participó este usuario."""
        # Buscar a través de matrículas
        cas = (CursoAcademicoArchivado.objects
               .filter(cursoarchivado__matriculaarchivada__student=obj)
               .distinct()
               .order_by('-fecha_creacion'))
        if not cas.exists():
            # También puede ser profesor
            cas = (CursoAcademicoArchivado.objects
                   .filter(cursoarchivado__teacher_actual=obj.usuario_actual)
                   .distinct()
                   .order_by('-fecha_creacion'))
        if not cas.exists():
            return "Sin cursos académicos registrados"
        links = []
        for ca in cas:
            url = reverse('admin:datos_archivados_cursoacademicoarchivado_change',
                          args=[ca.pk])
            links.append(format_html('<a href="{}">{}</a>', url, ca.nombre))
        return format_html(', '.join(str(l) for l in links))
    cursos_academicos_participados.short_description = 'Cursos Académicos'


# ─────────────────────────────────────────────────────────────────────────────
# CursoArchivado
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(CursoArchivado)
class CursoArchivadoAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'curso_academico_link', 'area', 'tipo',
        'teacher_name', 'status', 'class_quantity',
        'total_matriculas', 'profesor_vinculado', 'fecha_migracion',
    ]
    list_filter = [
        # El filtro más importante: por curso académico
        'curso_academico',
        'area', 'tipo', 'status', 'fecha_migracion',
    ]
    search_fields = [
        'name', 'teacher_name', 'description',
        'curso_academico__nombre',
        'teacher_actual__username', 'teacher_actual__first_name',
        'teacher_actual__last_name',
    ]
    readonly_fields = ['fecha_migracion', 'curso_academico_link', 'total_matriculas']
    raw_id_fields = ['teacher_actual']

    fieldsets = (
        ('Curso Académico', {
            'fields': ('curso_academico', 'curso_academico_link'),
        }),
        ('Información del Curso', {
            'fields': ('id_original', 'name', 'description', 'area', 'tipo',
                       'class_quantity', 'status'),
        }),
        ('Profesor', {
            'fields': ('teacher_id_original', 'teacher_name', 'teacher_actual'),
        }),
        ('Fechas', {
            'fields': ('enrollment_deadline', 'start_date'),
        }),
        ('Estadísticas', {
            'fields': ('total_matriculas',),
        }),
        ('Registro', {
            'fields': ('fecha_migracion',),
        }),
    )

    def curso_academico_link(self, obj):
        return link_curso_academico(obj.curso_academico)
    curso_academico_link.short_description = 'Curso Académico'

    def total_matriculas(self, obj):
        n = MatriculaArchivada.objects.filter(course=obj).count()
        if n:
            url = (reverse('admin:datos_archivados_matriculaarchivada_changelist')
                   + f'?course__id__exact={obj.pk}')
            return format_html('<a href="{}">{} matrículas</a>', url, n)
        return '0 matrículas'
    total_matriculas.short_description = 'Matrículas'

    def profesor_vinculado(self, obj):
        if obj.teacher_actual:
            url = reverse('admin:auth_user_change', args=[obj.teacher_actual.pk])
            return format_html('<a href="{}">{}</a>', url,
                               obj.teacher_actual.get_full_name() or obj.teacher_actual.username)
        return "No vinculado"
    profesor_vinculado.short_description = 'Profesor Actual'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# MatriculaArchivada
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(MatriculaArchivada)
class MatriculaArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'get_estudiante', 'get_curso', 'curso_academico_link',
        'estado', 'activo', 'fecha_matricula', 'fecha_migracion',
    ]
    list_filter = [
        # Filtro principal: por curso académico
        'course__curso_academico',
        'estado', 'activo', 'fecha_matricula',
        'course__area', 'fecha_migracion',
    ]
    search_fields = [
        'student__username', 'student__first_name', 'student__last_name',
        'course__name', 'course__curso_academico__nombre',
    ]
    readonly_fields = ['fecha_migracion', 'curso_academico_link']

    fieldsets = (
        ('Curso Académico', {
            'fields': ('curso_academico_link',),
        }),
        ('Matrícula', {
            'fields': ('id_original', 'course', 'student', 'estado', 'activo', 'fecha_matricula'),
        }),
        ('Registro', {
            'fields': ('fecha_migracion',),
        }),
    )

    def get_estudiante(self, obj):
        nombre = obj.student.first_name + ' ' + obj.student.last_name
        return nombre.strip() or obj.student.username
    get_estudiante.short_description = 'Estudiante'
    get_estudiante.admin_order_field = 'student__first_name'

    def get_curso(self, obj):
        url = reverse('admin:datos_archivados_cursoarchivado_change',
                      args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.name)
    get_curso.short_description = 'Curso'
    get_curso.admin_order_field = 'course__name'

    def curso_academico_link(self, obj):
        return link_curso_academico(obj.course.curso_academico)
    curso_academico_link.short_description = 'Curso Académico'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CalificacionArchivada
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(CalificacionArchivada)
class CalificacionArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'get_estudiante', 'get_curso', 'curso_academico_link',
        'average', 'total_notas', 'fecha_migracion',
    ]
    list_filter = [
        # Filtro principal: por curso académico
        'course__curso_academico',
        'course__area', 'fecha_migracion',
    ]
    search_fields = [
        'student__username', 'student__first_name', 'student__last_name',
        'course__name', 'course__curso_academico__nombre',
    ]
    readonly_fields = ['fecha_migracion', 'curso_academico_link', 'total_notas']

    fieldsets = (
        ('Curso Académico', {
            'fields': ('curso_academico_link',),
        }),
        ('Calificación', {
            'fields': ('id_original', 'course', 'student', 'matricula', 'average'),
        }),
        ('Estadísticas', {
            'fields': ('total_notas',),
        }),
        ('Registro', {
            'fields': ('fecha_migracion',),
        }),
    )

    def get_estudiante(self, obj):
        nombre = obj.student.first_name + ' ' + obj.student.last_name
        return nombre.strip() or obj.student.username
    get_estudiante.short_description = 'Estudiante'
    get_estudiante.admin_order_field = 'student__first_name'

    def get_curso(self, obj):
        url = reverse('admin:datos_archivados_cursoarchivado_change',
                      args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.name)
    get_curso.short_description = 'Curso'
    get_curso.admin_order_field = 'course__name'

    def curso_academico_link(self, obj):
        return link_curso_academico(obj.course.curso_academico)
    curso_academico_link.short_description = 'Curso Académico'

    def total_notas(self, obj):
        n = obj.notas_archivadas.count()
        return f'{n} nota(s)'
    total_notas.short_description = 'Notas Individuales'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# NotaIndividualArchivada
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(NotaIndividualArchivada)
class NotaIndividualArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'get_estudiante', 'get_curso', 'curso_academico_link',
        'valor', 'fecha_creacion', 'fecha_migracion',
    ]
    list_filter = [
        # Filtro principal: por curso académico
        'calificacion__course__curso_academico',
        'calificacion__course__area', 'fecha_creacion', 'fecha_migracion',
    ]
    search_fields = [
        'calificacion__student__username',
        'calificacion__student__first_name',
        'calificacion__student__last_name',
        'calificacion__course__name',
        'calificacion__course__curso_academico__nombre',
    ]
    readonly_fields = ['fecha_migracion', 'curso_academico_link']

    fieldsets = (
        ('Curso Académico', {
            'fields': ('curso_academico_link',),
        }),
        ('Nota', {
            'fields': ('id_original', 'calificacion', 'valor', 'fecha_creacion'),
        }),
        ('Registro', {
            'fields': ('fecha_migracion',),
        }),
    )

    def get_estudiante(self, obj):
        nombre = (obj.calificacion.student.first_name + ' '
                  + obj.calificacion.student.last_name)
        return nombre.strip() or obj.calificacion.student.username
    get_estudiante.short_description = 'Estudiante'
    get_estudiante.admin_order_field = 'calificacion__student__first_name'

    def get_curso(self, obj):
        url = reverse('admin:datos_archivados_cursoarchivado_change',
                      args=[obj.calificacion.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.calificacion.course.name)
    get_curso.short_description = 'Curso'
    get_curso.admin_order_field = 'calificacion__course__name'

    def curso_academico_link(self, obj):
        return link_curso_academico(obj.calificacion.course.curso_academico)
    curso_academico_link.short_description = 'Curso Académico'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# AsistenciaArchivada
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(AsistenciaArchivada)
class AsistenciaArchivadaAdmin(admin.ModelAdmin):
    list_display = [
        'get_estudiante', 'get_curso', 'curso_academico_link',
        'presente', 'date', 'fecha_migracion',
    ]
    list_filter = [
        # Filtro principal: por curso académico
        'course__curso_academico',
        'presente', 'course__area', 'date', 'fecha_migracion',
    ]
    search_fields = [
        'student__username', 'student__first_name', 'student__last_name',
        'course__name', 'course__curso_academico__nombre',
    ]
    readonly_fields = ['fecha_migracion', 'curso_academico_link']
    date_hierarchy = 'date'

    fieldsets = (
        ('Curso Académico', {
            'fields': ('curso_academico_link',),
        }),
        ('Asistencia', {
            'fields': ('id_original', 'course', 'student', 'presente', 'date'),
        }),
        ('Registro', {
            'fields': ('fecha_migracion',),
        }),
    )

    def get_estudiante(self, obj):
        nombre = obj.student.first_name + ' ' + obj.student.last_name
        return nombre.strip() or obj.student.username
    get_estudiante.short_description = 'Estudiante'
    get_estudiante.admin_order_field = 'student__first_name'

    def get_curso(self, obj):
        url = reverse('admin:datos_archivados_cursoarchivado_change',
                      args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.name)
    get_curso.short_description = 'Curso'
    get_curso.admin_order_field = 'course__name'

    def curso_academico_link(self, obj):
        return link_curso_academico(obj.course.curso_academico)
    curso_academico_link.short_description = 'Curso Académico'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# MigracionLog  (pertenece a la migración MariaDB — solo lectura)
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(MigracionLog)
class MigracionLogAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'estado', 'fecha_inicio', 'fecha_fin',
        'total_migrados', 'host_origen', 'base_datos_origen',
    ]
    list_filter = ['estado', 'fecha_inicio', 'host_origen']
    search_fields = ['usuario__username', 'host_origen', 'base_datos_origen']
    readonly_fields = [
        'fecha_inicio', 'fecha_fin', 'usuarios_migrados',
        'cursos_academicos_migrados', 'cursos_migrados',
        'matriculas_migradas', 'calificaciones_migradas',
        'notas_migradas', 'asistencias_migradas',
    ]

    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'estado', 'fecha_inicio', 'fecha_fin'),
        }),
        ('Origen de Datos', {
            'fields': ('host_origen', 'base_datos_origen'),
        }),
        ('Estadísticas de Migración', {
            'fields': (
                'usuarios_migrados', 'cursos_academicos_migrados', 'cursos_migrados',
                'matriculas_migradas', 'calificaciones_migradas',
                'notas_migradas', 'asistencias_migradas',
            ),
        }),
        ('Errores', {
            'fields': ('errores',),
            'classes': ('collapse',),
        }),
    )

    def total_migrados(self, obj):
        total = (
            obj.usuarios_migrados + obj.cursos_academicos_migrados
            + obj.cursos_migrados + obj.matriculas_migradas
            + obj.calificaciones_migradas + obj.notas_migradas
            + obj.asistencias_migradas
        )
        return format_html('<strong>{}</strong> registros', total)
    total_migrados.short_description = 'Total Migrado'

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# DatoArchivadoDinamico  (pertenece a la migración MariaDB — solo lectura)
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(DatoArchivadoDinamico)
class DatoArchivadoDinamicoAdmin(admin.ModelAdmin):
    list_display = [
        'tabla_origen', 'id_original', 'obtener_nombre_legible',
        'tipo_registro', 'fecha_migracion',
    ]
    list_filter = ['tabla_origen', 'tipo_registro', 'fecha_migracion']
    search_fields = ['tabla_origen', 'nombre_registro', 'tipo_registro']
    readonly_fields = ['fecha_migracion']

    fieldsets = (
        ('Información General', {
            'fields': ('tabla_origen', 'id_original', 'nombre_registro', 'tipo_registro'),
        }),
        ('Datos', {
            'fields': ('datos_originales', 'estructura_tabla'),
            'classes': ('collapse',),
        }),
        ('Sistema', {
            'fields': ('fecha_migracion',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-fecha_migracion')

    def has_add_permission(self, request):
        return False


# Nota: los títulos del sitio admin se configuran en principal/admin.py
# para evitar conflictos entre apps.
