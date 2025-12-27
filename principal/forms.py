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
    OpcionRespuesta, RespuestaEstudiante, CursoAcademico
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
    nacionalidad = forms.CharField(max_length=150, required=True, label='Nacionalidad')
    carnet = forms.CharField(max_length=11, required=True, label='Carnet')
    foto_carnet = forms.ImageField(required=False, label='Foto del Carnet')
    
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino')
    ]
    sexo = forms.ChoiceField(choices=SEXO_CHOICES, initial='M', label='Sexo')
    
    image = forms.ImageField(required=False, label='Imagen de perfil')
    address = forms.CharField(max_length=150, required=True, label='Dirección')
    location = forms.CharField(max_length=150, required=True, label='Municipio')
    provincia = forms.CharField(max_length=150, required=True, label='Provincia')
    telephone = forms.CharField(max_length=50, required=False, label='Teléfono')
    movil = forms.CharField(max_length=50, required=True, label='Móvil')
    
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
    
    titulo = forms.CharField(max_length=150, required=True, label='Título')
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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(f"El nombre de usuario '{username}' ya existe en la base de datos.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(f"El correo electrónico '{email}' ya está registrado en la base de datos.")
        return email

    def clean_carnet(self):
        carnet = self.cleaned_data.get('carnet')
        if not carnet or not carnet.strip():
            raise forms.ValidationError("El carnet es obligatorio.")
        if Registro.objects.filter(carnet=carnet).exists():
            raise forms.ValidationError(f"El número de carnet '{carnet}' ya está registrado en la base de datos.")
        return carnet

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        
        return password2

    def clean(self):
        cleaned_data = super().clean()
        
        # Validar campos obligatorios
        required_fields = {
            'username': 'nombre de usuario',
            'first_name': 'nombre',
            'last_name': 'apellidos', 
            'email': 'correo electrónico',
            'password1': 'contraseña',
            'password2': 'confirmación de contraseña',
            'nacionalidad': 'nacionalidad',
            'carnet': 'carnet',
            'address': 'dirección',
            'location': 'municipio',
            'provincia': 'provincia',
            'movil': 'móvil',
            'titulo': 'título'
        }
        
        missing_fields = []
        for field_name, field_label in required_fields.items():
            if not cleaned_data.get(field_name):
                missing_fields.append(field_label)
        
        if missing_fields:
            raise forms.ValidationError(f"Los siguientes campos obligatorios están vacíos: {', '.join(missing_fields)}.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Actualizar el registro existente creado por la señal
            try:
                registro = user.registro
                registro.nacionalidad = self.cleaned_data.get('nacionalidad', '')
                registro.carnet = self.cleaned_data.get('carnet', '')
                registro.foto_carnet = self.cleaned_data.get('foto_carnet') or registro.foto_carnet
                registro.sexo = self.cleaned_data.get('sexo', 'M')
                registro.image = self.cleaned_data.get('image') or registro.image
                registro.address = self.cleaned_data.get('address', '')
                registro.location = self.cleaned_data.get('location', '')
                registro.provincia = self.cleaned_data.get('provincia', '')
                registro.telephone = self.cleaned_data.get('telephone', '')
                registro.movil = self.cleaned_data.get('movil', '')
                registro.grado = self.cleaned_data.get('grado', 'grado1')
                registro.ocupacion = self.cleaned_data.get('ocupacion', 'ocupacion1')
                registro.titulo = self.cleaned_data.get('titulo', '')
                registro.foto_titulo = self.cleaned_data.get('foto_titulo') or registro.foto_titulo
                registro.es_religioso = self.cleaned_data.get('es_religioso', False)
                registro.save()
            except Registro.DoesNotExist:
                # Si por alguna razón no existe el registro, crearlo
                Registro.objects.create(
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
    enrollment_deadline = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'glass-input-compact'
        }),
        required=False,
        label='Fecha límite de inscripción'
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'glass-input-compact'
        }),
        required=False,
        label='Fecha de inicio del curso'
    )
    
    class Meta:
        model = Curso
        exclude = ['curso_academico']  # Excluir curso_academico ya que se asigna automáticamente
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Asignar automáticamente el curso académico activo
        try:
            curso_academico_activo = CursoAcademico.objects.get(activo=True)
            instance.curso_academico = curso_academico_activo
        except CursoAcademico.DoesNotExist:
            # Si no hay curso académico activo, crear uno para el año actual
            from datetime import datetime
            current_year = datetime.now().year
            next_year = current_year + 1
            nombre_curso = f"{current_year}-{next_year}"
            
            curso_academico_activo, created = CursoAcademico.objects.get_or_create(
                nombre=nombre_curso,
                defaults={'activo': True}
            )
            instance.curso_academico = curso_academico_activo
        
        if commit:
            instance.save()
        
        return instance


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


class RespuestaEstudianteForm(forms.Form):
    """
    Formulario dinámico para respuestas de estudiantes
    """
    def __init__(self, *args, **kwargs):
        # Extraer el parámetro pregunta si existe
        self.pregunta = kwargs.pop('pregunta', None)
        super().__init__(*args, **kwargs)
        
        # Si se proporciona una pregunta, configurar el formulario según el tipo
        if self.pregunta:
            self.configure_for_question()
    
    def configure_for_question(self):
        """Configura el formulario según el tipo de pregunta"""
        field_name = f'pregunta_{self.pregunta.id}'
        
        if self.pregunta.tipo == 'escritura_libre':
            # Para preguntas de escritura libre, crear un campo de texto
            self.fields[field_name] = forms.CharField(
                widget=forms.Textarea(attrs={
                    'rows': 3,
                    'class': 'form-control',
                    'placeholder': 'Escribe tu respuesta aquí...'
                }),
                required=self.pregunta.requerida,
                label=''
            )
        elif self.pregunta.tipo == 'seleccion_unica':
            # Para selección única, crear campo de radio buttons
            opciones = [(opcion.id, opcion.texto) for opcion in self.pregunta.opciones.all()]
            self.fields[field_name] = forms.ChoiceField(
                choices=opciones,
                widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
                required=self.pregunta.requerida,
                label=''
            )
        elif self.pregunta.tipo == 'seleccion_multiple':
            # Para selección múltiple, crear campo de checkboxes
            opciones = [(opcion.id, opcion.texto) for opcion in self.pregunta.opciones.all()]
            self.fields[field_name] = forms.MultipleChoiceField(
                choices=opciones,
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
                required=self.pregunta.requerida,
                label=''
            )