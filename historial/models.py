from django.db import models
from django.contrib.auth.models import User


class HistoricalArea(models.Model):
    """
    Modelo histórico para Docencia_area.

    Almacena registros históricos de áreas de docencia cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Replica exactamente la estructura de Docencia_area con campos adicionales
    de auditoría para rastrear el origen de los datos.

    Campos de auditoría:
        id_original: ID original del registro en la tabla de origen
        tabla_origen: Nombre de la tabla de origen
        fecha_consolidacion: Fecha y hora de consolidación
        dato_archivado: Referencia al registro archivado original

    Campos de datos:
        nombre: Nombre del área de docencia
        descripcion: Descripción detallada del área
        codigo: Código único identificador del área
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_areas'
    )

    # Campos de datos
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    codigo = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'historial_docenciaarea'
        verbose_name = 'Historical Area'
        verbose_name_plural = 'Historical Areas'

    def __str__(self):
        return self.nombre



class HistoricalCourseCategory(models.Model):
    """
    Modelo histórico para Docencia_coursecategory.
    
    Almacena registros históricos de categorías de cursos cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Replica exactamente la estructura de Docencia_coursecategory incluyendo
    relaciones jerárquicas (parent) y todos los campos de configuración.
    
    Campos principales:
        nombre: Nombre de la categoría del curso
        descripcion: Descripción detallada de la categoría
        parent: Relación jerárquica con categoría padre (self-referential)
        codigo: Código único identificador
        precio: Precio del curso
        es_servicio: Indica si es un servicio
        registro_abierto: Indica si el registro está abierto
        visible: Indica si la categoría es visible
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_course_categories'
    )
    
    # Campos de datos
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategories'
    )
    anio_maximo = models.IntegerField(blank=True, null=True)
    anio_minimo = models.IntegerField(blank=True, null=True)
    capacidad = models.IntegerField(blank=True, null=True)
    codigo = models.CharField(max_length=50, blank=True, null=True)
    comunicado = models.TextField(blank=True, null=True)
    creditos_minimos = models.IntegerField(blank=True, null=True)
    curriculum = models.TextField(blank=True, null=True)
    duracion = models.CharField(max_length=100, blank=True, null=True)
    es_servicio = models.BooleanField()
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_limite = models.DateField(blank=True, null=True)
    imagen = models.CharField(max_length=500, blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    precio_religioso = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    programa = models.TextField(blank=True, null=True)
    registro_abierto = models.BooleanField()
    reglamento = models.TextField(blank=True, null=True)
    requisitos = models.TextField(blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)
    tiene_solicitud = models.BooleanField()
    visible = models.BooleanField()
    visible_comunicado = models.BooleanField()

    class Meta:
        db_table = 'historial_docenciacoursecategory'
        verbose_name = 'Historical Course Category'
        verbose_name_plural = 'Historical Course Categories'

    def __str__(self):
        return self.nombre



class HistoricalCourseInformation(models.Model):
    """
    Modelo histórico para Docencia_courseinformation.
    
    Almacena registros históricos de información de cursos cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Replica exactamente la estructura de Docencia_courseinformation con relaciones
    a áreas y categorías históricas.
    
    Campos:
        nombre: Nombre del curso
        descripcion: Descripción detallada del curso
        codigo: Código único identificador del curso
        area: Foreign key a HistoricalArea
        categoria: Foreign key a HistoricalCourseCategory
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_course_informations'
    )
    
    # Campos de datos
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    codigo = models.CharField(max_length=50, blank=True, null=True)
    area = models.ForeignKey(
        HistoricalArea,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='courses'
    )
    categoria = models.ForeignKey(
        HistoricalCourseCategory,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='courses'
    )

    class Meta:
        db_table = 'historial_docenciacourseinformation'
        verbose_name = 'Historical Course Information'
        verbose_name_plural = 'Historical Course Information'

    def __str__(self):
        return self.nombre


class HistoricalCourseInformationAdminTeachers(models.Model):
    """
    Modelo histórico para Docencia_courseinformation_adminteachers.
    
    Almacena registros históricos de la relación many-to-many entre cursos y
    profesores administradores. Se utiliza cuando se realizan combinaciones de
    tablas en la sección "datos archivados dinámicos" del admin.
    
    Campos:
        curso: Foreign key a HistoricalCourseInformation
        profesor: Foreign key a User (auth_user)
    
    Nota: Mantiene la relación con auth_user sin cambios, como se especifica
    en los requisitos.
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_course_information_admin_teachers'
    )
    
    # Campos de datos
    curso = models.ForeignKey(
        HistoricalCourseInformation,
        on_delete=models.CASCADE,
        related_name='admin_teachers'
    )
    profesor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='administered_courses'
    )

    class Meta:
        db_table = 'historial_docenciacourseinformation_adminteachers'
        verbose_name = 'Historical Course Information Admin Teacher'
        verbose_name_plural = 'Historical Course Information Admin Teachers'
        unique_together = (('curso', 'profesor'),)

    def __str__(self):
        return f"{self.curso.nombre} - {self.profesor.username}"


