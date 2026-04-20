from django import forms
from .models import Comentario, Noticia, Categoria

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
            'categoria', 'estado', 'visibilidad', 'destacada', 'fecha_publicacion', 
            'meta_descripcion'
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
            'fecha_publicacion': 'Fecha de publicación',
            'meta_descripcion': 'Meta descripción (SEO)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear la fecha para el input datetime-local
        if self.instance and self.instance.fecha_publicacion:
            self.initial['fecha_publicacion'] = self.instance.fecha_publicacion.strftime('%Y-%m-%dT%H:%M')