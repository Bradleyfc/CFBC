"""
Módulo para guardar datos de tablas de docencia en modelos históricos.

Este módulo contiene la lógica para detectar y guardar datos de las 11 tablas
de docencia en sus correspondientes modelos históricos en la app historial.
"""

import logging
from django.db import transaction
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from mapeos_campos_docencia import aplicar_mapeo_campos


# Mapeo de tablas de docencia a modelos históricos
DOCENCIA_TABLES_MAPPING = {
    'Docencia_area': 'HistoricalArea',
    'Docencia_coursecategory': 'HistoricalCourseCategory',
    'Docencia_courseinformation_adminteachers': 'HistoricalCourseInformationAdminTeachers',
    'Docencia_courseinformation': 'HistoricalCourseInformation',
    'Docencia_enrollmentapplication': 'HistoricalEnrollmentApplication',
    'Docencia_enrollmentpay': 'HistoricalEnrollmentPay',
    'Docencia_accountnumber': 'HistoricalAccountNumber',
    'Docencia_enrollment': 'HistoricalEnrollment',
    'Docencia_subjectinformation': 'HistoricalSubjectInformation',
    'Docencia_edition': 'HistoricalEdition',
    'Docencia_application': 'HistoricalApplication',
}


def es_tabla_docencia(tabla_nombre):
    """
    Verifica si una tabla es una tabla de docencia que debe guardarse en historial.
    
    Args:
        tabla_nombre: Nombre de la tabla a verificar
        
    Returns:
        bool: True si es una tabla de docencia, False en caso contrario
    """
    return tabla_nombre in DOCENCIA_TABLES_MAPPING


def son_todas_tablas_docencia(tablas_seleccionadas):
    """
    Verifica si todas las tablas seleccionadas son tablas de docencia.
    
    Args:
        tablas_seleccionadas: Lista de nombres de tablas
        
    Returns:
        bool: True si todas son tablas de docencia, False en caso contrario
    """

    return all(es_tabla_docencia(tabla) for tabla in tablas_seleccionadas)


def copiar_campos_a_modelo_historico(objeto_destino, datos_origen, campos_excluir=None, logger=None):
    """
    Copia campos dinámicamente de datos_origen a objeto_destino.
    
    Args:
        objeto_destino: Instancia del modelo histórico
        datos_origen: Diccionario con los datos originales
        campos_excluir: Lista de campos a excluir de la copia
        logger: Logger para registrar operaciones
    """
    if campos_excluir is None:
        campos_excluir = ['id', 'pk']
    
    campos_copiados = 0
    for campo, valor in datos_origen.items():
        if campo in campos_excluir:
            continue
        
        try:
            if hasattr(objeto_destino, campo):
                # Convertir valores especiales
                if valor == 'NULL' or valor == 'null':
                    valor = None
                elif isinstance(valor, str) and valor.lower() in ['true', 'false']:
                    valor = valor.lower() == 'true'
                
                setattr(objeto_destino, campo, valor)
                campos_copiados += 1
        except Exception as e:
            if logger:
                logger.warning(f"No se pudo copiar campo {campo}: {str(e)}")
    
    if logger:
        logger.debug(f"Campos copiados: {campos_copiados}")
    
    return campos_copiados
