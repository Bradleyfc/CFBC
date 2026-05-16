from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone

from .models import Evaluacion, IntentoEvaluacion, CalificacionEvaluacion, PreguntaEvaluacion, OpcionEvaluacion
from .forms import EvaluacionForm, PreguntaEvaluacionFormSet, CalificarIntentoForm, ResponderEvaluacionForm


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_curso_or_404(curso_id):
    from principal.models import Curso
    return get_object_or_404(Curso, pk=curso_id)


def _build_opciones_json(evaluacion):
    """
    Devuelve un dict {pregunta_pk: [{"id":..,"texto":..,"es_correcta":..,"orden":..}]}
    serializado como JSON string, listo para embeber en el template.
    """
    import json
    data = {}
    for pregunta in evaluacion.preguntas.prefetch_related('opciones').all():
        data[str(pregunta.pk)] = [
            {
                'id': op.id,
                'texto': op.texto,
                'es_correcta': op.es_correcta,
                'orden': op.orden,
            }
            for op in pregunta.opciones.all()
        ]
    return json.dumps(data, ensure_ascii=False)


def _guardar_opciones_desde_post(request, evaluacion):
    """
    Procesa los campos hidden opcion_preguntas-N-M_texto / _correcta
    enviados por el template crear_editar.html y crea las OpcionEvaluacion
    correspondientes para cada pregunta guardada.

    Maneja dos casos:
    - Pregunta existente: preguntas-N-id tiene el PK en el POST
    - Pregunta nueva: preguntas-N-id está vacío, se busca la pregunta
      por su texto (que también viene en preguntas-N-texto)
    """
    import re

    patron = re.compile(r'^opcion_(preguntas-\d+)_(\d+)_texto$')
    grupos = {}
    for key, val in request.POST.items():
        m = patron.match(key)
        if m:
            prefix = m.group(1)
            idx = int(m.group(2))
            if prefix not in grupos:
                grupos[prefix] = {}
            grupos[prefix][idx] = {
                'texto': val.strip(),
                'correcta': request.POST.get(f'opcion_{prefix}_{idx}_correcta', '0') == '1',
            }

    for prefix, opciones_dict in grupos.items():
        # Intentar obtener la pregunta por PK (preguntas existentes)
        pk_val = request.POST.get(f'{prefix}-id', '').strip()
        pregunta = None

        if pk_val:
            try:
                pregunta = PreguntaEvaluacion.objects.get(pk=int(pk_val), evaluacion=evaluacion)
            except (PreguntaEvaluacion.DoesNotExist, ValueError):
                pregunta = None

        if pregunta is None:
            # Pregunta nueva: buscar por texto dentro de esta evaluación
            texto_pregunta = request.POST.get(f'{prefix}-texto', '').strip()
            if texto_pregunta:
                pregunta = (
                    PreguntaEvaluacion.objects
                    .filter(evaluacion=evaluacion, texto=texto_pregunta)
                    .first()
                )

        if pregunta is None:
            continue

        if pregunta.tipo not in ('opcion_multiple', 'seleccion_unica', 'verdadero_falso'):
            continue

        pregunta.opciones.all().delete()
        for idx in sorted(opciones_dict.keys()):
            datos = opciones_dict[idx]
            if not datos['texto']:
                continue
            OpcionEvaluacion.objects.create(
                pregunta=pregunta,
                texto=datos['texto'],
                es_correcta=datos['correcta'],
                orden=idx,
            )


