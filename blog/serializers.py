"""
Django REST Framework serializers for Blog app.

Validates: Requirements 11.2, 10.1
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Noticia, Categoria, Comentario, ReporteComentario, SancionUsuario, MetricaComunidad


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Categoria model."""
    
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'slug']
        read_only_fields = ['id', 'slug']


class BlogPostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for blog post lists (without full content)."""
    
    categoria = serializers.StringRelatedField(read_only=True)
    autor_username = serializers.CharField(source='autor.username', read_only=True)
    imagen_principal_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Noticia
        fields = [
            'id',
            'titulo',
            'slug',
            'resumen',
            'imagen_principal_url',
            'categoria',
            'autor_username',
            'estado',
            'fecha_publicacion',
            'meta_descripcion',
            'destacada',
        ]
        read_only_fields = ['id', 'slug', 'fecha_publicacion']
    
    def get_imagen_principal_url(self, obj):
        """Build absolute URL for the main image."""
        if obj.imagen_principal:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.imagen_principal.url)
            return obj.imagen_principal.url
        return None


class BlogPostSerializer(serializers.ModelSerializer):
    """Full serializer for blog post detail view."""
    
    categoria = serializers.StringRelatedField(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        required=False,
        allow_null=True,
        queryset=Categoria.objects.all(),
        source='categoria',
        help_text='ID de la categoría (opcional, se usa la primera categoría por defecto)'
    )
    autor_username = serializers.CharField(source='autor.username', read_only=True)
    imagen_principal_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Noticia
        fields = [
            'id',
            'titulo',
            'slug',
            'resumen',
            'contenido',
            'imagen_principal_url',
            'categoria',
            'categoria_id',
            'autor_username',
            'estado',
            'visibilidad',
            'destacada',
            'permitir_comentarios',
            'fecha_creacion',
            'fecha_actualizacion',
            'fecha_publicacion',
            'meta_descripcion',
            'notas_editor',
        ]
        read_only_fields = [
            'id',
            'slug',
            'fecha_creacion',
            'fecha_actualizacion',
            'fecha_publicacion'
        ]
    
    def get_imagen_principal_url(self, obj):
        """Build absolute URL for the main image."""
        if obj.imagen_principal:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.imagen_principal.url)
            return obj.imagen_principal.url
        return None
    
    def create(self, validated_data):
        """Handle categoria field for write operations.
        
        The categoria_id field (PrimaryKeyRelatedField with source='categoria')
        resolves the category ID to a Categoria instance during validation.
        If no category is provided, assign the first available category as default.
        """
        if 'categoria' not in validated_data or validated_data['categoria'] is None:
            default_categoria = Categoria.objects.first()
            if default_categoria:
                validated_data['categoria'] = default_categoria
            else:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'categoria_id': 'Se requiere una categoría. No hay categorías disponibles.'})
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle categoria field for update operations.
        
        The categoria_id field (PrimaryKeyRelatedField with source='categoria')
        resolves the category ID to a Categoria instance during validation.
        Only update category if explicitly provided.
        """
        return super().update(instance, validated_data)


class CommentReportSerializer(serializers.ModelSerializer):
    """Serializer for ReporteComentario model."""
    
    reportado_por_username = serializers.CharField(source='reportado_por.username', read_only=True)
    resuelto_por_username = serializers.CharField(source='resuelto_por.username', read_only=True, allow_null=True)
    comentario_contenido = serializers.CharField(source='comentario.contenido', read_only=True)
    comentario_autor = serializers.CharField(source='comentario.autor.username', read_only=True)
    
    class Meta:
        model = ReporteComentario
        fields = [
            'id',
            'comentario',
            'comentario_contenido',
            'comentario_autor',
            'reportado_por',
            'reportado_por_username',
            'motivo',
            'fecha_reporte',
            'estado',
            'resuelto_por',
            'resuelto_por_username',
            'fecha_resolucion',
        ]
        read_only_fields = ['id', 'fecha_reporte', 'fecha_resolucion']


class UserSanctionSerializer(serializers.ModelSerializer):
    """Serializer for SancionUsuario model."""
    
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    aplicada_por_username = serializers.CharField(source='aplicada_por.username', read_only=True, allow_null=True)
    levantada_por_username = serializers.CharField(source='levantada_por.username', read_only=True, allow_null=True)
    
    class Meta:
        model = SancionUsuario
        fields = [
            'id',
            'usuario',
            'usuario_username',
            'tipo_sancion',
            'motivo',
            'fecha_inicio',
            'fecha_fin',
            'aplicada_por',
            'aplicada_por_username',
            'activa',
            'fecha_levantamiento',
            'levantada_por',
            'levantada_por_username',
        ]
        read_only_fields = ['id', 'fecha_inicio', 'fecha_levantamiento']


class CommunityMetricsSerializer(serializers.ModelSerializer):
    """Serializer for MetricaComunidad model."""
    
    usuario_mas_activo_username = serializers.CharField(
        source='usuario_mas_activo.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = MetricaComunidad
        fields = [
            'id',
            'fecha',
            'total_reportes',
            'total_comentarios',
            'total_sanciones',
            'usuario_mas_activo',
            'usuario_mas_activo_username',
            'pico_toxicidad',
            'generada_en',
        ]
        read_only_fields = ['id', 'generada_en']
