from django import forms

# ─────────────────────────────────────────────────────────────────────────────
# CalificarIntentoForm — Tarea 4.3
# Requisitos: 6.3, 6.5, 9.9, 9.10
# ─────────────────────────────────────────────────────────────────────────────

_TAILWIND_BASE = (
    'w-full border border-gray-300 rounded-lg px-3 py-2 '
    'focus:outline-none focus:ring-2 focus:ring-blue-500'
)


class CalificarIntentoForm(forms.ModelForm):
    """
    Formulario para que el Profesor o Secretaria califique un Intento
    de Evaluación_Libre manualmente.

    Campos:
    - puntaje: valor decimal entre 0 y 10 (Requisitos 6.3, 9.9)
    - comentario: texto opcional para el estudiante (Requisitos 6.5, 9.10)

    Valida que puntaje esté en el rango [0, 10].
    """

    class Meta:
        from evaluaciones.models import CalificacionEvaluacion  # importación local para evitar ciclos
        model = CalificacionEvaluacion
        fields = ['puntaje', 'comentario']
        widgets = {
            'puntaje': forms.NumberInput(attrs={
                'class': _TAILWIND_BASE,
                'placeholder': '0.00 - 10.00',
                'step': '0.01',
                'min': '0',
                'max': '10',
            }),
            'comentario': forms.Textarea(attrs={
                'class': _TAILWIND_BASE + ' resize-y',
                'rows': 4,
                'placeholder': 'Escribe un comentario para el estudiante...',
            }),
        }
        labels = {
            'puntaje': 'Puntaje (0 – 10)',
            'comentario': 'Comentario (opcional)',
        }

    def clean_puntaje(self):
        puntaje = self.cleaned_data.get('puntaje')
        if puntaje is not None and (puntaje < 0 or puntaje > 10):
            raise forms.ValidationError('El puntaje debe estar entre 0 y 10.')
        return puntaje


class ResponderEvaluacionForm(forms.Form):
    """
    Formulario dinámico para que un estudiante responda una evaluación.
    Genera campos según el tipo de cada pregunta.
    """

    def __init__(self, evaluacion, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evaluacion = evaluacion

        for pregunta in evaluacion.preguntas.all():
            field_name = f'pregunta_{pregunta.id}'
            opciones = [(str(op.id), op.texto) for op in pregunta.opciones.all()]

            if pregunta.tipo == 'opcion_multiple':
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=pregunta.texto,
                    choices=opciones,
                    required=False,
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'class': 'accent-blue-600',
                    }),
                )

            elif pregunta.tipo in ('seleccion_unica', 'verdadero_falso'):
                self.fields[field_name] = forms.ChoiceField(
                    label=pregunta.texto,
                    choices=[('', '— Selecciona una opción —')] + opciones,
                    required=False,
                    widget=forms.RadioSelect(attrs={
                        'class': 'accent-blue-600',
                    }),
                )

            elif pregunta.tipo == 'escritura_libre':
                self.fields[field_name] = forms.CharField(
                    label=pregunta.texto,
                    required=False,
                    widget=forms.Textarea(attrs={
                        'class': (
                            'w-full rounded-lg border border-gray-300 '
                            'p-3 text-sm focus:outline-none '
                            'focus:ring-2 focus:ring-blue-500'
                        ),
                        'rows': 5,
                        'placeholder': 'Escribe tu respuesta aquí…',
                    }),
                )

    def clean(self):
        cleaned_data = super().clean()

        for pregunta in self.evaluacion.preguntas.all():
            if not pregunta.requerida:
                continue

            field_name = f'pregunta_{pregunta.id}'
            value = cleaned_data.get(field_name)

            # MultipleChoiceField returns a list; ChoiceField/CharField return str
            if value is None or value == '' or value == [] or value == ['']:
                self.add_error(
                    field_name,
                    'Esta pregunta es requerida.',
                )

        return cleaned_data


# ─────────────────────────────────────────────────────────────────────────────
# EvaluacionForm — Tarea 4.1
# Requisitos: 2.1, 2.8
# ─────────────────────────────────────────────────────────────────────────────

TAILWIND_INPUT = (
    'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm '
    'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
)


class EvaluacionForm(forms.ModelForm):
    """
    Formulario para crear y editar una Evaluación.

    Campos: titulo, descripcion, tipo, estado, fecha_limite.
    Valida que el título no esté vacío (Requisito 2.8).
    """

    class Meta:
        from evaluaciones.models import Evaluacion  # importación local para evitar ciclos
        model = Evaluacion
        fields = ['titulo', 'descripcion', 'tipo', 'estado', 'fecha_limite']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Título de la evaluación',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': TAILWIND_INPUT,
                'rows': 4,
                'placeholder': 'Descripción opcional de la evaluación',
            }),
            'tipo': forms.Select(attrs={
                'class': TAILWIND_INPUT,
            }),
            'estado': forms.Select(attrs={
                'class': TAILWIND_INPUT,
            }),
            'fecha_limite': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={
                    'type': 'datetime-local',
                    'class': TAILWIND_INPUT,
                },
            ),
        }
        labels = {
            'titulo': 'Título',
            'descripcion': 'Descripción',
            'tipo': 'Tipo de evaluación',
            'estado': 'Estado',
            'fecha_limite': 'Fecha límite de entrega',
        }

    def clean(self):
        cleaned_data = super().clean()
        titulo = cleaned_data.get('titulo', '')
        if not titulo or not titulo.strip():
            raise forms.ValidationError(
                'El título de la evaluación es obligatorio.'
            )
        return cleaned_data


