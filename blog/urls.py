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
]