def completar_campos_obligatorios(objeto_destino, logger=None):
    """
    Completa campos obligatorios con valores por defecto si están vacíos.

    Args:
        objeto_destino: Instancia del modelo histórico
        logger: Logger para registrar operaciones
    """
    from django.db import models
    from django.utils import timezone

    campos_completados = 0

    # Iterar sobre todos los campos del modelo
    for field in objeto_destino._meta.fields:
        # Saltar campos que permiten null o tienen default
        if field.null or field.has_default():
            continue

        # Saltar campos de auditoría que ya deben estar establecidos
        if field.name in ['id', 'id_original', 'tabla_origen', 'fecha_consolidacion', 'dato_archivado']:
            continue

        # Obtener el valor actual
        valor_actual = getattr(objeto_destino, field.name, None)

        # Si el campo está vacío, asignar un valor por defecto según el tipo
        if valor_actual is None or valor_actual == '':
            if isinstance(field, models.BooleanField):
                setattr(objeto_destino, field.name, False)
                campos_completados += 1
                if logger:
                    logger.debug(f"Campo {field.name} (Boolean) completado con False")

            elif isinstance(field, models.DateTimeField):
                setattr(objeto_destino, field.name, timezone.now())
                campos_completados += 1
                if logger:
                    logger.debug(f"Campo {field.name} (DateTime) completado con fecha actual")

            elif isinstance(field, models.DateField):
                setattr(objeto_destino, field.name, timezone.now().date())
                campos_completados += 1
                if logger:
                    logger.debug(f"Campo {field.name} (Date) completado con fecha actual")

            elif isinstance(field, models.CharField):
                setattr(objeto_destino, field.name, '')
                campos_completados += 1
                if logger:
                    logger.debug(f"Campo {field.name} (Char) completado con cadena vacía")

            elif isinstance(field, models.IntegerField):
                setattr(objeto_destino, field.name, 0)
                campos_completados += 1
                if logger:
                    logger.debug(f"Campo {field.name} (Integer) completado con 0")

            elif isinstance(field, models.DecimalField):
                setattr(objeto_destino, field.name, 0)
                campos_completados += 1
                if logger:
                    logger.debug(f"Campo {field.name} (Decimal) completado con 0")

    return campos_completados



