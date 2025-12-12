from django.contrib import admin
from .models import CategoriaFAQ, FAQ, FAQVariation, ChatInteraction, DocumentEmbedding


@admin.register(CategoriaFAQ)
class CategoriaFAQAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'icono', 'orden']
    list_editable = ['orden']
    search_fields = ['nombre', 'descripcion']
    prepopulated_fields = {'slug': ('nombre',)}
    ordering = ['orden', 'nombre']


class FAQVariationInline(admin.TabularInline):
    model = FAQVariation
    extra = 2
    fields = ['texto_variacion']
    verbose_name = 'Variación de pregunta'
    verbose_name_plural = 'Variaciones de pregunta (sinónimos, jerga local, formas alternativas)'
    
    def get_extra(self, request, obj=None, **kwargs):
        # Show more empty forms for new FAQs
        if obj is None:
            return 3
        return 1


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['pregunta_corta', 'categoria', 'prioridad', 'destacada', 'activa', 'veces_usada', 'tasa_exito', 'variaciones_count']
    list_filter = ['categoria', 'destacada', 'activa', 'fecha_creacion', 'categoria__nombre']
    list_editable = ['prioridad', 'destacada', 'activa']
    search_fields = ['pregunta', 'respuesta', 'variaciones__texto_variacion']
    readonly_fields = ['veces_usada', 'ultima_fecha_uso', 'tasa_exito', 'fecha_creacion', 'fecha_actualizacion']
    ordering = ['-destacada', '-prioridad', '-veces_usada']
    inlines = [FAQVariationInline]
    actions = ['make_destacada', 'make_no_destacada', 'activate_faqs', 'deactivate_faqs']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('pregunta', 'respuesta', 'categoria'),
            'description': 'Información básica de la FAQ. La pregunta principal y su respuesta.'
        }),
        ('Configuración', {
            'fields': ('prioridad', 'destacada', 'activa'),
            'description': 'Configuración de visualización y prioridad en los resultados de búsqueda.'
        }),
        ('Métricas de Uso', {
            'fields': ('veces_usada', 'ultima_fecha_uso', 'tasa_exito'),
            'classes': ('collapse',),
            'description': 'Estadísticas de uso y efectividad de esta FAQ.'
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',),
            'description': 'Fechas de creación y última modificación.'
        }),
    )
    
    def pregunta_corta(self, obj):
        return obj.pregunta[:80] + '...' if len(obj.pregunta) > 80 else obj.pregunta
    pregunta_corta.short_description = 'Pregunta'
    pregunta_corta.admin_order_field = 'pregunta'
    
    def variaciones_count(self, obj):
        count = obj.variaciones.count()
        if count == 0:
            return '0'
        return f'{count} variación{"es" if count != 1 else ""}'
    variaciones_count.short_description = 'Variaciones'
    
    def make_destacada(self, request, queryset):
        updated = queryset.update(destacada=True)
        self.message_user(request, f'{updated} FAQ(s) marcadas como destacadas.')
    make_destacada.short_description = 'Marcar como destacadas'
    
    def make_no_destacada(self, request, queryset):
        updated = queryset.update(destacada=False)
        self.message_user(request, f'{updated} FAQ(s) desmarcadas como destacadas.')
    make_no_destacada.short_description = 'Desmarcar como destacadas'
    
    def activate_faqs(self, request, queryset):
        updated = queryset.update(activa=True)
        self.message_user(request, f'{updated} FAQ(s) activadas.')
    activate_faqs.short_description = 'Activar FAQs seleccionadas'
    
    def deactivate_faqs(self, request, queryset):
        updated = queryset.update(activa=False)
        self.message_user(request, f'{updated} FAQ(s) desactivadas.')
    deactivate_faqs.short_description = 'Desactivar FAQs seleccionadas'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('categoria').prefetch_related('variaciones')