def _registrar_nota_en_calificaciones(estudiante, curso, puntaje):
    """
    Crea una NotaIndividual en el registro de Calificaciones del estudiante
    para el curso dado. Si no existe el registro de Calificaciones, lo crea.
    """
    from principal.models import Calificaciones, NotaIndividual, CursoAcademico
    from decimal import Decimal

    curso_academico = curso.curso_academico or CursoAcademico.objects.filter(activo=True).first()

    calificacion_obj, _ = Calificaciones.objects.get_or_create(
        course=curso,
        student=estudiante,
        curso_academico=curso_academico,
    )

    NotaIndividual.objects.create(
        calificacion=calificacion_obj,
        valor=Decimal(str(puntaje)),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6.1  EvaluacionListView

class EvaluacionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Evaluacion
    template_name = 'evaluaciones/profesor/lista.html'
    context_object_name = 'evaluaciones'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.curso = _get_curso_or_404(kwargs['curso_id'])

    def test_func(self):
        return self.request.user == self.curso.teacher

    def get_queryset(self):
        return Evaluacion.objects.filter(curso=self.curso).order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curso'] = self.curso
        evaluaciones = context['evaluaciones']
        pendientes_por_eval = {}
        for ev in evaluaciones:
            if ev.tipo == 'libre':
                pendientes_por_eval[ev.pk] = ev.intentos.filter(estado='enviado').count()
            else:
                pendientes_por_eval[ev.pk] = 0
        context['pendientes_por_eval'] = pendientes_por_eval
        context['total_pendientes'] = sum(pendientes_por_eval.values())
        return context


# ─────────────────────────────────────────────────────────────────────────────
# 6.2  EvaluacionCreateView  (funcion)
# Requirements: 2.1, 2.2, 2.6, 2.7, 2.9
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def evaluacion_create(request, curso_id):
    curso = _get_curso_or_404(curso_id)

    if request.user != curso.teacher:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if request.method == 'POST':
        form = EvaluacionForm(request.POST)
        formset = PreguntaEvaluacionFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            preguntas_validas = [
                f for f in formset.forms
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
            ]
            if not preguntas_validas:
                messages.error(request, 'Debes agregar al menos una pregunta a la evaluacion.')
            else:
                evaluacion = form.save(commit=False)
                evaluacion.curso = curso
                evaluacion.save()
                formset.instance = evaluacion
                formset.save()
                _guardar_opciones_desde_post(request, evaluacion)
                messages.success(request, f'Evaluacion "{evaluacion.titulo}" creada correctamente.')
                return redirect('evaluaciones:lista_curso', curso_id=curso.pk)
    else:
        form = EvaluacionForm()
        formset = PreguntaEvaluacionFormSet()

    return render(request, 'evaluaciones/profesor/crear_editar.html', {
        'form': form,
        'formset': formset,
        'curso': curso,
        'accion': 'Crear',
        'titulo': 'Nueva Evaluacion',
        'opciones_json': '{}',
    })


# ─────────────────────────────────────────────────────────────────────────────
# 6.3  EvaluacionUpdateView  (funcion)
# Requirements: 2.10
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def evaluacion_update(request, pk):
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    curso = evaluacion.curso

    if request.user != curso.teacher:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    if request.method == 'POST':
        form = EvaluacionForm(request.POST, instance=evaluacion)
        formset = PreguntaEvaluacionFormSet(request.POST, instance=evaluacion)

        if form.is_valid() and formset.is_valid():
            preguntas_validas = [
                f for f in formset.forms
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
            ]
            if not preguntas_validas:
                messages.error(request, 'Debes mantener al menos una pregunta en la evaluacion.')
            else:
                form.save()
                formset.save()
                _guardar_opciones_desde_post(request, evaluacion)
                messages.success(request, f'Evaluacion "{evaluacion.titulo}" actualizada correctamente.')
                return redirect('evaluaciones:lista_curso', curso_id=curso.pk)
    else:
        form = EvaluacionForm(instance=evaluacion)
        formset = PreguntaEvaluacionFormSet(instance=evaluacion)

    return render(request, 'evaluaciones/profesor/crear_editar.html', {
        'form': form,
        'formset': formset,
        'curso': curso,
        'evaluacion': evaluacion,
        'accion': 'Editar',
        'titulo': f'Editar: {evaluacion.titulo}',
        'opciones_json': _build_opciones_json(evaluacion),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 6.4  EvaluacionDeleteView
# Requirements: 2.11, 2.12
# ─────────────────────────────────────────────────────────────────────────────

class EvaluacionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Evaluacion
    template_name = 'evaluaciones/profesor/confirmar_eliminar.html'

    def test_func(self):
        evaluacion = self.get_object()
        return self.request.user == evaluacion.curso.teacher

    def get_success_url(self):
        return reverse('evaluaciones:lista_curso', kwargs={'curso_id': self.object.curso.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        titulo = self.object.titulo
        curso_id = self.object.curso.pk
        self.object.delete()
        messages.success(request, f'Evaluación "{titulo}" eliminada correctamente.')
        return redirect('evaluaciones:lista_curso', curso_id=curso_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curso'] = self.object.curso
        context['num_intentos'] = self.object.intentos.count()
        return context


# ─────────────────────────────────────────────────────────────────────────────
# 6.5  IntentoListView
# Requirements: 6.1, 6.2
# ─────────────────────────────────────────────────────────────────────────────

class IntentoListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = IntentoEvaluacion
    template_name = 'evaluaciones/profesor/intentos_lista.html'
    context_object_name = 'intentos'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.evaluacion = get_object_or_404(Evaluacion, pk=kwargs['pk'])

    def test_func(self):
        return self.request.user == self.evaluacion.curso.teacher

    def get_queryset(self):
        return (
            IntentoEvaluacion.objects
            .filter(evaluacion=self.evaluacion)
            .select_related('estudiante')
            .order_by('-fecha_envio')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evaluacion'] = self.evaluacion
        context['curso'] = self.evaluacion.curso
        context['pendientes'] = self.get_queryset().filter(estado='enviado').count()
        return context


# ─────────────────────────────────────────────────────────────────────────────
# 6.5  CalificarIntentoView  (funcion)
# Requirements: 6.3, 6.4, 6.5, 6.6
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def calificar_intento(request, pk):
    intento = get_object_or_404(
        IntentoEvaluacion.objects.select_related('evaluacion__curso', 'estudiante'),
        pk=pk
    )
    evaluacion = intento.evaluacion
    curso = evaluacion.curso

    if request.user != curso.teacher:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    calificacion_existente = getattr(intento, 'calificacion', None)

    respuestas = (
        intento.respuestas
        .select_related('pregunta')
        .prefetch_related('opciones_seleccionadas')
        .order_by('pregunta__orden')
    )

    if request.method == 'POST':
        form = CalificarIntentoForm(request.POST, instance=calificacion_existente)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.intento = intento
            calificacion.es_automatica = False
            calificacion.save()

            intento.estado = 'calificado'
            intento.save(update_fields=['estado'])

            # Guardar también como NotaIndividual en el sistema de calificaciones existente
            _registrar_nota_en_calificaciones(intento.estudiante, curso, calificacion.puntaje)

            nombre = intento.estudiante.get_full_name() or intento.estudiante.username
            messages.success(request, f'Respuesta de {nombre} calificada y nota registrada en calificaciones.')
            return redirect('evaluaciones:intentos_lista', pk=evaluacion.pk)
    else:
        form = CalificarIntentoForm(instance=calificacion_existente)

    return render(request, 'evaluaciones/profesor/calificar_intento.html', {
        'intento': intento,
        'evaluacion': evaluacion,
        'curso': curso,
        'respuestas': respuestas,
        'form': form,
        'calificacion_existente': calificacion_existente,
    })


# ────────────────────────────────────────────────────────────────────────────
# 7.1  EvaluacionEstudianteListView
# Requirements: 3.1, 3.2, 3.3, 3.4
# ────────────────────────────────────────────────────────────────────────────

class EvaluacionEstudianteListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Evaluacion
    template_name = 'evaluaciones/estudiante/lista.html'
    context_object_name = 'evaluaciones'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.curso = _get_curso_or_404(kwargs['curso_id'])

    def test_func(self):
        from principal.models import Matriculas
        return Matriculas.objects.filter(
            course=self.curso,
            student=self.request.user,
            activo=True,
        ).exists()

    def get_queryset(self):
        return Evaluacion.objects.filter(
            curso=self.curso,
            estado='publicada',
        ).order_by('-fecha_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curso'] = self.curso
        ahora = timezone.now()

        evaluaciones_info = []
        for ev in context['evaluaciones']:
            cerrada = ev.fecha_limite is not None and ahora > ev.fecha_limite
            try:
                intento = ev.intentos.get(estudiante=self.request.user)
                estado_intento = intento.estado  # 'enviado' o 'calificado'
            except IntentoEvaluacion.DoesNotExist:
                intento = None
                estado_intento = 'pendiente'

            evaluaciones_info.append({
                'evaluacion': ev,
                'cerrada': cerrada,
                'estado_intento': estado_intento,
                'intento': intento,
            })

        context['evaluaciones_info'] = evaluaciones_info
        return context


# ────────────────────────────────────────────────────────────────────────────
# 7.2  ResponderEvaluacionView  (función)
# Requirements: 4.1, 4.2, 4.4, 4.5, 5.1, 5.2, 5.3
# ────────────────────────────────────────────────────────────────────────────

@login_required
def responder_evaluacion(request, pk):
    from principal.models import Matriculas
    from .services import CalificacionService

    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    curso = evaluacion.curso

    # Verificar matrícula activa
    if not Matriculas.objects.filter(course=curso, student=request.user, activo=True).exists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Verificar que la evaluación está publicada
    if evaluacion.estado != 'publicada':
        messages.error(request, 'Esta evaluación no está disponible.')
        return redirect('evaluaciones:mis_evaluaciones', curso_id=curso.pk)

    # Verificar si ya existe un intento previo → redirigir a resultado
    intento_existente = IntentoEvaluacion.objects.filter(
        evaluacion=evaluacion,
        estudiante=request.user,
    ).first()
    if intento_existente:
        return redirect('evaluaciones:resultado', pk=intento_existente.pk)

    # Verificar fecha límite
    if evaluacion.fecha_limite is not None and timezone.now() > evaluacion.fecha_limite:
        messages.error(request, 'El plazo para responder esta evaluación ha vencido.')
        return redirect('evaluaciones:mis_evaluaciones', curso_id=curso.pk)

    if request.method == 'POST':
        form = ResponderEvaluacionForm(evaluacion=evaluacion, data=request.POST)
        if form.is_valid():
            # 1. Crear el intento
            intento = IntentoEvaluacion.objects.create(
                evaluacion=evaluacion,
                estudiante=request.user,
            )

            # 2. Crear RespuestaIntento por cada pregunta
            for pregunta in evaluacion.preguntas.all():
                field_name = f'pregunta_{pregunta.id}'
                valor = form.cleaned_data.get(field_name)

                respuesta = intento.respuestas.create(pregunta=pregunta)

                if pregunta.tipo == 'escritura_libre':
                    respuesta.texto_respuesta = valor or ''
                    respuesta.save(update_fields=['texto_respuesta'])
                elif pregunta.tipo == 'opcion_multiple':
                    # valor es una lista de ids como strings
                    if valor:
                        from .models import OpcionEvaluacion
                        opciones = OpcionEvaluacion.objects.filter(
                            pk__in=[int(v) for v in valor],
                            pregunta=pregunta,
                        )
                        respuesta.opciones_seleccionadas.set(opciones)
                else:
                    # seleccion_unica / verdadero_falso: valor es un string con el id
                    if valor:
                        from .models import OpcionEvaluacion
                        try:
                            opcion = OpcionEvaluacion.objects.get(pk=int(valor), pregunta=pregunta)
                            respuesta.opciones_seleccionadas.set([opcion])
                        except (OpcionEvaluacion.DoesNotExist, ValueError):
                            pass

            # 3. Calificar o dejar en revisión
            if evaluacion.tipo == 'momentanea':
                CalificacionService.calcular_calificacion_momentanea(intento)
            # Para 'libre': intento queda con estado 'enviado' (default)

            return redirect('evaluaciones:resultado', pk=intento.pk)
    else:
        form = ResponderEvaluacionForm(evaluacion=evaluacion)

    return render(request, 'evaluaciones/estudiante/responder.html', {
        'form': form,
        'evaluacion': evaluacion,
        'curso': curso,
        'preguntas': evaluacion.preguntas.prefetch_related('opciones').all(),
    })


# ────────────────────────────────────────────────────────────────────────────
# 7.3  ResultadoEvaluacionView  (función)
# Requirements: 4.4, 5.4, 7.1, 7.2, 7.3
# ────────────────────────────────────────────────────────────────────────────

@login_required
def resultado_evaluacion(request, pk):
    from .services import CalificacionService

    intento = get_object_or_404(
        IntentoEvaluacion.objects.select_related('evaluacion__curso', 'estudiante'),
        pk=pk,
    )

    # Solo el estudiante dueño puede ver su resultado
    if intento.estudiante != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    evaluacion = intento.evaluacion
    calificacion = getattr(intento, 'calificacion', None)

    respuestas_detalle = []
    if evaluacion.tipo == 'momentanea':
        respuestas = (
            intento.respuestas
            .select_related('pregunta')
            .prefetch_related('opciones_seleccionadas')
            .order_by('pregunta__orden')
        )
        for resp in respuestas:
            es_correcta = CalificacionService.es_respuesta_correcta(resp)
            respuestas_detalle.append({
                'respuesta': resp,
                'es_correcta': es_correcta,
            })

    return render(request, 'evaluaciones/estudiante/resultado.html', {
        'intento': intento,
        'evaluacion': evaluacion,
        'curso': evaluacion.curso,
        'calificacion': calificacion,
        'respuestas_detalle': respuestas_detalle,
    })


# ────────────────────────────────────────────────────────────────────────────
# 9.1  SecretariaEvaluacionListView
# Requirements: 9.1, 9.2, 9.3, 9.4
# ────────────────────────────────────────────────────────────────────────────

class SecretariaEvaluacionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Evaluacion
    template_name = 'evaluaciones/secretaria/lista.html'
    context_object_name = 'evaluaciones'

    def test_func(self):
        return self.request.user.groups.filter(name='Secretaria').exists()

    def get_queryset(self):
        from principal.models import Curso
        qs = Evaluacion.objects.select_related('curso').order_by('-fecha_creacion')
        curso_id = self.request.GET.get('curso_id')
        if curso_id:
            qs = qs.filter(curso_id=curso_id)
        return qs

    def get_context_data(self, **kwargs):
        from principal.models import Curso
        context = super().get_context_data(**kwargs)
        evaluaciones = context['evaluaciones']
        pendientes_por_eval = {}
        for ev in evaluaciones:
            if ev.tipo == 'libre':
                pendientes_por_eval[ev.pk] = ev.intentos.filter(estado='enviado').count()
            else:
                pendientes_por_eval[ev.pk] = 0
        context['pendientes_por_eval'] = pendientes_por_eval
        context['total_pendientes'] = sum(pendientes_por_eval.values())
        context['cursos'] = Curso.objects.all().order_by('name')
        context['curso_id_filtro'] = self.request.GET.get('curso_id', '')
        return context


# ────────────────────────────────────────────────────────────────────────────
# 9.1  SecretariaEvaluacionCreateView  (función)
# Requirements: 9.7, 9.8
# ────────────────────────────────────────────────────────────────────────────

@login_required
def secretaria_evaluacion_create(request):
    from principal.models import Curso
    from django.core.exceptions import PermissionDenied

    if not request.user.groups.filter(name='Secretaria').exists():
        raise PermissionDenied

    cursos = Curso.objects.all().order_by('name')

    if request.method == 'POST':
        form = EvaluacionForm(request.POST)
        formset = PreguntaEvaluacionFormSet(request.POST)
        curso_id = request.POST.get('curso_id')
        curso = get_object_or_404(Curso, pk=curso_id) if curso_id else None

        if not curso:
            messages.error(request, 'Debes seleccionar un curso.')
        elif form.is_valid() and formset.is_valid():
            preguntas_validas = [
                f for f in formset.forms
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
            ]
            if not preguntas_validas:
                messages.error(request, 'Debes agregar al menos una pregunta a la evaluacion.')
            else:
                evaluacion = form.save(commit=False)
                evaluacion.curso = curso
                evaluacion.save()
                formset.instance = evaluacion
                formset.save()
                messages.success(request, f'Evaluacion "{evaluacion.titulo}" creada correctamente.')
                _guardar_opciones_desde_post(request, evaluacion)
                return redirect('evaluaciones:secretaria_lista')
    else:
        form = EvaluacionForm()
        formset = PreguntaEvaluacionFormSet()
        curso = None

    return render(request, 'evaluaciones/secretaria/crear.html', {
        'form': form,
        'formset': formset,
        'cursos': cursos,
        'curso': curso,
        'accion': 'Crear',
        'titulo': 'Nueva Evaluacion (Secretaria)',
    })


# ────────────────────────────────────────────────────────────────────────────
# 9.2  SecretariaIntentoListView
# Requirements: 9.5, 9.6
# ────────────────────────────────────────────────────────────────────────────

class SecretariaIntentoListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = IntentoEvaluacion
    template_name = 'evaluaciones/secretaria/intentos_lista.html'
    context_object_name = 'intentos'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.evaluacion = get_object_or_404(Evaluacion, pk=kwargs['eval_id'])

    def test_func(self):
        return self.request.user.groups.filter(name='Secretaria').exists()

    def get_queryset(self):
        return (
            IntentoEvaluacion.objects
            .filter(evaluacion=self.evaluacion)
            .select_related('estudiante')
            .order_by('-fecha_envio')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evaluacion'] = self.evaluacion
        context['curso'] = self.evaluacion.curso
        context['pendientes'] = self.get_queryset().filter(estado='enviado').count()
        return context


# ────────────────────────────────────────────────────────────────────────────
# 9.2  SecretariaCalificarIntentoView  (función)
# Requirements: 9.9, 9.10, 9.11
# ────────────────────────────────────────────────────────────────────────────

@login_required
def secretaria_calificar_intento(request, pk):
    from django.core.exceptions import PermissionDenied

    if not request.user.groups.filter(name='Secretaria').exists():
        raise PermissionDenied

    intento = get_object_or_404(
        IntentoEvaluacion.objects.select_related('evaluacion__curso', 'estudiante'),
        pk=pk
    )
    evaluacion = intento.evaluacion
    curso = evaluacion.curso

    calificacion_existente = getattr(intento, 'calificacion', None)

    respuestas = (
        intento.respuestas
        .select_related('pregunta')
        .prefetch_related('opciones_seleccionadas')
        .order_by('pregunta__orden')
    )

    if request.method == 'POST':
        form = CalificarIntentoForm(request.POST, instance=calificacion_existente)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.intento = intento
            calificacion.es_automatica = False
            calificacion.save()

            intento.estado = 'calificado'
            intento.save(update_fields=['estado'])

            # Guardar también como NotaIndividual en el sistema de calificaciones existente
            _registrar_nota_en_calificaciones(intento.estudiante, curso, calificacion.puntaje)

            nombre = intento.estudiante.get_full_name() or intento.estudiante.username
            messages.success(request, f'Respuesta de {nombre} calificada y nota registrada en calificaciones.')
            return redirect('evaluaciones:secretaria_intentos_lista', eval_id=evaluacion.pk)
    else:
        form = CalificarIntentoForm(instance=calificacion_existente)

    return render(request, 'evaluaciones/secretaria/calificar_intento.html', {
        'intento': intento,
        'evaluacion': evaluacion,
        'curso': curso,
        'respuestas': respuestas,
        'form': form,
        'calificacion_existente': calificacion_existente,
    })


# ────────────────────────────────────────────────────────────────────────────
# 9.1  SecretariaEvaluacionListView
# Requirements: 9.1, 9.2, 9.3, 9.4
# ────────────────────────────────────────────────────────────────────────────

class SecretariaEvaluacionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Evaluacion
    template_name = 'evaluaciones/secretaria/lista.html'
    context_object_name = 'evaluaciones'

    def test_func(self):
        return self.request.user.groups.filter(name='Secretaria').exists()

    def get_queryset(self):
        from principal.models import Curso
        qs = Evaluacion.objects.select_related('curso').order_by('-fecha_creacion')
        curso_id = self.request.GET.get('curso_id')
        if curso_id:
            qs = qs.filter(curso_id=curso_id)
        return qs

    def get_context_data(self, **kwargs):
        from principal.models import Curso
        context = super().get_context_data(**kwargs)
        evaluaciones = context['evaluaciones']
        pendientes_por_eval = {}
        for ev in evaluaciones:
            if ev.tipo == 'libre':
                pendientes_por_eval[ev.pk] = ev.intentos.filter(estado='enviado').count()
            else:
                pendientes_por_eval[ev.pk] = 0
        context['pendientes_por_eval'] = pendientes_por_eval
        context['total_pendientes'] = sum(pendientes_por_eval.values())
        context['cursos'] = Curso.objects.all().order_by('name')
        context['curso_id_filtro'] = self.request.GET.get('curso_id', '')
        return context


# ────────────────────────────────────────────────────────────────────────────
# 9.1  SecretariaEvaluacionCreateView  (funcion)
# Requirements: 9.7, 9.8
# ────────────────────────────────────────────────────────────────────────────

@login_required
def secretaria_evaluacion_create(request):
    from principal.models import Curso
    from django.core.exceptions import PermissionDenied

    if not request.user.groups.filter(name='Secretaria').exists():
        raise PermissionDenied

    cursos = Curso.objects.all().order_by('name')

    if request.method == 'POST':
        form = EvaluacionForm(request.POST)
        formset = PreguntaEvaluacionFormSet(request.POST)
        curso_id = request.POST.get('curso_id')
        curso = get_object_or_404(Curso, pk=curso_id) if curso_id else None

        if not curso:
            messages.error(request, 'Debes seleccionar un curso.')
        elif form.is_valid() and formset.is_valid():
            preguntas_validas = [
                f for f in formset.forms
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
            ]
            if not preguntas_validas:
                messages.error(request, 'Debes agregar al menos una pregunta a la evaluacion.')
            else:
                evaluacion = form.save(commit=False)
                evaluacion.curso = curso
                evaluacion.save()
                formset.instance = evaluacion
                formset.save()
                messages.success(request, f'Evaluacion "{evaluacion.titulo}" creada correctamente.')
                _guardar_opciones_desde_post(request, evaluacion)
                return redirect('evaluaciones:secretaria_lista')
    else:
        form = EvaluacionForm()
        formset = PreguntaEvaluacionFormSet()
        curso = None

    return render(request, 'evaluaciones/secretaria/crear.html', {
        'form': form,
        'formset': formset,
        'cursos': cursos,
        'curso': curso,
        'accion': 'Crear',
        'titulo': 'Nueva Evaluacion (Secretaria)',
    })


# ────────────────────────────────────────────────────────────────────────────
# 9.2  SecretariaIntentoListView
# Requirements: 9.5, 9.6
# ────────────────────────────────────────────────────────────────────────────

class SecretariaIntentoListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = IntentoEvaluacion
    template_name = 'evaluaciones/secretaria/intentos_lista.html'
    context_object_name = 'intentos'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.evaluacion = get_object_or_404(Evaluacion, pk=kwargs['eval_id'])

    def test_func(self):
        return self.request.user.groups.filter(name='Secretaria').exists()

    def get_queryset(self):
        return (
            IntentoEvaluacion.objects
            .filter(evaluacion=self.evaluacion)
            .select_related('estudiante')
            .order_by('-fecha_envio')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['evaluacion'] = self.evaluacion
        context['curso'] = self.evaluacion.curso
        context['pendientes'] = self.get_queryset().filter(estado='enviado').count()
        return context


# ────────────────────────────────────────────────────────────────────────────
# 9.2  SecretariaCalificarIntentoView  (funcion)
# Requirements: 9.9, 9.10, 9.11
# ────────────────────────────────────────────────────────────────────────────

@login_required
def secretaria_calificar_intento(request, pk):
    from django.core.exceptions import PermissionDenied

    if not request.user.groups.filter(name='Secretaria').exists():
        raise PermissionDenied

    intento = get_object_or_404(
        IntentoEvaluacion.objects.select_related('evaluacion__curso', 'estudiante'),
        pk=pk
    )
    evaluacion = intento.evaluacion
    curso = evaluacion.curso

    calificacion_existente = getattr(intento, 'calificacion', None)

    respuestas = (
        intento.respuestas
        .select_related('pregunta')
        .prefetch_related('opciones_seleccionadas')
        .order_by('pregunta__orden')
    )

    if request.method == 'POST':
        form = CalificarIntentoForm(request.POST, instance=calificacion_existente)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.intento = intento
            calificacion.es_automatica = False
            calificacion.save()

            intento.estado = 'calificado'
            intento.save(update_fields=['estado'])

            # Guardar también como NotaIndividual en el sistema de calificaciones existente
            _registrar_nota_en_calificaciones(intento.estudiante, curso, calificacion.puntaje)

            nombre = intento.estudiante.get_full_name() or intento.estudiante.username
            messages.success(request, f'Respuesta de {nombre} calificada y nota registrada en calificaciones.')
            return redirect('evaluaciones:secretaria_intentos_lista', eval_id=evaluacion.pk)
    else:
        form = CalificarIntentoForm(instance=calificacion_existente)

    return render(request, 'evaluaciones/secretaria/calificar_intento.html', {
        'intento': intento,
        'evaluacion': evaluacion,
        'curso': curso,
        'respuestas': respuestas,
        'form': form,
        'calificacion_existente': calificacion_existente,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Gestión de opciones de respuesta para preguntas (AJAX)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def opciones_pregunta(request, pregunta_id):
    """
    GET  → devuelve las opciones actuales de la pregunta como JSON
    POST → crea/actualiza opciones enviadas como JSON
    """
    import json
    from django.http import JsonResponse

    pregunta = get_object_or_404(PreguntaEvaluacion, pk=pregunta_id)
    evaluacion = pregunta.evaluacion

    # Solo el profesor del curso puede gestionar opciones
    if request.user != evaluacion.curso.teacher:
        return JsonResponse({'error': 'Sin permiso'}, status=403)

    if request.method == 'GET':
        opciones = list(pregunta.opciones.values('id', 'texto', 'es_correcta', 'orden'))
        return JsonResponse({'opciones': opciones})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        opciones_data = data.get('opciones', [])

        # Eliminar opciones existentes y recrear (más simple que diff)
        pregunta.opciones.all().delete()

        creadas = []
        for i, op in enumerate(opciones_data):
            texto = str(op.get('texto', '')).strip()
            if not texto:
                continue
            nueva = OpcionEvaluacion.objects.create(
                pregunta=pregunta,
                texto=texto,
                es_correcta=bool(op.get('es_correcta', False)),
                orden=i,
            )
            creadas.append({'id': nueva.id, 'texto': nueva.texto,
                            'es_correcta': nueva.es_correcta, 'orden': nueva.orden})

        return JsonResponse({'opciones': creadas})

    return JsonResponse({'error': 'Método no permitido'}, status=405)
