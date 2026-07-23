"""
Cached versions of blog views using Redis caching.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.utils.timezone import now
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy

from .models import Noticia, Categoria, Comentario, SancionUsuario, ReporteComentario, ComentarioFijado, MetricaComunidad
from .forms import ComentarioForm, NoticiaForm, EditorRevisionForm, AutorNoticiaForm
from .forms import validar_imagen_autor
from cfbc.cache_utils import (
    get_cached_noticias_publicadas, 
    get_cached_categorias,
    invalidate_noticias_cache,
    invalidate_categorias_cache,
    CacheMetrics,
    cached_with_metrics
)


def es_moderador(user):
    """Check if user is a moderator."""
    return user.is_authenticated and user.groups.filter(name='Blog Moderador').exists()


def es_autor(user):
    """Check if user is an author."""
    return user.is_authenticated and user.groups.filter(name='Blog Autor').exists()


def es_editor(user):
    """Check if user is an editor."""
    return user.is_authenticated and user.groups.filter(name='Editor').exists()


@cached_with_metrics(timeout=300, key_prefix='blog:lista_noticias_filtered')
def get_filtered_noticias(user, categoria_slug=None, busqueda=None):
    """
    Get filtered news with caching support.
    
    Args:
        user: Current user for visibility filtering
        categoria_slug: Optional category slug filter
        busqueda: Optional search query
        
    Returns:
        Filtered QuerySet of Noticia objects
    """
    # Start with cached published news
    noticias = get_cached_noticias_publicadas()
    
    # Apply visibility filter
    if not user.is_authenticated:
        noticias = noticias.exclude(visibilidad='solo_registrados')
    
    # Apply category filter
    if categoria_slug:
        categoria = Categoria.objects.get(slug=categoria_slug)
        noticias = noticias.filter(categoria=categoria)
    
    # Apply search filter
    if busqueda:
        noticias = noticias.filter(
            Q(titulo__icontains=busqueda) | 
            Q(resumen__icontains=busqueda) |
            Q(contenido__icontains=busqueda)
        )
    
    return noticias


@cached_with_metrics(timeout=300, key_prefix='blog:noticias_destacadas')
def get_destacadas_noticias(user):
    """
    Get featured news with caching support.
    
    Args:
        user: Current user for visibility filtering
        
    Returns:
        QuerySet of featured Noticia objects
    """
    noticias_destacadas_qs = Noticia.objects.filter(
        estado='publicado',
        destacada=True
    )
    
    if not user.is_authenticated:
        noticias_destacadas_qs = noticias_destacadas_qs.exclude(visibilidad='solo_registrados')
    
    return noticias_destacadas_qs[:10]


@cached_with_metrics(timeout=3600, key_prefix='blog:categorias_with_counts')
def get_categorias_with_counts():
    """
    Get categories with news counts using caching.
    
    Returns:
        QuerySet of Categoria objects with annotation
    """
    from django.db.models import Count
    return Categoria.objects.annotate(
        noticias_publicadas_count=Count(
            'noticias',
            filter=Q(noticias__estado='publicado')
        )
    ).order_by('nombre')[:10]


def lista_noticias_cached(request):
    """
    Cached version of lista_noticias view with Redis caching.
    
    Validates: Requirements 2.1, 2.2, 2.5, 2.6, 2.8
    """
    # Get filter parameters
    categoria_slug = request.GET.get('categoria')
    busqueda = request.GET.get('q')
    
    # Get filtered news using cached function
    noticias = get_filtered_noticias(request.user, categoria_slug, busqueda)
    
    # Pagination
    paginator = Paginator(noticias, 6)  # 6 noticias por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get featured news using cached function
    noticias_destacadas = get_destacadas_noticias(request.user)
    
    # Get categories with counts using cached function
    categorias = get_categorias_with_counts()
    
    # Context data
    is_editor = request.user.is_authenticated and request.user.groups.filter(name='Editor').exists()
    is_moderador = request.user.is_authenticated and es_moderador(request.user)
    is_autor = request.user.is_authenticated and es_autor(request.user)
    
    context = {
        'page_obj': page_obj,
        'noticias_destacadas': noticias_destacadas,
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_actual': categoria_slug,
        'is_editor': is_editor,
        'is_moderador': is_moderador,
        'is_autor': is_autor,
    }
    
    # Record cache metrics for this view
    CacheMetrics.record_hit('blog:lista_noticias_view')
    
    return render(request, 'blog/lista_noticias.html', context)


def noticias_por_categoria_cached(request, slug):
    """
    Cached version of noticias_por_categoria view.
    
    Validates: Requirements 2.1, 2.2, 2.5, 2.6, 2.8
    """
    categoria = get_object_or_404(Categoria, slug=slug)
    
    # Get filtered news for this category using cached function
    noticias = get_filtered_noticias(request.user, categoria_slug=slug)
    
    # Pagination
    paginator = Paginator(noticias, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get featured news using cached function
    noticias_destacadas = get_destacadas_noticias(request.user)
    
    # Get categories with counts using cached function
    categorias = get_categorias_with_counts()
    
    # Context data
    is_editor = request.user.is_authenticated and request.user.groups.filter(name='Editor').exists()
    is_moderador = request.user.is_authenticated and es_moderador(request.user)
    is_autor = request.user.is_authenticated and es_autor(request.user)
    
    context = {
        'categoria': categoria,
        'page_obj': page_obj,
        'noticias_destacadas': noticias_destacadas,
        'categorias': categorias,
        'categoria_actual': slug,
        'is_editor': is_editor,
        'is_moderador': is_moderador,
        'is_autor': is_autor,
    }
    
    # Record cache metrics for this view
    CacheMetrics.record_hit('blog:noticias_por_categoria_view')
    
    return render(request, 'blog/lista_noticias.html', context)


# Cache invalidation signal handlers
def invalidate_cache_on_noticia_save(sender, instance, **kwargs):
    """
    Signal handler to invalidate cache when a Noticia is saved.
    
    This ensures cache consistency when news are created, updated, or deleted.
    """
    # Only invalidate if estado changed to/from 'publicado'
    if instance.pk:
        try:
            old_instance = Noticia.objects.get(pk=instance.pk)
            if old_instance.estado != instance.estado:
                invalidate_noticias_cache()
                invalidate_categorias_cache()
        except Noticia.DoesNotExist:
            pass
    else:
        # New instance
        if instance.estado == 'publicado':
            invalidate_noticias_cache()
            invalidate_categorias_cache()


def invalidate_cache_on_categoria_save(sender, instance, **kwargs):
    """
    Signal handler to invalidate cache when a Categoria is saved.
    """
    invalidate_categorias_cache()
    # Also invalidate news cache since categories affect news listings
    invalidate_noticias_cache()


# Function to get cache statistics for monitoring
def get_cache_stats():
    """
    Get cache statistics for monitoring and debugging.
    
    Returns:
        Dictionary with cache statistics
    """
    return CacheMetrics.get_stats()