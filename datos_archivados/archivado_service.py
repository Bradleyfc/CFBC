"""
Servicio para archivar automáticamente los datos de un CursoAcademico
cuando este pasa al estado archivado.

Proceso:
  1. Copia Cursos, Matrículas, Asistencias, Calificaciones y NotasIndividuales
     del curso académico a los modelos de datos_archivados.
  2. Elimina esos mismos datos de la app principal para dejar el sistema limpio
     y listo para el nuevo curso académico activo.

NO toca:
  - DatoArchivadoDinamico  (pertenece a la migración MariaDB)
  - MigracionLog           (pertenece a la migración MariaDB)
  - CursoAcademico         (solo cambia estado, no se elimina)
  - User / Registro        (los usuarios del sistema no se eliminan)
"""

import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def archivar_datos_curso_academico(curso_academico):
    """
    Archiva todos los datos asociados a un CursoAcademico en los modelos
    de datos_archivados y luego los elimina de principal.

    Parámetros:
        curso_academico: instancia de principal.CursoAcademico ya marcada
                         como archivado=True.

    Retorna:
        dict con contadores de registros archivados/eliminados,
        o None si ya estaba archivado previamente en datos_archivados.
    """
    from datos_archivados.models import (
        CursoAcademicoArchivado,
        CursoArchivado,
        UsuarioArchivado,
        MatriculaArchivada,
        CalificacionArchivada,
        NotaIndividualArchivada,
        AsistenciaArchivada,
    )
    from principal.models import (
        Curso, Matriculas, Asistencia, Calificaciones, NotaIndividual,
        SolicitudInscripcion, RespuestaEstudiante,
        FormularioAplicacion, PreguntaFormulario, OpcionRespuesta,
    )

    # Evitar duplicar si ya fue archivado antes
    if CursoAcademicoArchivado.objects.filter(id_original=curso_academico.pk).exists():
        logger.info(
            f"CursoAcademico '{curso_academico.nombre}' (id={curso_academico.pk}) "
            f"ya existe en datos_archivados. Se omite el archivado."
        )
        return None

    contadores = {
        'cursos': 0,
        'usuarios': 0,
        'matriculas': 0,
        'calificaciones': 0,
        'notas': 0,
        'asistencias': 0,
    }

    with transaction.atomic():

        # ── 1. Crear CursoAcademicoArchivado ──────────────────────────────────
        curso_academico_archivado = CursoAcademicoArchivado.objects.create(
            id_original=curso_academico.pk,
            nombre=curso_academico.nombre,
            activo=False,
            archivado=True,
            fecha_creacion=curso_academico.fecha_creacion,
        )
        logger.info(f"CursoAcademicoArchivado creado: {curso_academico_archivado}")

        # ── 2. Archivar Cursos ────────────────────────────────────────────────
        cursos_qs = Curso.objects.filter(
            curso_academico=curso_academico
        ).select_related('teacher')

        # Mapa user.pk → UsuarioArchivado para evitar duplicados en esta sesión
        usuarios_archivados_map = {}

        def obtener_o_crear_usuario_archivado(user):
            """Devuelve el UsuarioArchivado para un User, creándolo si no existe."""
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
            contadores['usuarios'] += 1
            usuarios_archivados_map[user.pk] = ua
            return ua

        # Mapa curso.pk → CursoArchivado
        cursos_archivados_map = {}

        for curso in cursos_qs:
            obtener_o_crear_usuario_archivado(curso.teacher)  # archivar profesor

            ca = CursoArchivado.objects.create(
                id_original=curso.pk,
                name=curso.name,
                description=curso.description,
                area=curso.area,
                tipo=curso.tipo,
                teacher_id_original=curso.teacher.pk,
                teacher_name=curso.teacher.get_full_name() or curso.teacher.username,
                class_quantity=curso.class_quantity,
                status=curso.status,
                curso_academico=curso_academico_archivado,
                enrollment_deadline=curso.enrollment_deadline,
                start_date=curso.start_date,
                teacher_actual=curso.teacher,
            )
            cursos_archivados_map[curso.pk] = ca
            contadores['cursos'] += 1

        # ── 3. Archivar Matrículas ────────────────────────────────────────────
        matriculas_qs = Matriculas.objects.filter(
            curso_academico=curso_academico
        ).select_related('student', 'course')

        matriculas_archivadas_map = {}

        for matricula in matriculas_qs:
            curso_archivado = cursos_archivados_map.get(matricula.course.pk)
            if not curso_archivado:
                # Curso sin curso_academico asignado pero con matrícula vinculada
                existente = CursoArchivado.objects.filter(
                    id_original=matricula.course.pk
                ).first()
                if not existente:
                    obtener_o_crear_usuario_archivado(matricula.course.teacher)
                    existente = CursoArchivado.objects.create(
                        id_original=matricula.course.pk,
                        name=matricula.course.name,
                        description=matricula.course.description,
                        area=matricula.course.area,
                        tipo=matricula.course.tipo,
                        teacher_id_original=matricula.course.teacher.pk,
                        teacher_name=matricula.course.teacher.get_full_name() or matricula.course.teacher.username,
                        class_quantity=matricula.course.class_quantity,
                        status=matricula.course.status,
                        curso_academico=curso_academico_archivado,
                        enrollment_deadline=matricula.course.enrollment_deadline,
                        start_date=matricula.course.start_date,
                        teacher_actual=matricula.course.teacher,
                    )
                    contadores['cursos'] += 1
                cursos_archivados_map[matricula.course.pk] = existente
                curso_archivado = existente

            estudiante_archivado = obtener_o_crear_usuario_archivado(matricula.student)

            ma = MatriculaArchivada.objects.create(
                id_original=matricula.pk,
                course=curso_archivado,
                student=estudiante_archivado,
                activo=matricula.activo,
                fecha_matricula=matricula.fecha_matricula,
                estado=matricula.estado,
            )
            matriculas_archivadas_map[matricula.pk] = ma
            contadores['matriculas'] += 1

        # ── 4. Archivar Calificaciones y Notas Individuales ───────────────────
        calificaciones_qs = Calificaciones.objects.filter(
            curso_academico=curso_academico
        ).select_related('student', 'course', 'matricula').prefetch_related('notas')

        for calificacion in calificaciones_qs:
            curso_archivado = cursos_archivados_map.get(calificacion.course.pk)
            if not curso_archivado:
                curso_archivado = CursoArchivado.objects.filter(
                    id_original=calificacion.course.pk
                ).first()
                if not curso_archivado:
                    logger.warning(
                        f"No se encontró CursoArchivado para course.pk="
                        f"{calificacion.course.pk}. Se omite esta calificación."
                    )
                    continue

            estudiante_archivado = obtener_o_crear_usuario_archivado(calificacion.student)

            # Buscar la matrícula archivada correspondiente
            matricula_archivada = None
            if calificacion.matricula:
                matricula_archivada = matriculas_archivadas_map.get(calificacion.matricula.pk)
                if not matricula_archivada:
                    matricula_archivada = MatriculaArchivada.objects.filter(
                        id_original=calificacion.matricula.pk
                    ).first()

            if not matricula_archivada:
                # Matrícula mínima de respaldo (ID negativo para distinguir)
                matricula_archivada = MatriculaArchivada.objects.create(
                    id_original=calificacion.pk * -1,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    activo=True,
                    fecha_matricula=calificacion.course.start_date or timezone.now().date(),
                    estado='P',
                )
                contadores['matriculas'] += 1

            calificacion_archivada = CalificacionArchivada.objects.create(
                id_original=calificacion.pk,
                matricula=matricula_archivada,
                course=curso_archivado,
                student=estudiante_archivado,
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

        # ── 5. Archivar Asistencias ───────────────────────────────────────────
        cursos_ids = list(cursos_archivados_map.keys())
        asistencias_qs = Asistencia.objects.filter(
            course__pk__in=cursos_ids
        ).select_related('student', 'course')

        for asistencia in asistencias_qs:
            curso_archivado = cursos_archivados_map.get(asistencia.course.pk)
            if not curso_archivado:
                continue

            estudiante_archivado = obtener_o_crear_usuario_archivado(asistencia.student)

            AsistenciaArchivada.objects.create(
                id_original=asistencia.pk,
                course=curso_archivado,
                student=estudiante_archivado,
                presente=asistencia.presente,
                date=asistencia.date,
            )
            contadores['asistencias'] += 1

        logger.info(
            f"Archivado completado para '{curso_academico.nombre}': "
            f"{contadores['cursos']} cursos, "
            f"{contadores['usuarios']} usuarios, "
            f"{contadores['matriculas']} matrículas, "
            f"{contadores['calificaciones']} calificaciones, "
            f"{contadores['notas']} notas, "
            f"{contadores['asistencias']} asistencias."
        )

        # ── 6. Limpiar datos de principal (dentro de la misma transacción) ────
        # El orden importa: primero los hijos, luego los padres.

        # 6a. Notas individuales
        NotaIndividual.objects.filter(
            calificacion__curso_academico=curso_academico
        ).delete()

        # 6b. Calificaciones
        Calificaciones.objects.filter(
            curso_academico=curso_academico
        ).delete()

        # 6c. Asistencias
        Asistencia.objects.filter(
            course__pk__in=cursos_ids
        ).delete()

        # 6d. Respuestas de estudiantes y solicitudes de inscripción
        solicitudes_qs = SolicitudInscripcion.objects.filter(
            curso__pk__in=cursos_ids
        )
        for solicitud in solicitudes_qs:
            RespuestaEstudiante.objects.filter(solicitud=solicitud).delete()
        solicitudes_qs.delete()

        # 6e. Matrículas
        Matriculas.objects.filter(
            curso_academico=curso_academico
        ).delete()

        # 6f. Opciones, preguntas y formularios de aplicación
        formularios_qs = FormularioAplicacion.objects.filter(
            curso__pk__in=cursos_ids
        )
        for formulario in formularios_qs:
            for pregunta in formulario.preguntas.all():
                OpcionRespuesta.objects.filter(pregunta=pregunta).delete()
            PreguntaFormulario.objects.filter(formulario=formulario).delete()
        formularios_qs.delete()

        # 6g. Cursos (al final, después de eliminar todos sus dependientes)
        Curso.objects.filter(
            curso_academico=curso_academico
        ).delete()

        logger.info(
            f"Limpieza de principal completada para '{curso_academico.nombre}'."
        )

    return contadores
