from django.contrib import admin
from .models import (
    HistoricalArea,
    HistoricalCourseCategory,
    HistoricalCourseInformationAdminTeachers,
    HistoricalCourseInformation,
    HistoricalEnrollmentApplication,
    HistoricalEnrollmentPay,
    HistoricalAccountNumber,
    HistoricalEnrollment,
    HistoricalSubjectInformation,
    HistoricalEdition,
    HistoricalApplication,
    HistoricalClass,
    HistoricalClassStudentView,
)


@admin.register(HistoricalArea)
class HistoricalAreaAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalArea.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de áreas de docencia. Incluye búsqueda por nombre y código,
    y visualización de campos clave en la lista.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - nombre: Nombre descriptivo del área de docencia
    # - codigo: Código único que identifica el área
    # - descripcion: Descripción detallada del área
    list_display = ['id', 'nombre', 'codigo', 'descripcion']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar áreas por nombre, código o descripción
    search_fields = ['nombre', 'codigo', 'descripcion']

    # list_filter: Filtros laterales en la interfaz del admin
    # No hay foreign keys en HistoricalArea, por lo que no se requieren filtros
    list_filter = []

    # raw_id_fields: Campos de foreign key que usan widget de búsqueda
    # No hay foreign keys en HistoricalArea
    raw_id_fields = []


@admin.register(HistoricalCourseCategory)
class HistoricalCourseCategoryAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalCourseCategory.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de categorías de cursos. Incluye filtros por relación jerárquica
    (parent), estado de servicio, registro y visibilidad. Usa raw_id_fields
    para la relación self-referential parent.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - nombre: Nombre de la categoría de curso
    # - codigo: Código único de la categoría
    # - parent: Categoría padre (relación jerárquica self-referential)
    # - es_servicio: Indica si la categoría es de tipo servicio
    # - registro_abierto: Indica si el registro está abierto para esta categoría
    # - visible: Indica si la categoría es visible en el sistema
    list_display = ['id', 'nombre', 'codigo', 'parent', 'es_servicio', 'registro_abierto', 'visible']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por nombre, código, descripción o slug de la categoría
    search_fields = ['nombre', 'codigo', 'descripcion', 'slug']

    # list_filter: Filtros laterales en la interfaz del admin
    # - parent: Filtrar por categoría padre
    # - es_servicio: Filtrar por tipo de servicio
    # - registro_abierto: Filtrar por estado de registro
    # - visible: Filtrar por visibilidad
    # - tiene_solicitud: Filtrar por si tiene solicitudes asociadas
    list_filter = ['parent', 'es_servicio', 'registro_abierto', 'visible', 'tiene_solicitud']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - parent: Relación self-referential que puede tener muchos registros
    raw_id_fields = ['parent']


@admin.register(HistoricalCourseInformationAdminTeachers)
class HistoricalCourseInformationAdminTeachersAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalCourseInformationAdminTeachers.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de la relación many-to-many entre cursos y profesores administradores.
    Usa raw_id_fields para curso y profesor debido al potencial alto volumen de registros.
    Permite búsqueda por nombre de curso y datos del profesor.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - curso: Curso al que está asociado el profesor administrador
    # - profesor: Usuario que actúa como profesor administrador del curso
    list_display = ['id', 'curso', 'profesor']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por nombre/código del curso o username/email del profesor
    # Usa __ para acceder a campos de modelos relacionados
    search_fields = ['curso__nombre', 'curso__codigo', 'profesor__username', 'profesor__email']

    # list_filter: Filtros laterales en la interfaz del admin
    # - curso: Filtrar por curso específico
    # - profesor: Filtrar por profesor específico
    list_filter = ['curso', 'profesor']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - curso: Puede haber muchos cursos en el sistema
    # - profesor: Puede haber muchos profesores en el sistema
    raw_id_fields = ['curso', 'profesor']


