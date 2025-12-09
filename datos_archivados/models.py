from django.db import models
from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal

# Modelos para datos archivados de la base de datos MariaDB antigua

class CursoAcademicoArchivado(models.Model):
    """
    Modelo para almacenar cursos académicos archivados de la base de datos antigua
    """
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    nombre = models.CharField(max_length=50, verbose_name='Nombre del Curso Académico')
    activo = models.BooleanField(default=False, verbose_name='Activo')
    archivado = models.BooleanField(default=True, verbose_name='Archivado')
    fecha_creacion = models.DateField(verbose_name='Fecha de creación')
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    def __str__(self):
        return f"{self.nombre} (Archivado - ID Original: {self.id_original})"
    
    class Meta:
        verbose_name = 'Curso Académico Archivado'
        verbose_name_plural = 'Cursos Académicos Archivados'
        ordering = ['-fecha_creacion']

class UsuarioArchivado(models.Model):
    """
    Modelo para almacenar usuarios archivados de la base de datos antigua
    """
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino')
    ]
    
    GRADO_CHOICES = [
        ("grado1", "Ninguno"),
        ("grado2", "Noveno Grado"),
        ("grado3", "Bachiller"),
        ("grado4", "Superior"),
    ]
    
    OCUPACION_CHOICES = [
        ("ocupacion1", "Desocupado"),
        ("ocupacion2", "Estudiante"),
        ("ocupacion3", "Ama de Casa"),
        ("ocupacion4", "Trabajador Estatal"),
        ("ocupacion5", "Trabajador por Cuenta Propia"),
    ]
    
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    username = models.CharField(max_length=150, verbose_name='Nombre de usuario')
    first_name = models.CharField(max_length=150, blank=True, verbose_name='Nombre')
    last_name = models.CharField(max_length=150, blank=True, verbose_name='Apellidos')
    email = models.EmailField(blank=True, verbose_name='Email')
    date_joined = models.DateTimeField(verbose_name='Fecha de registro')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    # Campos del perfil
    nacionalidad = models.CharField(max_length=150, null=True, blank=True, verbose_name='Nacionalidad')
    carnet = models.CharField(max_length=11, null=True, blank=True, verbose_name='Carnet')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, default='M', verbose_name='Sexo')
    address = models.CharField(max_length=150, null=True, blank=True, verbose_name='Dirección')
    location = models.CharField(max_length=150, null=True, blank=True, verbose_name='Municipio')
    provincia = models.CharField(max_length=150, null=True, blank=True, verbose_name='Provincia')
    telephone = models.CharField(max_length=50, null=True, blank=True, verbose_name='Teléfono')
    movil = models.CharField(max_length=50, null=True, blank=True, verbose_name='Móvil')
    grado = models.CharField(max_length=50, choices=GRADO_CHOICES, default="grado1", verbose_name='Grado Académico')
    ocupacion = models.CharField(max_length=100, choices=OCUPACION_CHOICES, default="ocupacion1", verbose_name='Ocupación')
    titulo = models.CharField(max_length=150, null=True, blank=True, verbose_name='Título')
    
    # Campos de grupo/rol
    grupo = models.CharField(max_length=50, blank=True, verbose_name='Grupo')
    
    # Vinculación con usuario actual (si existe)
    usuario_actual = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='datos_archivados', verbose_name='Usuario Actual Vinculado')
    
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    def __str__(self):
        return f"{self.username} - {self.first_name} {self.last_name} (ID Original: {self.id_original})"
    
    class Meta:
        verbose_name = 'Usuario Archivado'
        verbose_name_plural = 'Usuarios Archivados'
        ordering = ['-date_joined']

class CursoArchivado(models.Model):
    """
    Modelo para almacenar cursos archivados de la base de datos antigua
    """
    STATUS_CHOICES = [
        ('I', 'En etapa de inscripción'),
        ('IT', 'Plazo de Inscripción Terminado'),
        ('P', 'En progreso'),
        ('F', 'Finalizado'),
    ]
    
    AREA_CHOICES = [
        ('idiomas', 'Idiomas'),
        ('humanidades', 'Humanidades'),
        ('computacion', 'Computación'),
        ('diseno', 'Diseño'),
        ('adolescentes', 'Adolescentes'),
        ('teologia', 'Teología'),
    ]
    
    TIPO_CHOICES = [
        ('curso', 'Curso'),
        ('diplomado', 'Diplomado'),
        ('grado', 'Grado'),
        ('taller', 'Taller'),
    ]
    
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    name = models.CharField(max_length=90, verbose_name='Nombre')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    area = models.CharField(max_length=20, choices=AREA_CHOICES, default='idiomas', verbose_name='Área')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='curso', verbose_name='Tipo')
    teacher_id_original = models.IntegerField(verbose_name='ID Original del Profesor en MariaDB')
    teacher_name = models.CharField(max_length=200, verbose_name='Nombre del Profesor')
    class_quantity = models.PositiveIntegerField(default=0, verbose_name='Cantidad de Clases')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='I', verbose_name='Estado')
    curso_academico = models.ForeignKey(CursoAcademicoArchivado, on_delete=models.CASCADE, 
                                      verbose_name='Curso Académico Archivado')
    enrollment_deadline = models.DateField(verbose_name='Fecha límite de inscripción', null=True, blank=True)
    start_date = models.DateField(verbose_name='Fecha de inicio del curso', null=True, blank=True)
    
    # Vinculación con profesor actual (si existe)
    teacher_actual = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     limit_choices_to={'groups__name': 'Profesores'}, 
                                     verbose_name='Profesor Actual Vinculado')
    
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    def __str__(self):
        return f"{self.name} - {self.curso_academico.nombre} (ID Original: {self.id_original})"
    
    class Meta:
        verbose_name = 'Curso Archivado'
        verbose_name_plural = 'Cursos Archivados'
        ordering = ['-curso_academico__fecha_creacion', 'name']

