"""
Servicio para restaurar los datos de un CursoAcademico archivado
cuando este vuelve a activarse.

Proceso inverso al archivado:
  1. Lee los datos de datos_archivados (CursoArchivado, MatriculaArchivada, etc.)
  2. Recrea los registros en la app principal (Curso, Matriculas, etc.)
  3. Elimina los registros de datos_archivados correspondientes a ese CA.

Condición de uso:
  - Solo se ejecuta si NO hay ningún CursoAcademico activo en el sistema
    (para evitar conflictos con datos del curso activo actual).
  - Solo se ejecuta si el CursoAcademico tiene datos archivados en datos_archivados.

Manejo de errores:
  - Si la restauración falla, se lanza RestauradoError con mensaje descriptivo.
  - La transacción atómica garantiza que NINGÚN dato parcial queda en principal
    si la restauración no se completó correctamente.
  - El llamador debe capturar RestauradoError y mostrar el error al usuario.
"""

import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class RestauradoError(Exception):
    """
    Excepción lanzada cuando el proceso de restauración de un CursoAcademico falla.
    """
    pass


def hay_datos_archivados(curso_academico):
    """
    Verifica si un CursoAcademico tiene datos guardados en datos_archivados.

    Retorna True si existe un CursoAcademicoArchivado con id_original == curso_academico.pk.
    """
    from datos_archivados.models import CursoAcademicoArchivado
    return CursoAcademicoArchivado.objects.filter(
        id_original=curso_academico.pk
    ).exists()