@admin.register(HistoricalCourseInformation)
class HistoricalCourseInformationAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalCourseInformation.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de información de cursos. Incluye filtros por área y categoría,
    y usa raw_id_fields para foreign keys con muchos registros potenciales.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - nombre: Nombre del curso
    # - codigo: Código único del curso
    # - area: Área de docencia a la que pertenece el curso
    # - categoria: Categoría del curso
    list_display = ['id', 'nombre', 'codigo', 'area', 'categoria']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar cursos por nombre, código o descripción
    search_fields = ['nombre', 'codigo', 'descripcion']

    # list_filter: Filtros laterales en la interfaz del admin
    # - area: Filtrar por área de docencia
    # - categoria: Filtrar por categoría de curso
    list_filter = ['area', 'categoria']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - area: Puede haber muchas áreas en el sistema
    # - categoria: Puede haber muchas categorías en el sistema
    raw_id_fields = ['area', 'categoria']


@admin.register(HistoricalEnrollmentApplication)
class HistoricalEnrollmentApplicationAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalEnrollmentApplication.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de solicitudes de inscripción. Incluye filtros por curso, usuario,
    estado y fecha. Permite búsqueda por datos del usuario y del curso.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - usuario: Usuario que realizó la solicitud de inscripción
    # - curso: Curso al que se solicita inscripción
    # - fecha_solicitud: Fecha en que se realizó la solicitud
    # - estado: Estado actual de la solicitud (pendiente, aprobada, rechazada, etc.)
    list_display = ['id', 'usuario', 'curso', 'fecha_solicitud', 'estado']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por username/email del usuario, nombre/código del curso, o estado
    search_fields = ['usuario__username', 'usuario__email', 'curso__nombre', 'curso__codigo', 'estado']

    # list_filter: Filtros laterales en la interfaz del admin
    # - curso: Filtrar por curso específico
    # - usuario: Filtrar por usuario específico
    # - estado: Filtrar por estado de la solicitud
    # - fecha_solicitud: Filtrar por fecha de solicitud
    list_filter = ['curso', 'usuario', 'estado', 'fecha_solicitud']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - curso: Puede haber muchos cursos en el sistema
    # - usuario: Puede haber muchos usuarios en el sistema
    raw_id_fields = ['curso', 'usuario']


@admin.register(HistoricalEnrollmentPay)
class HistoricalEnrollmentPayAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalEnrollmentPay.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de pagos de inscripción. Incluye filtros por solicitud, cuenta,
    estado de aceptación y fecha. Permite búsqueda por usuario, método de pago
    y número de cuenta.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - solicitud: Solicitud de inscripción asociada al pago
    # - monto: Monto del pago realizado
    # - fecha_pago: Fecha en que se realizó el pago
    # - metodo_pago: Método utilizado para el pago (transferencia, tarjeta, etc.)
    # - aceptado: Indica si el pago fue aceptado/verificado
    # - cuenta: Cuenta bancaria asociada al pago
    list_display = ['id', 'solicitud', 'monto', 'fecha_pago', 'metodo_pago', 'aceptado', 'cuenta']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por username del usuario de la solicitud, método de pago, o número de cuenta
    search_fields = ['solicitud__usuario__username', 'metodo_pago', 'cuenta__numero_cuenta']

    # list_filter: Filtros laterales en la interfaz del admin
    # - solicitud: Filtrar por solicitud específica
    # - cuenta: Filtrar por cuenta bancaria
    # - aceptado: Filtrar por estado de aceptación del pago
    # - fecha_pago: Filtrar por fecha de pago
    list_filter = ['solicitud', 'cuenta', 'aceptado', 'fecha_pago']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - solicitud: Puede haber muchas solicitudes en el sistema
    # - cuenta: Puede haber muchas cuentas bancarias en el sistema
    raw_id_fields = ['solicitud', 'cuenta']


@admin.register(HistoricalAccountNumber)
class HistoricalAccountNumberAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalAccountNumber.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de números de cuenta bancaria. Incluye filtros por usuario y banco,
    y permite búsqueda por número de cuenta y datos del usuario.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - numero_cuenta: Número de la cuenta bancaria
    # - banco: Nombre del banco
    # - usuario: Usuario propietario de la cuenta
    list_display = ['id', 'numero_cuenta', 'banco', 'usuario']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por número de cuenta, banco, username o email del usuario
    search_fields = ['numero_cuenta', 'banco', 'usuario__username', 'usuario__email']

    # list_filter: Filtros laterales en la interfaz del admin
    # - usuario: Filtrar por usuario propietario
    # - banco: Filtrar por banco
    list_filter = ['usuario', 'banco']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - usuario: Puede haber muchos usuarios en el sistema
    raw_id_fields = ['usuario']


