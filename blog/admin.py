from django.contrib import admin
from .models import Categoria, Noticia, Comentario

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