def guardar_datos_docencia_en_historial(tablas_seleccionadas, logger=None):
    """
    Guarda los datos de las tablas de docencia seleccionadas en los modelos históricos.
    
    Args:
        tablas_seleccionadas: Lista de nombres de tablas de docencia
        logger: Logger para registrar operaciones
        
    Returns:
        dict: Estadísticas de la operación con contadores por tabla
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    from .models import DatoArchivadoDinamico
    from historial.models import (
        HistoricalArea,
        HistoricalCourseCategory,
        HistoricalCourseInformation,
        HistoricalCourseInformationAdminTeachers,
        HistoricalEnrollmentApplication,
        HistoricalEnrollmentPay,
        HistoricalAccountNumber,
        HistoricalEnrollment,
        HistoricalSubjectInformation,
        HistoricalEdition,
        HistoricalApplication,
    )
    
    # Mapeo de modelos históricos
    modelos_historicos = {
        'Docencia_area': HistoricalArea,
        'Docencia_coursecategory': HistoricalCourseCategory,
        'Docencia_courseinformation': HistoricalCourseInformation,

        'Docencia_courseinformation_adminteachers': HistoricalCourseInformationAdminTeachers,
        'Docencia_enrollmentapplication': HistoricalEnrollmentApplication,
        'Docencia_enrollmentpay': HistoricalEnrollmentPay,
        'Docencia_accountnumber': HistoricalAccountNumber,
        'Docencia_enrollment': HistoricalEnrollment,
        'Docencia_subjectinformation': HistoricalSubjectInformation,
        'Docencia_edition': HistoricalEdition,
        'Docencia_application': HistoricalApplication,
    }
    
    # Estadísticas
    estadisticas = {
        'total_registros_guardados': 0,
        'tablas_procesadas': 0,
        'errores': 0,
    }
    
    # Mapeos para mantener relaciones FK
    mapeo_areas = {}
    mapeo_categorias = {}
    mapeo_cursos = {}
    mapeo_asignaturas = {}
    mapeo_ediciones = {}
    mapeo_solicitudes = {}
    mapeo_cuentas = {}
    
    # Orden de procesamiento para respetar dependencias FK
    orden_procesamiento = [
        'Docencia_area',
        'Docencia_coursecategory',
        'Docencia_courseinformation',
        'Docencia_courseinformation_adminteachers',
        'Docencia_subjectinformation',
        'Docencia_edition',
        'Docencia_enrollmentapplication',
        'Docencia_accountnumber',
        'Docencia_enrollmentpay',
        'Docencia_enrollment',
        'Docencia_application',
    ]
    
    logger.info("=== INICIANDO GUARDADO DE DATOS DE DOCENCIA EN HISTORIAL ===")
    logger.info(f"Tablas a procesar: {tablas_seleccionadas}")
    
    try:
        # Procesar tablas en orden
        for tabla in orden_procesamiento:
            if tabla not in tablas_seleccionadas:
                continue
            
            logger.info(f"\n--- Procesando tabla: {tabla} ---")
            
            # Obtener datos de la tabla
            datos_tabla = DatoArchivadoDinamico.objects.filter(tabla_origen=tabla)
            total_registros = datos_tabla.count()
            logger.info(f"Encontrados {total_registros} registros en {tabla}")
            
            if total_registros == 0:
                logger.warning(f"No hay registros para procesar en {tabla}")
                continue
            
            # Obtener modelo histórico correspondiente
            ModeloHistorico = modelos_historicos.get(tabla)
            if not ModeloHistorico:
                logger.error(f"No se encontró modelo histórico para {tabla}")
                continue
            
            registros_guardados = 0
            
            # Procesar según la tabla
            if tabla == 'Docencia_area':
                registros_guardados = _procesar_areas(
                    datos_tabla, ModeloHistorico, mapeo_areas, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )

            
            elif tabla == 'Docencia_coursecategory':
                registros_guardados = _procesar_categorias(
                    datos_tabla, ModeloHistorico, mapeo_categorias, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_courseinformation':
                registros_guardados = _procesar_cursos(
                    datos_tabla, ModeloHistorico, mapeo_cursos, 
                    mapeo_areas, mapeo_categorias, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_courseinformation_adminteachers':
                registros_guardados = _procesar_admin_teachers(
                    datos_tabla, ModeloHistorico, mapeo_cursos, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_subjectinformation':
                registros_guardados = _procesar_asignaturas(
                    datos_tabla, ModeloHistorico, mapeo_asignaturas, mapeo_cursos, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_edition':
                registros_guardados = _procesar_ediciones(
                    datos_tabla, ModeloHistorico, mapeo_ediciones, mapeo_cursos, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_enrollmentapplication':
                registros_guardados = _procesar_solicitudes(
                    datos_tabla, ModeloHistorico, mapeo_solicitudes, mapeo_cursos, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_accountnumber':
                registros_guardados = _procesar_cuentas(
                    datos_tabla, ModeloHistorico, mapeo_cuentas, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_enrollmentpay':
                registros_guardados = _procesar_pagos(
                    datos_tabla, ModeloHistorico, mapeo_solicitudes, mapeo_cuentas, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_enrollment':
                registros_guardados = _procesar_inscripciones(
                    datos_tabla, ModeloHistorico, mapeo_asignaturas, mapeo_ediciones, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            elif tabla == 'Docencia_application':
                registros_guardados = _procesar_aplicaciones(
                    datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_ediciones, logger,
                    estadisticas, tablas_seleccionadas, tabla
                )
            
            # Actualizar estadísticas
            estadisticas['total_registros_guardados'] += registros_guardados
            estadisticas['tablas_procesadas'] += 1
            estadisticas[f'{tabla}_guardados'] = registros_guardados
            
            logger.info(f"✅ {tabla}: {registros_guardados} registros guardados en historial")
            
            # Actualizar progreso en cache con información de la tabla completada
            _actualizar_progreso_cache(
                tabla, 
                estadisticas, 
                tablas_seleccionadas,
                registros_procesados=total_registros,  # Tabla completada
                total_registros=total_registros
            )
        
        logger.info("\n=== GUARDADO EN HISTORIAL COMPLETADO EXITOSAMENTE ===")
        logger.info(f"Total de registros guardados: {estadisticas['total_registros_guardados']}")
        logger.info(f"Tablas procesadas: {estadisticas['tablas_procesadas']}")
        
        return estadisticas
        
    except Exception as e:
        logger.error(f"Error guardando datos en historial: {str(e)}", exc_info=True)
        estadisticas['error'] = str(e)
        raise




def _procesar_areas(datos_tabla, ModeloHistorico, mapeo_areas, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda áreas en HistoricalArea."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_area')
                
                # Crear nueva área histórica
                area = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_area',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(area, datos_mapeados, campos_excluir=['id', 'pk'], logger=logger)
                completar_campos_obligatorios(area, logger=logger)
                area.save()
                
                # Guardar mapeo
                mapeo_areas[id_original] = area
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Área guardada: {area.nombre} (ID original: {id_original})")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando área: {str(e)}")
                continue
    
    return registros_guardados


def _procesar_categorias(datos_tabla, ModeloHistorico, mapeo_categorias, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda categorías en HistoricalCourseCategory."""
    registros_guardados = 0
    
    # Primer paso: crear todas las categorías sin parent
    categorias_pendientes = []
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)

    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                parent_id = datos.get('parent_id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_coursecategory')
                
                # Crear categoría
                categoria = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_coursecategory',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    categoria, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'parent_id', 'parent'], 
                    logger=logger
                )
                completar_campos_obligatorios(categoria, logger=logger)
                categoria.save()
                
                # Guardar mapeo
                mapeo_categorias[id_original] = categoria
                registros_guardados += 1
                
                # Si tiene parent, guardar para procesar después
                if parent_id:
                    categorias_pendientes.append((categoria, parent_id))
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Categoría guardada: {categoria.nombre} (ID original: {id_original})")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando categoría: {str(e)}")
                continue
    
    # Segundo paso: asignar relaciones parent
    with transaction.atomic():
        for categoria, parent_id in categorias_pendientes:
            try:
                if parent_id in mapeo_categorias:
                    categoria.parent = mapeo_categorias[parent_id]
                    completar_campos_obligatorios(categoria, logger=logger)
                    categoria.save()
                    logger.debug(f"Parent asignado a categoría {categoria.nombre}")
            except Exception as e:
                logger.error(f"Error asignando parent a categoría: {str(e)}")
    
    return registros_guardados




