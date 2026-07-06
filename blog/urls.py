from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # URLs públicas
    path('', views.lista_noticias, name='lista_noticias'),
    path('noticia/<slug:slug>/', views.detalle_noticia, name='detalle_noticia'),
    path('noticia/<slug:slug>/comentar/', views.agregar_comentario, name='agregar_comentario'),
    path('categoria/<slug:slug>/', views.noticias_por_categoria, name='categoria_noticias'),
    
    # URLs para editor
    path('editores/', views.panel_editores, name='panel_editores'),
    path('editores/mis-noticias/', views.mis_noticias, name='mis_noticias'),
    path('editores/crear/', views.crear_noticia, name='crear_noticia'),
    path('editores/editar/<int:pk>/', views.editar_noticia, name='editar_noticia'),
    path('editores/eliminar/<int:pk>/', views.eliminar_noticia, name='eliminar_noticia'),
    path('editores/comentarios/<int:pk>/', views.gestionar_comentarios, name='gestionar_comentarios'),
    path('editores/comentarios/eliminar/<int:pk>/', views.eliminar_comentario, name='eliminar_comentario'),
    path('editores/categorias/', views.gestionar_categorias, name='gestionar_categorias'),
    path('editores/categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('editores/bandeja-revision/', views.bandeja_revision, name='bandeja_revision'),
    path('editores/revisar/<int:pk>/', views.revisar_noticia, name='revisar_noticia'),
    path('editores/todas-las-noticias/', views.todas_las_noticias, name='todas_las_noticias'),
    path('editores/todas-las-noticias/editar/<int:pk>/', views.editar_noticia_editor, name='editar_noticia_editor'),
    path('editores/todas-las-noticias/eliminar/<int:pk>/', views.eliminar_noticia_editor, name='eliminar_noticia_editor'),

    # URLs para autores
    path('autores/', views.panel_autores, name='panel_autores'),
    path('autores/mis-noticias/', views.mis_noticias_autor, name='mis_noticias_autor'),
    path('autores/crear/', views.crear_noticia_autor, name='crear_noticia_autor'),
    path('autores/editar/<int:pk>/', views.editar_noticia_autor, name='editar_noticia_autor'),
    path('autores/eliminar/<int:pk>/', views.eliminar_noticia_autor, name='eliminar_noticia_autor'),
    path('autores/enviar-revision/<int:pk>/', views.enviar_revision, name='enviar_revision'),
    path('autores/borradores/', views.borradores_autor, name='borradores_autor'),

    # URLs para moderadores
    path('moderadores/', views.panel_moderadores, name='panel_moderadores'),
    path('moderadores/comentarios/', views.mod_gestionar_comentarios, name='mod_comentarios'),
    path('moderadores/comentarios/<int:pk>/editar/', views.mod_editar_comentario, name='mod_editar_comentario'),
    path('moderadores/comentarios/<int:pk>/mover/', views.mod_mover_comentario, name='mod_mover_comentario'),
    path('moderadores/comentarios/<int:pk>/fijar/', views.mod_fijar_comentario, name='mod_fijar'),
    path('moderadores/comentarios/<int:pk>/desfijar/', views.mod_desfijar_comentario, name='mod_desfijar'),
    path('moderadores/reportes/', views.mod_bandeja_reportes, name='mod_reportes'),
    path('moderadores/reportes/<int:pk>/resolver/', views.mod_resolver_reporte, name='mod_resolver_reporte'),
    path('moderadores/sanciones/crear/<int:user_id>/', views.mod_sancionar_usuario, name='mod_sancionar'),
    path('moderadores/sanciones/levantar/<int:sancion_id>/', views.mod_levantar_sancion, name='mod_levantar'),
    path('moderadores/noticias/<int:pk>/toggle-comentarios/', views.mod_toggle_comentarios, name='mod_toggle_comentarios'),
    path('moderadores/metricas/', views.mod_metricas, name='mod_metricas'),
]