# ──────────────────────────────────────────────────────────────────────────────
# PreguntaEvaluacionForm y OpcionEvaluacionForm — Tarea 4.2
# Requisitos: 2.2, 2.3, 2.5, 2.9
# ──────────────────────────────────────────────────────────────────────────────

class PreguntaEvaluacionForm(forms.ModelForm):
    """
    Formulario para una pregunta dentro de una Evaluación.
    Campos: texto, tipo, requerida, orden.
    Requisitos: 2.2, 2.3
    """

    class Meta:
        from evaluaciones.models import PreguntaEvaluacion  # importación local
        model = PreguntaEvaluacion
        fields = ['texto', 'tipo', 'requerida', 'orden']
        widgets = {
            'texto': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Texto de la pregunta',
            }),
            'tipo': forms.Select(attrs={
                'class': TAILWIND_INPUT,
            }),
            'requerida': forms.CheckboxInput(attrs={
                'class': (
                    'rounded border-gray-300 text-blue-600 shadow-sm '
                    'focus:border-blue-300 focus:ring focus:ring-blue-200 '
                    'focus:ring-opacity-50'
                ),
            }),
            'orden': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'min': 0,
                'placeholder': 'Orden',
            }),
        }
        labels = {
            'texto': 'Texto de la pregunta',
            'tipo': 'Tipo',
            'requerida': 'Requerida',
            'orden': 'Orden',
        }


class OpcionEvaluacionForm(forms.ModelForm):
    """
    Formulario para una opción de respuesta dentro de una PreguntaEvaluacion.
    Campos: texto, es_correcta, orden.
    Requisitos: 2.5
    """

    class Meta:
        from evaluaciones.models import OpcionEvaluacion  # importación local
        model = OpcionEvaluacion
        fields = ['texto', 'es_correcta', 'orden']
        widgets = {
            'texto': forms.TextInput(attrs={
                'class': TAILWIND_INPUT,
                'placeholder': 'Texto de la opción',
            }),
            'es_correcta': forms.CheckboxInput(attrs={
                'class': (
                    'rounded border-gray-300 text-blue-600 shadow-sm '
                    'focus:border-blue-300 focus:ring focus:ring-blue-200 '
                    'focus:ring-opacity-50'
                ),
            }),
            'orden': forms.NumberInput(attrs={
                'class': TAILWIND_INPUT,
                'min': 0,
                'placeholder': 'Orden',
            }),
        }
        labels = {
            'texto': 'Texto de la opción',
            'es_correcta': 'Es correcta',
            'orden': 'Orden',
        }


# ──────────────────────────────────────────────────────────────────────────────
# OpcionEvaluacionFormSet
# inlineformset_factory(PreguntaEvaluacion, OpcionEvaluacion, ...)
# extra=2, can_delete=True
# Requisitos: 2.5
# ──────────────────────────────────────────────────────────────────────────────

from django.forms import inlineformset_factory
from evaluaciones.models import Evaluacion, PreguntaEvaluacion, OpcionEvaluacion

OpcionEvaluacionFormSet = inlineformset_factory(
    PreguntaEvaluacion,
    OpcionEvaluacion,
    form=OpcionEvaluacionForm,
    extra=2,
    can_delete=True,
)


# ──────────────────────────────────────────────────────────────────────────────
# PreguntaEvaluacionFormSet
# inlineformset_factory(Evaluacion, PreguntaEvaluacion, ...)
# extra=1, can_delete=True, sin límite de preguntas
# Validación: preguntas de opción múltiple/única deben tener al menos una
# opción y al menos una opción correcta (Requisitos 2.9)
# ──────────────────────────────────────────────────────────────────────────────

def _make_pregunta_evaluacion_formset():
    _BaseFormSet = inlineformset_factory(
        Evaluacion,
        PreguntaEvaluacion,
        form=PreguntaEvaluacionForm,
        extra=1,
        can_delete=True,
    )

    class PreguntaEvaluacionFormSetWithValidation(_BaseFormSet):
        """
        Formset para preguntas de evaluación.
        La validación de opciones se delega a _guardar_opciones_desde_post
        en la vista, ya que las opciones llegan como campos hidden del JS
        y no están disponibles en el ciclo de validación del formset.
        """
        pass

    return PreguntaEvaluacionFormSetWithValidation


PreguntaEvaluacionFormSet = _make_pregunta_evaluacion_formset()