def _procesar_cursos(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_areas, mapeo_categorias, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda cursos en HistoricalCourseInformation."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                area_id = datos.get('area_id')
                categoria_id = datos.get('categoria_id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_courseinformation')
                
                # Crear curso
                curso = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_courseinformation',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    curso, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'area_id', 'categoria_id', 'area', 'categoria'], 
                    logger=logger
                )
                
                # Asignar relaciones FK
                if area_id and area_id in mapeo_areas:
                    curso.area = mapeo_areas[area_id]
                
                if categoria_id and categoria_id in mapeo_categorias:
                    curso.categoria = mapeo_categorias[categoria_id]
                
                completar_campos_obligatorios(curso, logger=logger)
                curso.save()
                
                # Guardar mapeo
                mapeo_cursos[id_original] = curso
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Curso guardado: {curso.nombre} (ID original: {id_original})")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando curso: {str(e)}")
                continue
    
    return registros_guardados


def _procesar_admin_teachers(datos_tabla, ModeloHistorico, mapeo_cursos, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda relaciones curso-profesor en HistoricalCourseInformationAdminTeachers."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                curso_id = datos.get('courseinformation_id')
                profesor_id = datos.get('user_id')
                
                # Validar que existan las relaciones
                if not curso_id or curso_id not in mapeo_cursos:
                    logger.warning(f"Curso no encontrado: {curso_id}")
                    transaction.savepoint_rollback(sid)
                    continue
                
                if not profesor_id:
                    logger.warning(f"Profesor ID no encontrado")
                    transaction.savepoint_rollback(sid)
                    continue
                
                try:
                    profesor = User.objects.get(id=profesor_id)
                except User.DoesNotExist:
                    logger.warning(f"Usuario profesor no encontrado: {profesor_id}")
                    transaction.savepoint_rollback(sid)
                    continue
                
                curso = mapeo_cursos[curso_id]
                id_original = datos.get('id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_courseinformation_adminteachers')
                
                # Crear relación (evitar duplicados)
                relacion, created = ModeloHistorico.objects.get_or_create(
                    id_original=id_original,
                    tabla_origen='Docencia_courseinformation_adminteachers',
                    dato_archivado=dato,
                    defaults={
                        'curso': curso,
                        'profesor': profesor
                    }
                )
                
                if created:
                    registros_guardados += 1
                    logger.debug(f"Relación curso-profesor guardada: {curso.nombre} - {profesor.username}")
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando admin teacher: {str(e)}")
                continue
    
    return registros_guardados




def _procesar_asignaturas(datos_tabla, ModeloHistorico, mapeo_asignaturas, mapeo_cursos, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda asignaturas en HistoricalSubjectInformation."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                curso_id = datos.get('curso_id', datos.get('course_id'))
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_subjectinformation')
                
                # Crear asignatura
                asignatura = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_subjectinformation',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    asignatura, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'curso_id', 'course_id', 'curso', 'course'], 
                    logger=logger
                )
                
                # Asignar relación FK
                if curso_id and curso_id in mapeo_cursos:
                    asignatura.curso = mapeo_cursos[curso_id]
                
                completar_campos_obligatorios(asignatura, logger=logger)
                asignatura.save()
                
                # Guardar mapeo
                mapeo_asignaturas[id_original] = asignatura
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Asignatura guardada: {asignatura.nombre} (ID original: {id_original})")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando asignatura: {str(e)}")
                continue
    
    return registros_guardados