class MatriculaArchivada(models.Model):
    """
    Modelo para almacenar matrículas archivadas de la base de datos antigua
    """
    ESTADO_CHOICES = [
        ('P', 'Pendiente'),
        ('A', 'Aprobado'),
        ('R', 'Reprobado'),
        ('L', 'Licencia'),
        ('B', 'Baja'),
    ]
    
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    course = models.ForeignKey(CursoArchivado, on_delete=models.CASCADE, verbose_name="Curso Archivado")
    student = models.ForeignKey(UsuarioArchivado, on_delete=models.CASCADE, 
                              related_name='matriculas_archivadas', verbose_name='Estudiante Archivado')
    activo = models.BooleanField(default=True, verbose_name='Habilitado')
    fecha_matricula = models.DateField(verbose_name='Fecha de Matrícula')
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P', verbose_name='Estado')
    
    # Vinculación con matrícula actual (si existe)
    # matricula_actual = models.ForeignKey('principal.Matriculas', on_delete=models.SET_NULL, 
    #                                    null=True, blank=True, verbose_name='Matrícula Actual Vinculada')
    
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    def __str__(self):
        return f'{self.student.username} - {self.course.name} (ID Original: {self.id_original})'
    
    class Meta:
        verbose_name = 'Matrícula Archivada'
        verbose_name_plural = 'Matrículas Archivadas'
        ordering = ['-fecha_matricula']

class CalificacionArchivada(models.Model):
    """
    Modelo para almacenar calificaciones archivadas de la base de datos antigua
    """
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    matricula = models.ForeignKey(MatriculaArchivada, on_delete=models.CASCADE, 
                                related_name='calificaciones_archivadas', verbose_name='Matrícula Archivada')
    course = models.ForeignKey(CursoArchivado, on_delete=models.CASCADE, verbose_name="Curso Archivado")
    student = models.ForeignKey(UsuarioArchivado, on_delete=models.CASCADE, verbose_name='Estudiante Archivado')
    average = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, verbose_name='Promedio')
    
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    def __str__(self):
        return f"Calificación de {self.student.username} en {self.course.name} (ID Original: {self.id_original})"
    
    class Meta:
        verbose_name = 'Calificación Archivada'
        verbose_name_plural = 'Calificaciones Archivadas'

class NotaIndividualArchivada(models.Model):
    """
    Modelo para almacenar notas individuales archivadas de la base de datos antigua
    """
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    calificacion = models.ForeignKey(CalificacionArchivada, on_delete=models.CASCADE, 
                                   related_name='notas_archivadas', verbose_name='Calificación Archivada')
    valor = models.PositiveIntegerField(verbose_name='Valor de la Nota')
    fecha_creacion = models.DateField(verbose_name='Fecha de Creación')
    
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    def __str__(self):
        return f"Nota {self.valor} para {self.calificacion.student.username} en {self.calificacion.course.name} (ID Original: {self.id_original})"
    
    class Meta:
        verbose_name = 'Nota Individual Archivada'
        verbose_name_plural = 'Notas Individuales Archivadas'
        ordering = ['fecha_creacion']

class AsistenciaArchivada(models.Model):
    """
    Modelo para almacenar asistencias archivadas de la base de datos antigua
    """
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    course = models.ForeignKey(CursoArchivado, on_delete=models.CASCADE, verbose_name="Curso Archivado")
    student = models.ForeignKey(UsuarioArchivado, on_delete=models.CASCADE, 
                              related_name='asistencias_archivadas', verbose_name='Estudiante Archivado')
    presente = models.BooleanField(default=False, blank=True, null=True, verbose_name='Asistió')
    date = models.DateField(null=False, blank=False, verbose_name='Fecha')
    
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    def __str__(self):
        return f"Asistencia de {self.student.first_name} {self.student.last_name} en {self.course.name} el {self.date} (ID Original: {self.id_original})"
    
    class Meta:
        verbose_name = 'Asistencia Archivada'
        verbose_name_plural = 'Asistencias Archivadas'
        ordering = ['-date']

