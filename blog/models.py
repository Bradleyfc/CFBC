from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

class Noticia(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente_revision', 'Pendiente de revisión'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado'),
    ]

    VISIBILIDAD_CHOICES = [
        ('solo_registrados', 'Solo usuarios registrados'),
        ('publico', 'Público (cualquier visitante)'),
        ('indexable', 'Público e indexable en buscadores'),
    ]
    
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    resumen = models.TextField(max_length=300, help_text="Breve resumen de la noticia")
    contenido = models.TextField()
    imagen_principal = models.ImageField(upload_to='noticias/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='noticias')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='noticias')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='borrador')
    visibilidad = models.CharField(
        max_length=20,
        choices=VISIBILIDAD_CHOICES,
        default='publico',
        help_text="Controla quién puede ver esta noticia y si aparece en buscadores"
    )
    destacada = models.BooleanField(default=False, help_text="Marcar como noticia destacada")
    permitir_comentarios = models.BooleanField(default=True, help_text="Permitir que los usuarios comenten esta noticia")
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateTimeField(default=timezone.now)
    
    # SEO
    meta_descripcion = models.CharField(max_length=160, blank=True, help_text="Descripción para SEO")
    
    # Flujo editorial
    notas_editor = models.TextField(blank=True, default='', max_length=1000, help_text='Notas del editor al devolver un artículo al autor')
    
    class Meta:
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        ordering = ['-fecha_publicacion']
    
    def __str__(self):
        return self.titulo
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:detalle_noticia', kwargs={'slug': self.slug})

class Comentario(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    nota_moderacion = models.TextField(
        blank=True,
        default='',
        help_text="Notas internas del moderador (movimientos, auditoría)"
    )
    
    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f'Comentario de {self.autor.username} en {self.noticia.titulo}'


class ReporteComentario(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('resuelto_retirado', 'Resuelto - Retirado'),
        ('resuelto_mantenido', 'Resuelto - Mantenido'),
    ]

    comentario = models.ForeignKey(
        Comentario,
        on_delete=models.CASCADE,
        related_name='reportes'
    )
    reportado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reportes_enviados'
    )
    motivo = models.CharField(max_length=1000)
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    resuelto_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportes_resueltos'
    )
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Reporte de comentario"
        verbose_name_plural = "Reportes de comentarios"
        ordering = ['-fecha_reporte']

    def __str__(self):
        return f'Reporte de {self.reportado_por.username} sobre comentario #{self.comentario.id} ({self.estado})'


class SancionUsuario(models.Model):
    TIPO_CHOICES = [
        ('silencio', 'Silencio temporal'),
        ('silencio_permanente', 'Silencio permanente'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sanciones'
    )
    tipo_sancion = models.CharField(max_length=20, choices=TIPO_CHOICES)
    motivo = models.CharField(max_length=1000)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    aplicada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sanciones_aplicadas'
    )
    activa = models.BooleanField(default=True)
    fecha_levantamiento = models.DateTimeField(null=True, blank=True)
    levantada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sanciones_levantadas'
    )

    class Meta:
        verbose_name = "Sanción de usuario"
        verbose_name_plural = "Sanciones de usuarios"
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'Sanción {self.tipo_sancion} a {self.usuario.username} ({"activa" if self.activa else "inactiva"})'


class ComentarioFijado(models.Model):
    comentario = models.OneToOneField(
        Comentario,
        on_delete=models.CASCADE,
        related_name='fijado'
    )
    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.CASCADE,
        related_name='comentarios_fijados'
    )
    fijado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comentarios_fijados'
    )
    fecha_fijado = models.DateTimeField(auto_now_add=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Comentario fijado"
        verbose_name_plural = "Comentarios fijados"
        ordering = ['orden']

    def __str__(self):
        return f'Comentario #{self.comentario.id} fijado en "{self.noticia.titulo}" (orden {self.orden})'


class MetricaComunidad(models.Model):
    fecha = models.DateField(unique=True)
    total_reportes = models.PositiveIntegerField(default=0)
    total_comentarios = models.PositiveIntegerField(default=0)
    total_sanciones = models.PositiveIntegerField(default=0)
    usuario_mas_activo = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    pico_toxicidad = models.FloatField(null=True, blank=True)
    generada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Métrica de comunidad"
        verbose_name_plural = "Métricas de comunidad"
        ordering = ['-fecha']

    def __str__(self):
        return f'Métricas del {self.fecha} (reportes: {self.total_reportes}, sanciones: {self.total_sanciones})'