def restaurar_datos_curso_academico(curso_academico):
    """
    Restaura todos los datos de un CursoAcademico archivado de vuelta a la app principal.

    Parámetros:
        curso_academico: instancia de principal.CursoAcademico ya marcada como activo=True.

    Retorna:
        dict con contadores de registros restaurados,
        o None si no hay datos archivados para este curso.

    Lanza:
        RestauradoError si el proceso falla.
    """
    from datos_archivados.models import (
        CursoAcademicoArchivado,
        CursoArchivado,
        MatriculaArchivada,
        CalificacionArchivada,
        NotaIndividualArchivada,
        AsistenciaArchivada,
    )
    from principal.models import (
        Curso, Matriculas, Calificaciones, NotaIndividual, Asistencia,
    )
    from django.contrib.auth.models import User

    # Buscar el snapshot archivado
    try:
        ca_archivado = CursoAcademicoArchivado.objects.get(
            id_original=curso_academico.pk
        )
    except CursoAcademicoArchivado.DoesNotExist:
        logger.info(
            f"No hay datos archivados para CursoAcademico '{curso_academico.nombre}' "
            f"(id={curso_academico.pk}). No se restaura nada."
        )
        return None

    contadores = {
        'cursos': 0,
        'matriculas': 0,
        'calificaciones': 0,
        'notas': 0,
        'asistencias': 0,
    }

    try:
        with transaction.atomic():

            # ── 1. Restaurar Cursos ───────────────────────────────────────────
            # Mapa id_original → Curso (nuevo) para resolver FKs
            cursos_map = {}  # CursoArchivado.pk → Curso

            cursos_archivados = CursoArchivado.objects.filter(
                curso_academico=ca_archivado
            ).select_related('teacher_actual')

            for ca in cursos_archivados:
                # Resolver el profesor: usar teacher_actual si existe,
                # si no buscar por id_original
                teacher = ca.teacher_actual
                if teacher is None:
                    teacher = User.objects.filter(pk=ca.teacher_id_original).first()
                if teacher is None:
                    logger.warning(
                        f"No se encontró profesor para CursoArchivado '{ca.name}' "
                        f"(teacher_id_original={ca.teacher_id_original}). Se omite."
                    )
                    continue

                # Crear el Curso en principal
                curso = Curso.objects.create(
                    name=ca.name,
                    description=ca.description,
                    area=ca.area,
                    tipo=ca.tipo,
                    teacher=teacher,
                    class_quantity=ca.class_quantity,
                    status=ca.status,
                    curso_academico=curso_academico,
                    enrollment_deadline=ca.enrollment_deadline,
                    start_date=ca.start_date,
                )
                # Restaurar imagen si existe y el archivo físico sigue en disco
                if ca.image:
                    import os
                    from django.conf import settings
                    ruta_absoluta = os.path.join(settings.MEDIA_ROOT, ca.image)
                    if os.path.exists(ruta_absoluta):
                        curso.image = ca.image
                        curso.save(update_fields=['image'])
                cursos_map[ca.pk] = curso
                contadores['cursos'] += 1
                logger.debug(f"Curso restaurado: '{curso.name}' (id={curso.pk})")

            # ── 1b. Restaurar SemestreCurso ──────────────────────────────────
            from datos_archivados.models import SemestreCursoArchivado
            from principal.models import SemestreCurso

            for ca in cursos_archivados:
                curso_nuevo = cursos_map.get(ca.pk)
                if curso_nuevo is None:
                    continue
                semestres_archivados = SemestreCursoArchivado.objects.filter(
                    curso_archivado=ca
                )
                for sa in semestres_archivados:
                    # Evitar duplicados usando id_original
                    if SemestreCurso.objects.filter(pk=sa.id_original).exists():
                        logger.debug(
                            f"SemestreCurso id={sa.id_original} ya existe. Se omite."
                        )
                        continue
                    SemestreCurso.objects.create(
                        pk=sa.id_original,
                        curso=curso_nuevo,
                        numero_semestre=sa.numero_semestre,
                        activo=sa.activo,
                        curso_academico=curso_academico,
                        fecha_inicio=sa.fecha_inicio,
                        fecha_cierre=sa.fecha_cierre,
                        fecha_creacion=sa.fecha_creacion,
                    )
                    logger.debug(
                        f"SemestreCurso restaurado: semestre={sa.numero_semestre}, "
                        f"curso='{curso_nuevo.name}'"
                    )

            # ── 2. Restaurar Matrículas ───────────────────────────────────────
            # Mapa MatriculaArchivada.pk → Matriculas (nueva)
            matriculas_map = {}

            matriculas_archivadas = MatriculaArchivada.objects.filter(
                course__curso_academico=ca_archivado
            ).select_related('course', 'student__usuario_actual')

            for ma in matriculas_archivadas:
                curso = cursos_map.get(ma.course.pk)
                if curso is None:
                    logger.warning(
                        f"No se encontró Curso restaurado para MatriculaArchivada "
                        f"id={ma.pk}. Se omite."
                    )
                    continue

                # Resolver el estudiante
                student = None
                if ma.student.usuario_actual:
                    student = ma.student.usuario_actual
                else:
                    student = User.objects.filter(pk=ma.student.id_original).first()
                if student is None:
                    logger.warning(
                        f"No se encontró estudiante para MatriculaArchivada id={ma.pk}. "
                        f"Se omite."
                    )
                    continue

                # Evitar duplicados (unique_together: student, course, curso_academico)
                matricula, created = Matriculas.objects.get_or_create(
                    course=curso,
                    student=student,
                    curso_academico=curso_academico,
                    defaults={
                        'activo': ma.activo,
                        'fecha_matricula': ma.fecha_matricula,
                        'estado': ma.estado,
                    }
                )
                if created:
                    matriculas_map[ma.pk] = matricula
                    contadores['matriculas'] += 1
                else:
                    # Ya existía (raro, pero posible si se restauró parcialmente antes)
                    matriculas_map[ma.pk] = matricula
                    logger.debug(
                        f"Matrícula ya existía: student={student.username}, "
                        f"course={curso.name}"
                    )

            # ── 3. Restaurar Calificaciones y Notas Individuales ─────────────
            calificaciones_archivadas = CalificacionArchivada.objects.filter(
                course__curso_academico=ca_archivado
            ).select_related('course', 'student__usuario_actual', 'matricula')

            for cala in calificaciones_archivadas:
                curso = cursos_map.get(cala.course.pk)
                if curso is None:
                    continue

                # Resolver estudiante
                student = None
                if cala.student.usuario_actual:
                    student = cala.student.usuario_actual
                else:
                    student = User.objects.filter(pk=cala.student.id_original).first()
                if student is None:
                    continue

                # Resolver matrícula
                matricula = matriculas_map.get(cala.matricula.pk) if cala.matricula else None
                if matricula is None:
                    # Intentar buscar por student+course+curso_academico
                    matricula = Matriculas.objects.filter(
                        course=curso,
                        student=student,
                        curso_academico=curso_academico,
                    ).first()

                # Evitar duplicados (unique_together: course, student, curso_academico)
                calificacion, created = Calificaciones.objects.get_or_create(
                    course=curso,
                    student=student,
                    curso_academico=curso_academico,
                    defaults={
                        'matricula': matricula,
                        'average': cala.average,
                    }
                )
                if not created:
                    # Actualizar matrícula y promedio si ya existía
                    if matricula and calificacion.matricula is None:
                        calificacion.matricula = matricula
                        calificacion.save(update_fields=['matricula'])
                    logger.debug(
                        f"Calificación ya existía: student={student.username}, "
                        f"course={curso.name}"
                    )

                if created:
                    contadores['calificaciones'] += 1

                # Restaurar notas individuales (solo si la calificación fue creada nueva
                # o si no tiene notas aún)
                if not calificacion.notas.exists():
                    notas_archivadas = NotaIndividualArchivada.objects.filter(
                        calificacion=cala
                    )
                    for na in notas_archivadas:
                        NotaIndividual.objects.create(
                            calificacion=calificacion,
                            valor=na.valor,
                            fecha_creacion=na.fecha_creacion,
                        )
                        contadores['notas'] += 1

            # ── 4. Restaurar Asistencias ──────────────────────────────────────
            asistencias_archivadas = AsistenciaArchivada.objects.filter(
                course__curso_academico=ca_archivado
            ).select_related('course', 'student__usuario_actual')

            for aa in asistencias_archivadas:
                curso = cursos_map.get(aa.course.pk)
                if curso is None:
                    continue

                # Resolver estudiante
                student = None
                if aa.student.usuario_actual:
                    student = aa.student.usuario_actual
                else:
                    student = User.objects.filter(pk=aa.student.id_original).first()
                if student is None:
                    continue

                # Evitar duplicados (unique_together: student, date, course)
                _, created = Asistencia.objects.get_or_create(
                    course=curso,
                    student=student,
                    date=aa.date,
                    defaults={'presente': aa.presente},
                )
                if created:
                    contadores['asistencias'] += 1

            # ── 5. Reconectar carpetas de documentos ─────────────────────────
            # Al archivar, las DocumentFolder quedaron con curso=None pero
            # conservaron curso_academico y curso_id_original.
            # Las reconectamos al Curso restaurado usando curso_id_original.
            from course_documents.models import DocumentFolder

            for ca in cursos_archivados:
                curso_nuevo = cursos_map.get(ca.pk)
                if curso_nuevo is None:
                    continue

                reconectadas = DocumentFolder.objects.filter(
                    curso__isnull=True,
                    curso_academico=curso_academico,
                    curso_id_original=ca.id_original,
                )
                if reconectadas.exists():
                    reconectadas.update(curso=curso_nuevo)
                    contadores['carpetas_documentos'] = (
                        contadores.get('carpetas_documentos', 0) + reconectadas.count()
                    )

            logger.info(
                f"Carpetas de documentos reconectadas: "
                f"{contadores.get('carpetas_documentos', 0)}"
            )

            logger.info(
                f"Restauración completada para '{curso_academico.nombre}': "
                f"{contadores['cursos']} cursos, "
                f"{contadores['matriculas']} matrículas, "
                f"{contadores['calificaciones']} calificaciones, "
                f"{contadores['notas']} notas, "
                f"{contadores['asistencias']} asistencias, "
                f"{contadores.get('carpetas_documentos', 0)} carpetas de documentos."
            )

            # ── 5. Eliminar datos de datos_archivados ─────────────────────────
            # El orden importa: primero los hijos, luego los padres.
            # Solo se ejecuta si todo lo anterior fue exitoso.

            # Obtener IDs de cursos archivados de este CA para filtrar en cascada
            cursos_archivados_ids = list(
                CursoArchivado.objects.filter(
                    curso_academico=ca_archivado
                ).values_list('pk', flat=True)
            )

            # 5a. Notas individuales archivadas
            NotaIndividualArchivada.objects.filter(
                calificacion__course__pk__in=cursos_archivados_ids
            ).delete()

            # 5b. Calificaciones archivadas
            CalificacionArchivada.objects.filter(
                course__pk__in=cursos_archivados_ids
            ).delete()

            # 5c. Asistencias archivadas
            AsistenciaArchivada.objects.filter(
                course__pk__in=cursos_archivados_ids
            ).delete()

            # 5d. Matrículas archivadas
            MatriculaArchivada.objects.filter(
                course__pk__in=cursos_archivados_ids
            ).delete()

            # 5d-bis. SemestreCursoArchivado
            SemestreCursoArchivado.objects.filter(
                curso_archivado__pk__in=cursos_archivados_ids
            ).delete()

            # 5e. Cursos archivados
            CursoArchivado.objects.filter(
                curso_academico=ca_archivado
            ).delete()

            # 5f. CursoAcademicoArchivado
            ca_archivado.delete()

            logger.info(
                f"Datos archivados eliminados para '{curso_academico.nombre}'."
            )

    except Exception as exc:
        logger.error(
            f"[RestauradoError] Falló la restauración del CursoAcademico "
            f"'{curso_academico.nombre}' (id={curso_academico.pk}). "
            f"La transacción fue revertida. Los datos archivados se conservan intactos.",
            exc_info=True,
        )
        raise RestauradoError(
            f"No se pudieron restaurar los datos del curso '{curso_academico.nombre}'. "
            f"Los datos archivados se conservan intactos. "
            f"Causa: {exc}"
        ) from exc

    return contadores
