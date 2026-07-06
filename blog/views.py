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

def lista_noticias(request):
    """Vista para mostrar todas las noticias publicadas"""
    noticias = Noticia.objects.filter(estado='publicado').select_related('categoria', 'autor').order_by('-fecha_actualizacion', '-fecha_creacion')

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
    
    # Noticias destacadas para el sidebar (solo publicadas)
    noticias_destacadas_qs = Noticia.objects.filter(
        estado='publicado',
        destacada=True
    )
    if not request.user.is_authenticated:
        noticias_destacadas_qs = noticias_destacadas_qs.exclude(visibilidad='solo_registrados')
    noticias_destacadas = noticias_destacadas_qs[:10]
    
    # Categorías con conteo de noticias publicadas
    from django.db.models import Count
    categorias = Categoria.objects.annotate(
        noticias_publicadas_count=Count(
            'noticias',
            filter=Q(noticias__estado='publicado')
        )
    ).order_by('nombre')[:10]
    
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
    
    # Comentarios fijados (activos) ordenados por su posición
    fijados_ids = ComentarioFijado.objects.filter(
        noticia=noticia
    ).values_list('comentario_id', flat=True)

    comentarios_fijados = noticia.comentarios.filter(
        id__in=fijados_ids, activo=True
    ).select_related('autor').order_by('fijado__orden')

    comentarios_normales = noticia.comentarios.filter(
        activo=True
    ).exclude(id__in=fijados_ids).select_related('autor').order_by('fecha_creacion')

    # Combinar para el contexto
    comentarios = list(comentarios_fijados) + list(comentarios_normales)
    
    # Formulario para nuevos comentarios (solo si la noticia permite comentarios)
    comentario_form = ComentarioForm() if noticia.permitir_comentarios else None
    
    # Noticias relacionadas (misma categoría)
    noticias_relacionadas_qs = Noticia.objects.filter(
        categoria=noticia.categoria,
        estado='publicado'
    ).exclude(id=noticia.id)
    if not request.user.is_authenticated:
        noticias_relacionadas_qs = noticias_relacionadas_qs.exclude(visibilidad='solo_registrados')
    noticias_relacionadas = noticias_relacionadas_qs[:4]
    
    is_editor = request.user.is_authenticated and request.user.groups.filter(name='Editor').exists()
    is_moderador = request.user.is_authenticated and es_moderador(request.user)
    is_autor = request.user.is_authenticated and es_autor(request.user)
    context = {
        'noticia': noticia,
        'comentarios': comentarios,
        'comentarios_fijados_ids': list(fijados_ids),
        'comentario_form': comentario_form,
        'noticias_relacionadas': noticias_relacionadas,
        'is_editor': is_editor,
        'is_moderador': is_moderador,
        'is_autor': is_autor,
    }
    
    return render(request, 'blog/detalle_noticia.html', context)

def usuario_sancionado(user):
    """Retorna True si el usuario tiene una sanción activa vigente."""
    return SancionUsuario.objects.filter(
        usuario=user,
        activa=True
    ).filter(
        Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=timezone.now())
    ).exists()


