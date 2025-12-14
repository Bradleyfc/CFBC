from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
import re
import os

from .models import DocumentFolder, CourseDocument


class DocumentFolderForm(forms.ModelForm):
    """
    Formulario para crear carpetas de documentos
    """
    
    class Meta:
        model = DocumentFolder
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la carpeta (máximo 200 caracteres)',
                'maxlength': 200,
                'required': True,
                'data-bs-toggle': 'tooltip',
                'title': 'Máximo 200 caracteres. No se permiten: < > : " / \\ | ? *'
            })
        }
        labels = {
            'name': 'Nombre de la carpeta'
        }
    
    def clean_name(self):
        """Validar nombre de carpeta"""
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError("El nombre de la carpeta es requerido.")
        
        # Eliminar espacios al inicio y final
        name = name.strip()
        
        if not name:
            raise ValidationError("El nombre de la carpeta no puede estar vacío o contener solo espacios.")
        
        # Verificar caracteres no permitidos
        forbidden_chars = r'[<>:"/\\|?*]'
        if re.search(forbidden_chars, name):
            raise ValidationError(
                "El nombre de la carpeta contiene caracteres no permitidos: < > : \" / \\ | ? *"
            )
        
        # Verificar longitud
        if len(name) > 200:
            raise ValidationError("El nombre de la carpeta no puede exceder 200 caracteres.")
        
        return name


class CourseDocumentForm(forms.ModelForm):
    """
    Formulario para subir documentos
    """
    
    # Tipos de archivo permitidos
    ALLOWED_EXTENSIONS = [
        'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 
        'txt', 'zip', 'rar', '7z', 'jpg', 'jpeg', 'png', 'gif'
    ]
    
    # Tamaño máximo de archivo (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB en bytes
    
    class Meta:
        model = CourseDocument
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del documento (máximo 200 caracteres)',
                'maxlength': 200,
                'required': True,
                'data-bs-toggle': 'tooltip',
                'title': 'Máximo 200 caracteres'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.zip,.rar,.7z,.jpg,.jpeg,.png,.gif',
                'required': True,
                'data-bs-toggle': 'tooltip',
                'title': 'Tamaño máximo: 50MB. Tipos permitidos: PDF, DOC, PPT, XLS, TXT, ZIP, imágenes'
            })
        }
        labels = {
            'name': 'Nombre del documento',
            'file': 'Archivo'
        }
    
    def clean_name(self):
        """Validar nombre del documento"""
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError("El nombre del documento es requerido.")
        
        # Eliminar espacios al inicio y final
        name = name.strip()
        
        if not name:
            raise ValidationError("El nombre del documento no puede estar vacío o contener solo espacios.")
        
        # Verificar longitud
        if len(name) > 200:
            raise ValidationError("El nombre del documento no puede exceder 200 caracteres.")
        
        return name
    
    def clean_file(self):
        """Validar archivo subido"""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise ValidationError("Debe seleccionar un archivo.")
        
        # Verificar tamaño del archivo
        if file.size > self.MAX_FILE_SIZE:
            size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(f"El archivo es demasiado grande. Tamaño máximo permitido: {size_mb:.0f}MB")
        
        # Verificar extensión del archivo
        file_extension = self.get_file_extension(file.name)
        if file_extension not in self.ALLOWED_EXTENSIONS:
            allowed_extensions_str = ', '.join(self.ALLOWED_EXTENSIONS)
            raise ValidationError(
                f"Tipo de archivo no permitido. Extensiones permitidas: {allowed_extensions_str}"
            )
        
        # Verificar que el archivo no esté vacío
        if file.size == 0:
            raise ValidationError("El archivo está vacío.")
        
        return file
    
    def get_file_extension(self, filename):
        """Obtener extensión del archivo en minúsculas"""
        if not filename:
            return ''
        
        # Obtener la extensión y convertir a minúsculas
        _, extension = os.path.splitext(filename)
        return extension.lower().lstrip('.')
    
    def clean(self):
        """Validación adicional del formulario"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        file = cleaned_data.get('file')
        
        # Si no se proporciona nombre, usar el nombre del archivo
        if file and not name:
            # Usar el nombre del archivo sin extensión como nombre por defecto
            filename_without_ext = os.path.splitext(file.name)[0]
            cleaned_data['name'] = filename_without_ext
        
        return cleaned_data


class BulkUploadForm(forms.Form):
    """
    Formulario para subida masiva de documentos (futuro)
    """
    # Usar un campo personalizado para múltiples archivos
    files = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        help_text='Formulario para subida masiva - implementación futura'
    )
    
    def clean_files(self):
        """Validar archivos múltiples - implementación futura"""
        # Por ahora, este formulario es solo un placeholder
        return self.cleaned_data.get('files', '')