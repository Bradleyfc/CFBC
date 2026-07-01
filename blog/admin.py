from django.contrib import admin
from .models import Categoria, Noticia, Comentario, ReporteComentario, SancionUsuario, ComentarioFijado, MetricaComunidad

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ['nombre']

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'autor', 'estado', 'visibilidad', 'destacada', 'fecha_publicacion']
    list_filter = ['estado', 'visibilidad', 'categoria', 'destacada', 'fecha_publicacion']
    search_fields = ['titulo', 'contenido']
    prepopulated_fields = {'slug': ('titulo',)}
    date_hierarchy = 'fecha_publicacion'
    ordering = ['-fecha_publicacion']
    
    fieldsets = (
        ('Información básica', {
            'fields': ('titulo', 'slug', 'resumen', 'contenido', 'imagen_principal')
        }),
        ('Clasificación', {
            'fields': ('categoria', 'autor', 'estado', 'visibilidad', 'destacada')
        }),
        ('Fechas', {
            'fields': ('fecha_publicacion',)
        }),
        ('SEO', {
            'fields': ('meta_descripcion',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un objeto nuevo
            obj.autor = request.user
        super().save_model(request, obj, form, change)

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ['autor', 'noticia', 'fecha_creacion', 'activo']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['autor__username', 'noticia__titulo', 'contenido']
    actions = ['activar_comentarios', 'desactivar_comentarios']
    
    def activar_comentarios(self, request, queryset):
        queryset.update(activo=True)
        self.message_user(request, f'{queryset.count()} comentarios activados.')
    activar_comentarios.short_description = "Activar comentarios seleccionados"
    
    def desactivar_comentarios(self, request, queryset):
        queryset.update(activo=False)
        self.message_user(request, f'{queryset.count()} comentarios desactivados.')
    desactivar_comentarios.short_description = "Desactivar comentarios seleccionados"


@admin.register(ReporteComentario)
class ReporteComentarioAdmin(admin.ModelAdmin):
    list_display = ['comentario', 'reportado_por', 'estado', 'fecha_reporte', 'resuelto_por']
    list_filter = ['estado', 'fecha_reporte']
    search_fields = ['reportado_por__username', 'motivo']
    readonly_fields = ['fecha_reporte', 'fecha_resolucion']


@admin.register(SancionUsuario)
class SancionUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_sancion', 'activa', 'fecha_inicio', 'fecha_fin', 'aplicada_por']
    list_filter = ['tipo_sancion', 'activa']
    search_fields = ['usuario__username', 'motivo']
    readonly_fields = ['fecha_inicio', 'fecha_levantamiento']


@admin.register(ComentarioFijado)
class ComentarioFijadoAdmin(admin.ModelAdmin):
    list_display = ['comentario', 'noticia', 'orden', 'fijado_por', 'fecha_fijado']
    search_fields = ['noticia__titulo', 'comentario__contenido']


@admin.register(MetricaComunidad)
class MetricaComunidadAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'total_reportes', 'total_comentarios', 'total_sanciones', 'pico_toxicidad']
    readonly_fields = ['fecha', 'total_reportes', 'total_comentarios',
                       'total_sanciones', 'usuario_mas_activo', 'pico_toxicidad', 'generada_en']

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
