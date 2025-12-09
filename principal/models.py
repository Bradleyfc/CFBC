from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from accounts.models import Registro
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import date
from decimal import Decimal
import json

# Create your models here.
# CURSOS
class Curso(models.Model):
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
    
    image = models.ImageField(default='default/plantilla.jpg', upload_to='imagenes/', verbose_name='Imagen de curso')
    name = models.CharField(max_length=90, verbose_name='Nombre')
    description= models.TextField(blank=True, null=True, verbose_name='Descripcion')
    area = models.CharField(max_length=20, choices=AREA_CHOICES, default='idiomas', verbose_name='Área')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='curso', verbose_name='Tipo')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Profesores'}, verbose_name='Profesor')
    class_quantity = models.PositiveIntegerField(default=0, verbose_name='Cantidad de Clases')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='I', verbose_name='Estado')
    curso_academico = models.ForeignKey('CursoAcademico', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Curso Académico')
    enrollment_deadline = models.DateField(verbose_name='Fecha límite de inscripción', null=True, blank=True)
    start_date = models.DateField(verbose_name='Fecha de inicio del curso', null=True, blank=True)

    def get_dynamic_status(self):
        """
        Obtiene el estado dinámico del curso basado en la fecha límite de inscripción
        y la fecha actual del servidor.
        """
        if not self.enrollment_deadline:
            # Si no hay fecha límite, usar el estado manual
            return self.status
        
        # Obtener la fecha actual del servidor
        today = date.today()
        
        # Si ya pasó la fecha límite de inscripción
        if today > self.enrollment_deadline:
            # Si el curso estaba en inscripción, cambiar a "Plazo Terminado"
            if self.status == 'I':
                return 'IT'
            # Para otros estados, mantener el estado actual
            return self.status
        else:
            # Si aún no ha pasado la fecha límite
            # Si el estado manual es "Plazo Terminado" pero aún no ha pasado la fecha, 
            # cambiar a "En inscripción"
            if self.status == 'IT':
                return 'I'
            # Para otros estados, mantener el estado actual
            return self.status
    
    def get_dynamic_status_display(self):
        """
        Obtiene la descripción del estado dinámico
        """
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.get_dynamic_status(), self.get_status_display())

    def __str__(self):
        if self.curso_academico:
            return f"{self.name} ({self.curso_academico.nombre})"
        return self.name

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

        
# Curso y cambio de curso escolar

class CursoAcademico(models.Model):
    
    nombre = models.CharField(max_length=50, unique=True)  # Ej: "2025-2026"
    activo = models.BooleanField(default=False)
    archivado = models.BooleanField(default=False, verbose_name='Archivado')
    fecha_creacion = models.DateField(default=timezone.now, verbose_name='Fecha de creación')
    
    def archivar(self):
        """Archiva este curso académico y todas sus matrículas"""
        self.archivado = True
        self.activo = False
        self.save()
        
        # También podríamos desactivar todas las matrículas de este curso
        # Matriculas.objects.filter(curso_academico=self).update(activo=False)
        
        return True
    
    def activar(self):
        """Activa este curso y desactiva todos los demás"""
         # Primero, obtener y actualizar todos los cursos activos anteriores
        cursos_activos = CursoAcademico.objects.filter(activo=True)
        for curso in cursos_activos:
            if curso != self:
                curso.activo = False
                curso.archivado = True
                curso.save()



        # Activar este curso
        self.activo = True
        self.archivado = False  # Si estaba archivado, lo desarchivamos
        self.save()
        return True


    def save(self, *args, **kwargs):
        if self.activo and not self.pk:  # Si es un nuevo curso y se marca como activo
            # Desactivar y archivar todos los demás cursos académicos activos
            CursoAcademico.objects.filter(activo=True).update(activo=False, archivado=True)
        elif self.activo and self.pk: # Si es un curso existente y se está activando
            # Desactivar y archivar todos los demás cursos académicos activos, excepto este
            CursoAcademico.objects.filter(activo=True).exclude(pk=self.pk).update(activo=False, archivado=True)
        
        # Asegurarse de que si este curso está activo, no esté archivado
        if self.activo:
            self.archivado = False

        super().save(*args, **kwargs)






    def __str__(self):
        estado = "(Activo)" if self.activo else "(Inactivo)"
        if self.archivado:
            estado = "(Archivado)"
        return f"{self.nombre} {estado}"

# MATRICULAS

