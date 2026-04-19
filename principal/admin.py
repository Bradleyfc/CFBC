from django.contrib import admin
from django import forms
from.models import (
    Curso, Matriculas, Asistencia, Calificaciones, CursoAcademico, NotaIndividual,
    FormularioAplicacion, PreguntaFormulario, OpcionRespuesta, SolicitudInscripcion, RespuestaEstudiante
)
# Register your models here.

from .models import CursoAcademico

class CursoAdmin(admin.ModelAdmin):
    list_display = ('name', 'area', 'tipo', 'teacher', 'class_quantity', 'curso_academico')
    list_filter = ('area', 'tipo', 'teacher', 'curso_academico')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Only filter if the user is not a superuser
        if not request.user.is_superuser:
            # Check if a specific curso_academico is selected in the filter
            curso_academico_id = request.GET.get('curso_academico__id__exact') or request.GET.get('curso_academico__id__iexact')
            if curso_academico_id:
                # If a specific academic year is selected, filter by it
                qs = qs.filter(curso_academico__id=curso_academico_id)
            else:
                # If no specific academic year is selected, filter by the active one
                active_academic_year = CursoAcademico.objects.filter(activo=True).first()
                if active_academic_year:
                    qs = qs.filter(curso_academico=active_academic_year)
                else:
                    # If no active academic year and no filter, show no courses
                    qs = qs.none()
        return qs

admin.site.register(Curso, CursoAdmin)   

class MatriculasAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'curso_academico', 'estado', 'activo', 'fecha_matricula')
    list_filter = ('curso_academico', 'course', 'estado', 'activo')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'course__name')
    date_hierarchy = 'fecha_matricula'
    actions = ['aprobar_matriculas', 'promover_al_siguiente_curso']
    
    def aprobar_matriculas(self, request, queryset):
        queryset.update(estado='A')
    aprobar_matriculas.short_description = "Marcar matrículas seleccionadas como aprobadas"
    
    def promover_al_siguiente_curso(self, request, queryset):
        # Solo promover matrículas aprobadas
        aprobadas = queryset.filter(estado='A')
        curso_actual = CursoAcademico.objects.filter(activo=True).first()
        
        if not curso_actual:
            self.message_user(request, "No hay un curso académico activo configurado")
            return
            
        contador = 0
        for matricula in aprobadas:
            # Crear nueva matrícula en el curso actual
            Matriculas.objects.create(
                student=matricula.student,
                course=matricula.course,
                curso_academico=curso_actual,
                activo=True,
                estado='P'  # Comienza como pendiente en el nuevo curso
            )
            contador += 1
            
        self.message_user(request, f"{contador} matrículas han sido promovidas al curso {curso_actual}")
    promover_al_siguiente_curso.short_description = "Promover matrículas aprobadas al curso actual"

admin.site.register(Matriculas, MatriculasAdmin) 

class AsistenciaAdmin(admin.ModelAdmin):
    list_display= ('course' , 'student', 'date', 'presente')
    list_filter = ('course', 'student', 'date', 'presente')

admin.site.register(Asistencia, AsistenciaAdmin)   


class NotaIndividualInline(admin.TabularInline):
    model = NotaIndividual
    extra = 1 # Permite añadir una nota individual extra por defecto

class CalificacionesAdmin(admin.ModelAdmin):
    list_display= ('course' , 'student', 'average', 'display_notas_individuales') # Actualiza list_display
    list_filter = ('course', )
    exclude=('average',)
    inlines = [NotaIndividualInline] # Añade el inline para NotaIndividual

    def display_notas_individuales(self, obj):
        # Muestra las notas individuales como una lista en el admin
        notas = obj.notas.all().order_by('id')
        return ", ".join([f"{n.valor}" for n in notas])
    display_notas_individuales.short_description = 'Notas Individuales'

admin.site.register(Calificaciones, CalificacionesAdmin)  

class CursoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'archivado', 'fecha_creacion', 'ver_detalles_curso_academico')
    list_filter = ('activo', 'archivado')
    search_fields = ('nombre',)
    actions = ['activar_curso', 'archivar_curso', 'desarchivar_curso']
    
    def activar_curso(self, request, queryset):
        # Desactivar todos los cursos primero
        CursoAcademico.objects.all().update(activo=False)
        # Activar solo el seleccionado
        if queryset.count() > 0:
            curso = queryset.first()
            curso.activar()
            self.message_user(request, f"El curso {curso.nombre} ha sido activado")
    activar_curso.short_description = "Activar curso seleccionado (desactiva los demás)"
    
    def archivar_curso(self, request, queryset):
        # Archivar los cursos seleccionados
        contador = 0
        for curso in queryset:
            curso.archivar()
            contador += 1
        
        if contador == 1:
            self.message_user(request, f"El curso ha sido archivado")
        else:
            self.message_user(request, f"{contador} cursos han sido archivados")
    archivar_curso.short_description = "Archivar cursos seleccionados"
    
    def desarchivar_curso(self, request, queryset):
        # Desarchivar los cursos seleccionados (sin activarlos)
        queryset.update(archivado=False)
        contador = queryset.count()
        
        if contador == 1:
            self.message_user(request, f"El curso ha sido desarchivado")
        else:
            self.message_user(request, f"{contador} cursos han sido desarchivados")
    desarchivar_curso.short_description = "Desarchivar cursos seleccionados (sin activarlos)"

    def ver_detalles_curso_academico(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        url = reverse('principal:principal_cursoacademico_detail', args=[obj.pk])
        return format_html('<a href="{}">Detalles</a>', url)
    ver_detalles_curso_academico.short_description = 'Detalles'

admin.site.register(CursoAcademico, CursoAcademicoAdmin)

# ADMINISTRACIÓN DE FORMULARIOS DE APLICACIÓN A CURSOS

class OpcionRespuestaInline(admin.TabularInline):
    """Inline para gestionar opciones de respuesta dentro de una pregunta"""
    model = OpcionRespuesta
    extra = 1
    fields = ('texto', 'orden')
    ordering = ['orden']

class PreguntaFormularioInline(admin.StackedInline):
    """Inline para gestionar preguntas dentro de un formulario"""
    model = PreguntaFormulario
    extra = 1
    fields = ('texto', 'tipo', 'requerida', 'orden')
    ordering = ['orden']



class FormularioAplicacionAdmin(admin.ModelAdmin):
    """Administración de formularios de aplicación"""
    list_display = ('titulo', 'curso', 'activo', 'fecha_creacion', 'fecha_modificacion')
    list_filter = ('activo', 'fecha_creacion', 'curso__curso_academico')
    search_fields = ('titulo', 'curso__name', 'descripcion')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    inlines = [PreguntaFormularioInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('curso', 'titulo', 'descripcion', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

class PreguntaFormularioAdmin(admin.ModelAdmin):
    """Administración de preguntas de formulario"""
    list_display = ('texto_corto', 'formulario', 'tipo', 'requerida', 'orden')
    list_filter = ('tipo', 'requerida', 'formulario__curso')
    search_fields = ('texto', 'formulario__titulo')
    ordering = ['formulario', 'orden']
    inlines = [OpcionRespuestaInline]
    
    def texto_corto(self, obj):
        """Muestra una versión corta del texto de la pregunta"""
        return obj.texto[:50] + '...' if len(obj.texto) > 50 else obj.texto
    texto_corto.short_description = 'Pregunta'

class OpcionRespuestaAdminForm(forms.ModelForm):
    """Formulario para OpcionRespuesta sin filtro"""
    
    class Meta:
        model = OpcionRespuesta
        fields = ['pregunta', 'texto', 'orden']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar etiquetas de los campos
        self.fields['pregunta'].label = "❓ Pregunta"
        self.fields['pregunta'].help_text = "Selecciona la pregunta a la que pertenece esta opción"
        self.fields['texto'].label = "✅ Texto de la opción"
        self.fields['orden'].label = "🔢 Orden"
        
        # Configurar queryset ordenado por curso para facilitar la búsqueda
        preguntas_queryset = PreguntaFormulario.objects.select_related(
            'formulario__curso'
        ).order_by('formulario__curso__name', 'formulario__titulo', 'orden')
        
        self.fields['pregunta'].queryset = preguntas_queryset

class OpcionRespuestaAdmin(admin.ModelAdmin):
    """Administración de opciones de respuesta"""
    form = OpcionRespuestaAdminForm
    list_display = ('texto', 'pregunta_texto_corto', 'curso_relacionado', 'formulario_relacionado', 'orden')
    list_filter = ('pregunta__formulario__curso', 'pregunta__formulario', 'pregunta__tipo')
    search_fields = ('texto', 'pregunta__texto', 'pregunta__formulario__titulo', 'pregunta__formulario__curso__name')
    ordering = ['pregunta__formulario__curso', 'pregunta__formulario', 'pregunta', 'orden']
    
    # Configurar el formulario
    fieldsets = (
        ('📝 Información de la Opción', {
            'fields': ('pregunta', 'texto', 'orden')
        }),
        ('ℹ️ Información Relacionada (Solo Lectura)', {
            'fields': ('curso_info', 'formulario_info'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('curso_info', 'formulario_info')
    
    def pregunta_texto_corto(self, obj):
        """Muestra una versión corta del texto de la pregunta asociada"""
        return obj.pregunta.texto[:30] + '...' if len(obj.pregunta.texto) > 30 else obj.pregunta.texto
    pregunta_texto_corto.short_description = 'Pregunta'
    
    def curso_relacionado(self, obj):
        """Muestra el curso relacionado con esta opción"""
        return obj.pregunta.formulario.curso.name if obj.pregunta and obj.pregunta.formulario else 'Sin curso'
    curso_relacionado.short_description = 'Curso'
    
    def formulario_relacionado(self, obj):
        """Muestra el formulario relacionado con esta opción"""
        return obj.pregunta.formulario.titulo if obj.pregunta and obj.pregunta.formulario else 'Sin formulario'
    formulario_relacionado.short_description = 'Formulario'
    
    def curso_info(self, obj):
        """Información del curso para mostrar en el formulario"""
        if obj.pregunta and obj.pregunta.formulario:
            curso = obj.pregunta.formulario.curso
            return f"{curso.name} (Profesor: {curso.teacher.get_full_name() or curso.teacher.username})"
        return 'No disponible'
    curso_info.short_description = 'Curso Asociado'
    
    def formulario_info(self, obj):
        """Información del formulario para mostrar en el formulario"""
        if obj.pregunta and obj.pregunta.formulario:
            formulario = obj.pregunta.formulario
            return f"{formulario.titulo} ({'Activo' if formulario.activo else 'Inactivo'})"
        return 'No disponible'
    formulario_info.short_description = 'Formulario Asociado'
    
    def get_urls(self):
        """Agregar URLs personalizadas para el filtrado AJAX"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('filtrar-preguntas/', self.admin_site.admin_view(self.filtrar_preguntas_view), name='opcionrespuesta_filtrar_preguntas'),
            path('todas-preguntas/', self.admin_site.admin_view(self.todas_preguntas_view), name='opcionrespuesta_todas_preguntas'),
        ]
        return custom_urls + urls
    
    def filtrar_preguntas_view(self, request):
        """Vista AJAX para filtrar preguntas por curso"""
        from django.http import JsonResponse
        
        curso_id = request.GET.get('curso_id')
        if not curso_id:
            return JsonResponse({'preguntas': []})
        
        try:
            preguntas = PreguntaFormulario.objects.filter(
                formulario__curso_id=curso_id
            ).select_related('formulario').order_by('formulario__titulo', 'orden')
            
            preguntas_data = []
            for pregunta in preguntas:
                preguntas_data.append({
                    'id': pregunta.id,
                    'texto': pregunta.texto[:60] + ('...' if len(pregunta.texto) > 60 else ''),
                    'formulario': pregunta.formulario.titulo,
                    'tipo': pregunta.get_tipo_display()
                })
            
            return JsonResponse({'preguntas': preguntas_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def todas_preguntas_view(self, request):
        """Vista AJAX para obtener todas las preguntas"""
        from django.http import JsonResponse
        
        try:
            preguntas = PreguntaFormulario.objects.select_related(
                'formulario__curso'
            ).order_by('formulario__curso__name', 'formulario__titulo', 'orden')
            
            preguntas_data = []
            for pregunta in preguntas:
                preguntas_data.append({
                    'id': pregunta.id,
                    'texto': pregunta.texto[:50] + ('...' if len(pregunta.texto) > 50 else ''),
                    'curso': pregunta.formulario.curso.name,
                    'formulario': pregunta.formulario.titulo,
                    'tipo': pregunta.get_tipo_display()
                })
            
            return JsonResponse({'preguntas': preguntas_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personaliza el campo de selección de pregunta para mostrar información del curso"""
        if db_field.name == "pregunta":
            # Ordenar las preguntas por curso y formulario para facilitar la selección
            kwargs["queryset"] = PreguntaFormulario.objects.select_related(
                'formulario__curso'
            ).order_by(
                'formulario__curso__name', 
                'formulario__titulo', 
                'orden'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class RespuestaEstudianteInline(admin.TabularInline):
    """Inline para mostrar respuestas dentro de una solicitud"""
    model = RespuestaEstudiante
    extra = 0
    readonly_fields = ('pregunta', 'get_opciones_seleccionadas')
    fields = ('pregunta', 'get_opciones_seleccionadas')
    
    def get_opciones_seleccionadas(self, obj):
        """Muestra las opciones seleccionadas como texto"""
        if obj.pk:
            opciones = obj.opciones_seleccionadas.all()
            return ', '.join([opcion.texto for opcion in opciones]) if opciones else 'Sin respuesta'
        return 'Sin respuesta'
    get_opciones_seleccionadas.short_description = 'Respuestas'

class SolicitudInscripcionAdmin(admin.ModelAdmin):
    """Administración de solicitudes de inscripción"""
    list_display = ('estudiante_nombre', 'curso', 'estado', 'fecha_solicitud', 'fecha_revision', 'revisado_por')
    list_filter = ('estado', 'curso', 'fecha_solicitud', 'curso__curso_academico')
    search_fields = ('estudiante__username', 'estudiante__first_name', 'estudiante__last_name', 'curso__name')
    date_hierarchy = 'fecha_solicitud'
    readonly_fields = ('fecha_solicitud', 'fecha_revision')
    actions = ['aprobar_solicitudes', 'rechazar_solicitudes']
    inlines = [RespuestaEstudianteInline]
    
    fieldsets = (
        ('Información de la Solicitud', {
            'fields': ('estudiante', 'curso', 'formulario', 'estado')
        }),
        ('Revisión', {
            'fields': ('revisado_por', 'fecha_revision'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud',),
            'classes': ('collapse',)
        }),
    )
    
    def estudiante_nombre(self, obj):
        """Muestra el nombre completo del estudiante"""
        return obj.estudiante.get_full_name() or obj.estudiante.username
    estudiante_nombre.short_description = 'Estudiante'
    
    def aprobar_solicitudes(self, request, queryset):
        """Acción para aprobar solicitudes seleccionadas"""
        contador = 0
        for solicitud in queryset.filter(estado='pendiente'):
            try:
                solicitud.aprobar(request.user)
                contador += 1
            except Exception as e:
                self.message_user(request, f"Error al aprobar solicitud de {solicitud.estudiante}: {str(e)}", level='ERROR')
        
        if contador > 0:
            self.message_user(request, f"{contador} solicitudes han sido aprobadas y se crearon las matrículas correspondientes")
    aprobar_solicitudes.short_description = "Aprobar solicitudes seleccionadas"
    
    def rechazar_solicitudes(self, request, queryset):
        """Acción para rechazar solicitudes seleccionadas"""
        contador = 0
        for solicitud in queryset.filter(estado='pendiente'):
            solicitud.rechazar(request.user)
            contador += 1
        
        if contador > 0:
            self.message_user(request, f"{contador} solicitudes han sido rechazadas")
    rechazar_solicitudes.short_description = "Rechazar solicitudes seleccionadas"

class RespuestaEstudianteAdmin(admin.ModelAdmin):
    """Administración de respuestas de estudiantes"""
    list_display = ('solicitud_info', 'pregunta_texto_corto', 'get_opciones_seleccionadas')
    list_filter = ('solicitud__curso', 'solicitud__estado', 'pregunta__tipo')
    search_fields = ('solicitud__estudiante__username', 'pregunta__texto')
    
    def solicitud_info(self, obj):
        """Información de la solicitud"""
        return f"{obj.solicitud.estudiante.username} - {obj.solicitud.curso.name}"
    solicitud_info.short_description = 'Solicitud'
    
    def pregunta_texto_corto(self, obj):
        """Versión corta del texto de la pregunta"""
        return obj.pregunta.texto[:40] + '...' if len(obj.pregunta.texto) > 40 else obj.pregunta.texto
    pregunta_texto_corto.short_description = 'Pregunta'
    
    def get_opciones_seleccionadas(self, obj):
        """Muestra las opciones seleccionadas"""
        opciones = obj.opciones_seleccionadas.all()
        return ', '.join([opcion.texto for opcion in opciones]) if opciones else 'Sin respuesta'
    get_opciones_seleccionadas.short_description = 'Respuestas'

# REGISTRAR MODELOS DE FORMULARIOS DE APLICACIÓN EN EL ADMIN

# Registrar los modelos originales con clases admin personalizadas
admin.site.register(FormularioAplicacion, FormularioAplicacionAdmin)
admin.site.register(PreguntaFormulario, PreguntaFormularioAdmin)
admin.site.register(OpcionRespuesta, OpcionRespuestaAdmin)
admin.site.register(SolicitudInscripcion, SolicitudInscripcionAdmin)
admin.site.register(RespuestaEstudiante, RespuestaEstudianteAdmin)

# CONFIGURACIÓN PERSONALIZADA DEL ADMIN PARA AGRUPAR FORMULARIOS

def custom_get_app_list(self, request, app_label=None):
    """
    Personaliza la lista de aplicaciones para agrupar los modelos de formularios
    y separar los datos archivados de cursos de los datos de migración MariaDB.
    """
    app_dict = self._build_app_dict(request, app_label)

    # ── Gestión Académica: separar formularios de inscripción ────────────────
    if 'principal' in app_dict:
        principal_app = app_dict['principal']

        formularios_models = []
        otros_models = []

        for model in principal_app['models']:
            model_name = model['object_name']
            if model_name in ['FormularioAplicacion', 'PreguntaFormulario', 'OpcionRespuesta',
                              'SolicitudInscripcion', 'RespuestaEstudiante']:
                formularios_models.append(model)
            else:
                otros_models.append(model)

        principal_app['models'] = otros_models
        principal_app['name'] = 'Gestión Académica'

        if formularios_models:
            app_dict['formularios_inscripcion'] = {
                'name': 'Formularios de Inscripción',
                'app_label': 'formularios_inscripcion',
                'app_url': '/admin/principal/',
                'has_module_perms': True,
                'models': formularios_models,
            }

    # ── Datos Archivados: separar archivado de cursos de migración MariaDB ───
    if 'datos_archivados' in app_dict:
        da_app = app_dict['datos_archivados']

        # Modelos que pertenecen al archivado de cursos académicos del sistema
        MODELOS_ARCHIVADO_CURSOS = {
            'CursoAcademicoArchivado',
            'UsuarioArchivado',
            'CursoArchivado',
            'MatriculaArchivada',
            'CalificacionArchivada',
            'NotaIndividualArchivada',
            'AsistenciaArchivada',
        }
        # Modelos que pertenecen a la migración de la BD MariaDB antigua
        MODELOS_MIGRACION_MARIADB = {
            'DatoArchivadoDinamico',
            'MigracionLog',
            'CodigoVerificacionReclamacion',
        }

        archivado_models = []
        mariadb_models = []

        for model in da_app['models']:
            if model['object_name'] in MODELOS_ARCHIVADO_CURSOS:
                archivado_models.append(model)
            elif model['object_name'] in MODELOS_MIGRACION_MARIADB:
                mariadb_models.append(model)
            else:
                archivado_models.append(model)  # por defecto al grupo de archivado

        # Reemplazar la app original con solo los modelos de archivado de cursos
        da_app['models'] = archivado_models
        da_app['name'] = 'Datos Archivados (Cursos)'

        # Crear sección separada para migración MariaDB
        if mariadb_models:
            app_dict['migracion_mariadb'] = {
                'name': 'Migración Base de Datos MariaDB',
                'app_label': 'migracion_mariadb',
                'app_url': '/admin/datos_archivados/',
                'has_module_perms': True,
                'models': mariadb_models,
            }

    # ── Ordenar las secciones ────────────────────────────────────────────────
    ORDEN = {
        'Gestión Académica': 1,
        'Formularios de Inscripción': 2,
        'Datos Archivados (Cursos)': 3,
        'Migración Base de Datos MariaDB': 4,
        'Authentication and Authorization': 5,
        'Accounts': 6,
    }

    app_list = sorted(
        app_dict.values(),
        key=lambda x: ORDEN.get(x['name'], 999)
    )

    return app_list

# Aplicar la personalización al sitio admin
admin.site.get_app_list = custom_get_app_list.__get__(admin.site, admin.AdminSite)

# Personalizar títulos del sitio admin
admin.site.site_header = 'Centro Fray Bartolomé de las Casas - Administración'
admin.site.site_title = 'CFBC Admin'
admin.site.index_title = 'Panel de Administración'