def _procesar_ediciones(datos_tabla, ModeloHistorico, mapeo_ediciones, mapeo_cursos, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda ediciones en HistoricalEdition."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                curso_id = datos.get('curso_id', datos.get('course_id'))
                instructor_id = datos.get('instructor_id')
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_edition')
                
                # Crear edición
                edicion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_edition',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    edicion, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'curso_id', 'course_id', 'instructor_id', 'curso', 'course', 'instructor'], 
                    logger=logger
                )
                
                # Asignar relaciones FK
                if curso_id and curso_id in mapeo_cursos:
                    edicion.curso = mapeo_cursos[curso_id]
                
                if instructor_id:
                    try:
                        instructor = User.objects.get(id=instructor_id)
                        edicion.instructor = instructor
                    except User.DoesNotExist:
                        logger.warning(f"Instructor no encontrado: {instructor_id}")
                
                completar_campos_obligatorios(edicion, logger=logger)
                edicion.save()
                
                # Guardar mapeo
                mapeo_ediciones[id_original] = edicion
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Edición guardada: {edicion.nombre} (ID original: {id_original})")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando edición: {str(e)}")
                continue
    
    return registros_guardados




def _procesar_solicitudes(datos_tabla, ModeloHistorico, mapeo_solicitudes, mapeo_cursos, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda solicitudes de inscripción en HistoricalEnrollmentApplication."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                curso_id = datos.get('curso_id', datos.get('course_id'))
                usuario_id = datos.get('usuario_id', datos.get('user_id', datos.get('student_id')))
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_enrollmentapplication')
                
                # Crear solicitud
                solicitud = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollmentapplication',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    solicitud, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'curso_id', 'course_id', 'usuario_id', 'user_id', 'curso', 'course', 'usuario', 'user'], 
                    logger=logger
                )
                
                # Asignar relaciones FK
                if curso_id and curso_id in mapeo_cursos:
                    solicitud.curso = mapeo_cursos[curso_id]
                
                if usuario_id:
                    try:
                        usuario = User.objects.get(id=usuario_id)
                        solicitud.usuario = usuario
                    except User.DoesNotExist:
                        logger.warning(f"Usuario no encontrado: {usuario_id}")
                
                completar_campos_obligatorios(solicitud, logger=logger)
                solicitud.save()
                
                # Guardar mapeo
                mapeo_solicitudes[id_original] = solicitud
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Solicitud guardada (ID original: {id_original})")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando solicitud: {str(e)}")
                continue
    
    return registros_guardados


