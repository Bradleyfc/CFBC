from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, HTML, Div, Row, Column
from crispy_forms.bootstrap import InlineRadios
from django.forms import inlineformset_factory, modelformset_factory


# Importar modelos necesarios
from .models import (
    Curso, Calificaciones, NotaIndividual, FormularioAplicacion, PreguntaFormulario,
    OpcionRespuesta, RespuestaEstudiante
)
from accounts.models import Registro


class CustomUserCreationForm(UserCreationForm):
    """
    Formulario de registro de usuario personalizado con todos los campos del modelo Registro
    """
    # Campos del User model
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellidos')
    email = forms.EmailField(required=True, label='Correo Electrónico')
    
    # Campos del Registro model
    nacionalidad = forms.CharField(max_length=150, required=False, label='Nacionalidad')
    carnet = forms.CharField(max_length=11, required=False, label='Carnet')
    foto_carnet = forms.ImageField(required=False, label='Foto del Carnet')
    
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino')
    ]
    sexo = forms.ChoiceField(choices=SEXO_CHOICES, initial='M', label='Sexo')
    
    image = forms.ImageField(required=False, label='Imagen de perfil')
    address = forms.CharField(max_length=150, required=False, label='Dirección')
    location = forms.CharField(max_length=150, required=False, label='Municipio')
    provincia = forms.CharField(max_length=150, required=False, label='Provincia')
    telephone = forms.CharField(max_length=50, required=False, label='Teléfono')
    movil = forms.CharField(max_length=50, required=False, label='Móvil')
    
    GRADO_CHOICES = [
        ("grado1", "Ninguno"),
        ("grado2", "Noveno Grado"),
        ("grado3", "Bachiller"),
        ("grado4", "Superior"),
    ]
    grado = forms.ChoiceField(choices=GRADO_CHOICES, initial="grado1", label='Grado Académico')
    
    OCUPACION_CHOICES = [
        ("ocupacion1", "Desocupado"),
        ("ocupacion2", "Estudiante"),
        ("ocupacion3", "Ama de Casa"),
        ("ocupacion4", "Trabajador Estatal"),
        ("ocupacion5", "Trabajador por Cuenta Propia"),
    ]
    ocupacion = forms.ChoiceField(choices=OCUPACION_CHOICES, initial="ocupacion1", label='Ocupación')
    
    titulo = forms.CharField(max_length=150, required=False, label='Título')
    foto_titulo = forms.ImageField(required=False, label='Foto del Título')
    es_religioso = forms.BooleanField(required=False, label='Es Religioso')
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar clases de Tailwind a todos los campos
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50'
                })
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Crear el registro asociado
            registro = Registro.objects.create(
                user=user,
                nacionalidad=self.cleaned_data.get('nacionalidad', ''),
                carnet=self.cleaned_data.get('carnet', ''),
                foto_carnet=self.cleaned_data.get('foto_carnet'),
                sexo=self.cleaned_data.get('sexo', 'M'),
                image=self.cleaned_data.get('image'),
                address=self.cleaned_data.get('address', ''),
                location=self.cleaned_data.get('location', ''),
                provincia=self.cleaned_data.get('provincia', ''),
                telephone=self.cleaned_data.get('telephone', ''),
                movil=self.cleaned_data.get('movil', ''),
                grado=self.cleaned_data.get('grado', 'grado1'),
                ocupacion=self.cleaned_data.get('ocupacion', 'ocupacion1'),
                titulo=self.cleaned_data.get('titulo', ''),
                foto_titulo=self.cleaned_data.get('foto_titulo'),
                es_religioso=self.cleaned_data.get('es_religioso', False),
            )
        
        return user


class CustomLoginForm(AuthenticationForm):
    """
    Formulario de login personalizado con crispy forms y Tailwind CSS
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'max-w-md mx-auto'
        
        # Personalizar campos
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Ingrese su nombre de usuario'
        })
        
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Ingrese su contraseña'
        })


class CourseForm(forms.ModelForm):
    """
    Formulario para crear y editar cursos
    """
    class Meta:
        model = Curso
        fields = '__all__'


class CalificacionesForm(forms.ModelForm):
    """
    Formulario para calificaciones
    """
    class Meta:
        model = Calificaciones
        fields = '__all__'


# Formset para notas individuales
NotaIndividualFormSet = modelformset_factory(
    NotaIndividual,
    fields=('valor',),
    extra=0
)


class FormularioAplicacionForm(forms.ModelForm):
    """
    Formulario para aplicaciones de formularios
    """
    class Meta:
        model = FormularioAplicacion
        fields = '__all__'


class PreguntaFormularioForm(forms.ModelForm):
    """
    Formulario para preguntas de formulario
    """
    class Meta:
        model = PreguntaFormulario
        fields = '__all__'


class OpcionRespuestaForm(forms.ModelForm):
    """
    Formulario para opciones de respuesta
    """
    class Meta:
        model = OpcionRespuesta
        fields = '__all__'


# Formsets
OpcionRespuestaFormSet = inlineformset_factory(
    PreguntaFormulario,
    OpcionRespuesta,
    form=OpcionRespuestaForm,
    extra=1,
    can_delete=True
)

PreguntaFormularioFormSet = inlineformset_factory(
    FormularioAplicacion,
    PreguntaFormulario,
    form=PreguntaFormularioForm,
    extra=1,
    can_delete=True
)


class RespuestaEstudianteForm(forms.ModelForm):
    """
    Formulario para respuestas de estudiantes
    """
    class Meta:
        model = RespuestaEstudiante
        fields = '__all__'