from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import Registro

# Register your models here.

class RegistroAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_full_name', 'get_grupo', 'nacionalidad', 'carnet', 'sexo', 'telephone', 'movil', 'grado', 'ocupacion', 'provincia', 'es_religioso')
    list_filter = ('user__groups', 'sexo', 'grado', 'ocupacion', 'nacionalidad', 'provincia', 'es_religioso')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'carnet', 'telephone', 'movil')
    ordering = ['-id']
    
    # Campos de solo lectura para mostrar información del usuario
    readonly_fields = ('get_username', 'get_full_name', 'get_email', 'get_grupo')
    
    # CSS y JS personalizado para barra de desplazamiento fija
    class Media:
        css = {
            'all': ('admin/css/registro_admin.css',)
        }
        js = ('admin/js/registro_admin.js',)
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'get_username', 'get_full_name', 'get_email', 'get_grupo')
        }),
        ('Información Personal', {
            'fields': ('nacionalidad', 'carnet', 'foto_carnet', 'sexo', 'image')
        }),
        ('Ubicación', {
            'fields': ('address', 'location', 'provincia')
        }),
        ('Contacto', {
            'fields': ('telephone', 'movil')
        }),
        ('Información Académica/Laboral', {
            'fields': ('grado', 'ocupacion', 'titulo', 'foto_titulo', 'es_religioso')
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        """Personaliza la vista de lista para agregar CSS personalizado"""
        extra_context = extra_context or {}
        extra_context['title'] = 'Registros de Usuarios (Estudiantes, Profesores, etc.)'
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_username(self, obj):
        """Obtiene el nombre de usuario"""
        return obj.user.username
    get_username.short_description = 'Usuario'
    get_username.admin_order_field = 'user__username'
    
    def get_full_name(self, obj):
        """Obtiene el nombre completo del usuario"""
        full_name = obj.user.get_full_name()
        return full_name if full_name else obj.user.username
    get_full_name.short_description = 'Nombre Completo'
    get_full_name.admin_order_field = 'user__first_name'
    
    def get_email(self, obj):
        """Obtiene el email del usuario"""
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
    
    def get_grupo(self, obj):
        """Obtiene el grupo principal del usuario"""
        grupo = obj.user.groups.first()
        return grupo.name if grupo else 'Sin grupo'
    get_grupo.short_description = 'Grupo'
    
    def get_queryset(self, request):
        """Personaliza el queryset para incluir información relacionada"""
        return super().get_queryset(request).select_related('user').prefetch_related('user__groups')

admin.site.register(Registro, RegistroAdmin)
