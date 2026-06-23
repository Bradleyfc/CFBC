"""
Servicio para gestionar los semestres de los cursos.

Funciones principales:
  - crear_semestre_inicial(curso): Crea el SemestreCurso inicial (numero_semestre=1)
    para un Curso recién creado. Llamado desde la señal post_save de Curso.
  - terminar_semestre(curso): Ejecuta el proceso completo de cierre de semestre:
    archiva los datos académicos en datos_archivados y reinicia el curso para
    el siguiente semestre.

Manejo de errores:
  - Si terminar_semestre falla, se lanza SemestreError con mensaje descriptivo.
  - La transacción atómica garantiza que no quedan datos parciales.
"""

import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class SemestreError(Exception):
    """
    Excepción lanzada cuando el proceso de terminar semestre falla.
    La transacción atómica garantiza que no quedan datos parciales.
    """
    pass


def crear_semestre_inicial(curso):
    """
    Crea el SemestreCurso inicial (numero_semestre=1, activo=True) para un Curso recién creado.
    Llamado desde la señal post_save de Curso cuando created=True.

    Asocia el semestre al CursoAcademico activo (o None si no hay ninguno).

    Parámetros:
        curso: instancia de principal.Curso recién creada.

    Retorna:
        SemestreCurso creado.
    """
    from principal.models import SemestreCurso, CursoAcademico

    # Obtener el CursoAcademico activo (puede ser None)
    curso_academico = CursoAcademico.objects.filter(activo=True).first()
    if curso_academico is None:
        logger.warning(
            f"No hay CursoAcademico activo al crear SemestreCurso inicial "
            f"para '{curso.name}' (id={curso.pk}). Se crea sin CursoAcademico."
        )

    semestre = SemestreCurso.objects.create(
        curso=curso,
        numero_semestre=1,
        activo=True,
        curso_academico=curso_academico,
        fecha_inicio=curso.start_date,
    )
    logger.info(
        f"SemestreCurso inicial creado para '{curso.name}' "
        f"(semestre=1, ca={curso_academico.nombre if curso_academico else 'None'})."
    )
    return semestre


