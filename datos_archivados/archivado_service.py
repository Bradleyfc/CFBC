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

Manejo de errores:
  - Si el archivado falla, se lanza ArchivadoError con un mensaje descriptivo.
  - La transacción atómica garantiza que NINGÚN dato de gestión académica
    se elimina si el archivado no se completó correctamente.
  - El llamador (señal o acción de admin) debe capturar ArchivadoError
    y revertir el estado archivado=True del CursoAcademico.
"""

import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class ArchivadoError(Exception):
    """
    Excepción lanzada cuando el proceso de archivado de un CursoAcademico falla.
    Garantiza que el llamador pueda distinguir este error de otros inesperados
    y revertir el estado del modelo si es necesario.
    """
    pass


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

    Lanza:
        ArchivadoError si el proceso falla. La transacción atómica garantiza
        que los datos de gestión académica NO se eliminan en caso de error.
    """
    from datos_archivados.models import (
        CursoAcademicoArchivado,
        CursoArchivado,
        UsuarioArchivado,
        MatriculaArchivada,
        CalificacionArchivada,
        NotaIndividualArchivada,
        AsistenciaArchivada,
        ReglamentoCursoArchivado,
        ArticuloReglamentoArchivado,
    )
    from principal.models import (
        Curso, Matriculas, Asistencia, Calificaciones, NotaIndividual,
        SolicitudInscripcion, RespuestaEstudiante,
        FormularioAplicacion, PreguntaFormulario, OpcionRespuesta,
        ReglamentoCurso, ArticuloReglamento,
    )

    contadores = {
        'cursos': 0,
        'usuarios': 0,
        'matriculas': 0,
        'calificaciones': 0,
        'notas': 0,
        'asistencias': 0,
        'reglamentos': 0,
        'articulos_reglamento': 0,
    }

    # Si el CursoAcademicoArchivado ya existe (creado por terminar_semestre previos),
    # no saltamos el proceso: puede haber SemestreCurso pendientes de archivar
    # (los cerrados con "finalizar_curso" que nunca se movieron a datos_archivados).
    ca_ya_existia = CursoAcademicoArchivado.objects.filter(
        id_original=curso_academico.pk
    ).exists()

    if ca_ya_existia:
        logger.info(
            f"CursoAcademico '{curso_academico.nombre}' (id={curso_academico.pk}) "
            f"ya existe en datos_archivados. Se procesarán solo los SemestreCurso pendientes."
        )
        # Delegar al helper que archiva solo los semestres y cursos pendientes
        return _archivar_semestres_pendientes(curso_academico, contadores)

    try:
        with transaction.atomic():

            # ── 1. Crear CursoAcademicoArchivado ─────────────────────────────
            curso_academico_archivado = CursoAcademicoArchivado.objects.create(
                id_original=curso_academico.pk,
                nombre=curso_academico.nombre,
                activo=False,
                archivado=True,
                fecha_creacion=curso_academico.fecha_creacion,
            )
            logger.info(f"CursoAcademicoArchivado creado: {curso_academico_archivado}")

            # ── 2. Archivar Cursos ────────────────────────────────────────────
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
                    image=curso.image.name if curso.image else None,
                    class_quantity=curso.class_quantity,
                    status=curso.get_dynamic_status(),
                    curso_academico=curso_academico_archivado,
                    enrollment_deadline=curso.enrollment_deadline,
                    start_date=curso.start_date,
                    teacher_actual=curso.teacher,
                )
                cursos_archivados_map[curso.pk] = ca
                contadores['cursos'] += 1

            # ── 3. Archivar Reglamentos de Cursos ────────────────────────────
            for curso_pk, curso_archivado in cursos_archivados_map.items():
                try:
                    reglamento = ReglamentoCurso.objects.get(curso__pk=curso_pk)
                except ReglamentoCurso.DoesNotExist:
                    continue  # el curso no tiene reglamento, se omite

                reglamento_archivado = ReglamentoCursoArchivado.objects.create(
                    id_original=reglamento.pk,
                    curso=curso_archivado,
                    introduccion=reglamento.introduccion,
                    fecha_creacion=reglamento.fecha_creacion,
                )
                contadores['reglamentos'] += 1

                for articulo in reglamento.articulos.all().order_by('orden'):
                    ArticuloReglamentoArchivado.objects.create(
                        id_original=articulo.pk,
                        reglamento=reglamento_archivado,
                        titulo=articulo.titulo,
                        cuerpo=articulo.cuerpo,
                        orden=articulo.orden,
                        fecha_creacion=articulo.fecha_creacion,
                    )
                    contadores['articulos_reglamento'] += 1

            # ── 3b. Archivar SemestreCurso ───────────────────────────────────
            from principal.models import SemestreCurso
            from datos_archivados.models import SemestreCursoArchivado

            # Fecha de cierre de facto para semestres que estaban abiertos al archivar
            fecha_archivado = timezone.now().date()

            # Mapa semestre.pk → SemestreCursoArchivado (para vincular matrículas/calificaciones/asistencias)
            semestres_archivados_map = {}

            for curso_pk, curso_archivado in cursos_archivados_map.items():
                semestres = SemestreCurso.objects.filter(curso__pk=curso_pk).order_by('numero_semestre', '-activo', '-pk')
                numeros_vistos = set()
                for semestre in semestres:
                    # Evitar duplicados por id_original
                    existente_arch = SemestreCursoArchivado.objects.filter(id_original=semestre.pk).first()
                    if existente_arch:
                        logger.info(f"SemestreCurso id={semestre.pk} ya archivado. Se reutiliza.")
                        semestres_archivados_map[semestre.pk] = existente_arch
                        numeros_vistos.add(semestre.numero_semestre)
                        continue
                    # Evitar duplicados por (curso_archivado, numero_semestre)
                    if semestre.numero_semestre in numeros_vistos:
                        logger.info(
                            f"SemestreCurso semestre={semestre.numero_semestre} del curso "
                            f"'{curso_archivado.name}' ya procesado. Se omite duplicado id={semestre.pk}."
                        )
                        continue
                    numeros_vistos.add(semestre.numero_semestre)
                    # Si el semestre estaba abierto al momento del archivado, cerrarlo ahora
                    fecha_cierre = semestre.fecha_cierre or (fecha_archivado if semestre.activo else None)
                    sa = SemestreCursoArchivado.objects.create(
                        id_original=semestre.pk,
                        curso_archivado=curso_archivado,
                        numero_semestre=semestre.numero_semestre,
                        activo=False,  # al archivar el CA todos los semestres quedan cerrados
                        curso_academico_archivado=curso_academico_archivado,
                        fecha_inicio=semestre.fecha_inicio,
                        fecha_cierre=fecha_cierre,
                        fecha_creacion=semestre.fecha_creacion,
                    )
                    semestres_archivados_map[semestre.pk] = sa

            # ── 4. Archivar Matrículas ────────────────────────────────────────
            matriculas_qs = Matriculas.objects.filter(
                curso_academico=curso_academico
            ).select_related('student', 'course', 'semestre')

            matriculas_archivadas_map = {}

            for matricula in matriculas_qs:
                curso_archivado = cursos_archivados_map.get(matricula.course.pk)
                if not curso_archivado:
                    existente = CursoArchivado.objects.filter(id_original=matricula.course.pk).first()
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
                            image=matricula.course.image.name if matricula.course.image else None,
                            class_quantity=matricula.course.class_quantity,
                            status=matricula.course.get_dynamic_status(),
                            curso_academico=curso_academico_archivado,
                            enrollment_deadline=matricula.course.enrollment_deadline,
                            start_date=matricula.course.start_date,
                            teacher_actual=matricula.course.teacher,
                        )
                        contadores['cursos'] += 1
                    cursos_archivados_map[matricula.course.pk] = existente
                    curso_archivado = existente

                estudiante_archivado = obtener_o_crear_usuario_archivado(matricula.student)

                # Resolver semestre archivado
                semestre_arch = None
                if matricula.semestre_id:
                    semestre_arch = semestres_archivados_map.get(matricula.semestre_id)

                ma = MatriculaArchivada.objects.create(
                    id_original=matricula.pk,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_arch,
                    activo=matricula.activo,
                    fecha_matricula=matricula.fecha_matricula,
                    estado=matricula.estado,
                )
                matriculas_archivadas_map[matricula.pk] = ma
                contadores['matriculas'] += 1

            # ── 5. Archivar Calificaciones y Notas Individuales ───────────────
            calificaciones_qs = Calificaciones.objects.filter(
                curso_academico=curso_academico
            ).select_related('student', 'course', 'matricula', 'semestre').prefetch_related('notas')

            for calificacion in calificaciones_qs:
                curso_archivado = cursos_archivados_map.get(calificacion.course.pk)
                if not curso_archivado:
                    curso_archivado = CursoArchivado.objects.filter(id_original=calificacion.course.pk).first()
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
                    matricula_archivada = MatriculaArchivada.objects.create(
                        id_original=calificacion.pk * -1,
                        course=curso_archivado,
                        student=estudiante_archivado,
                        activo=True,
                        fecha_matricula=calificacion.course.start_date or timezone.now().date(),
                        estado='P',
                    )
                    contadores['matriculas'] += 1

                # Resolver semestre archivado
                semestre_arch = None
                if calificacion.semestre_id:
                    semestre_arch = semestres_archivados_map.get(calificacion.semestre_id)

                calificacion_archivada = CalificacionArchivada.objects.create(
                    id_original=calificacion.pk,
                    matricula=matricula_archivada,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_arch,
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
            cursos_ids = list(cursos_archivados_map.keys())

            # Incluir cursos del CA sin matrículas (finalizados, etc.)
            todos_cursos_del_ca = list(
                Curso.objects.filter(curso_academico=curso_academico).values_list('pk', flat=True)
            )
            for cid in todos_cursos_del_ca:
                if cid not in cursos_ids:
                    cursos_ids.append(cid)

            asistencias_qs = Asistencia.objects.filter(
                course__pk__in=cursos_ids
            ).select_related('student', 'course', 'semestre')

            for asistencia in asistencias_qs:
                curso_archivado = cursos_archivados_map.get(asistencia.course.pk)
                if not curso_archivado:
                    continue

                estudiante_archivado = obtener_o_crear_usuario_archivado(asistencia.student)

                # Resolver semestre archivado
                semestre_arch = None
                if asistencia.semestre_id:
                    semestre_arch = semestres_archivados_map.get(asistencia.semestre_id)

                AsistenciaArchivada.objects.create(
                    id_original=asistencia.pk,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_arch,
                    presente=asistencia.presente,
                    date=asistencia.date,
                )
                contadores['asistencias'] += 1

            logger.info(
                f"Archivado completado para '{curso_academico.nombre}': "
                f"{contadores['cursos']} cursos, "
                f"{contadores['reglamentos']} reglamentos ({contadores['articulos_reglamento']} artículos), "
                f"{contadores['usuarios']} usuarios, "
                f"{contadores['matriculas']} matrículas, "
                f"{contadores['calificaciones']} calificaciones, "
                f"{contadores['notas']} notas, "
                f"{contadores['asistencias']} asistencias."
            )

            # ── 7. Limpiar datos de principal (dentro de la misma transacción) ─
            # El orden importa: primero los hijos, luego los padres.
            # Esta fase SOLO se ejecuta si todo el archivado anterior fue exitoso.

            # 7a. Notas individuales
            NotaIndividual.objects.filter(
                calificacion__curso_academico=curso_academico
            ).delete()

            # 7b. Calificaciones
            Calificaciones.objects.filter(
                curso_academico=curso_academico
            ).delete()

            # 7c. Asistencias
            Asistencia.objects.filter(
                course__pk__in=cursos_ids
            ).delete()

            # 7d. Respuestas de estudiantes y solicitudes de inscripción
            solicitudes_qs = SolicitudInscripcion.objects.filter(
                curso__pk__in=cursos_ids
            )
            for solicitud in solicitudes_qs:
                RespuestaEstudiante.objects.filter(solicitud=solicitud).delete()
            solicitudes_qs.delete()

            # 7e. Matrículas
            Matriculas.objects.filter(
                curso_academico=curso_academico
            ).delete()

            # 7e-bis. SemestreCurso
            SemestreCurso.objects.filter(curso__curso_academico=curso_academico).delete()

            # 7f. Opciones, preguntas y formularios de aplicación
            formularios_qs = FormularioAplicacion.objects.filter(
                curso__pk__in=cursos_ids
            )
            for formulario in formularios_qs:
                for pregunta in formulario.preguntas.all():
                    OpcionRespuesta.objects.filter(pregunta=pregunta).delete()
                PreguntaFormulario.objects.filter(formulario=formulario).delete()
            formularios_qs.delete()

            # ── 7g. Cursos (al final, después de eliminar todos sus dependientes)
            # IMPORTANTE: antes de eliminar los Curso, desvinculamos las carpetas
            # de documentos para que no se eliminen en cascada. Las carpetas
            # conservan su curso_academico y sus archivos físicos intactos.
            from course_documents.models import DocumentFolder as DocFolder

            # Primero: aseguramos que TODAS las carpetas de estos cursos tengan
            # curso_academico asignado (cubre cursos finalizados sin CA en carpeta)
            carpetas_sin_ca = DocFolder.objects.filter(
                curso__pk__in=cursos_ids,
                curso_academico__isnull=True
            )
            for carpeta in carpetas_sin_ca:
                carpeta.curso_academico = curso_academico
                carpeta.save(update_fields=['curso_academico'])

            # Segundo: desvincular el curso de TODAS las carpetas de estos cursos
            # (usando cursos_ids que incluye todos los cursos del CA, incluso finalizados)
            DocFolder.objects.filter(
                curso__pk__in=cursos_ids
            ).update(curso=None)

            Curso.objects.filter(
                curso_academico=curso_academico
            ).delete()

            logger.info(
                f"Limpieza de principal completada para '{curso_academico.nombre}'."
            )

    except Exception as exc:
        # Registrar el error completo para diagnóstico
        logger.error(
            f"[ArchivadoError] Falló el archivado del CursoAcademico "
            f"'{curso_academico.nombre}' (id={curso_academico.pk}). "
            f"La transacción fue revertida. Los datos de gestión académica "
            f"NO fueron eliminados.",
            exc_info=True,
        )
        # Re-lanzar como ArchivadoError para que el llamador pueda revertir
        # el estado archivado=True del CursoAcademico y mostrar alerta al usuario.
        raise ArchivadoError(
            f"No se pudieron guardar los datos del curso '{curso_academico.nombre}' "
            f"en datos archivados. Los datos de gestión académica se conservan intactos. "
            f"Causa: {exc}"
        ) from exc

    return contadores


def _archivar_semestres_pendientes(curso_academico, contadores):
    """
    Se llama cuando el CursoAcademicoArchivado ya existe (creado previamente
    por terminar_semestre). Archiva los SemestreCurso que aún no tienen
    SemestreCursoArchivado (incluido el semestre activo / último semestre) y
    luego elimina los Curso y SemestreCurso pendientes de principal.

    El semestre activo al momento del archivado (ej. semestre 3) nunca pasó
    por terminar_semestre, por lo que sus matrículas, calificaciones y
    asistencias deben archivarse aquí antes de eliminarlas.
    """
    from datos_archivados.models import (
        CursoAcademicoArchivado,
        CursoArchivado,
        SemestreCursoArchivado,
        UsuarioArchivado,
        MatriculaArchivada,
        CalificacionArchivada,
        NotaIndividualArchivada,
        AsistenciaArchivada,
    )
    from principal.models import (
        Curso, SemestreCurso,
        Matriculas, Calificaciones, NotaIndividual, Asistencia,
        SolicitudInscripcion, RespuestaEstudiante,
        FormularioAplicacion, PreguntaFormulario, OpcionRespuesta,
    )

    ca_archivado = CursoAcademicoArchivado.objects.filter(
        id_original=curso_academico.pk
    ).first()
    if ca_archivado is None:
        logger.error(
            f"[_archivar_semestres_pendientes] No se encontró CursoAcademicoArchivado "
            f"para id_original={curso_academico.pk}. Se omite."
        )
        return contadores

    fecha_archivado = timezone.now().date()

    # Helper de usuario archivado (reutilizable dentro de la transacción)
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
        contadores['usuarios'] += 1
        usuarios_archivados_map[user.pk] = ua
        return ua

    try:
        with transaction.atomic():

            # Obtener todos los cursos del CA que siguen en principal
            cursos_pendientes = list(
                Curso.objects.filter(curso_academico=curso_academico).select_related('teacher')
            )
            cursos_ids = [c.pk for c in cursos_pendientes]

            # Mapa curso.pk → CursoArchivado (para vincular matrículas/calificaciones/asistencias)
            cursos_archivados_map = {}
            # Mapa semestre.pk → SemestreCursoArchivado (para semestres que se crean en este paso)
            semestres_archivados_nuevos_map = {}

            for curso in cursos_pendientes:
                # Buscar el CursoArchivado ya existente para este curso
                curso_archivado = CursoArchivado.objects.filter(
                    id_original=curso.pk
                ).order_by('-pk').first()

                if curso_archivado is None:
                    # Caso inesperado: crear el CursoArchivado si falta
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
                        status=curso.get_dynamic_status(),
                        curso_academico=ca_archivado,
                        enrollment_deadline=curso.enrollment_deadline,
                        start_date=curso.start_date,
                        teacher_actual=curso.teacher,
                    )
                    logger.info(
                        f"CursoArchivado creado para curso '{curso.name}' "
                        f"(id_original={curso.pk}) en _archivar_semestres_pendientes."
                    )
                    contadores['cursos'] += 1

                cursos_archivados_map[curso.pk] = curso_archivado

                # ── Archivar SemestreCurso pendientes ─────────────────────────
                # Incluye el semestre activo (último semestre, ej. semestre 3)
                # que nunca pasó por terminar_semestre.
                semestres = SemestreCurso.objects.filter(
                    curso=curso
                ).order_by('numero_semestre')

                numeros_ya_archivados = set(
                    SemestreCursoArchivado.objects.filter(
                        curso_archivado=curso_archivado
                    ).values_list('numero_semestre', flat=True)
                )

                for semestre in semestres:
                    # Saltar si ya existe un SemestreCursoArchivado para este id_original
                    existente_arch = SemestreCursoArchivado.objects.filter(
                        id_original=semestre.pk
                    ).first()
                    if existente_arch:
                        # Ya archivado (por terminar_semestre previo), registrar en el mapa
                        semestres_archivados_nuevos_map[semestre.pk] = existente_arch
                        numeros_ya_archivados.add(semestre.numero_semestre)
                        continue
                    # Saltar si ya existe uno con el mismo número de semestre para ese curso
                    if semestre.numero_semestre in numeros_ya_archivados:
                        logger.info(
                            f"Semestre {semestre.numero_semestre} de '{curso.name}' "
                            f"ya archivado por número. Se omite id={semestre.pk}."
                        )
                        continue

                    fecha_cierre = semestre.fecha_cierre or fecha_archivado
                    nuevo_sa = SemestreCursoArchivado.objects.create(
                        id_original=semestre.pk,
                        curso_archivado=curso_archivado,
                        numero_semestre=semestre.numero_semestre,
                        activo=False,
                        curso_academico_archivado=ca_archivado,
                        fecha_inicio=semestre.fecha_inicio,
                        fecha_cierre=fecha_cierre,
                        fecha_creacion=semestre.fecha_creacion,
                    )
                    semestres_archivados_nuevos_map[semestre.pk] = nuevo_sa
                    numeros_ya_archivados.add(semestre.numero_semestre)
                    logger.info(
                        f"SemestreCursoArchivado creado: semestre {semestre.numero_semestre} "
                        f"de '{curso.name}' (id_original={semestre.pk})."
                    )

            # ── Archivar Matrículas pendientes (semestre activo) ──────────────
            # Las matrículas que quedaron en principal sin archivar pertenecen
            # al semestre activo (último semestre). Se archivan ahora antes de
            # eliminarlas.
            matriculas_pendientes = Matriculas.objects.filter(
                course__pk__in=cursos_ids
            ).select_related('student', 'course', 'semestre')

            matriculas_archivadas_map = {}

            for matricula in matriculas_pendientes:
                # Evitar duplicado si ya fue archivada (no debería, pero por seguridad)
                if MatriculaArchivada.objects.filter(id_original=matricula.pk).exists():
                    continue

                curso_archivado = cursos_archivados_map.get(matricula.course.pk)
                if not curso_archivado:
                    curso_archivado = CursoArchivado.objects.filter(
                        id_original=matricula.course.pk
                    ).first()
                if not curso_archivado:
                    logger.warning(
                        f"No se encontró CursoArchivado para course.pk={matricula.course.pk}. "
                        f"Se omite matrícula id={matricula.pk}."
                    )
                    continue

                estudiante_archivado = obtener_o_crear_usuario_archivado(matricula.student)

                semestre_arch = None
                if matricula.semestre_id:
                    semestre_arch = semestres_archivados_nuevos_map.get(matricula.semestre_id)
                    if semestre_arch is None:
                        semestre_arch = SemestreCursoArchivado.objects.filter(
                            id_original=matricula.semestre_id
                        ).first()

                ma = MatriculaArchivada.objects.create(
                    id_original=matricula.pk,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_arch,
                    activo=matricula.activo,
                    fecha_matricula=matricula.fecha_matricula,
                    estado=matricula.estado,
                )
                matriculas_archivadas_map[matricula.pk] = ma
                contadores['matriculas'] += 1

            # ── Archivar Calificaciones y Notas pendientes ────────────────────
            calificaciones_pendientes = Calificaciones.objects.filter(
                course__pk__in=cursos_ids
            ).select_related('student', 'course', 'matricula', 'semestre').prefetch_related('notas')

            for calificacion in calificaciones_pendientes:
                if CalificacionArchivada.objects.filter(id_original=calificacion.pk).exists():
                    continue

                curso_archivado = cursos_archivados_map.get(calificacion.course.pk)
                if not curso_archivado:
                    curso_archivado = CursoArchivado.objects.filter(
                        id_original=calificacion.course.pk
                    ).first()
                if not curso_archivado:
                    logger.warning(
                        f"No se encontró CursoArchivado para course.pk={calificacion.course.pk}. "
                        f"Se omite calificación id={calificacion.pk}."
                    )
                    continue

                estudiante_archivado = obtener_o_crear_usuario_archivado(calificacion.student)

                matricula_archivada = None
                if calificacion.matricula_id:
                    matricula_archivada = matriculas_archivadas_map.get(calificacion.matricula_id)
                    if not matricula_archivada:
                        matricula_archivada = MatriculaArchivada.objects.filter(
                            id_original=calificacion.matricula_id
                        ).first()

                if not matricula_archivada:
                    matricula_archivada = MatriculaArchivada.objects.create(
                        id_original=calificacion.pk * -1,
                        course=curso_archivado,
                        student=estudiante_archivado,
                        activo=True,
                        fecha_matricula=calificacion.course.start_date or fecha_archivado,
                        estado='P',
                    )
                    contadores['matriculas'] += 1

                semestre_arch = None
                if calificacion.semestre_id:
                    semestre_arch = semestres_archivados_nuevos_map.get(calificacion.semestre_id)
                    if semestre_arch is None:
                        semestre_arch = SemestreCursoArchivado.objects.filter(
                            id_original=calificacion.semestre_id
                        ).first()

                calificacion_archivada = CalificacionArchivada.objects.create(
                    id_original=calificacion.pk,
                    matricula=matricula_archivada,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_arch,
                    average=calificacion.average,
                )
                contadores['calificaciones'] += 1

                for nota in calificacion.notas.all():
                    if not NotaIndividualArchivada.objects.filter(id_original=nota.pk).exists():
                        NotaIndividualArchivada.objects.create(
                            id_original=nota.pk,
                            calificacion=calificacion_archivada,
                            valor=nota.valor if nota.valor is not None else 0,
                            fecha_creacion=nota.fecha_creacion,
                        )
                        contadores['notas'] += 1

            # ── Archivar Asistencias pendientes ───────────────────────────────
            asistencias_pendientes = Asistencia.objects.filter(
                course__pk__in=cursos_ids
            ).select_related('student', 'course', 'semestre')

            for asistencia in asistencias_pendientes:
                if AsistenciaArchivada.objects.filter(id_original=asistencia.pk).exists():
                    continue

                curso_archivado = cursos_archivados_map.get(asistencia.course.pk)
                if not curso_archivado:
                    curso_archivado = CursoArchivado.objects.filter(
                        id_original=asistencia.course.pk
                    ).first()
                if not curso_archivado:
                    continue

                estudiante_archivado = obtener_o_crear_usuario_archivado(asistencia.student)

                semestre_arch = None
                if asistencia.semestre_id:
                    semestre_arch = semestres_archivados_nuevos_map.get(asistencia.semestre_id)
                    if semestre_arch is None:
                        semestre_arch = SemestreCursoArchivado.objects.filter(
                            id_original=asistencia.semestre_id
                        ).first()

                AsistenciaArchivada.objects.create(
                    id_original=asistencia.pk,
                    course=curso_archivado,
                    student=estudiante_archivado,
                    semestre_archivado=semestre_arch,
                    presente=asistencia.presente,
                    date=asistencia.date,
                )
                contadores['asistencias'] += 1

            logger.info(
                f"_archivar_semestres_pendientes: datos del semestre activo archivados para "
                f"'{curso_academico.nombre}': {contadores['matriculas']} matrículas, "
                f"{contadores['calificaciones']} calificaciones, "
                f"{contadores.get('notas', 0)} notas, "
                f"{contadores['asistencias']} asistencias."
            )

            # ── Limpiar datos de principal para estos cursos ──────────────────

            # Solicitudes de inscripción
            solicitudes_qs = SolicitudInscripcion.objects.filter(curso__pk__in=cursos_ids)
            for solicitud in solicitudes_qs:
                RespuestaEstudiante.objects.filter(solicitud=solicitud).delete()
            solicitudes_qs.delete()

            # Formularios de aplicación
            formularios_qs = FormularioAplicacion.objects.filter(curso__pk__in=cursos_ids)
            for formulario in formularios_qs:
                for pregunta in formulario.preguntas.all():
                    OpcionRespuesta.objects.filter(pregunta=pregunta).delete()
                PreguntaFormulario.objects.filter(formulario=formulario).delete()
            formularios_qs.delete()

            # Notas, calificaciones, asistencias, matrículas residuales
            NotaIndividual.objects.filter(calificacion__course__pk__in=cursos_ids).delete()
            Calificaciones.objects.filter(course__pk__in=cursos_ids).delete()
            Asistencia.objects.filter(course__pk__in=cursos_ids).delete()
            Matriculas.objects.filter(course__pk__in=cursos_ids).delete()

            # SemestreCurso
            SemestreCurso.objects.filter(curso__pk__in=cursos_ids).delete()

            # Carpetas de documentos: desvincular curso antes de eliminar
            from course_documents.models import DocumentFolder as DocFolder
            carpetas_sin_ca = DocFolder.objects.filter(
                curso__pk__in=cursos_ids,
                curso_academico__isnull=True
            )
            for carpeta in carpetas_sin_ca:
                carpeta.curso_academico = curso_academico
                carpeta.save(update_fields=['curso_academico'])
            DocFolder.objects.filter(curso__pk__in=cursos_ids).update(curso=None)

            # Eliminar Cursos
            Curso.objects.filter(curso_academico=curso_academico).delete()

            logger.info(
                f"_archivar_semestres_pendientes completado para "
                f"'{curso_academico.nombre}': {len(cursos_pendientes)} cursos procesados."
            )

    except Exception as exc:
        logger.error(
            f"[_archivar_semestres_pendientes] Falló para '{curso_academico.nombre}'. "
            f"Transacción revertida.",
            exc_info=True,
        )
        raise ArchivadoError(
            f"No se pudieron archivar los semestres pendientes de '{curso_academico.nombre}'. "
            f"Causa: {exc}"
        ) from exc

    return contadores