@login_required
def agregar_comentario(request, slug):
    """Vista para agregar un comentario a una noticia"""
    noticia = get_object_or_404(Noticia, slug=slug, estado='publicado')

    if not noticia.permitir_comentarios:
        messages.error(request, 'Esta noticia no permite comentarios.')
        return redirect('blog:detalle_noticia', slug=slug)

    if usuario_sancionado(request.user):
        messages.error(request, 'Tu cuenta tiene una sanción activa que impide comentar.')
        return redirect('blog:detalle_noticia', slug=slug)

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
    ).select_related('categoria', 'autor').order_by('-fecha_actualizacion', '-fecha_creacion')

    # Filtrar por visibilidad
    if not request.user.is_authenticated:
        noticias = noticias.exclude(visibilidad='solo_registrados')

    # Paginación
    paginator = Paginator(noticias, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Noticias destacadas para el sidebar
    noticias_destacadas_qs = Noticia.objects.filter(
        estado='publicado',
        destacada=True
    )
    if not request.user.is_authenticated:
        noticias_destacadas_qs = noticias_destacadas_qs.exclude(visibilidad='solo_registrados')
    noticias_destacadas = noticias_destacadas_qs[:10]

    # Categorías con conteo de noticias publicadas
    from django.db.models import Count
    categorias = Categoria.objects.annotate(
        noticias_publicadas_count=Count(
            'noticias',
            filter=Q(noticias__estado='publicado')
        )
    ).order_by('nombre')[:10]

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

    return render(request, 'blog/lista_noticias.html', context)

# ── PANEL AUTOR ────────────────────────────────────────────────────────────

def es_autor(user):
    return user.is_authenticated and (
        user.groups.filter(name='Blog Autor').exists() or
        user.is_staff or
        user.is_superuser
    )


@user_passes_test(es_autor)
def panel_autores(request):
    """Panel principal del autor con estadísticas propias."""
    mis_total = Noticia.objects.filter(autor=request.user).count()
    mis_publicadas = Noticia.objects.filter(autor=request.user, estado='publicado').count()
    mis_borradores = Noticia.objects.filter(autor=request.user, estado='borrador').count()
    mis_en_revision = Noticia.objects.filter(autor=request.user, estado='pendiente_revision').count()
    mis_comentarios = Comentario.objects.filter(
        noticia__autor=request.user, activo=True
    ).count()
    ultima_publicacion = (
        Noticia.objects
        .filter(autor=request.user, estado='publicado')
        .order_by('-fecha_publicacion')
        .first()
    )
    ultimas_noticias = (
        Noticia.objects
        .filter(autor=request.user)
        .order_by('-fecha_creacion')[:5]
    )

    context = {
        'mis_total': mis_total,
        'mis_publicadas': mis_publicadas,
        'mis_borradores': mis_borradores,
        'mis_en_revision': mis_en_revision,
        'mis_comentarios': mis_comentarios,
        'ultima_publicacion': ultima_publicacion,
        'ultimas_noticias': ultimas_noticias,
    }
    return render(request, 'blog/autores/panel.html', context)


@user_passes_test(es_autor)
def mis_noticias_autor(request):
    """Lista de noticias propias del autor con filtros y paginación."""
    noticias = Noticia.objects.filter(autor=request.user).order_by('-fecha_creacion')

    estado = request.GET.get('estado')
    estados_validos = ('borrador', 'pendiente_revision', 'publicado', 'archivado')
    if estado in estados_validos:
        noticias = noticias.filter(estado=estado)

    categoria_id = request.GET.get('categoria')
    if categoria_id:
        noticias = noticias.filter(categoria_id=categoria_id)

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
    return render(request, 'blog/autores/mis_noticias.html', context)


@user_passes_test(es_autor)
def crear_noticia_autor(request):
    """Crea un nuevo borrador para el autor."""
    if request.method == 'POST':
        form = AutorNoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.estado = 'borrador'
            noticia.save()
            messages.success(request, 'Borrador creado exitosamente.')
            return redirect('blog:editar_noticia_autor', pk=noticia.pk)
    else:
        form = AutorNoticiaForm()

    return render(request, 'blog/autores/crear_noticia.html', {'form': form})


@user_passes_test(es_autor)
def editar_noticia_autor(request, pk):
    """Edita un borrador propio del autor."""
    noticia = get_object_or_404(Noticia, pk=pk)

    if noticia.autor != request.user:
        messages.error(request, 'No tienes permisos para editar esta noticia.')
        return redirect('blog:mis_noticias_autor')

    if request.method == 'POST':
        if noticia.estado != 'borrador':
            messages.error(request, 'Solo puedes editar borradores.')
            return redirect('blog:mis_noticias_autor')

        imagen_actual = noticia.imagen_principal.name if noticia.imagen_principal else ''

        form = AutorNoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            noticia_guardada = form.save(commit=False)
            noticia_guardada.autor = request.user
            noticia_guardada.estado = 'borrador'

            archivo = request.FILES.get('imagen_principal')
            if archivo:
                try:
                    validar_imagen_autor(archivo)
                except Exception as e:
                    messages.error(request, str(e))
                    return redirect('blog:editar_noticia_autor', pk=pk)
                # Eliminar imagen anterior
                if imagen_actual:
                    from django.core.files.storage import default_storage
                    try:
                        default_storage.delete(imagen_actual)
                    except Exception:
                        pass
                # Asignar archivo nuevo directamente al campo
                noticia_guardada.imagen_principal = archivo
            else:
                # Sin archivo nuevo: forzar el valor anterior antes de guardar
                noticia_guardada.imagen_principal = imagen_actual

            noticia_guardada.save()
            messages.success(request, 'Borrador actualizado.')
            return redirect('blog:editar_noticia_autor', pk=pk)
    else:
        form = AutorNoticiaForm(instance=noticia)

    return render(request, 'blog/autores/editar_noticia.html', {
        'form': form,
        'noticia': noticia,
    })


@user_passes_test(es_autor)
def eliminar_noticia_autor(request, pk):
    """Elimina un borrador propio del autor."""
    noticia = get_object_or_404(Noticia, pk=pk)

    if noticia.autor != request.user:
        messages.error(request, 'No tienes permisos para eliminar esta noticia.')
        return redirect('blog:mis_noticias_autor')

    if noticia.estado != 'borrador':
        messages.error(request, 'Solo puedes eliminar borradores.')
        return redirect('blog:mis_noticias_autor')

    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Borrador eliminado exitosamente.')
        return redirect('blog:mis_noticias_autor')

    return render(request, 'blog/autores/eliminar_noticia.html', {'noticia': noticia})


@user_passes_test(es_autor)
def enviar_revision(request, pk):
    """Envía un borrador propio a revisión del editor."""
    noticia = get_object_or_404(Noticia, pk=pk)

    if noticia.autor != request.user:
        messages.error(request, 'No tienes permisos para enviar esta noticia a revisión.')
        return redirect('blog:mis_noticias_autor')

    if noticia.estado != 'borrador':
        messages.error(
            request,
            'Esta noticia ya fue enviada a revisión o no es un borrador.'
        )
        return redirect('blog:mis_noticias_autor')

    noticia.estado = 'pendiente_revision'
    noticia.save(update_fields=['estado'])
    messages.success(request, f'"{noticia.titulo}" enviada a revisión correctamente.')
    return redirect('blog:mis_noticias_autor')


@user_passes_test(es_autor)
def borradores_autor(request):
    """Lista de borradores del autor, incluyendo los devueltos por el editor con notas."""
    borradores = (
        Noticia.objects
        .filter(autor=request.user, estado='borrador')
        .select_related('categoria')
        .order_by('-fecha_actualizacion')
    )

    paginator = Paginator(borradores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_borradores': borradores.count(),
    }
    return render(request, 'blog/autores/borradores.html', context)


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
        'pendientes_count': Noticia.objects.filter(estado='pendiente_revision').count(),
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
        imagen_actual = noticia.imagen_principal.name if noticia.imagen_principal else ''
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            noticia_guardada = form.save(commit=False)
            archivo = request.FILES.get('imagen_principal')
            if archivo:
                if imagen_actual:
                    from django.core.files.storage import default_storage
                    try:
                        default_storage.delete(imagen_actual)
                    except Exception:
                        pass
                noticia_guardada.imagen_principal = archivo
            else:
                noticia_guardada.imagen_principal = imagen_actual
            noticia_guardada.save()
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


@user_passes_test(es_editor)
def todas_las_noticias(request):
    """Lista todas las noticias del sistema (cualquier autor) para el editor."""
    noticias = Noticia.objects.select_related('autor', 'categoria').order_by('-fecha_creacion')

    # Filtros
    estado = request.GET.get('estado')
    estados_validos = ('borrador', 'pendiente_revision', 'publicado', 'archivado')
    if estado in estados_validos:
        noticias = noticias.filter(estado=estado)

    categoria_id = request.GET.get('categoria')
    if categoria_id:
        noticias = noticias.filter(categoria_id=categoria_id)

    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        noticias = noticias.filter(
            Q(titulo__icontains=busqueda) |
            Q(autor__username__icontains=busqueda) |
            Q(resumen__icontains=busqueda)
        )

    # Paginación
    paginator = Paginator(noticias, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categorias = Categoria.objects.all()

    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'estado_actual': estado,
        'categoria_actual': categoria_id,
        'busqueda': busqueda,
        'total_noticias': noticias.count(),
    }
    return render(request, 'blog/editores/todas_las_noticias.html', context)


@user_passes_test(es_editor)
def editar_noticia_editor(request, pk):
    """Edita cualquier noticia (acceso de editor sin restricción de autoría).
    Redirige de vuelta a todas_las_noticias al guardar."""
    noticia = get_object_or_404(Noticia, pk=pk)
    autor_original = noticia.autor  # preservar autor antes de cualquier operación

    if request.method == 'POST':
        imagen_actual = noticia.imagen_principal.name if noticia.imagen_principal else ''
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            noticia_guardada = form.save(commit=False)
            noticia_guardada.autor = autor_original  # nunca sobreescribir el autor
            archivo = request.FILES.get('imagen_principal')
            if archivo:
                if imagen_actual:
                    from django.core.files.storage import default_storage
                    try:
                        default_storage.delete(imagen_actual)
                    except Exception:
                        pass
                noticia_guardada.imagen_principal = archivo
            else:
                noticia_guardada.imagen_principal = imagen_actual
            noticia_guardada.save()
            messages.success(request, f'Noticia "{noticia_guardada.titulo}" actualizada exitosamente.')
            return redirect('blog:todas_las_noticias')
    else:
        form = NoticiaForm(instance=noticia)

    return render(request, 'blog/editores/editar_noticia_editor.html', {
        'form': form,
        'noticia': noticia,
    })


@user_passes_test(es_editor)
def eliminar_noticia_editor(request, pk):
    """Elimina cualquier noticia (acceso de editor sin restricción de autoría).
    Redirige de vuelta a todas_las_noticias tras eliminar."""
    noticia = get_object_or_404(Noticia, pk=pk)

    if request.method == 'POST':
        noticia.delete()
        messages.success(request, f'Noticia "{noticia.titulo}" eliminada exitosamente.')
        return redirect('blog:todas_las_noticias')

    return render(request, 'blog/editores/eliminar_noticia.html', {
        'noticia': noticia,
        'cancelar_url': 'todas_las_noticias',
    })

# Vista para gestionar comentarios de una noticia
@user_passes_test(es_editor)
def gestionar_comentarios(request, pk):
    """Gestionar comentarios de una noticia"""
    noticia = get_object_or_404(Noticia, pk=pk)

    if noticia.autor != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para gestionar esta noticia.')
        return redirect('blog:mis_noticias')

    comentarios = noticia.comentarios.all().select_related('autor').order_by('-fecha_creacion')

    return render(request, 'blog/editores/gestionar_comentarios.html', {
        'noticia': noticia,
        'comentarios': comentarios,
    })

# Vista para eliminar un comentario
@user_passes_test(es_editor)
def eliminar_comentario(request, pk):
    """Eliminar un comentario"""
    comentario = get_object_or_404(Comentario, pk=pk)
    noticia = comentario.noticia

    if noticia.autor != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permisos para eliminar este comentario.')
        return redirect('blog:mis_noticias')

    if request.method == 'POST':
        comentario.delete()
        messages.success(request, 'Comentario eliminado exitosamente.')

    return redirect('blog:gestionar_comentarios', pk=noticia.pk)

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


@user_passes_test(es_editor)
def eliminar_categoria(request, pk):
    """Elimina una categoría. Si tiene noticias, las mueve a 'Sin categoría' y las oculta."""
    categoria = get_object_or_404(Categoria, pk=pk)

    # No permitir eliminar la categoría especial 'Sin categoría'
    if categoria.slug == 'sin-categoria':
        messages.error(request, 'No puedes eliminar la categoría "Sin categoría".')
        return redirect('blog:gestionar_categorias')

    if request.method == 'POST':
        noticias_count = categoria.noticias.count()
        if noticias_count > 0:
            # Obtener o crear la categoría "Sin categoría"
            sin_cat, _ = Categoria.objects.get_or_create(
                slug='sin-categoria',
                defaults={
                    'nombre': 'Sin categoría',
                    'descripcion': 'Categoría para noticias sin clasificación',
                }
            )
            # Mover noticias y ocultarlas (solo_registrados las hace invisibles públicamente)
            categoria.noticias.update(
                categoria=sin_cat,
                visibilidad='solo_registrados',
            )

        nombre = categoria.nombre
        categoria.delete()
        messages.success(request, f'Categoría "{nombre}" eliminada. {noticias_count} noticia(s) movida(s) a "Sin categoría".' if noticias_count else f'Categoría "{nombre}" eliminada.')
        return redirect('blog:gestionar_categorias')

    # GET — no se usa, redirige siempre
    return redirect('blog:gestionar_categorias')


# Vista de bandeja de revisión (noticias pendientes de revisión)
@user_passes_test(es_editor)
def bandeja_revision(request):
    """Bandeja de noticias pendientes de revisión para el editor"""
    noticias_pendientes = (
        Noticia.objects
        .filter(estado='pendiente_revision')
        .select_related('autor', 'categoria')
        .order_by('-fecha_actualizacion')
    )

    pendientes_count = noticias_pendientes.count()

    paginator = Paginator(noticias_pendientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'pendientes_count': pendientes_count,
    }

    return render(request, 'blog/editores/bandeja_revision.html', context)


# Vista para revisar una noticia pendiente (publicar o devolver)
@user_passes_test(es_editor)
def revisar_noticia(request, pk):
    """Revisar una noticia pendiente: publicar o devolver con notas"""
    noticia = get_object_or_404(Noticia, pk=pk, estado='pendiente_revision')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'publicar':
            noticia.estado = 'publicado'
            noticia.fecha_publicacion = timezone.now()
            noticia.notas_editor = ''
            noticia.save(update_fields=['estado', 'fecha_publicacion', 'notas_editor'])
            messages.success(request, f'La noticia "{noticia.titulo}" ha sido publicada.')
            return redirect('blog:bandeja_revision')

        elif accion == 'devolver':
            notas_editor = request.POST.get('notas_editor', '').strip()
            if len(notas_editor) < 10:
                messages.error(
                    request,
                    'Las notas al autor deben tener al menos 10 caracteres.'
                )
                form = EditorRevisionForm(request.POST)
                return render(request, 'blog/editores/revisar_noticia.html', {
                    'noticia': noticia,
                    'form': form,
                })
            noticia.estado = 'borrador'
            noticia.notas_editor = notas_editor
            noticia.save(update_fields=['estado', 'notas_editor'])
            messages.success(
                request,
                f'La noticia "{noticia.titulo}" ha sido devuelta al autor con notas.'
            )
            return redirect('blog:bandeja_revision')

    # GET
    form = EditorRevisionForm()
    return render(request, 'blog/editores/revisar_noticia.html', {
        'noticia': noticia,
        'form': form,
    })


# ── MODERACIÓN ─────────────────────────────────────────────────────────────

def es_moderador(user):
    return user.is_authenticated and (
        user.groups.filter(name='Blog Moderador').exists() or
        user.is_staff or user.is_superuser
    )

@user_passes_test(es_moderador)
def panel_moderadores(request):
    """Panel principal del moderador con resumen de actividad."""
    context = {
        'total_reportes_pendientes': ReporteComentario.objects.filter(estado='pendiente').count(),
        'total_sanciones_activas': SancionUsuario.objects.filter(activa=True).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=timezone.now())
        ).count(),
        'total_comentarios_ocultos': Comentario.objects.filter(activo=False).count(),
    }
    return render(request, 'blog/moderadores/panel.html', context)

