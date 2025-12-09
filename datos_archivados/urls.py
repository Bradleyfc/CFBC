from django.urls import path
from . import views

app_name = 'datos_archivados'

urlpatterns = [
    # Dashboard principal
    path('', views.DashboardArchivadosView.as_view(), name='dashboard'),
    
    # Datos archivados dinámicos
    path('tablas/', views.TablasArchivadosListView.as_view(), name='tablas_list'),
    path('tablas/eliminar/', views.eliminar_tablas, name='eliminar_tablas'),
    path('combinar-datos/', views.combinar_datos_archivados, name='combinar_datos'),
    path('tablas/<str:tabla>/', views.DatosArchivadosListView.as_view(), name='datos_list'),
    path('tablas/<str:tabla>/excel/', views.exportar_tabla_excel, name='exportar_tabla_excel'),
    path('datos/<int:pk>/', views.detalle_dato_archivado, name='dato_detail'),
    path('datos/<int:pk>/excel/', views.exportar_excel, name='exportar_excel'),
    
    # Migración automática
    path('migracion/configurar/', views.configurar_migracion_view, name='configurar_migracion'),
    path('migracion/estado/', views.estado_migracion_ajax, name='estado_migracion'),
    
    # Usuarios archivados - DESHABILITADO (ya no es necesario con la nueva implementación de combinación)
    # path('reclamar-usuario/', views.reclamar_usuario_archivado, name='reclamar_usuario'),
    # path('verificar-codigo-reclamacion-tradicional/', views.verificar_codigo_reclamacion_tradicional, name='verificar_codigo_reclamacion_tradicional'),
    # path('reenviar-codigo-reclamacion-tradicional/', views.reenviar_codigo_reclamacion_tradicional, name='reenviar_codigo_reclamacion_tradicional'),
    # path('iniciar-reclamacion/<int:dato_id>/', views.iniciar_reclamacion_usuario, name='iniciar_reclamacion_usuario'),
    # path('verificar-codigo-reclamacion/', views.verificar_codigo_reclamacion, name='verificar_codigo_reclamacion'),
    # path('reenviar-codigo-reclamacion/', views.reenviar_codigo_reclamacion, name='reenviar_codigo_reclamacion'),
    # path('reclamar-usuario-dinamico/<int:dato_id>/', views.reclamar_usuario_dinamico, name='reclamar_usuario_dinamico'),
    # path('buscar-usuario/', views.buscar_usuario_archivado, name='buscar_usuario'),
    
    # Búsqueda AJAX
    path('buscar-ajax/', views.buscar_datos_ajax, name='buscar_datos_ajax'),
    path('tablas/<str:tabla>/buscar-ajax/', views.buscar_en_tabla_ajax, name='buscar_en_tabla_ajax'),
    
    # Debug
    path('debug/', views.debug_permisos, name='debug_permisos'),
]