def terminar_semestre(curso):
    """
    Ejecuta el proceso completo de cierre de semestre dentro de transaction.atomic().

    Pasos:
      1. Obtener el SemestreCurso activo del curso (o usar numero_semestre=1 si no hay).
      2. Verificar que no exista ya un SemestreCursoArchivado con ese id_original.
      3. Crear SemestreCursoArchivado en datos_archivados.
      4. Archivar Matriculas, Calificaciones, NotaIndividual, Asistencia.
      5. Eliminar esos datos de principal.
      6. Marcar SemestreCurso actual como activo=False.
      7. Crear nuevo SemestreCurso con numero_semestre = anterior + 1.
      8. Cambiar Curso.status = 'I'.

    Parámetros:
        curso: instancia de principal.Curso.

    Retorna:
        dict con contadores {semestre_num, matriculas, calificaciones, notas, asistencias}.

    Lanza:
        SemestreError si cualquier paso falla (transacción revertida).
    """
    from principal.models import (
        SemestreCurso, CursoAcademico,
        Matriculas, Calificaciones, NotaIndividual, Asistencia,
    )
    from datos_archivados.models import (
        SemestreCursoArchivado,
        CursoAcademicoArchivado,
        UsuarioArchivado,
        MatriculaArchivada,
        CalificacionArchivada,
        NotaIndividualArchivada,
        AsistenciaArchivada,
    )

    # Obtener el semestre activo actual
    semestre_activo = SemestreCurso.objects.filter(
        curso=curso, activo=True
    ).order_by('-numero_semestre').first()

    numero_semestre_actual = semestre_activo.numero_semestre if semestre_activo else 1

    # Verificar duplicado
    if semestre_activo and SemestreCursoArchivado.objects.filter(
        id_original=semestre_activo.pk
    ).exists():
        raise SemestreError(
            f"Este semestre (Semestre {numero_semestre_actual} de '{curso.name}') "
            f"ya fue archivado previamente."
        )

    contadores = {
        'semestre_num': numero_semestre_actual,
        'matriculas': 0,
        'calificaciones': 0,
        'notas': 0,
        'asistencias': 0,
    }

    try:
        with transaction.atomic():

            # ── 1. Obtener CursoAcademico activo para el nuevo semestre ───────
            curso_academico_activo = CursoAcademico.objects.filter(activo=True).first()
            if curso_academico_activo is None:
                logger.warning(
                    f"No hay CursoAcademico activo al terminar semestre "
                    f"de '{curso.name}'. El nuevo SemestreCurso se creará sin CA."
                )

            # ── 2. Crear SemestreCursoArchivado ───────────────────────────────
            # Buscar CursoAcademicoArchivado correspondiente al CA del semestre activo
            ca_archivado = None
            if semestre_activo and semestre_activo.curso_academico:
                ca_archivado = CursoAcademicoArchivado.objects.filter(
                    id_original=semestre_activo.curso_academico.pk
                ).first()

            # Necesitamos un CursoArchivado para vincular el SemestreCursoArchivado.
            # Como el curso NO se elimina (a diferencia del archivado de CursoAcademico),
            # creamos un registro de semestre archivado directamente con los datos del curso.
            # Usamos un enfoque simplificado: guardamos los datos del semestre en
            # SemestreCursoArchivado con referencia al CursoArchivado si existe,
            # o creamos uno temporal para este semestre.

            # Buscar si ya existe un CursoArchivado para este curso
            from datos_archivados.models import CursoArchivado
            curso_archivado = CursoArchivado.objects.filter(
                id_original=curso.pk
            ).order_by('-fecha_migracion').first()

            if curso_archivado is None:
                # Crear un CursoArchivado temporal para este semestre
                # Necesitamos un CursoAcademicoArchivado de referencia
                if ca_archivado is None:
                    # Crear un CursoAcademicoArchivado de referencia si no existe
                    ca_ref = semestre_activo.curso_academico if semestre_activo else None
                    if ca_ref:
                        ca_archivado, _ = CursoAcademicoArchivado.objects.get_or_create(
                            id_original=ca_ref.pk,
                            defaults={
                                'nombre': ca_ref.nombre,
                                'activo': ca_ref.activo,
                                'archivado': True,
                                'fecha_creacion': ca_ref.fecha_creacion,
                            }
                        )
                    else:
                        # Sin CA, crear uno genérico para este semestre
                        ca_archivado, _ = CursoAcademicoArchivado.objects.get_or_create(
                            id_original=0,
                            defaults={
                                'nombre': f'Semestre {numero_semestre_actual} - {curso.name}',
                                'activo': False,
                                'archivado': True,
                                'fecha_creacion': timezone.now().date(),
                            }
                        )

                curso_archivado = CursoArchivado.objects.create(
                    id_original=curso.pk,
                    name=curso.name,
                    description=curso.description,
                    area=curso.area,
                    tipo=curso.tipo,
                    teacher_id_original=curso.teacher.pk,
                    teacher_name=curso.teacher.get_full_name() or curso.teacher.username,
                    image=curso.image.name if curso.image else None,
                    class_quantity=curso.class_quantity,
                    status=curso.status,
                    curso_academico=ca_archivado,
                    enrollment_deadline=curso.enrollment_deadline,
                    start_date=curso.start_date,
                    teacher_actual=curso.teacher,
                )

            # Crear el SemestreCursoArchivado
            semestre_archivado = SemestreCursoArchivado.objects.create(
                id_original=semestre_activo.pk if semestre_activo else 0,
                curso_archivado=curso_archivado,
                numero_semestre=numero_semestre_actual,
                activo=True,
                curso_academico_archivado=ca_archivado,
                fecha_inicio=semestre_activo.fecha_inicio if semestre_activo else None,
                fecha_cierre=timezone.now().date(),
                fecha_creacion=semestre_activo.fecha_creacion if semestre_activo else timezone.now(),
            )

            # ── 3. Archivar usuarios (helper) ─────────────────────────────────
            usuarios_archivados_map = {}

            def obtener_o_crear_usuario_archivado(user):
                if user.pk in usuarios_archivados_map:
                    return usuarios_archivados_map[user.pk]
                existente = UsuarioArchivado.objects.filter(
                    id_original=user.pk,
                    usuario_actual=user
                ).first()
                if existente:
                    usuarios_archivados_map[user.pk] = existente
                    return existente
                perfil = getattr(user, 'registro', None)
                ua = UsuarioArchivado.objects.create(
                    id_original=user.pk,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    date_joined=user.date_joined,
                    is_active=user.is_active,
                    nacionalidad=getattr(perfil, 'nacionalidad', None) if perfil else None,
                    carnet=getattr(perfil, 'carnet', None) if perfil else None,
                    sexo=getattr(perfil, 'sexo', 'M') if perfil else 'M',
                    address=getattr(perfil, 'address', None) if perfil else None,
                    location=getattr(perfil, 'location', None) if perfil else None,
                    provincia=getattr(perfil, 'provincia', None) if perfil else None,
                    telephone=getattr(perfil, 'telephone', None) if perfil else None,
                    movil=getattr(perfil, 'movil', None) if perfil else None,
                    grado=getattr(perfil, 'grado', 'grado1') if perfil else 'grado1',
                    ocupacion=getattr(perfil, 'ocupacion', 'ocupacion1') if perfil else 'ocupacion1',
                    titulo=getattr(perfil, 'titulo', None) if perfil else None,
                    grupo=', '.join(user.groups.values_list('name', flat=True)),
                    usuario_actual=user,
                )
                usuarios_archivados_map[user.pk] = ua
                return ua

            # ── 4. Archivar Matrículas ────────────────────────────────────────
            matriculas_qs = Matriculas.objects.filter(course=curso).select_related('student')
            matriculas_archivadas_map = {}

            for matricula in matriculas_qs:
                estudiante_archivado = obtener_o_crear_usuario_archivado(matricula.student)
                ma = MatriculaArchivada.objects.create(
                    id_original=matricula.pk,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_archivado,
                    activo=matricula.activo,
                    fecha_matricula=matricula.fecha_matricula,
                    estado=matricula.estado,
                )
                matriculas_archivadas_map[matricula.pk] = ma
                contadores['matriculas'] += 1

            # ── 5. Archivar Calificaciones y Notas ────────────────────────────
            calificaciones_qs = Calificaciones.objects.filter(
                course=curso
            ).select_related('student', 'matricula').prefetch_related('notas')

            for calificacion in calificaciones_qs:
                estudiante_archivado = obtener_o_crear_usuario_archivado(calificacion.student)
                matricula_archivada = None
                if calificacion.matricula:
                    matricula_archivada = matriculas_archivadas_map.get(calificacion.matricula.pk)

                if not matricula_archivada:
                    matricula_archivada = MatriculaArchivada.objects.create(
                        id_original=calificacion.pk * -1,
                        course=curso_archivado,
                        student=estudiante_archivado,
                        activo=True,
                        fecha_matricula=curso.start_date or timezone.now().date(),
                        estado='P',
                    )

                calificacion_archivada = CalificacionArchivada.objects.create(
                    id_original=calificacion.pk,
                    matricula=matricula_archivada,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_archivado,
                    average=calificacion.average,
                )
                contadores['calificaciones'] += 1

                for nota in calificacion.notas.all():
                    NotaIndividualArchivada.objects.create(
                        id_original=nota.pk,
                        calificacion=calificacion_archivada,
                        valor=nota.valor if nota.valor is not None else 0,
                        fecha_creacion=nota.fecha_creacion,
                    )
                    contadores['notas'] += 1

            # ── 6. Archivar Asistencias ───────────────────────────────────────
            asistencias_qs = Asistencia.objects.filter(
                course=curso
            ).select_related('student')

            for asistencia in asistencias_qs:
                estudiante_archivado = obtener_o_crear_usuario_archivado(asistencia.student)
                AsistenciaArchivada.objects.create(
                    id_original=asistencia.pk,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_archivado,
                    presente=asistencia.presente,
                    date=asistencia.date,
                )
                contadores['asistencias'] += 1

            logger.info(
                f"Datos del semestre {numero_semestre_actual} de '{curso.name}' archivados: "
                f"{contadores['matriculas']} matrículas, "
                f"{contadores['calificaciones']} calificaciones, "
                f"{contadores['notas']} notas, "
                f"{contadores['asistencias']} asistencias."
            )

            # ── 7. Limpiar datos de principal ─────────────────────────────────
            # Solo se ejecuta si el archivado fue exitoso (dentro de la misma transacción)

            # 7a. Notas individuales
            NotaIndividual.objects.filter(calificacion__course=curso).delete()

            # 7b. Calificaciones
            Calificaciones.objects.filter(course=curso).delete()

            # 7c. Asistencias
            Asistencia.objects.filter(course=curso).delete()

            # 7d. Matrículas
            Matriculas.objects.filter(course=curso).delete()

            # 7e. Solicitudes de inscripción y sus respuestas
            # IMPORTANTE: se deben limpiar para que los estudiantes puedan
            # volver a aplicar en el nuevo semestre del mismo curso.
            from principal.models import SolicitudInscripcion, RespuestaEstudiante
            solicitudes_del_curso = SolicitudInscripcion.objects.filter(curso=curso)
            for solicitud in solicitudes_del_curso:
                RespuestaEstudiante.objects.filter(solicitud=solicitud).delete()
            solicitudes_del_curso.delete()
            logger.info(
                f"Solicitudes de inscripción del semestre {numero_semestre_actual} "
                f"de '{curso.name}' eliminadas para el nuevo semestre."
            )

            # ── 8. Actualizar SemestreCurso ───────────────────────────────────
            if semestre_activo:
                semestre_activo.activo = False
                semestre_activo.fecha_cierre = timezone.now().date()
                semestre_activo.save(update_fields=['activo', 'fecha_cierre'])

            # ── 9. Crear nuevo SemestreCurso ──────────────────────────────────
            nuevo_numero = numero_semestre_actual + 1
            # El nuevo semestre hereda el mismo CursoAcademico del semestre que se cierra,
            # no el CA "activo global". Así el curso permanece vinculado a su CA original
            # aunque se use el modal después de que ese CA haya sido archivado.
            ca_nuevo_semestre = semestre_activo.curso_academico if semestre_activo else curso_academico_activo
            SemestreCurso.objects.create(
                curso=curso,
                numero_semestre=nuevo_numero,
                activo=True,
                curso_academico=ca_nuevo_semestre,
                fecha_inicio=timezone.now().date(),
            )

            # ── 10. Reiniciar estado del Curso ────────────────────────────────
            from principal.models import Curso as CursoModel
            CursoModel.objects.filter(pk=curso.pk).update(status='I')
            curso.status = 'I'

            logger.info(
                f"Semestre {numero_semestre_actual} terminado para '{curso.name}'. "
                f"Nuevo semestre: {nuevo_numero}. Curso reiniciado a estado 'I'."
            )

    except SemestreError:
        raise
    except Exception as exc:
        logger.error(
            f"[SemestreError] Falló terminar_semestre para '{curso.name}' "
            f"(semestre={numero_semestre_actual}). Transacción revertida.",
            exc_info=True,
        )
        raise SemestreError(
            f"No se pudo terminar el semestre {numero_semestre_actual} de '{curso.name}'. "
            f"Los datos se conservan intactos. Causa: {exc}"
        ) from exc

    return contadores