def _procesar_cuentas(datos_tabla, ModeloHistorico, mapeo_cuentas, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda cuentas bancarias en HistoricalAccountNumber."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                usuario_id = datos.get('usuario_id', datos.get('user_id', datos.get('student_id')))
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_accountnumber')
                
                # Crear cuenta
                cuenta = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_accountnumber',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    cuenta, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'usuario_id', 'user_id', 'usuario', 'user'], 
                    logger=logger
                )
                
                # Asignar relación FK
                if usuario_id:
                    try:
                        usuario = User.objects.get(id=usuario_id)
                        cuenta.usuario = usuario
                    except User.DoesNotExist:
                        logger.warning(f"Usuario no encontrado: {usuario_id}")
                
                completar_campos_obligatorios(cuenta, logger=logger)
                cuenta.save()
                
                # Guardar mapeo
                mapeo_cuentas[id_original] = cuenta
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Cuenta guardada: {cuenta.numero_cuenta} (ID original: {id_original})")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando cuenta: {str(e)}")
                continue
    
    return registros_guardados




def _procesar_pagos(datos_tabla, ModeloHistorico, mapeo_solicitudes, mapeo_cuentas, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda pagos en HistoricalEnrollmentPay."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                solicitud_id = datos.get('solicitud_id', datos.get('application_id'))
                cuenta_id = datos.get('cuenta_id', datos.get('account_id'))
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_enrollmentpay')
                
                # Crear pago
                pago = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollmentpay',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    pago, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'solicitud_id', 'application_id', 'cuenta_id', 'account_id', 'solicitud', 'application', 'cuenta', 'account'], 
                    logger=logger
                )
                
                # Asignar relaciones FK
                if solicitud_id and solicitud_id in mapeo_solicitudes:
                    pago.solicitud = mapeo_solicitudes[solicitud_id]
                
                if cuenta_id and cuenta_id in mapeo_cuentas:
                    pago.cuenta = mapeo_cuentas[cuenta_id]
                
                completar_campos_obligatorios(pago, logger=logger)
                pago.save()
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Pago guardado: {pago.monto}")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando pago: {str(e)}")
                continue
    
    return registros_guardados


def _procesar_inscripciones(datos_tabla, ModeloHistorico, mapeo_asignaturas, mapeo_ediciones, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda inscripciones en HistoricalEnrollment."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                curso_id = datos.get('curso_id', datos.get('course_id'))
                usuario_id = datos.get('usuario_id', datos.get('user_id', datos.get('student_id')))
                edicion_id = datos.get('edicion_id', datos.get('edition_id'))
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_enrollment')
                
                # Crear inscripción
                inscripcion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_enrollment',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    inscripcion, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'curso_id', 'course_id', 'usuario_id', 'user_id', 'edicion_id', 'edition_id', 'curso', 'course', 'usuario', 'user', 'edicion', 'edition'], 
                    logger=logger
                )
                
                # Asignar relaciones FK
                if curso_id and curso_id in mapeo_asignaturas:
                    inscripcion.curso = mapeo_asignaturas[curso_id]
                
                if usuario_id:
                    try:
                        usuario = User.objects.get(id=usuario_id)
                        inscripcion.usuario = usuario
                    except User.DoesNotExist:
                        logger.warning(f"Usuario no encontrado: {usuario_id}")
                
                if edicion_id and edicion_id in mapeo_ediciones:
                    inscripcion.edicion = mapeo_ediciones[edicion_id]
                
                completar_campos_obligatorios(inscripcion, logger=logger)
                inscripcion.save()
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Inscripción guardada")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando inscripción: {str(e)}")
                continue
    
    return registros_guardados