class HistoricalEnrollmentApplication(models.Model):
    """
    Modelo histórico para Docencia_enrollmentapplication.

    Almacena registros históricos de solicitudes de inscripción cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva la información de solicitudes de estudiantes a cursos.

    Campos:
        fecha_solicitud: Fecha y hora de la solicitud
        estado: Estado actual de la solicitud
        curso: Foreign key a HistoricalCourseInformation
        usuario: Foreign key a User (auth_user)
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_enrollment_applications'
    )

    # Campos de datos
    fecha_solicitud = models.DateTimeField()
    estado = models.CharField(max_length=50, blank=True, null=True)
    curso = models.ForeignKey(
        HistoricalCourseInformation,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='enrollment_applications'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='enrollment_applications'
    )

    class Meta:
        db_table = 'historial_docenciaenrollmentapplication'
        verbose_name = 'Historical Enrollment Application'
        verbose_name_plural = 'Historical Enrollment Applications'

    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Unknown'} - {self.curso.nombre if self.curso else 'Unknown'}"


class HistoricalAccountNumber(models.Model):
    """
    Modelo histórico para Docencia_accountnumber.
    
    Almacena registros históricos de números de cuenta bancaria cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva información de cuentas asociadas a usuarios.
    
    Campos:
        numero_cuenta: Número de cuenta bancaria
        banco: Nombre del banco
        usuario: Foreign key a User (auth_user)
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_account_numbers'
    )
    
    # Campos de datos
    numero_cuenta = models.CharField(max_length=100)
    banco = models.CharField(max_length=255, blank=True, null=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='account_numbers'
    )

    class Meta:
        db_table = 'historial_docenciaaccountnumber'
        verbose_name = 'Historical Account Number'
        verbose_name_plural = 'Historical Account Numbers'

    def __str__(self):
        return f"{self.numero_cuenta} - {self.banco or 'Unknown Bank'}"


class HistoricalEnrollmentPay(models.Model):
    """
    Modelo histórico para Docencia_enrollmentpay.
    
    Almacena registros históricos de pagos de inscripción cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva información de pagos asociados a solicitudes de inscripción.
    
    Campos:
        monto: Monto del pago
        fecha_pago: Fecha y hora del pago
        metodo_pago: Método utilizado para el pago
        solicitud: Foreign key a HistoricalEnrollmentApplication
        aceptado: Indica si el pago fue aceptado
        cuenta: Foreign key a HistoricalAccountNumber
    """
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField()
    metodo_pago = models.CharField(max_length=100, blank=True, null=True)
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_enrollment_pays'
    )
    
    # Campos de datos
    solicitud = models.ForeignKey(
        HistoricalEnrollmentApplication,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='payments'
    )
    aceptado = models.BooleanField()
    cuenta = models.ForeignKey(
        HistoricalAccountNumber,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='payments'
    )

    class Meta:
        db_table = 'historial_docenciaenrollmentpay'
        verbose_name = 'Historical Enrollment Pay'
        verbose_name_plural = 'Historical Enrollment Pays'

    def __str__(self):
        return f"Payment {self.id} - {self.monto}"


