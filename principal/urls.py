from django.urls import path
from . import views
from .views_registro_respuestas import (
    RegistroRespuestasGeneralView, RegistroRespuestasCursoView, 
    RegistroRespuestasEstudianteView, exportar_respuestas_excel
)

app_name = 'principal'

urlpatterns = [
    path('usuarios-registrados/', views.UsuariosRegistradosView.as_view(), name='usuarios_registrados'),
    path('test-usuarios/', views.UsuariosRegistradosView.as_view(), name='test_usuarios'),
    path('admin/principal/cursoacademico/<int:pk>/detail/', views.CursoAcademicoDetailView.as_view(), name='principal_cursoacademico_detail'),
    path('', views.HomeView.as_view(), name='home'),
    path('listado_cursos/', views.ListadoCursosView.as_view(), name='listado_cursos'),
    path('login_redirect/', views.LoginRedirectView.as_view(), name='login_redirect'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('create_course/', views.CourseCreateView.as_view(), name='create_course'),
    path('update_course/<int:pk>/', views.CourseUpdateView.as_view(), name='update_course'),
    path('inscribirse_curso/<int:course_id>/', views.inscribirse_curso, name='inscribirse_curso'),
    path('eliminar_curso/<int:course_id>/', views.eliminar_curso, name='eliminar_curso'),
    path('student_list_notas/', views.StudentListNotasView.as_view(), name='student_list_notas'),
    path('add_nota/<int:matricula_id>/', views.AddNotaView.as_view(), name='add_nota'),
    path('historico_alumno/<int:student_id>/', views.historico_alumno, name='historico_alumno'),
    path('logout/', views.logout_view, name='logout_view'),
    path('registro/', views.registro, name='registro'),
    path('cursos/', views.CoursesView.as_view(), name='cursos'),
    path('cursos/create/', views.CourseCreateView.as_view(), name='crear_cursos'),
    path('cursos/inscribirse/<int:curso_id>/', views.inscribirse_curso, name='inscribirse_curso'),
    path('cursos/editar/<int:pk>/', views.CourseUpdateView.as_view(), name='editar_curso'),
    path('cursos/eliminar/<int:curso_id>/', views.eliminar_curso, name='eliminar_curso'),
    path('cursos/<int:course_id>/', views.StudentListNotasView.as_view(), name='student_list_notas_by_course'),
    path('matricula/<int:matricula_id>/add_nota/', views.AddNotaView.as_view(), name='add_nota'),
    path('cursos/<int:course_id>/asistencias/', views.AsistenciaView.as_view(), name='asistencias'),
    path('student/<int:student_id>/course/<int:course_id>/attendances/', views.StudentCourseAttendanceView.as_view(), name='student_course_attendances'),
    path('student/<int:student_id>/course/<int:course_id>/notes/', views.StudentCourseNotesView.as_view(), name='student_course_notes'),
    path('matriculas/', views.MatriculasListView.as_view(), name='matriculas'),
    path('calificaciones/', views.CalificacionesListView.as_view(), name='calificaciones'),
    path('asistencias_list/', views.AsistenciasListView.as_view(), name='asistencias_list'),
    path('cursos/<int:course_id>/addasistencias/', views.AddAsistenciaView.as_view(),name='add_asistencias' ),
    path('asistencias/eliminar/<int:asistencia_id>/', views.eliminar_asistencia, name='eliminar_asistencia'),
    path('asistencias/<int:course_id>/undo/', views.undo_last_asistencia, name='undo_last_asistencia'),
    path('matriculas/export-pdf/', views.export_matriculas_pdf, name='export_matriculas_pdf'),
    path('matriculas/export-excel/', views.export_matriculas_excel, name='export_matriculas_excel'),
    
    path('export-usuarios-excel/', views.export_usuarios_excel, name='export_usuarios_excel'),
    path('verify_email/', views.verify_email, name='verify_email'),
    
    # Rutas para el sistema de formularios de aplicación a cursos
    # Rutas para secretaria
    path('formularios/', views.FormularioAplicacionListView.as_view(), name='formulario_list'),
    path('formularios/crear/', views.FormularioAplicacionCreateView.as_view(), name='formulario_create'),
    path('formularios/<int:pk>/editar/', views.FormularioAplicacionUpdateView.as_view(), name='formulario_update'),
    path('formularios/<int:pk>/preguntas/', views.FormularioPreguntasView.as_view(), name='formulario_preguntas'),
    path('formularios/<int:pk>/eliminar/', views.eliminar_formulario, name='eliminar_formulario'),
    path('preguntas/<int:pk>/opciones/', views.PreguntaOpcionesView.as_view(), name='pregunta_opciones'),
    path('formularios/<int:formulario_id>/guardar-pregunta-y-redirigir/', views.guardar_pregunta_y_redirigir, name='guardar_pregunta_y_redirigir'),
    
    # Rutas para estudiantes
    path('cursos/aplicar/<int:curso_id>/', views.aplicar_curso, name='aplicar_curso'),
    path('cursos/solicitud-enviada/<int:curso_id>/', views.solicitud_enviada, name='solicitud_enviada'),
    
    # Rutas para profesores
    path('solicitudes/', views.SolicitudesInscripcionListView.as_view(), name='solicitudes_list'),
    path('solicitudes/<int:pk>/', views.SolicitudInscripcionDetailView.as_view(), name='solicitud_detail'),
    path('solicitudes/<int:pk>/aprobar/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('solicitudes/<int:pk>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
    
    # Rutas para recuperación de contraseña
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/resend-code/', views.password_reset_resend_code, name='password_reset_resend_code'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Rutas para registro
    path('registro/resend-code/', views.registro_resend_code, name='registro_resend_code'),
    
    # Rutas para registro de respuestas de formularios
    path('registro-respuestas/', RegistroRespuestasGeneralView.as_view(), name='registro_respuestas_general'),
    path('registro-respuestas/curso/<int:pk>/', RegistroRespuestasCursoView.as_view(), name='registro_respuestas_curso'),
    path('registro-respuestas/estudiante/<int:pk>/', RegistroRespuestasEstudianteView.as_view(), name='registro_respuestas_estudiante'),
    path('registro-respuestas/exportar-excel/', exportar_respuestas_excel, name='exportar_respuestas_excel'),
    path('registro-respuestas/exportar-excel/<int:curso_id>/', exportar_respuestas_excel, name='exportar_respuestas_excel_curso'),
]