class MigracionLog(models.Model):
    """
    Modelo para llevar registro de las migraciones realizadas
    """
    ESTADO_CHOICES = [
        ('iniciada', 'Iniciada'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('error', 'Error'),
    ]
    
    fecha_inicio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Inicio')
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Finalización')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='iniciada', verbose_name='Estado')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario que ejecutó la migración')
    
    # Contadores de registros migrados
    usuarios_migrados = models.IntegerField(default=0, verbose_name='Registros Migrados')
    cursos_academicos_migrados = models.IntegerField(default=0, verbose_name='Cursos Académicos Migrados')
    cursos_migrados = models.IntegerField(default=0, verbose_name='Cursos Migrados')
    matriculas_migradas = models.IntegerField(default=0, verbose_name='Matrículas Migradas')
    calificaciones_migradas = models.IntegerField(default=0, verbose_name='Calificaciones Migradas')
    notas_migradas = models.IntegerField(default=0, verbose_name='Notas Migradas')
    asistencias_migradas = models.IntegerField(default=0, verbose_name='Asistencias Migradas')
    
    # Información sobre tablas inspeccionadas
    tablas_inspeccionadas = models.IntegerField(default=0, verbose_name='Tablas Inspeccionadas')
    tablas_con_datos = models.IntegerField(default=0, verbose_name='Tablas con Datos')
    tablas_vacias = models.IntegerField(default=0, verbose_name='Tablas Vacías')
    
    # Información de errores
    errores = models.TextField(blank=True, verbose_name='Errores encontrados')
    
    # Configuración de conexión utilizada (sin credenciales sensibles)
    host_origen = models.CharField(max_length=255, verbose_name='Host de origen')
    base_datos_origen = models.CharField(max_length=255, verbose_name='Base de datos de origen')
    
    def __str__(self):
        return f"Migración {self.id} - {self.estado} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = 'Log de Migración'
        verbose_name_plural = 'Logs de Migración'
        ordering = ['-fecha_inicio']

class DatoArchivadoDinamico(models.Model):
    """
    Modelo para almacenar datos archivados de cualquier tabla de forma dinámica
    """
    tabla_origen = models.CharField(max_length=100, verbose_name='Tabla de Origen')
    id_original = models.IntegerField(verbose_name='ID Original en MariaDB')
    datos_originales = models.JSONField(verbose_name='Datos Originales')
    estructura_tabla = models.JSONField(verbose_name='Estructura de la Tabla', blank=True, null=True)
    fecha_migracion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de migración')
    
    # Campos adicionales para facilitar búsquedas
    nombre_registro = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nombre del Registro')
    tipo_registro = models.CharField(max_length=50, blank=True, null=True, verbose_name='Tipo de Registro')
    
    def __str__(self):
        return f"{self.tabla_origen} - ID {self.id_original} (Migrado: {self.fecha_migracion.strftime('%d/%m/%Y')})"
    
    def obtener_dato(self, campo):
        """Obtiene un dato específico del JSON"""
        return self.datos_originales.get(campo)
    
    def obtener_nombre_legible(self):
        """Intenta obtener un nombre legible del registro"""
        if self.nombre_registro:
            return self.nombre_registro
        
        # Intentar obtener nombre de campos comunes
        datos = self.datos_originales
        for campo in ['name', 'nombre', 'title', 'titulo', 'username', 'email']:
            if campo in datos and datos[campo]:
                return str(datos[campo])
        
        return f"Registro {self.id_original}"
    
    class Meta:
        verbose_name = 'Dato Archivado Dinámico'
        verbose_name_plural = 'Datos Archivados Dinámicos'
        ordering = ['-fecha_migracion']
        unique_together = ['tabla_origen', 'id_original']
        indexes = [
            models.Index(fields=['tabla_origen', 'id_original']),
            models.Index(fields=['fecha_migracion']),
            models.Index(fields=['tipo_registro']),
        ]

class CodigoVerificacionReclamacion(models.Model):
    """
    Modelo para almacenar códigos de verificación para reclamación de usuarios archivados
    """
    email = models.EmailField(verbose_name='Email')
    codigo = models.CharField(max_length=4, verbose_name='Código de Verificación')
    dato_archivado = models.ForeignKey(DatoArchivadoDinamico, on_delete=models.CASCADE, 
                                     null=True, blank=True, verbose_name='Dato Archivado')
    usuario_archivado = models.ForeignKey(UsuarioArchivado, on_delete=models.CASCADE, 
                                        null=True, blank=True, verbose_name='Usuario Archivado')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    fecha_expiracion = models.DateTimeField(verbose_name='Fecha de Expiración')
    usado = models.BooleanField(default=False, verbose_name='Usado')
    
    def __str__(self):
        return f"Código {self.codigo} para {self.email}"
    
    def is_expired(self):
        """Verifica si el código ha expirado"""
        from django.utils import timezone
        return timezone.now() > self.fecha_expiracion
    
    def is_valid(self):
        """Verifica si el código es válido (no usado y no expirado)"""
        return not self.usado and not self.is_expired()
    
    class Meta:
        verbose_name = 'Código de Verificación para Reclamación'
        verbose_name_plural = 'Códigos de Verificación para Reclamación'
        ordering = ['-fecha_creacion']