class Matriculas(models.Model):
    ESTADO_CHOICES = [
        ('P', 'Pendiente'),
        ('A', 'Aprobado'),
        ('R', 'Reprobado'),
        ('L', 'Licencia'),
        ('B', 'Baja'),
    ]
    course = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name="Curso")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matriculas', limit_choices_to={'groups__name': 'Estudiantes'}, verbose_name='Estudiante')
    activo = models.BooleanField(default=True, verbose_name='Habilitado')
    curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Curso Académico')
    fecha_matricula = models.DateField(auto_now_add=True, verbose_name='Fecha de Matrícula')
    estado = models.CharField(max_length=1, choices=ESTADO_CHOICES, default='P', verbose_name='Estado')
    
    @property
    def esta_aprobado(self):
        return self.estado == 'A'


    def __str__(self):
        return f'{self.student.username} - {self.course.name}'

    class Meta:
        verbose_name = 'Matricula'
        verbose_name_plural = 'Matriculas'
        unique_together = [['student', 'course', 'curso_academico']]


# ASISTENCIAS    

class Asistencia(models.Model):
    course = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name="Curso")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asistencias', limit_choices_to={'groups__name': 'Estudiantes'}, verbose_name='Estudiante') 
    presente = models.BooleanField(default=False, blank=True, null=True, verbose_name='Asistió')
    date = models.DateField(null=False, blank=False, verbose_name='Fecha')
    
    def __str__(self):
        return f"Asistencia de {self.student.first_name} {self.student.last_name} en {self.course.name} el {self.date}"

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        unique_together = ('student', 'date', 'course')


# CALIFICACIONES

class Calificaciones(models.Model):
    matricula = models.OneToOneField(Matriculas, on_delete=models.CASCADE, related_name='calificaciones', verbose_name='Matrícula', null=True, blank=True)
    course = models.ForeignKey(Curso, on_delete=models.CASCADE, verbose_name="Curso")
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Estudiantes'}, verbose_name='Estudiante') 
    curso_academico = models.ForeignKey(CursoAcademico, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Curso Académico')
    # Las notas individuales ahora se manejarán a través del modelo NotaIndividual
    average = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, verbose_name='Promedio', editable=False)


    def __str__(self):
        return str(self.course)

# Calcular el promedio 

    def calcular_promedio(self):
        # Obtener todas las notas individuales relacionadas con esta calificación
        notas_individuales = self.notas.all()
        notas_validas = [nota.valor for nota in notas_individuales if nota.valor is not None]
        if notas_validas:
            return sum(notas_validas) / len(notas_validas)
        return None


    def save(self, *args, **kwargs):
        # Save the instance first to ensure it has a primary key
        super().save(*args, **kwargs)
        
        # Now that the instance has a PK, calculate the average
        calculated_average = self.calcular_promedio()
        if calculated_average is not None:
            new_average = Decimal(str(calculated_average))
        else:
            new_average = None
        
        # Only update if the average has changed
        if self.average != new_average:
            self.average = new_average
            super().save(update_fields=['average'])

    class Meta:
        verbose_name= 'Calificacion'
        verbose_name_plural= 'Calificaciones'
        unique_together = ('course', 'student', 'curso_academico')
      

class NotaIndividual(models.Model):
    calificacion = models.ForeignKey(Calificaciones, on_delete=models.CASCADE, related_name='notas', verbose_name='Calificación')
    valor = models.PositiveIntegerField(verbose_name='Valor de la Nota')
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name='Fecha de Creación')

    def __str__(self):
        return f"Nota {self.valor} para {self.calificacion.student.username} en {self.calificacion.course.name}"

    class Meta:
        verbose_name = 'Nota Individual'
        verbose_name_plural = 'Notas Individuales'
        ordering = ['fecha_creacion'] # Opcional: ordenar notas por fecha

@receiver(post_save, sender=NotaIndividual)
@receiver(post_delete, sender=NotaIndividual)
def update_calificaciones_average(sender, instance, **kwargs):
    calificacion = instance.calificacion
    calificacion.save() # This will trigger the calcular_promedio and update the average

# FORMULARIOS DE APLICACIÓN A CURSOS

class FormularioAplicacion(models.Model):
    """
    Modelo para almacenar los formularios de aplicación creados por el grupo secretaria.
    Cada curso puede tener un formulario de aplicación personalizado.
    """
    curso = models.OneToOneField(Curso, on_delete=models.CASCADE, related_name='formulario_aplicacion', verbose_name='Curso')
    titulo = models.CharField(max_length=200, verbose_name='Título del formulario')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última modificación')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    
    def __str__(self):
        return f"Formulario para {self.curso.name}"
    
    class Meta:
        verbose_name = '📋 Formulario de Aplicación'
        verbose_name_plural = '📋 Formularios de Aplicación'
        ordering = ['-fecha_modificacion']

