from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.utils import timezone


class CategoriaFAQ(models.Model):
    """Categorías para organizar FAQs"""
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name='Slug')
    icono = models.CharField(max_length=50, blank=True, verbose_name='Icono', help_text='Nombre del icono (ej: book, question-circle)')
    orden = models.IntegerField(default=0, verbose_name='Orden', help_text='Orden de visualización')
    
    class Meta:
        verbose_name = 'Categoría FAQ'
        verbose_name_plural = 'Categorías FAQ'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)


class FAQ(models.Model):
    """Modelo para preguntas frecuentes"""
    pregunta = models.CharField(max_length=500, verbose_name='Pregunta')
    respuesta = models.TextField(verbose_name='Respuesta')
    categoria = models.ForeignKey(
        CategoriaFAQ, 
        on_delete=models.CASCADE, 
        related_name='faqs',
        verbose_name='Categoría'
    )
    prioridad = models.IntegerField(
        default=0, 
        verbose_name='Prioridad',
        help_text='Mayor número = mayor prioridad en resultados'
    )
    destacada = models.BooleanField(
        default=False, 
        verbose_name='Destacada',
        help_text='Las FAQs destacadas aparecen primero en los resultados'
    )
    activa = models.BooleanField(
        default=True, 
        verbose_name='Activa',
        help_text='Solo las FAQs activas se incluyen en las búsquedas'
    )
    
    # Métricas de uso
    veces_usada = models.IntegerField(
        default=0, 
        verbose_name='Veces usada',
        help_text='Contador de cuántas veces se ha usado esta FAQ en respuestas'
    )
    ultima_fecha_uso = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Última fecha de uso'
    )
    tasa_exito = models.FloatField(
        default=0.0, 
        verbose_name='Tasa de éxito',
        help_text='Porcentaje de feedback positivo (0.0 - 1.0)'
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Fecha de creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True, 
        verbose_name='Última actualización'
    )
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['-destacada', '-prioridad', '-veces_usada']
    
    def __str__(self):
        return self.pregunta[:100]
    
    def incrementar_uso(self):
        """Incrementa el contador de uso y actualiza la fecha"""
        self.veces_usada += 1
        self.ultima_fecha_uso = timezone.now()
        self.save(update_fields=['veces_usada', 'ultima_fecha_uso'])
    
    def actualizar_tasa_exito(self, feedback_positivo, feedback_total):
        """Actualiza la tasa de éxito basándose en el feedback"""
        if feedback_total > 0:
            self.tasa_exito = feedback_positivo / feedback_total
            self.save(update_fields=['tasa_exito'])
    
    def get_content_type(self):
        """Obtiene el ContentType para este modelo"""
        return ContentType.objects.get_for_model(self)


class FAQVariation(models.Model):
    """Variaciones de preguntas para una FAQ"""
    faq = models.ForeignKey(
        FAQ, 
        on_delete=models.CASCADE, 
        related_name='variaciones',
        verbose_name='FAQ'
    )
    texto_variacion = models.CharField(
        max_length=500, 
        verbose_name='Variación de la pregunta',
        help_text='Forma alternativa de hacer la misma pregunta'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Fecha de creación'
    )
    
    class Meta:
        verbose_name = 'Variación de FAQ'
        verbose_name_plural = 'Variaciones de FAQ'
        ordering = ['fecha_creacion']
    
    def __str__(self):
        return f"{self.texto_variacion[:50]}... (FAQ: {self.faq.pregunta[:30]}...)"


class ChatInteraction(models.Model):
    """Registro de interacciones del chatbot"""
    session_id = models.CharField(
        max_length=100, 
        verbose_name='ID de sesión',
        db_index=True
    )
    pregunta = models.TextField(verbose_name='Pregunta del usuario')
    respuesta = models.TextField(verbose_name='Respuesta generada')
    documentos_recuperados = models.JSONField(
        verbose_name='Documentos recuperados',
        help_text='Lista de documentos encontrados por la búsqueda semántica'
    )
    intencion_detectada = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        verbose_name='Intención detectada'
    )
    confianza = models.FloatField(
        verbose_name='Nivel de confianza',
        help_text='Confianza en la respuesta (0.0 - 1.0)'
    )
    fue_util = models.BooleanField(
        null=True, 
        blank=True,
        verbose_name='¿Fue útil?',
        help_text='Feedback del usuario sobre la utilidad de la respuesta'
    )
    fecha = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Fecha',
        db_index=True
    )
    tiempo_respuesta = models.FloatField(
        verbose_name='Tiempo de respuesta (segundos)',
        help_text='Tiempo que tomó generar la respuesta'
    )
    es_candidata_faq = models.BooleanField(
        default=False,
        verbose_name='Candidata para FAQ',
        help_text='Marcada como candidata para crear una nueva FAQ'
    )
    
    class Meta:
        verbose_name = 'Interacción de Chat'
        verbose_name_plural = 'Interacciones de Chat'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['-fecha']),
            models.Index(fields=['session_id']),
            models.Index(fields=['es_candidata_faq']),
        ]
    
    def __str__(self):
        return f"{self.pregunta[:50]}... ({self.fecha.strftime('%Y-%m-%d %H:%M')})"
    
    @staticmethod
    def anonimizar_datos(texto):
        """
        Anonimiza datos personales del texto
        Reemplaza emails, teléfonos, nombres propios detectados
        """
        import re
        # Anonimizar emails
        texto = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', texto)
        # Anonimizar teléfonos (formato nicaragüense y general)
        texto = re.sub(r'\b\d{4}[-\s]?\d{4}\b', '[TELÉFONO]', texto)
        texto = re.sub(r'\b\+?\d{1,3}[-\s]?\d{3,4}[-\s]?\d{4}\b', '[TELÉFONO]', texto)
        return texto


class DocumentEmbedding(models.Model):
    """Almacena embeddings y metadatos de documentos indexados"""
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        verbose_name='Tipo de contenido'
    )
    object_id = models.PositiveIntegerField(verbose_name='ID del objeto')
    content_object = GenericForeignKey('content_type', 'object_id')
    
    texto_indexado = models.TextField(
        verbose_name='Texto indexado',
        help_text='Texto que fue convertido a embedding'
    )
    embedding_vector = models.BinaryField(
        verbose_name='Vector de embedding',
        help_text='Embedding serializado con pickle/numpy'
    )
    categoria = models.CharField(
        max_length=50, 
        verbose_name='Categoría',
        db_index=True,
        help_text='Categoría para filtrado (cursos, inscripciones, pagos, etc.)'
    )
    
    # Campos para chunking
    chunk_index = models.IntegerField(
        default=0,
        verbose_name='Índice del chunk',
        help_text='Posición del chunk dentro del documento original'
    )
    chunk_type = models.CharField(
        max_length=50,
        default='text',
        verbose_name='Tipo de chunk',
        help_text='Tipo de chunk (question, answer, combined, etc.)'
    )
    
    fecha_indexacion = models.DateTimeField(
        auto_now=True, 
        verbose_name='Fecha de indexación'
    )
    
    class Meta:
        verbose_name = 'Embedding de Documento'
        verbose_name_plural = 'Embeddings de Documentos'
        ordering = ['-fecha_indexacion']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['categoria']),
        ]
    
    def __str__(self):
        return f"{self.content_type} #{self.object_id} - {self.categoria}"
    
    def save_embedding(self, embedding_vector):
        """Guarda el vector de embedding serializado"""
        import pickle
        self.embedding_vector = pickle.dumps(embedding_vector)
        self.save(update_fields=['embedding_vector'])
