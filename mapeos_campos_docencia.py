"""
Mapeos de campos de inglés a español para las tablas de docencia.

Este módulo contiene los mapeos de nombres de campos desde inglés (como vienen
en los datos archivados) a español (como están definidos en los modelos históricos).
"""

# Mapeo para Docencia_area
MAPEO_AREA = {
    'name': 'nombre',
    'code': 'codigo',
    'description': 'descripcion',
}

# Mapeo para Docencia_coursecategory
MAPEO_COURSECATEGORY = {
    'name': 'nombre',
    'description': 'descripcion',
    'parent_id': 'parent_id',
    'max_year': 'anio_maximo',
    'min_year': 'anio_minimo',
    'capacity': 'capacidad',
    'code': 'codigo',
    'announcement': 'comunicado',
    'minimum_credits': 'creditos_minimos',
    'curriculum': 'curriculum',
    'duration': 'duracion',
    'is_service': 'es_servicio',
    'start_date': 'fecha_inicio',
    'deadline': 'fecha_limite',
    'image': 'imagen',
    'price': 'precio',
    'religious_price': 'precio_religioso',
    'program': 'programa',
    'open_registration': 'registro_abierto',
    'regulations': 'reglamento',
    'requirements': 'requisitos',
    'slug': 'slug',
    'has_application': 'tiene_solicitud',
    'visible': 'visible',
    'visible_announcement': 'visible_comunicado',
}

# Mapeo para Docencia_courseinformation
MAPEO_COURSEINFORMATION = {
    'name': 'nombre',
    'description': 'descripcion',
    'area_id': 'area_id',
    'category_id': 'category_id',
    'code': 'codigo',
    'credits': 'creditos',
    'hours': 'horas',
    'level': 'nivel',
    'prerequisites': 'prerequisitos',
    'syllabus': 'programa',
    'visible': 'visible',
}

# Mapeo para Docencia_courseinformation_adminteachers
MAPEO_COURSEINFORMATION_ADMINTEACHERS = {
    'courseinformation_id': 'courseinformation_id',
    'user_id': 'user_id',
}

# Mapeo para Docencia_subjectinformation
MAPEO_SUBJECTINFORMATION = {
    'name': 'nombre',
    'code': 'codigo',
    'course_id': 'course_id',
    'credits': 'creditos',
    'description': 'descripcion',
    'hours': 'horas',
    'level': 'nivel',
    'prerequisites': 'prerequisitos',
    'syllabus': 'programa',
}

# Mapeo para Docencia_edition
MAPEO_EDITION = {
    'name': 'nombre',
    'course_id': 'course_id',
    'start_date': 'fecha_inicio',
    'end_date': 'fecha_fin',
    'capacity': 'capacidad',
    'visible': 'visible',
}

# Mapeo para Docencia_enrollmentapplication
MAPEO_ENROLLMENTAPPLICATION = {
    'user_id': 'user_id',
    'course_id': 'course_id',
    'status': 'estado',
    'application_date': 'fecha_solicitud',
    'comments': 'comentarios',
}

# Mapeo para Docencia_accountnumber
MAPEO_ACCOUNTNUMBER = {
    'account_number': 'numero_cuenta',
    'bank_name': 'nombre_banco',
    'account_type': 'tipo_cuenta',
}

# Mapeo para Docencia_enrollmentpay
MAPEO_ENROLLMENTPAY = {
    'enrollment_application_id': 'enrollment_application_id',
    'account_number_id': 'account_number_id',
    'amount': 'monto',
    'payment_date': 'fecha_pago',
    'payment_method': 'metodo_pago',
    'reference': 'referencia',
    'status': 'estado',
}

# Mapeo para Docencia_enrollment
MAPEO_ENROLLMENT = {
    'user_id': 'user_id',
    'subject_id': 'subject_id',
    'edition_id': 'edition_id',
    'enrollment_date': 'fecha_inscripcion',
    'status': 'estado',
    'grade': 'calificacion',
}

# Mapeo para Docencia_application
MAPEO_APPLICATION = {
    'user_id': 'user_id',
    'course_id': 'course_id',
    'edition_id': 'edition_id',
    'application_date': 'fecha_solicitud',
    'status': 'estado',
    'comments': 'comentarios',
}

# Diccionario principal que mapea tabla -> mapeo de campos
MAPEOS_POR_TABLA = {
    'Docencia_area': MAPEO_AREA,
    'Docencia_coursecategory': MAPEO_COURSECATEGORY,
    'Docencia_courseinformation': MAPEO_COURSEINFORMATION,
    'Docencia_courseinformation_adminteachers': MAPEO_COURSEINFORMATION_ADMINTEACHERS,
    'Docencia_subjectinformation': MAPEO_SUBJECTINFORMATION,
    'Docencia_edition': MAPEO_EDITION,
    'Docencia_enrollmentapplication': MAPEO_ENROLLMENTAPPLICATION,
    'Docencia_accountnumber': MAPEO_ACCOUNTNUMBER,
    'Docencia_enrollmentpay': MAPEO_ENROLLMENTPAY,
    'Docencia_enrollment': MAPEO_ENROLLMENT,
    'Docencia_application': MAPEO_APPLICATION,
}


def aplicar_mapeo_campos(datos_originales, tabla_origen):
    """
    Aplica el mapeo de campos de inglés a español según la tabla de origen.
    
    Args:
        datos_originales: Diccionario con los datos en inglés
        tabla_origen: Nombre de la tabla de origen (ej: 'Docencia_area')
    
    Returns:
        Diccionario con los campos mapeados a español
    """
    if tabla_origen not in MAPEOS_POR_TABLA:
        # Si no hay mapeo definido, devolver los datos originales
        return datos_originales
    
    mapeo = MAPEOS_POR_TABLA[tabla_origen]
    datos_mapeados = {}
    
    for campo_ingles, valor in datos_originales.items():
        # Si el campo está en el mapeo, usar el nombre en español
        if campo_ingles in mapeo:
            campo_espanol = mapeo[campo_ingles]
            datos_mapeados[campo_espanol] = valor
        else:
            # Si no está en el mapeo, mantener el nombre original
            datos_mapeados[campo_ingles] = valor
    
    return datos_mapeados