@admin.register(HistoricalEnrollment)
class HistoricalEnrollmentAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalEnrollment.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de inscripciones. Incluye filtros por curso, usuario, edición,
    estado y fecha. Muestra información clave como notas finales y permite
    búsqueda por datos del usuario y del curso.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - usuario: Usuario inscrito en el curso
    # - curso: Curso en el que está inscrito
    # - edicion: Edición específica del curso
    # - fecha_inscripcion: Fecha en que se realizó la inscripción
    # - estado: Estado de la inscripción (activo, completado, cancelado, etc.)
    # - nota_final: Nota final obtenida en el curso
    list_display = ['id', 'usuario', 'curso', 'edicion', 'fecha_inscripcion', 'estado', 'nota_final']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por username/email del usuario, nombre/código del curso, estado o slug
    search_fields = ['usuario__username', 'usuario__email', 'curso__nombre', 'curso__codigo', 'estado', 'slug']

    # list_filter: Filtros laterales en la interfaz del admin
    # - curso: Filtrar por curso específico
    # - usuario: Filtrar por usuario específico
    # - edicion: Filtrar por edición del curso
    # - estado: Filtrar por estado de la inscripción
    # - fecha_inscripcion: Filtrar por fecha de inscripción
    list_filter = ['curso', 'usuario', 'edicion', 'estado', 'fecha_inscripcion']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - curso: Puede haber muchos cursos en el sistema
    # - usuario: Puede haber muchos usuarios en el sistema
    # - edicion: Puede haber muchas ediciones en el sistema
    raw_id_fields = ['curso', 'usuario', 'edicion']


@admin.register(HistoricalSubjectInformation)
class HistoricalSubjectInformationAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalSubjectInformation.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de información de asignaturas. Incluye filtro por curso y
    permite búsqueda por nombre, código y curso asociado.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - nombre: Nombre de la asignatura
    # - codigo: Código único de la asignatura
    # - curso: Curso al que pertenece la asignatura
    list_display = ['id', 'nombre', 'codigo', 'curso']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por nombre, código o descripción de la asignatura, o nombre del curso
    search_fields = ['nombre', 'codigo', 'descripcion', 'curso__nombre']

    # list_filter: Filtros laterales en la interfaz del admin
    # - curso: Filtrar por curso específico
    list_filter = ['curso']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - curso: Puede haber muchos cursos en el sistema
    raw_id_fields = ['curso']


@admin.register(HistoricalEdition)
class HistoricalEditionAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalEdition.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de ediciones de cursos. Incluye filtros por curso, instructor
    y fechas. Permite búsqueda por nombre de edición, curso e instructor.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - nombre: Nombre de la edición del curso
    # - curso: Curso al que pertenece esta edición
    # - instructor: Instructor asignado a esta edición
    # - fecha_inicio: Fecha de inicio de la edición
    # - fecha_fin: Fecha de finalización de la edición
    list_display = ['id', 'nombre', 'curso', 'instructor', 'fecha_inicio', 'fecha_fin']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por nombre de edición, nombre/código del curso, o username del instructor
    search_fields = ['nombre', 'curso__nombre', 'curso__codigo', 'instructor__username']

    # list_filter: Filtros laterales en la interfaz del admin
    # - curso: Filtrar por curso específico
    # - instructor: Filtrar por instructor específico
    # - fecha_inicio: Filtrar por fecha de inicio
    # - fecha_fin: Filtrar por fecha de finalización
    list_filter = ['curso', 'instructor', 'fecha_inicio', 'fecha_fin']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - curso: Puede haber muchos cursos en el sistema
    # - instructor: Puede haber muchos instructores en el sistema
    raw_id_fields = ['curso', 'instructor']


