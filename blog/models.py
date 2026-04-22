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
    
    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f'Comentario de {self.autor.username} en {self.noticia.titulo}'
