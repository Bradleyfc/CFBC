from django.urls import path
from . import views

app_name = "evaluaciones"

urlpatterns = [
    # Vistas del Profesor
    path("curso/<int:curso_id>/", views.EvaluacionListView.as_view(), name="lista_curso"),
    path("curso/<int:curso_id>/crear/", views.evaluacion_create, name="crear"),
    path("<int:pk>/editar/", views.evaluacion_update, name="editar"),
    path("<int:pk>/eliminar/", views.EvaluacionDeleteView.as_view(), name="eliminar"),
    path("<int:pk>/intentos/", views.IntentoListView.as_view(), name="intentos_lista"),
    path("intento/<int:pk>/calificar/", views.calificar_intento, name="calificar_intento"),
    # Vistas del Estudiante
    path('mis-evaluaciones/<int:curso_id>/', views.EvaluacionEstudianteListView.as_view(), name='mis_evaluaciones'),
    path('<int:pk>/responder/', views.responder_evaluacion, name='responder'),
    path('intento/<int:pk>/resultado/', views.resultado_evaluacion, name='resultado'),
    # Vistas de la Secretaria
    path('secretaria/', views.SecretariaEvaluacionListView.as_view(), name='secretaria_lista'),
    path('secretaria/crear/', views.secretaria_evaluacion_create, name='secretaria_crear'),
    path('secretaria/<int:eval_id>/intentos/', views.SecretariaIntentoListView.as_view(), name='secretaria_intentos_lista'),
    path('secretaria/intento/<int:pk>/calificar/', views.secretaria_calificar_intento, name='secretaria_calificar_intento'),
]
