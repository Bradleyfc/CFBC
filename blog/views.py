from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from .models import Noticia, Categoria, Comentario
from .forms import ComentarioForm, NoticiaForm

def lista_noticias(request):
    """Vista para mostrar todas las noticias publicadas"""
    noticias = Noticia.objects.filter(estado='publicado').select_related('categoria', 'autor')

    # Filtrar por visibilidad: si el usuario no está autenticado, excluir las de solo_registrados
    if not request.user.is_authenticated:
        noticias = noticias.exclude(visibilidad='solo_registrados')
    
    # Filtro por categoría
    categoria_slug = request.GET.get('categoria')
    if categoria_slug:
        categoria = get_object_or_404(Categoria, slug=categoria_slug)
        noticias = noticias.filter(categoria=categoria)
    
    # Búsqueda
    busqueda = request.GET.get('q')
    if busqueda:
        noticias = noticias.filter(
            Q(titulo__icontains=busqueda) | 
            Q(resumen__icontains=busqueda) |
            Q(contenido__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(noticias, 6)  # 6 noticias por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Noticias destacadas para el sidebar
    noticias_destacadas_qs = Noticia.objects.filter(
        estado='publicado',
        destacada=True
    )
    if not request.user.is_authenticated:
        noticias_destacadas_qs = noticias_destacadas_qs.exclude(visibilidad='solo_registrados')
    noticias_destacadas = noticias_destacadas_qs[:5]
    
    # Categorías para el menú
    categorias = Categoria.objects.all()
    
    context = {
        'page_obj': page_obj,
        'noticias_destacadas': noticias_destacadas,
        'categorias': categorias,
        'busqueda': busqueda,
        'categoria_actual': categoria_slug,
    }
    
    return render(request, 'blog/lista_noticias.html', context)

def detalle_noticia(request, slug):
    """Vista para mostrar el detalle de una noticia"""
    noticia = get_object_or_404(
        Noticia.objects.select_related('categoria', 'autor'),
        slug=slug,
        estado='publicado'
    )

    # Aplicar restricción de visibilidad
    if noticia.visibilidad == 'solo_registrados' and not request.user.is_authenticated:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    # Comentarios de la noticia
    comentarios = noticia.comentarios.filter(activo=True).select_related('autor')
    
    # Formulario para nuevos comentarios
    comentario_form = ComentarioForm()
    
    # Noticias relacionadas (misma categoría)
    noticias_relacionadas_qs = Noticia.objects.filter(
        categoria=noticia.categoria,
        estado='publicado'
    ).exclude(id=noticia.id)
    if not request.user.is_authenticated:
        noticias_relacionadas_qs = noticias_relacionadas_qs.exclude(visibilidad='solo_registrados')
    noticias_relacionadas = noticias_relacionadas_qs[:4]
    
    context = {
        'noticia': noticia,
        'comentarios': comentarios,
        'comentario_form': comentario_form,
        'noticias_relacionadas': noticias_relacionadas,
    }
    
    return render(request, 'blog/detalle_noticia.html', context)

@login_required
def agregar_comentario(request, slug):
    """Vista para agregar un comentario a una noticia"""
    noticia = get_object_or_404(Noticia, slug=slug, estado='publicado')
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.noticia = noticia
            comentario.autor = request.user
            comentario.save()
            messages.success(request, 'Tu comentario ha sido agregado exitosamente.')
            return redirect('blog:detalle_noticia', slug=slug)
    
    return redirect('blog:detalle_noticia', slug=slug)

def noticias_por_categoria(request, slug):
    """Vista para mostrar noticias de una categoría específica"""
    categoria = get_object_or_404(Categoria, slug=slug)
    noticias = Noticia.objects.filter(
        categoria=categoria,
        estado='publicado'
    ).select_related('autor')

    # Filtrar por visibilidad
    if not request.user.is_authenticated:
        noticias = noticias.exclude(visibilidad='solo_registrados')
    
    # Paginación
    paginator = Paginator(noticias, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorías para el menú
    categorias = Categoria.objects.all()
    
    context = {
        'categoria': categoria,
        'page_obj': page_obj,
        'categorias': categorias,
    }
    
    return render(request, 'blog/categoria_noticias.html', context)

# Función para verificar si el usuario es editor
def es_editor(user):
    return user.is_authenticated and (
        user.groups.filter(name='Editor').exists() or 
        user.is_staff or 
        user.is_superuser
    )

# Vista para el panel de editor
@user_passes_test(es_editor)
def panel_editores(request):
    """Panel principal para editor"""
    # Estadísticas
    total_noticias = Noticia.objects.count()
    noticias_publicadas = Noticia.objects.filter(estado='publicado').count()
    noticias_borrador = Noticia.objects.filter(estado='borrador').count()
    mis_noticias = Noticia.objects.filter(autor=request.user).count()
    
    # Últimas noticias del usuario
    ultimas_noticias = Noticia.objects.filter(autor=request.user).order_by('-fecha_creacion')[:5]
    
    context = {
        'total_noticias': total_noticias,
        'noticias_publicadas': noticias_publicadas,
        'noticias_borrador': noticias_borrador,
        'mis_noticias': mis_noticias,
        'ultimas_noticias': ultimas_noticias,
    }
    
    return render(request, 'blog/editores/panel.html', context)

# Vista para listar noticias del editor
@user_passes_test(es_editor)
def mis_noticias(request):
    """Lista de noticias del editor actual"""
    noticias = Noticia.objects.filter(autor=request.user).order_by('-fecha_creacion')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        noticias = noticias.filter(estado=estado)
    
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        noticias = noticias.filter(categoria_id=categoria_id)
    
    # Paginación
    paginator = Paginator(noticias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categorias = Categoria.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'estado_actual': estado,
        'categoria_actual': categoria_id,
    }
    
    return render(request, 'blog/editores/mis_noticias.html', context)

# Vista para crear noticia
@user_passes_test(es_editor)
def crear_noticia(request):
    """Crear nueva noticia"""
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.save()
            messages.success(request, 'Noticia creada exitosamente.')
            return redirect('blog:editar_noticia', pk=noticia.pk)
    else:
        form = NoticiaForm()
    
    return render(request, 'blog/editores/crear_noticia.html', {'form': form})

# Vista para editar noticia
@user_passes_test(es_editor)
def editar_noticia(request, pk):
    """Editar noticia existente"""
    noticia = get_object_or_404(Noticia, pk=pk)
    
    # Solo el autor o staff puede editar
    if noticia.autor != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para editar esta noticia.')
        return redirect('blog:mis_noticias')
    
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('blog:editar_noticia', pk=noticia.pk)
    else:
        form = NoticiaForm(instance=noticia)
    
    return render(request, 'blog/editores/editar_noticia.html', {
        'form': form, 
        'noticia': noticia
    })

# Vista para eliminar noticia
@user_passes_test(es_editor)
def eliminar_noticia(request, pk):
    """Eliminar noticia"""
    noticia = get_object_or_404(Noticia, pk=pk)
    
    # Solo el autor o staff puede eliminar
    if noticia.autor != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para eliminar esta noticia.')
        return redirect('blog:mis_noticias')
    
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Noticia eliminada exitosamente.')
        return redirect('blog:mis_noticias')
    
    return render(request, 'blog/editores/eliminar_noticia.html', {'noticia': noticia})

# Vista para gestionar categorías
@user_passes_test(es_editor)
def gestionar_categorias(request):
    """Gestionar categorías"""
    categorias = Categoria.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        
        if nombre:
            categoria, created = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion}
            )
            if created:
                messages.success(request, f'Categoría "{nombre}" creada exitosamente.')
            else:
                messages.warning(request, f'La categoría "{nombre}" ya existe.')
        
        return redirect('blog:gestionar_categorias')
    
    return render(request, 'blog/editores/categorias.html', {'categorias': categorias})