class HistoricalSubjectInformation(models.Model):
    """
    Modelo histórico para Docencia_subjectinformation.
    
    Almacena registros históricos de información de asignaturas cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva información de asignaturas que forman parte de cursos.
    
    Campos:
        nombre: Nombre de la asignatura
        descripcion: Descripción detallada de la asignatura
        codigo: Código único identificador
        curso: Foreign key a HistoricalCourseInformation
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_subject_informations'
    )
    
    # Campos de datos
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    codigo = models.CharField(max_length=50, blank=True, null=True)
    curso = models.ForeignKey(
        HistoricalCourseInformation,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subjects'
    )

    class Meta:
        db_table = 'historial_docenciasubjectinformation'
        verbose_name = 'Historical Subject Information'
        verbose_name_plural = 'Historical Subject Information'

    def __str__(self):
        return self.nombre


class HistoricalEdition(models.Model):
    """
    Modelo histórico para Docencia_edition.
    
    Almacena registros históricos de ediciones de cursos cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva información de ediciones específicas de cursos con sus instructores.
    
    Campos:
        nombre: Nombre de la edición
        fecha_inicio: Fecha de inicio de la edición
        fecha_fin: Fecha de finalización de la edición
        curso: Foreign key a HistoricalCourseInformation
        instructor: Foreign key a User (auth_user)
    """
    nombre = models.CharField(max_length=255)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_editions'
    )
    
    # Campos de datos
    curso = models.ForeignKey(
        HistoricalCourseInformation,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='editions'
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='editions_instructed'
    )

    class Meta:
        db_table = 'historial_docenciaedition'
        verbose_name = 'Historical Edition'
        verbose_name_plural = 'Historical Editions'

    def __str__(self):
        return self.nombre


class HistoricalEnrollment(models.Model):
    """
    Modelo histórico para Docencia_enrollment.
    
    Almacena registros históricos de inscripciones cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva información completa de inscripciones de estudiantes incluyendo
    notas y asistencia.
    
    Campos principales:
        fecha_inscripcion: Fecha y hora de la inscripción
        estado: Estado actual de la inscripción
        curso: Foreign key a HistoricalSubjectInformation
        usuario: Foreign key a User (auth_user)
        edicion: Foreign key a HistoricalEdition
        ausencias: Número de ausencias
        intento: Número de intento
        nota_final: Nota final del estudiante
    """
    fecha_inscripcion = models.DateTimeField()
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_enrollments'
    )
    
    # Campos de datos
    estado = models.CharField(max_length=50, blank=True, null=True)
    curso = models.ForeignKey(
        HistoricalSubjectInformation,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='enrollments'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='enrollments'
    )
    edicion = models.ForeignKey(
        HistoricalEdition,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='enrollments'
    )
    ausencias = models.IntegerField()
    intento = models.IntegerField()
    nota_extra = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    nota_final = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    nota_primaria = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    nota_secundaria = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    slug = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'historial_docenciaenrollment'
        verbose_name = 'Historical Enrollment'
        verbose_name_plural = 'Historical Enrollments'

    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Unknown'} - {self.curso.nombre if self.curso else 'Unknown'}"


class HistoricalApplication(models.Model):
    """
    Modelo histórico para Docencia_application.
    
    Almacena registros históricos de aplicaciones cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva información de aplicaciones de estudiantes a cursos incluyendo
    notas y estado de becas.
    
    Campos principales:
        fecha_solicitud: Fecha de la solicitud
        estado: Estado actual de la aplicación
        beca: Información de beca
        pagado: Información de pago
        nota_final: Nota final
        curso: Foreign key a HistoricalCourseInformation
        edicion: Foreign key a HistoricalEdition
        usuario: Foreign key a User (auth_user)
    """
    fecha_solicitud = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    beca = models.IntegerField()
    pagado = models.IntegerField()
    nota_primaria = models.IntegerField()
    nota_secundaria = models.IntegerField()
    nota_final = models.IntegerField()
    nota_extra = models.IntegerField()
    comentarios = models.TextField(blank=True, null=True)
    curso = models.ForeignKey(
        HistoricalCourseInformation,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='applications'
    )
    edicion = models.ForeignKey(
        HistoricalEdition,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='applications'
    )
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_applications'
    )
    
    # Campos de datos
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='applications'
    )

    class Meta:
        db_table = 'historial_docenciaapplication'
        verbose_name = 'Historical Application'
        verbose_name_plural = 'Historical Applications'

    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Unknown'} - {self.curso.nombre if self.curso else 'Unknown'}"


class HistoricalClass(models.Model):
    """
    Modelo histórico para Docencia_class.

    Almacena registros históricos de clases cuando se realizan
    combinaciones de tablas en la sección "datos archivados dinámicos" del admin.
    Preserva información de clases asociadas a asignaturas.

    Campos principales:
        name: Nombre de la clase
        classbody: Contenido de la clase
        uploaddate: Fecha de carga
        datepub: Fecha de publicación
        dateend: Fecha de finalización
        slug: Slug único para la clase
        subject: Foreign key a HistoricalSubjectInformation
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_classes'
    )

    # Campos de datos
    name = models.CharField(max_length=100)
    classbody = models.TextField()
    uploaddate = models.DateField()
    datepub = models.DateTimeField()
    dateend = models.DateTimeField()
    slug = models.CharField(max_length=250)
    subject = models.ForeignKey(
        HistoricalSubjectInformation,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='classes'
    )

    class Meta:
        db_table = 'historial_docenciaclass'
        verbose_name = 'Historical Class'
        verbose_name_plural = 'Historical Classes'

    def __str__(self):
        return self.name


class HistoricalClassStudentView(models.Model):
    """
    Modelo histórico para Docencia_class_studentView.

    Almacena registros históricos de la relación many-to-many entre clases y
    aplicaciones de estudiantes. Se utiliza cuando se realizan combinaciones de
    tablas en la sección "datos archivados dinámicos" del admin.

    Campos:
        class_field: Foreign key a HistoricalClass (renombrado de class_id para evitar conflicto con palabra reservada)
        application: Foreign key a HistoricalApplication

    Nota: Mantiene la relación entre clases y aplicaciones de estudiantes.
    """
    # Campos de auditoría
    id_original = models.IntegerField()
    tabla_origen = models.CharField(max_length=255)
    fecha_consolidacion = models.DateTimeField(auto_now_add=True)
    dato_archivado = models.ForeignKey(
        'datos_archivados.DatoArchivadoDinamico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historical_class_student_views'
    )

    # Campos de datos
    class_field = models.ForeignKey(
        HistoricalClass,
        on_delete=models.CASCADE,
        related_name='student_views',
        db_column='class_id'
    )
    application = models.ForeignKey(
        HistoricalApplication,
        on_delete=models.CASCADE,
        related_name='class_views'
    )

    class Meta:
        db_table = 'historial_docenciaclass_studentview'
        verbose_name = 'Historical Class Student View'
        verbose_name_plural = 'Historical Class Student Views'
        unique_together = (('class_field', 'application'),)

    def __str__(self):
        return f"{self.class_field.name} - {self.application.usuario.username if self.application.usuario else 'Unknown'}"