def _procesar_aplicaciones(datos_tabla, ModeloHistorico, mapeo_cursos, mapeo_ediciones, logger, estadisticas=None, tablas_seleccionadas=None, tabla_actual=None):
    """Procesa y guarda aplicaciones en HistoricalApplication."""
    registros_guardados = 0
    
    
    # Obtener total de registros para progreso
    total_registros = len(datos_tabla)
    
    with transaction.atomic():
        for i, dato in enumerate(datos_tabla, 1):
            try:
                sid = transaction.savepoint()
                datos = dato.datos_originales
                id_original = datos.get('id')
                curso_id = datos.get('curso_id', datos.get('course_id'))
                usuario_id = datos.get('usuario_id', datos.get('user_id', datos.get('student_id')))
                edicion_id = datos.get('edicion_id', datos.get('edition_id'))
                
                # Aplicar mapeo de campos
                datos_mapeados = aplicar_mapeo_campos(datos, 'Docencia_application')
                
                # Crear aplicación
                aplicacion = ModeloHistorico(
                    id_original=id_original,
                    tabla_origen='Docencia_application',
                    dato_archivado=dato
                )
                copiar_campos_a_modelo_historico(
                    aplicacion, datos_mapeados, 
                    campos_excluir=['id', 'pk', 'curso_id', 'course_id', 'usuario_id', 'user_id', 'edicion_id', 'edition_id', 'curso', 'course', 'usuario', 'user', 'edicion', 'edition'], 
                    logger=logger
                )
                
                # Asignar relaciones FK
                if curso_id and curso_id in mapeo_cursos:
                    aplicacion.curso = mapeo_cursos[curso_id]
                
                if usuario_id:
                    try:
                        usuario = User.objects.get(id=usuario_id)
                        aplicacion.usuario = usuario
                    except User.DoesNotExist:
                        logger.warning(f"Usuario no encontrado: {usuario_id}")
                
                if edicion_id and edicion_id in mapeo_ediciones:
                    aplicacion.edicion = mapeo_ediciones[edicion_id]
                
                completar_campos_obligatorios(aplicacion, logger=logger)
                aplicacion.save()
                registros_guardados += 1
                
                transaction.savepoint_commit(sid)
                
                # Actualizar progreso cada 100 registros o al final
                if estadisticas and tablas_seleccionadas and tabla_actual and (i % 100 == 0 or i == total_registros):
                    _actualizar_progreso_cache(
                        tabla_actual,
                        estadisticas,
                        tablas_seleccionadas,
                        registros_procesados=i,
                        total_registros=total_registros
                    )
                logger.debug(f"Aplicación guardada")
                
            except Exception as e:
                transaction.savepoint_rollback(sid)
                logger.error(f"Error procesando aplicación: {str(e)}")
                continue
    
    return registros_guardados


def _actualizar_progreso_cache(tabla_actual, estadisticas, tablas_seleccionadas, registros_procesados=0, total_registros=0):
    """Actualiza el progreso en cache para mostrar en el frontend."""
    # Calcular porcentaje de la tabla actual
    porcentaje_tabla = int((registros_procesados / total_registros) * 100) if total_registros > 0 else 0
    
    progreso = {
        'paso_actual': f'Guardando {tabla_actual} en historial',
        'pasos_completados': estadisticas['tablas_procesadas'],
        'pasos_totales': len(tablas_seleccionadas),
        'fecha_inicio': timezone.now().isoformat(),
        'tipo_operacion': 'guardar_historial',
        'tablas_seleccionadas': tablas_seleccionadas,
        # Campos para progreso en tiempo real
        'tabla_actual_procesando': tabla_actual,
        'registros_procesados_tabla': registros_procesados,
        'total_registros_tabla': total_registros,
        'porcentaje_tabla': porcentaje_tabla,
        **estadisticas
    }
    cache.set('combinacion_en_progreso', progreso, timeout=300)