class PreguntaFormulario(models.Model):
    """
    Modelo para almacenar las preguntas de los formularios de aplicación.
    """
    TIPO_CHOICES = [
        ('seleccion_multiple', 'Selección Múltiple'),
        ('seleccion_unica', 'Selección Única'),
        ('escritura_libre', 'Escritura Libre'),
    ]
    
    formulario = models.ForeignKey(FormularioAplicacion, on_delete=models.CASCADE, related_name='preguntas', verbose_name='Formulario')
    texto = models.CharField(max_length=500, verbose_name='Texto de la pregunta')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='seleccion_multiple', verbose_name='Tipo de pregunta')
    requerida = models.BooleanField(default=True, verbose_name='Requerida')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    
    def __str__(self):
        curso_name = self.formulario.curso.name if self.formulario else "Sin curso"
        return f"{self.texto[:50]}... - {curso_name} ({self.get_tipo_display()})"
    
    class Meta:
        verbose_name = '❓ Pregunta de Formulario'
        verbose_name_plural = '❓ Preguntas de Formulario'
        ordering = ['orden']

class OpcionRespuesta(models.Model):
    """
    Modelo para almacenar las opciones de respuesta para cada pregunta.
    """
    pregunta = models.ForeignKey(PreguntaFormulario, on_delete=models.CASCADE, related_name='opciones', verbose_name='Pregunta')
    texto = models.CharField(max_length=255, verbose_name='Texto de la opción', blank=True, default='')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    
    def __str__(self):
        if self.pregunta and self.pregunta.formulario:
            curso_name = self.pregunta.formulario.curso.name
            return f"{self.texto} (Curso: {curso_name})"
        return self.texto
    
    class Meta:
        verbose_name = '✅ Opción de Respuesta'
        verbose_name_plural = '✅ Opciones de Respuesta'
        ordering = ['orden']

class SolicitudInscripcion(models.Model):
    """
    Modelo para almacenar las solicitudes de inscripción de los estudiantes.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='solicitudes', verbose_name='Curso')
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_inscripcion', limit_choices_to={'groups__name': 'Estudiantes'}, verbose_name='Estudiante')
    formulario = models.ForeignKey(FormularioAplicacion, on_delete=models.CASCADE, related_name='solicitudes', verbose_name='Formulario')
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    fecha_revision = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de revisión')
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_revisadas', verbose_name='Revisado por')
    
    def __str__(self):
        return f"Solicitud de {self.estudiante.get_full_name() or self.estudiante.username} para {self.curso.name}"
    
    class Meta:
        verbose_name = '📝 Solicitud de Inscripción'
        verbose_name_plural = '📝 Solicitudes de Inscripción'
        ordering = ['-fecha_solicitud']
        unique_together = [['estudiante', 'curso']]
    
    def aprobar(self, usuario):
        """
        Aprueba la solicitud y crea la matrícula correspondiente.
        """
        self.estado = 'aprobada'
        self.fecha_revision = timezone.now()
        self.revisado_por = usuario
        self.save()
        
        # Crear la matrícula
        curso_academico = self.curso.curso_academico
        matricula, created = Matriculas.objects.get_or_create(
            course=self.curso,
            student=self.estudiante,
            curso_academico=curso_academico,
            defaults={
                'activo': True,
                'estado': 'P'  # Pendiente
            }
        )
        return matricula
    
    def rechazar(self, usuario):
        """
        Rechaza la solicitud.
        """
        self.estado = 'rechazada'
        self.fecha_revision = timezone.now()
        self.revisado_por = usuario
        self.save()
        return True

class RespuestaEstudiante(models.Model):
    """
    Modelo para almacenar las respuestas de los estudiantes a las preguntas del formulario.
    """
    solicitud = models.ForeignKey(SolicitudInscripcion, on_delete=models.CASCADE, related_name='respuestas', verbose_name='Solicitud')
    pregunta = models.ForeignKey(PreguntaFormulario, on_delete=models.CASCADE, related_name='respuestas', verbose_name='Pregunta')
    opciones_seleccionadas = models.ManyToManyField(OpcionRespuesta, related_name='respuestas', verbose_name='Opciones seleccionadas')
    
    def __str__(self):
        return f"Respuesta a {self.pregunta.texto} por {self.solicitud.estudiante.username}"
    
    class Meta:
        verbose_name = '💬 Respuesta de Estudiante'
        verbose_name_plural = '💬 Respuestas de Estudiantes'
        unique_together = [['solicitud', 'pregunta']]