@permission_required('blog.change_comentario', raise_exception=True)
def mod_gestionar_comentarios(request):
    """Lista todos los comentarios con filtros para moderación."""
    comentarios = Comentario.objects.all().select_related('autor', 'noticia').order_by('-fecha_creacion')
    noticia_id = request.GET.get('noticia')
    activo = request.GET.get('activo')
    autor = request.GET.get('autor')
    if noticia_id:
        comentarios = comentarios.filter(noticia_id=noticia_id)
    if activo is not None and activo != '':
        comentarios = comentarios.filter(activo=(activo == 'true'))
    if autor:
        comentarios = comentarios.filter(autor__username__icontains=autor)
    paginator = Paginator(comentarios, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    noticias = Noticia.objects.filter(estado='publicado').order_by('titulo')
    return render(request, 'blog/moderadores/comentarios.html', {
        'page_obj': page_obj,
        'noticias': noticias,
    })

@permission_required('blog.change_comentario', raise_exception=True)
def mod_editar_comentario(request, pk):
    """Edita contenido o estado activo de un comentario."""
    comentario = get_object_or_404(Comentario, pk=pk)
    if request.method == 'POST':
        campos_permitidos = []
        if 'contenido' in request.POST:
            comentario.contenido = request.POST['contenido']
            campos_permitidos.append('contenido')
        if 'activo' in request.POST:
            comentario.activo = request.POST['activo'] == 'true'
            campos_permitidos.append('activo')
        if campos_permitidos:
            comentario.save(update_fields=campos_permitidos)
            messages.success(request, 'Comentario actualizado.')
        return redirect('blog:mod_comentarios')
    return redirect('blog:mod_comentarios')

@permission_required('blog.change_comentario', raise_exception=True)
def mod_mover_comentario(request, pk):
    """Mueve un comentario a otra noticia."""
    comentario = get_object_or_404(Comentario, pk=pk)
    if request.method == 'POST':
        noticia_destino_id = request.POST.get('noticia_destino')
        try:
            noticia_destino = Noticia.objects.get(pk=noticia_destino_id)
        except Noticia.DoesNotExist:
            messages.error(request, 'La noticia destino no existe.')
            return redirect('blog:mod_comentarios')
        if noticia_destino.id == comentario.noticia.id:
            messages.error(request, 'El comentario ya pertenece a esa noticia.')
            return redirect('blog:mod_comentarios')
        if not noticia_destino.permitir_comentarios:
            messages.error(request, 'El hilo de destino está cerrado.')
            return redirect('blog:mod_comentarios')
        noticia_origen_id = comentario.noticia.id
        comentario.noticia = noticia_destino
        comentario.nota_moderacion = (
            comentario.nota_moderacion +
            f'\n[Movido desde noticia #{noticia_origen_id} el {timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")} por {request.user.username}]'
        ).strip()
        comentario.save(update_fields=['noticia', 'nota_moderacion'])
        messages.success(request, f'Comentario movido a "{noticia_destino.titulo}".')
    return redirect('blog:mod_comentarios')

@permission_required('blog.change_reportecomentario', raise_exception=True)
def mod_bandeja_reportes(request):
    """Bandeja de reportes pendientes."""
    reportes = ReporteComentario.objects.filter(
        estado='pendiente'
    ).select_related('comentario', 'reportado_por', 'comentario__noticia', 'comentario__autor').order_by('-fecha_reporte')
    paginator = Paginator(reportes, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/moderadores/reportes.html', {'page_obj': page_obj})

@permission_required('blog.change_reportecomentario', raise_exception=True)
def mod_resolver_reporte(request, pk):
    """Resuelve un reporte como retirado o mantenido."""
    reporte = get_object_or_404(ReporteComentario, pk=pk)
    if request.method == 'POST':
        estado = request.POST.get('estado')
        if estado not in ['resuelto_retirado', 'resuelto_mantenido']:
            messages.error(request, 'Estado de resolución inválido.')
            return redirect('blog:mod_reportes')
        reporte.estado = estado
        reporte.resuelto_por = request.user
        reporte.fecha_resolucion = timezone.now()
        reporte.save(update_fields=['estado', 'resuelto_por', 'fecha_resolucion'])
        if estado == 'resuelto_retirado':
            comentario = reporte.comentario
            comentario.activo = False
            comentario.save(update_fields=['activo'])
        messages.success(request, f'Reporte resuelto como "{reporte.get_estado_display()}".')
    return redirect('blog:mod_reportes')

@permission_required('blog.add_sancionusuario', raise_exception=True)
def mod_sancionar_usuario(request, user_id):
    """Aplica una sanción a un usuario."""
    from django.contrib.auth.models import User as AuthUser
    usuario = get_object_or_404(AuthUser, pk=user_id)
    if request.method == 'POST':
        tipo = request.POST.get('tipo_sancion')
        motivo = request.POST.get('motivo', '')
        fecha_fin_str = request.POST.get('fecha_fin', '')
        if tipo not in ['silencio', 'baneo_temporal', 'baneo_permanente']:
            messages.error(request, 'Tipo de sanción inválido.')
            return redirect('blog:panel_moderadores')
        fecha_fin = None
        if fecha_fin_str:
            from django.utils.dateparse import parse_datetime
            fecha_fin = parse_datetime(fecha_fin_str)
        SancionUsuario.objects.create(
            usuario=usuario,
            tipo_sancion=tipo,
            motivo=motivo,
            fecha_fin=fecha_fin,
            aplicada_por=request.user,
        )
        messages.success(request, f'Sanción aplicada a {usuario.username}.')
        return redirect('blog:panel_moderadores')
    return render(request, 'blog/moderadores/sancionar.html', {'usuario': usuario})

@permission_required('blog.change_sancionusuario', raise_exception=True)
def mod_levantar_sancion(request, sancion_id):
    """Levanta una sanción existente."""
    sancion = get_object_or_404(SancionUsuario, pk=sancion_id)
    if request.method == 'POST':
        sancion.activa = False
        sancion.levantada_por = request.user
        sancion.fecha_levantamiento = timezone.now()
        sancion.save(update_fields=['activa', 'levantada_por', 'fecha_levantamiento'])
        messages.success(request, f'Sanción levantada para {sancion.usuario.username}.')
    return redirect('blog:panel_moderadores')

@permission_required('blog.change_noticia', raise_exception=True)
def mod_toggle_comentarios(request, pk):
    """Activa o desactiva la caja de comentarios de una noticia."""
    noticia = get_object_or_404(Noticia, pk=pk)
    if request.method == 'POST':
        # Solo permitir el campo permitir_comentarios
        campos_extra = set(request.POST.keys()) - {'csrfmiddlewaretoken', 'permitir_comentarios'}
        if campos_extra:
            messages.error(request, 'No tienes permisos para modificar esos campos.')
            return HttpResponseForbidden('Solo se puede modificar permitir_comentarios.')
        nuevo_valor = request.POST.get('permitir_comentarios', 'false') == 'true'
        noticia.permitir_comentarios = nuevo_valor
        noticia.save(update_fields=['permitir_comentarios'])
        estado = 'abierto' if nuevo_valor else 'cerrado'
        messages.success(request, f'Hilo de comentarios {estado} para "{noticia.titulo}".')
    return redirect('blog:detalle_noticia', slug=noticia.slug)

@permission_required('blog.add_comentariofijado', raise_exception=True)
def mod_fijar_comentario(request, pk):
    """Fija un comentario al inicio del hilo."""
    comentario = get_object_or_404(Comentario, pk=pk)
    if request.method == 'POST':
        if not comentario.activo:
            messages.error(request, 'No se puede fijar un comentario oculto.')
            return redirect('blog:mod_comentarios')
        if ComentarioFijado.objects.filter(comentario=comentario).exists():
            messages.error(request, 'Este comentario ya está fijado.')
            return redirect('blog:mod_comentarios')
        orden_max = ComentarioFijado.objects.filter(noticia=comentario.noticia).count()
        ComentarioFijado.objects.create(
            comentario=comentario,
            noticia=comentario.noticia,
            fijado_por=request.user,
            orden=orden_max,
        )
        messages.success(request, 'Comentario fijado.')
    return redirect('blog:mod_comentarios')

@permission_required('blog.delete_comentariofijado', raise_exception=True)
def mod_desfijar_comentario(request, pk):
    """Desfija un comentario."""
    comentario = get_object_or_404(Comentario, pk=pk)
    if request.method == 'POST':
        ComentarioFijado.objects.filter(comentario=comentario).delete()
        messages.success(request, 'Comentario desfijado.')
    return redirect('blog:mod_comentarios')

@permission_required('blog.view_metricacomunidad', raise_exception=True)
def mod_metricas(request):
    """Vista de métricas de comunidad (solo lectura)."""
    metricas = MetricaComunidad.objects.all().order_by('-fecha')
    paginator = Paginator(metricas, 30)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog/moderadores/metricas.html', {'page_obj': page_obj})
