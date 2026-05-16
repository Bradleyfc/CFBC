from django.db import models
from django.contrib.auth.models import User


class Evaluacion(models.Model):
    TIPO_CHOICES = [
        ('momentanea', 'Calificación Momentánea'),
        ('libre', 'Calificación Normal'),
    ]
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
    ]

    curso = models.ForeignKey(
        'principal.Curso', on_delete=models.CASCADE,
        related_name='evaluaciones', verbose_name='Curso'
    )
    titulo = models.CharField(max_length=200, verbose_name='Título')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='libre', verbose_name='Tipo')
    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES,
        default='borrador', verbose_name='Estado'
    )
    fecha_limite = models.DateTimeField(
        null=True, blank=True, verbose_name='Fecha límite de entrega'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.titulo} ({self.get_tipo_display()}) — {self.curso}'


class PreguntaEvaluacion(models.Model):
    TIPO_CHOICES = [
        ('opcion_multiple', 'Opción Múltiple'),
        ('seleccion_unica', 'Selección Única'),
        ('verdadero_falso', 'Verdadero / Falso'),
        ('escritura_libre', 'Escritura Libre'),
    ]

    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='preguntas', verbose_name='Evaluación'
    )
    texto = models.CharField(max_length=1000, verbose_name='Texto de la pregunta')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    requerida = models.BooleanField(default=True, verbose_name='Requerida')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    valor = models.DecimalField(
        max_digits=4, decimal_places=2, default=0,
        blank=True,
        verbose_name='Valor (puntos)',
        help_text='Puntos que vale esta pregunta (solo para evaluaciones momentáneas)'
    )

    class Meta:
        verbose_name = 'Pregunta de Evaluación'
        verbose_name_plural = 'Preguntas de Evaluación'
        ordering = ['orden']

    def __str__(self):
        return f'[{self.get_tipo_display()}] {self.texto[:80]}'


class OpcionEvaluacion(models.Model):
    pregunta = models.ForeignKey(
        PreguntaEvaluacion, on_delete=models.CASCADE,
        related_name='opciones', verbose_name='Pregunta'
    )
    texto = models.CharField(max_length=500, verbose_name='Texto de la opción')
    es_correcta = models.BooleanField(default=False, verbose_name='Es correcta')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')

    class Meta:
        verbose_name = 'Opción de Evaluación'
        verbose_name_plural = 'Opciones de Evaluación'
        ordering = ['orden']

    def __str__(self):
        correcta = ' ✓' if self.es_correcta else ''
        return f'{self.texto[:80]}{correcta}'


class IntentoEvaluacion(models.Model):
    ESTADO_CHOICES = [
        ('enviado', 'Enviado'),
        ('calificado', 'Calificado'),
    ]

    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='intentos', verbose_name='Evaluación'
    )
    estudiante = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='intentos_evaluacion', verbose_name='Estudiante'
    )
    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES,
        default='enviado', verbose_name='Estado'
    )
    fecha_envio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de envío')

    class Meta:
        unique_together = [['evaluacion', 'estudiante']]
        verbose_name = 'Intento de Evaluación'
        verbose_name_plural = 'Intentos de Evaluación'

    def __str__(self):
        return f'{self.estudiante} — {self.evaluacion} ({self.get_estado_display()})'


class RespuestaIntento(models.Model):
    intento = models.ForeignKey(
        IntentoEvaluacion, on_delete=models.CASCADE,
        related_name='respuestas', verbose_name='Intento'
    )
    pregunta = models.ForeignKey(
        PreguntaEvaluacion, on_delete=models.CASCADE,
        verbose_name='Pregunta'
    )
    opciones_seleccionadas = models.ManyToManyField(
        OpcionEvaluacion, blank=True,
        related_name='respuestas', verbose_name='Opciones seleccionadas'
    )
    texto_respuesta = models.TextField(
        blank=True, null=True, verbose_name='Respuesta de texto'
    )

    class Meta:
        unique_together = [['intento', 'pregunta']]
        verbose_name = 'Respuesta de Intento'
        verbose_name_plural = 'Respuestas de Intento'

    def __str__(self):
        return f'Respuesta de {self.intento.estudiante} a "{self.pregunta}"'


class CalificacionEvaluacion(models.Model):
    intento = models.OneToOneField(
        IntentoEvaluacion, on_delete=models.CASCADE,
        related_name='calificacion', verbose_name='Intento'
    )
    puntaje = models.DecimalField(
        max_digits=4, decimal_places=2, verbose_name='Puntaje (0-10)'
    )
    comentario = models.TextField(
        blank=True, null=True, verbose_name='Comentario del profesor'
    )
    es_automatica = models.BooleanField(default=True, verbose_name='Calificación automática')
    fecha_calificacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Calificación de Evaluación'
        verbose_name_plural = 'Calificaciones de Evaluación'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.puntaje is not None and (self.puntaje < 0 or self.puntaje > 10):
            raise ValidationError('El puntaje debe estar entre 0 y 10.')

    def __str__(self):
        return f'Calificación {self.puntaje} — {self.intento}'