@admin.register(ChatInteraction)
class ChatInteractionAdmin(admin.ModelAdmin):
    list_display = ['pregunta_corta', 'intencion_detectada', 'confianza', 'fue_util', 'es_candidata_faq', 'fecha', 'tiempo_respuesta']
    list_filter = ['intencion_detectada', 'fue_util', 'es_candidata_faq', 'fecha']
    search_fields = ['pregunta', 'respuesta', 'session_id']
    readonly_fields = ['session_id', 'pregunta', 'respuesta', 'documentos_recuperados', 'intencion_detectada', 'confianza', 'fecha', 'tiempo_respuesta']
    ordering = ['-fecha']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Interacción', {
            'fields': ('session_id', 'pregunta', 'respuesta', 'fecha', 'tiempo_respuesta')
        }),
        ('Análisis', {
            'fields': ('intencion_detectada', 'confianza', 'documentos_recuperados')
        }),
        ('Feedback', {
            'fields': ('fue_util', 'es_candidata_faq')
        }),
    )
    
    def pregunta_corta(self, obj):
        return obj.pregunta[:60] + '...' if len(obj.pregunta) > 60 else obj.pregunta
    pregunta_corta.short_description = 'Pregunta'
    
    def has_add_permission(self, request):
        # No permitir agregar interacciones manualmente
        return False



@admin.register(DocumentEmbedding)
class DocumentEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'object_id', 'categoria', 'texto_corto', 'fecha_indexacion']
    list_filter = ['content_type', 'categoria', 'fecha_indexacion']
    search_fields = ['texto_indexado']
    readonly_fields = ['content_type', 'object_id', 'texto_indexado', 'embedding_vector', 'categoria', 'fecha_indexacion']
    ordering = ['-fecha_indexacion']
    date_hierarchy = 'fecha_indexacion'
    
    def texto_corto(self, obj):
        return obj.texto_indexado[:80] + '...' if len(obj.texto_indexado) > 80 else obj.texto_indexado
    texto_corto.short_description = 'Texto'
    
    def has_add_permission(self, request):
        # No permitir agregar embeddings manualmente
        return False

# Custom admin site configuration
from django.contrib.admin import AdminSite
from django.urls import path
from .admin_views import (
    suggested_faqs_view, create_faq_from_suggestion, faq_metrics_view, 
    chatbot_dashboard, export_metrics, bulk_approve_faqs, dismiss_suggestion,
    rebuild_search_index
)


class ChatbotAdminMixin:
    """Mixin to add custom URLs to admin"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('suggested-faqs/', suggested_faqs_view, name='chatbot_suggested_faqs'),
            path('create-faq-from-suggestion/', create_faq_from_suggestion, name='chatbot_create_faq_from_suggestion'),
            path('faq-metrics/', faq_metrics_view, name='chatbot_faq_metrics'),
            path('dashboard/', chatbot_dashboard, name='chatbot_dashboard'),
            path('export-metrics/', export_metrics, name='chatbot_export_metrics'),
            path('bulk-approve-faqs/', bulk_approve_faqs, name='chatbot_bulk_approve_faqs'),
            path('dismiss-suggestion/', dismiss_suggestion, name='chatbot_dismiss_suggestion'),
            path('rebuild-index/', rebuild_search_index, name='chatbot_rebuild_index'),
        ]
        return custom_urls + urls


# Apply mixin to existing admin classes
class EnhancedFAQAdmin(ChatbotAdminMixin, FAQAdmin):
    pass

class EnhancedCategoriaFAQAdmin(ChatbotAdminMixin, CategoriaFAQAdmin):
    pass

class EnhancedChatInteractionAdmin(ChatbotAdminMixin, ChatInteractionAdmin):
    pass

class EnhancedDocumentEmbeddingAdmin(ChatbotAdminMixin, DocumentEmbeddingAdmin):
    pass

# Re-register with enhanced admin classes
admin.site.unregister(FAQ)
admin.site.unregister(CategoriaFAQ)
admin.site.unregister(ChatInteraction)
admin.site.unregister(DocumentEmbedding)

admin.site.register(FAQ, EnhancedFAQAdmin)
admin.site.register(CategoriaFAQ, EnhancedCategoriaFAQAdmin)
admin.site.register(ChatInteraction, EnhancedChatInteractionAdmin)
admin.site.register(DocumentEmbedding, EnhancedDocumentEmbeddingAdmin)