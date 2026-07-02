from django import forms
from django.core.exceptions import ValidationError
from .models import Comentario, Noticia, Categoria

# --- 2.1: Validador de imagen para el formulario del autor ---

EXTENSIONES_VALIDAS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MIMES_VALIDOS = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
LIMITE_BYTES = 5 * 1024 * 1024  # 5 MB


def validar_imagen_autor(imagen):
    extension = imagen.name.rsplit('.', 1)[-1].lower()
    if extension not in EXTENSIONES_VALIDAS:
        raise ValidationError(
            f'Extensión ".{extension}" no permitida. '
            'Use jpg, jpeg, png, gif o webp.'
        )
    if imagen.content_type not in MIMES_VALIDOS:
        raise ValidationError(
            f'Tipo de imagen "{imagen.content_type}" no permitido. '
            'Se aceptan imágenes JPEG, PNG, GIF o WebP.'
        )
    if imagen.size > LIMITE_BYTES:
        raise ValidationError(
            f'La imagen supera el límite de 5 MB '
            f'({imagen.size / (1024 * 1024):.1f} MB).'
        )

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu comentario aquí...'
            })
        }
        labels = {
            'contenido': 'Comentario'
        }

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = [
            'titulo', 'resumen', 'contenido', 'imagen_principal', 
            'categoria', 'estado', 'visibilidad', 'destacada', 'permitir_comentarios',
            'fecha_publicacion', 'meta_descripcion'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la noticia'
            }),
            'resumen': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Breve resumen de la noticia (máximo 300 caracteres)'
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Contenido completo de la noticia'
            }),
            'imagen_principal': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'visibilidad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'destacada': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'permitir_comentarios': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'fecha_publicacion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'meta_descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción para SEO (máximo 160 caracteres)'
            })
        }
        labels = {
            'titulo': 'Título',
            'resumen': 'Resumen',
            'contenido': 'Contenido',
            'imagen_principal': 'Imagen principal',
            'categoria': 'Categoría',
            'estado': 'Estado',
            'visibilidad': 'Visibilidad',
            'destacada': 'Noticia destacada',
            'permitir_comentarios': 'Permitir comentarios',
            'fecha_publicacion': 'Fecha de publicación',
            'meta_descripcion': 'Meta descripción (SEO)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear la fecha para el input datetime-local
        if self.instance and self.instance.fecha_publicacion:
            self.initial['fecha_publicacion'] = self.instance.fecha_publicacion.strftime('%Y-%m-%dT%H:%M')


# --- 2.2: Formulario del autor para crear/editar noticias ---

class AutorNoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = [
            'titulo', 'resumen', 'contenido',
            'imagen_principal', 'categoria',
            'fecha_publicacion',
        ]
        # Excluye: estado, autor, visibilidad, destacada,
        #          permitir_comentarios, meta_descripcion, notas_editor, slug
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la noticia',
            }),
            'resumen': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Breve resumen de la noticia (máximo 300 caracteres)',
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Contenido completo de la noticia',
            }),
            'imagen_principal': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select',
            }),
            'fecha_publicacion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
        }
        labels = {
            'titulo': 'Título',
            'resumen': 'Resumen',
            'contenido': 'Contenido',
            'imagen_principal': 'Imagen principal',
            'categoria': 'Categoría',
            'fecha_publicacion': 'Fecha de publicación',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear la fecha para el input datetime-local
        if self.instance and self.instance.fecha_publicacion:
            self.initial['fecha_publicacion'] = self.instance.fecha_publicacion.strftime('%Y-%m-%dT%H:%M')

    def clean_imagen_principal(self):
        imagen = self.cleaned_data.get('imagen_principal')
        if imagen and hasattr(imagen, 'name'):
            validar_imagen_autor(imagen)
        return imagen


# --- 2.3: Formulario del editor para revisar noticias ---

class EditorRevisionForm(forms.Form):
    notas_editor = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'glass-input',
            'placeholder': 'Escribe las correcciones para el autor...',
        }),
        required=False,
        max_length=1000,
        label='Notas para el autor',
    )