@admin.register(HistoricalApplication)
class HistoricalApplicationAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalApplication.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de aplicaciones. Incluye filtros por curso, edición, usuario,
    estado y fecha. Muestra información clave como notas finales y permite
    búsqueda por datos del usuario y del curso.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - usuario: Usuario que realizó la aplicación
    # - curso: Curso al que se aplica
    # - edicion: Edición específica del curso
    # - fecha_solicitud: Fecha en que se realizó la aplicación
    # - estado: Estado actual de la aplicación
    # - nota_final: Nota final obtenida
    list_display = ['id', 'usuario', 'curso', 'edicion', 'fecha_solicitud', 'estado', 'nota_final']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por username/email del usuario, nombre/código del curso, o estado
    search_fields = ['usuario__username', 'usuario__email', 'curso__nombre', 'curso__codigo', 'estado']

    # list_filter: Filtros laterales en la interfaz del admin
    # - curso: Filtrar por curso específico
    # - edicion: Filtrar por edición del curso
    # - usuario: Filtrar por usuario específico
    # - estado: Filtrar por estado de la aplicación
    # - fecha_solicitud: Filtrar por fecha de solicitud
    list_filter = ['curso', 'edicion', 'usuario', 'estado', 'fecha_solicitud']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - curso: Puede haber muchos cursos en el sistema
    # - edicion: Puede haber muchas ediciones en el sistema
    # - usuario: Puede haber muchos usuarios en el sistema
    raw_id_fields = ['curso', 'edicion', 'usuario']


@admin.register(HistoricalClass)
class HistoricalClassAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalClass.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de clases. Incluye filtros por asignatura y fechas,
    y permite búsqueda por nombre, slug y contenido de la clase.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - name: Nombre de la clase
    # - subject: Asignatura a la que pertenece la clase
    # - uploaddate: Fecha de carga de la clase
    # - datepub: Fecha de publicación de la clase
    # - dateend: Fecha de finalización de la clase
    list_display = ['id', 'name', 'subject', 'uploaddate', 'datepub', 'dateend']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por nombre, slug, contenido de la clase o nombre de la asignatura
    search_fields = ['name', 'slug', 'classbody', 'subject__nombre']

    # list_filter: Filtros laterales en la interfaz del admin
    # - subject: Filtrar por asignatura específica
    # - uploaddate: Filtrar por fecha de carga
    # - datepub: Filtrar por fecha de publicación
    # - dateend: Filtrar por fecha de finalización
    list_filter = ['subject', 'uploaddate', 'datepub', 'dateend']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - subject: Puede haber muchas asignaturas en el sistema
    raw_id_fields = ['subject']


@admin.register(HistoricalClassStudentView)
class HistoricalClassStudentViewAdmin(admin.ModelAdmin):
    """
    Configuración de Django Admin para HistoricalClassStudentView.

    Proporciona interfaz administrativa para visualizar y gestionar registros
    históricos de la relación many-to-many entre clases y aplicaciones de estudiantes.
    Usa raw_id_fields para class_field y application debido al potencial alto volumen de registros.
    Permite búsqueda por nombre de clase y datos del estudiante.
    """

    # list_display: Campos mostrados en la vista de lista del admin
    # - id: Identificador único del registro histórico
    # - class_field: Clase asociada
    # - application: Aplicación del estudiante asociada
    list_display = ['id', 'class_field', 'application']

    # search_fields: Campos habilitados para búsqueda de texto
    # Permite buscar por nombre/slug de la clase o username/email del estudiante de la aplicación
    # Usa __ para acceder a campos de modelos relacionados
    search_fields = ['class_field__name', 'class_field__slug', 'application__usuario__username', 'application__usuario__email']

    # list_filter: Filtros laterales en la interfaz del admin
    # - class_field: Filtrar por clase específica
    # - application: Filtrar por aplicación específica
    list_filter = ['class_field', 'application']

    # raw_id_fields: Usa widget de búsqueda para foreign keys con muchos registros
    # - class_field: Puede haber muchas clases en el sistema
    # - application: Puede haber muchas aplicaciones en el sistema
    raw_id_fields = ['class_field', 'application']
