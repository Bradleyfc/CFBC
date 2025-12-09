import mysql.connector
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction, connection
from django.db import models
from django.apps import apps
import logging
import json
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

class InspectorBaseDatos:
    """
    Clase para inspeccionar automáticamente la estructura de una base de datos MariaDB
    y crear modelos Django dinámicamente
    """
    
    def __init__(self, connection):
        self.connection = connection
        self.tablas_inspeccionadas = {}
        self.modelos_dinamicos = {}
    
    def obtener_tablas(self):
        """Obtiene la lista de tablas de la base de datos"""
        cursor = self.connection.cursor()
        cursor.execute("SHOW TABLES")
        tablas = [tabla[0] for tabla in cursor.fetchall()]
        cursor.close()
        return tablas
    
    def inspeccionar_tabla(self, nombre_tabla):
        """Inspecciona la estructura de una tabla específica"""
        cursor = self.connection.cursor(dictionary=True)
        
        # Obtener información de las columnas
        cursor.execute(f"DESCRIBE {nombre_tabla}")
        columnas = cursor.fetchall()
        
        # Obtener información de las claves foráneas
        cursor.execute(f"""
            SELECT 
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
            WHERE TABLE_NAME = '{nombre_tabla}' 
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        claves_foraneas = cursor.fetchall()
        
        cursor.close()
        
        estructura = {
            'nombre': nombre_tabla,
            'columnas': columnas,
            'claves_foraneas': {fk['COLUMN_NAME']: {
                'tabla_referenciada': fk['REFERENCED_TABLE_NAME'],
                'columna_referenciada': fk['REFERENCED_COLUMN_NAME']
            } for fk in claves_foraneas}
        }
        
        self.tablas_inspeccionadas[nombre_tabla] = estructura
        return estructura
    
    def mapear_tipo_campo(self, tipo_mysql, es_nullable, es_clave_primaria, longitud_maxima=None):
        """Mapea tipos de datos MySQL a campos Django"""
        try:
            tipo_mysql = str(tipo_mysql).lower()
            
            # Mapeo básico de tipos
            if 'int' in tipo_mysql:
                if es_clave_primaria:
                    return models.AutoField(primary_key=True)
                elif 'bigint' in tipo_mysql:
                    return models.BigIntegerField(null=es_nullable, blank=es_nullable)
                else:
                    return models.IntegerField(null=es_nullable, blank=es_nullable)
            
            elif 'varchar' in tipo_mysql or 'char' in tipo_mysql:
                max_length = longitud_maxima or 255
                # Limitar longitud máxima para evitar errores
                if max_length > 500:
                    return models.TextField(null=es_nullable, blank=es_nullable)
                return models.CharField(max_length=max_length, null=es_nullable, blank=es_nullable)
            
            elif 'text' in tipo_mysql or 'longtext' in tipo_mysql or 'mediumtext' in tipo_mysql:
                return models.TextField(null=es_nullable, blank=es_nullable)
            
            elif 'decimal' in tipo_mysql or 'numeric' in tipo_mysql:
                return models.DecimalField(max_digits=10, decimal_places=2, null=es_nullable, blank=es_nullable)
            
            elif 'float' in tipo_mysql or 'double' in tipo_mysql:
                return models.FloatField(null=es_nullable, blank=es_nullable)
            
            elif 'date' in tipo_mysql and 'datetime' not in tipo_mysql:
                return models.DateField(null=es_nullable, blank=es_nullable)
            
            elif 'datetime' in tipo_mysql or 'timestamp' in tipo_mysql:
                return models.DateTimeField(null=es_nullable, blank=es_nullable)
            
            elif 'time' in tipo_mysql:
                return models.TimeField(null=es_nullable, blank=es_nullable)
            
            elif 'bool' in tipo_mysql or 'tinyint(1)' in tipo_mysql:
                return models.BooleanField(default=False, null=es_nullable)
            
            elif 'tinyint' in tipo_mysql:
                return models.SmallIntegerField(null=es_nullable, blank=es_nullable)
            
            elif 'json' in tipo_mysql:
                return models.JSONField(null=es_nullable, blank=es_nullable)
            
            elif 'blob' in tipo_mysql or 'binary' in tipo_mysql:
                return models.BinaryField(null=es_nullable, blank=es_nullable)
            
            else:
                # Tipo por defecto - usar TextField para tipos desconocidos
                return models.TextField(null=es_nullable, blank=es_nullable)
                
        except Exception as e:
            logger.warning(f"Error mapeando tipo {tipo_mysql}: {e}. Usando TextField por defecto.")
            return models.TextField(null=True, blank=True)
    
    def crear_modelo_dinamico(self, estructura_tabla):
        """Crea un modelo Django dinámico basado en la estructura de la tabla"""
        nombre_tabla = estructura_tabla['nombre']
        nombre_modelo = self.convertir_nombre_modelo(nombre_tabla)
        
        # Diccionario para almacenar los campos del modelo
        campos = {}
        
        # Procesar cada columna
        for columna in estructura_tabla['columnas']:
            nombre_campo = columna['Field']
            tipo_campo = columna['Type']
            es_nullable = columna['Null'] == 'YES'
            es_clave_primaria = columna['Key'] == 'PRI'
            
            # Extraer longitud máxima si está disponible
            longitud_maxima = None
            if '(' in tipo_campo:
                import re
                match = re.search(r'\((\d+)\)', tipo_campo)
                if match:
                    longitud_maxima = int(match.group(1))
            
            # Verificar si es clave foránea
            if nombre_campo in estructura_tabla['claves_foraneas']:
                # Por ahora, tratamos las claves foráneas como IntegerField
                # En una implementación más compleja, se podrían crear las relaciones
                campos[nombre_campo] = models.IntegerField(
                    null=es_nullable, 
                    blank=es_nullable,
                    verbose_name=f'ID de {estructura_tabla["claves_foraneas"][nombre_campo]["tabla_referenciada"]}'
                )
            else:
                # Campo normal
                campos[nombre_campo] = self.mapear_tipo_campo(
                    tipo_campo, es_nullable, es_clave_primaria, longitud_maxima
                )
        
        # Agregar metadatos del modelo
        campos['Meta'] = type('Meta', (), {
            'db_table': nombre_tabla,
            'managed': False,  # Django no gestionará esta tabla
            'verbose_name': nombre_modelo,
            'verbose_name_plural': f'{nombre_modelo}s'
        })
        
        # Agregar el módulo requerido para Django
        campos['__module__'] = 'datos_archivados.models'
        
        # Crear el modelo dinámico
        modelo_dinamico = type(nombre_modelo, (models.Model,), campos)
        
        self.modelos_dinamicos[nombre_tabla] = modelo_dinamico
        return modelo_dinamico
    
    def convertir_nombre_modelo(self, nombre_tabla):
        """Convierte el nombre de tabla a un nombre de modelo válido"""
        # Remover prefijos comunes y limpiar el nombre
        nombre = nombre_tabla.lower()
        
        # Remover prefijos conocidos
        prefijos_a_remover = ['principal_', 'auth_', 'django_', 'blog_', 'docencia_', 'sapereAude_']
        for prefijo in prefijos_a_remover:
            if nombre.startswith(prefijo.lower()):
                nombre = nombre[len(prefijo):]
                break
        
        # Limpiar caracteres especiales y convertir a CamelCase
        nombre = nombre.replace('-', '_').replace(' ', '_')
        partes = [parte for parte in nombre.split('_') if parte]  # Filtrar partes vacías
        
        # Crear nombre válido para modelo Django
        nombre_modelo = ''.join(palabra.capitalize() for palabra in partes)
        
        # Asegurar que empiece con letra mayúscula y sea válido
        if not nombre_modelo:
            nombre_modelo = 'TablaArchivada'
        elif not nombre_modelo[0].isupper():
            nombre_modelo = nombre_modelo.capitalize()
        
        # Agregar sufijo para evitar conflictos
        return nombre_modelo + 'Archivado'
    
    def inspeccionar_base_datos_completa(self):
        """Inspecciona toda la base de datos y crea modelos dinámicos"""
        tablas = self.obtener_tablas()
        modelos_creados = {}
        
        # Filtrar tablas que nos interesan (evitar tablas del sistema)
        tablas_interes = [t for t in tablas if not t.startswith('django_') 
                         and not t.startswith('auth_group') 
                         and not t.startswith('auth_permission')
                         and t != 'auth_user_groups'
                         and t != 'auth_user_user_permissions']
        
        logger.info(f"Inspeccionando {len(tablas_interes)} tablas: {tablas_interes}")
        
        for tabla in tablas_interes:
            try:
                estructura = self.inspeccionar_tabla(tabla)
                modelo = self.crear_modelo_dinamico(estructura)
                modelos_creados[tabla] = modelo
                logger.info(f"Modelo dinámico creado para tabla: {tabla}")
            except Exception as e:
                logger.error(f"Error creando modelo para tabla {tabla}: {str(e)}")
                # Continuar con las demás tablas aunque una falle
                continue
        
        return modelos_creados

class MigracionService:
    """
    Servicio para migrar datos desde MariaDB hacia PostgreSQL con inspección automática
    """
    
    def __init__(self, host, database, user, password, port=3306):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None
        self.migration_log = None
        self.inspector = None
        self.modelos_dinamicos = {}
    
    def conectar_mariadb(self):
        """
        Establece conexión con la base de datos MariaDB
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info(f"Conexión establecida con MariaDB: {self.host}:{self.port}/{self.database}")
            return True
        except mysql.connector.Error as e:
            logger.error(f"Error al conectar con MariaDB: {e}")
            return False
    
    def desconectar_mariadb(self):
        """
        Cierra la conexión con MariaDB
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión con MariaDB cerrada")
    
    def iniciar_migracion(self, usuario):
        """
        Inicia el proceso de migración y crea el log correspondiente
        """
        # Crear el log de migración usando el modelo existente
        from .models import MigracionLog
        self.migration_log = MigracionLog.objects.create(
            usuario=usuario,
            estado='iniciada',
            host_origen=self.host,
            base_datos_origen=self.database
        )
        logger.info(f"Migración iniciada por {usuario.username} - Log ID: {self.migration_log.id}")
        return self.migration_log
    
    def finalizar_migracion(self, estado='completada', errores=''):
        """
        Finaliza el proceso de migración
        """
        if self.migration_log:
            self.migration_log.fecha_fin = timezone.now()
            self.migration_log.estado = estado
            if errores:
                self.migration_log.errores = errores
            self.migration_log.save()
            logger.info(f"Migración finalizada - Estado: {estado}")
    
    def migrar_cursos_academicos(self):
        """
        Migra los cursos académicos desde MariaDB
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Consulta para obtener cursos académicos de MariaDB
            query = """
            SELECT id, nombre, activo, archivado, fecha_creacion
            FROM principal_cursoacademico
            ORDER BY fecha_creacion DESC
            """
            cursor.execute(query)
            cursos_academicos = cursor.fetchall()
            
            migrados = 0
            for curso_data in cursos_academicos:
                # Verificar si ya existe
                if not CursoAcademicoArchivado.objects.filter(id_original=curso_data['id']).exists():
                    CursoAcademicoArchivado.objects.create(
                        id_original=curso_data['id'],
                        nombre=curso_data['nombre'],
                        activo=False,  # Los archivados siempre están inactivos
                        archivado=True,
                        fecha_creacion=curso_data['fecha_creacion']
                    )
                    migrados += 1
            
            self.migration_log.cursos_academicos_migrados = migrados
            self.migration_log.save()
            logger.info(f"Cursos académicos migrados: {migrados}")
            return migrados
            
        except Exception as e:
            logger.error(f"Error migrando cursos académicos: {e}")
            raise
        finally:
            cursor.close()
    
    def migrar_usuarios(self):
        """
        Migra los usuarios y sus perfiles desde MariaDB
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Consulta para obtener usuarios con sus perfiles
            query = """
            SELECT 
                u.id, u.username, u.first_name, u.last_name, u.email, 
                u.date_joined, u.is_active,
                r.nacionalidad, r.carnet, r.sexo, r.address, r.location, 
                r.provincia, r.telephone, r.movil, r.grado, r.ocupacion, r.titulo,
                g.name as grupo_nombre
            FROM auth_user u
            LEFT JOIN accounts_registro r ON u.id = r.user_id
            LEFT JOIN auth_user_groups ug ON u.id = ug.user_id
            LEFT JOIN auth_group g ON ug.group_id = g.id
            ORDER BY u.date_joined DESC
            """
            cursor.execute(query)
            usuarios = cursor.fetchall()
            
            migrados = 0
            for user_data in usuarios:
                # Verificar si ya existe
                if not UsuarioArchivado.objects.filter(id_original=user_data['id']).exists():
                    # Intentar vincular con usuario actual por email o username
                    usuario_actual = None
                    if user_data['email']:
                        usuario_actual = User.objects.filter(email=user_data['email']).first()
                    if not usuario_actual and user_data['username']:
                        usuario_actual = User.objects.filter(username=user_data['username']).first()
                    
                    UsuarioArchivado.objects.create(
                        id_original=user_data['id'],
                        username=user_data['username'] or '',
                        first_name=user_data['first_name'] or '',
                        last_name=user_data['last_name'] or '',
                        email=user_data['email'] or '',
                        date_joined=user_data['date_joined'],
                        is_active=user_data['is_active'],
                        nacionalidad=user_data['nacionalidad'],
                        carnet=user_data['carnet'],
                        sexo=user_data['sexo'] or 'M',
                        address=user_data['address'],
                        location=user_data['location'],
                        provincia=user_data['provincia'],
                        telephone=user_data['telephone'],
                        movil=user_data['movil'],
                        grado=user_data['grado'] or 'grado1',
                        ocupacion=user_data['ocupacion'] or 'ocupacion1',
                        titulo=user_data['titulo'],
                        grupo=user_data['grupo_nombre'] or '',
                        usuario_actual=usuario_actual
                    )
                    migrados += 1
            
            self.migration_log.usuarios_migrados = migrados
            self.migration_log.save()
            logger.info(f"Usuarios migrados: {migrados}")
            return migrados
            
        except Exception as e:
            logger.error(f"Error migrando usuarios: {e}")
            raise
        finally:
            cursor.close()
    
    def migrar_cursos(self):
        """
        Migra los cursos desde MariaDB
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Consulta para obtener cursos con información del profesor
            query = """
            SELECT 
                c.id, c.name, c.description, c.area, c.tipo, c.teacher_id,
                c.class_quantity, c.status, c.curso_academico_id,
                c.enrollment_deadline, c.start_date,
                u.username as teacher_username, u.first_name as teacher_first_name,
                u.last_name as teacher_last_name, u.email as teacher_email
            FROM principal_curso c
            LEFT JOIN auth_user u ON c.teacher_id = u.id
            ORDER BY c.id DESC
            """
            cursor.execute(query)
            cursos = cursor.fetchall()
            
            migrados = 0
            for curso_data in cursos:
                # Verificar si ya existe
                if not CursoArchivado.objects.filter(id_original=curso_data['id']).exists():
                    # Buscar el curso académico archivado correspondiente
                    curso_academico = CursoAcademicoArchivado.objects.filter(
                        id_original=curso_data['curso_academico_id']
                    ).first()
                    
                    if curso_academico:
                        # Intentar vincular con profesor actual
                        teacher_actual = None
                        if curso_data['teacher_email']:
                            teacher_actual = User.objects.filter(
                                email=curso_data['teacher_email'],
                                groups__name='Profesores'
                            ).first()
                        if not teacher_actual and curso_data['teacher_username']:
                            teacher_actual = User.objects.filter(
                                username=curso_data['teacher_username'],
                                groups__name='Profesores'
                            ).first()
                        
                        teacher_name = f"{curso_data['teacher_first_name'] or ''} {curso_data['teacher_last_name'] or ''}".strip()
                        if not teacher_name:
                            teacher_name = curso_data['teacher_username'] or 'Profesor Desconocido'
                        
                        CursoArchivado.objects.create(
                            id_original=curso_data['id'],
                            name=curso_data['name'],
                            description=curso_data['description'],
                            area=curso_data['area'] or 'idiomas',
                            tipo=curso_data['tipo'] or 'curso',
                            teacher_id_original=curso_data['teacher_id'],
                            teacher_name=teacher_name,
                            class_quantity=curso_data['class_quantity'] or 0,
                            status=curso_data['status'] or 'F',
                            curso_academico=curso_academico,
                            enrollment_deadline=curso_data['enrollment_deadline'],
                            start_date=curso_data['start_date'],
                            teacher_actual=teacher_actual
                        )
                        migrados += 1
            
            self.migration_log.cursos_migrados = migrados
            self.migration_log.save()
            logger.info(f"Cursos migrados: {migrados}")
            return migrados
            
        except Exception as e:
            logger.error(f"Error migrando cursos: {e}")
            raise
        finally:
            cursor.close()
    
    def migrar_matriculas(self):
        """
        Migra las matrículas desde MariaDB y las vincula con las actuales si es posible
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Consulta para obtener matrículas
            query = """
            SELECT 
                m.id, m.course_id, m.student_id, m.activo, 
                m.curso_academico_id, m.fecha_matricula, m.estado
            FROM principal_matriculas m
            ORDER BY m.fecha_matricula DESC
            """
            cursor.execute(query)
            matriculas = cursor.fetchall()
            
            migrados = 0
            for matricula_data in matriculas:
                # Verificar si ya existe
                if not MatriculaArchivada.objects.filter(id_original=matricula_data['id']).exists():
                    # Buscar curso y estudiante archivados
                    curso_archivado = CursoArchivado.objects.filter(
                        id_original=matricula_data['course_id']
                    ).first()
                    estudiante_archivado = UsuarioArchivado.objects.filter(
                        id_original=matricula_data['student_id']
                    ).first()
                    
                    if curso_archivado and estudiante_archivado:
                        # Intentar vincular con matrícula actual
                        matricula_actual = None
                        if (estudiante_archivado.usuario_actual and 
                            curso_archivado.teacher_actual):
                            # Buscar si existe una matrícula actual similar
                            # matricula_actual = Matriculas.objects.filter(
                            #     student=estudiante_archivado.usuario_actual,
                            #     course__teacher=curso_archivado.teacher_actual,
                            #     course__name__icontains=curso_archivado.name[:20]  # Búsqueda parcial
                            # ).first()
                            matricula_actual = None
                        
                        MatriculaArchivada.objects.create(
                            id_original=matricula_data['id'],
                            course=curso_archivado,
                            student=estudiante_archivado,
                            activo=matricula_data['activo'],
                            fecha_matricula=matricula_data['fecha_matricula'],
                            estado=matricula_data['estado'] or 'P',
                            matricula_actual=matricula_actual
                        )
                        migrados += 1
            
            self.migration_log.matriculas_migradas = migrados
            self.migration_log.save()
            logger.info(f"Matrículas migradas: {migrados}")
            return migrados
            
        except Exception as e:
            logger.error(f"Error migrando matrículas: {e}")
            raise
        finally:
            cursor.close()
    
    def migrar_calificaciones_y_notas(self):
        """
        Migra las calificaciones y notas individuales desde MariaDB
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Consulta para obtener calificaciones
            query = """
            SELECT 
                c.id, c.matricula_id, c.course_id, c.student_id, 
                c.curso_academico_id, c.average
            FROM principal_calificaciones c
            ORDER BY c.id DESC
            """
            cursor.execute(query)
            calificaciones = cursor.fetchall()
            
            calificaciones_migradas = 0
            notas_migradas = 0
            
            for calif_data in calificaciones:
                # Verificar si ya existe
                if not CalificacionArchivada.objects.filter(id_original=calif_data['id']).exists():
                    # Buscar matrícula archivada
                    matricula_archivada = MatriculaArchivada.objects.filter(
                        id_original=calif_data['matricula_id']
                    ).first()
                    curso_archivado = CursoArchivado.objects.filter(
                        id_original=calif_data['course_id']
                    ).first()
                    estudiante_archivado = UsuarioArchivado.objects.filter(
                        id_original=calif_data['student_id']
                    ).first()
                    
                    if matricula_archivada and curso_archivado and estudiante_archivado:
                        calificacion_archivada = CalificacionArchivada.objects.create(
                            id_original=calif_data['id'],
                            matricula=matricula_archivada,
                            course=curso_archivado,
                            student=estudiante_archivado,
                            average=calif_data['average']
                        )
                        calificaciones_migradas += 1
                        
                        # Migrar notas individuales para esta calificación
                        cursor_notas = self.connection.cursor(dictionary=True)
                        query_notas = """
                        SELECT id, valor, fecha_creacion
                        FROM principal_notaindividual
                        WHERE calificacion_id = %s
                        ORDER BY fecha_creacion ASC
                        """
                        cursor_notas.execute(query_notas, (calif_data['id'],))
                        notas = cursor_notas.fetchall()
                        
                        for nota_data in notas:
                            if not NotaIndividualArchivada.objects.filter(id_original=nota_data['id']).exists():
                                NotaIndividualArchivada.objects.create(
                                    id_original=nota_data['id'],
                                    calificacion=calificacion_archivada,
                                    valor=nota_data['valor'],
                                    fecha_creacion=nota_data['fecha_creacion']
                                )
                                notas_migradas += 1
                        
                        cursor_notas.close()
            
            self.migration_log.calificaciones_migradas = calificaciones_migradas
            self.migration_log.notas_migradas = notas_migradas
            self.migration_log.save()
            logger.info(f"Calificaciones migradas: {calificaciones_migradas}, Notas migradas: {notas_migradas}")
            return calificaciones_migradas, notas_migradas
            
        except Exception as e:
            logger.error(f"Error migrando calificaciones y notas: {e}")
            raise
        finally:
            cursor.close()
    
    def migrar_asistencias(self):
        """
        Migra las asistencias desde MariaDB
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Consulta para obtener asistencias
            query = """
            SELECT 
                a.id, a.course_id, a.student_id, a.presente, a.date
            FROM principal_asistencia a
            ORDER BY a.date DESC
            """
            cursor.execute(query)
            asistencias = cursor.fetchall()
            
            migrados = 0
            for asistencia_data in asistencias:
                # Verificar si ya existe
                if not AsistenciaArchivada.objects.filter(id_original=asistencia_data['id']).exists():
                    # Buscar curso y estudiante archivados
                    curso_archivado = CursoArchivado.objects.filter(
                        id_original=asistencia_data['course_id']
                    ).first()
                    estudiante_archivado = UsuarioArchivado.objects.filter(
                        id_original=asistencia_data['student_id']
                    ).first()
                    
                    if curso_archivado and estudiante_archivado:
                        AsistenciaArchivada.objects.create(
                            id_original=asistencia_data['id'],
                            course=curso_archivado,
                            student=estudiante_archivado,
                            presente=asistencia_data['presente'],
                            date=asistencia_data['date']
                        )
                        migrados += 1
            
            self.migration_log.asistencias_migradas = migrados
            self.migration_log.save()
            logger.info(f"Asistencias migradas: {migrados}")
            return migrados
            
        except Exception as e:
            logger.error(f"Error migrando asistencias: {e}")
            raise
        finally:
            cursor.close()
    
    @transaction.atomic
    def ejecutar_migracion_completa(self, usuario):
        """
        Ejecuta la migración completa de todos los datos
        """
        try:
            # Iniciar migración
            self.iniciar_migracion(usuario)
            self.migration_log.estado = 'en_progreso'
            self.migration_log.save()
            
            # Conectar a MariaDB
            if not self.conectar_mariadb():
                raise Exception("No se pudo conectar a la base de datos MariaDB")
            
            # Ejecutar migraciones en orden
            logger.info("Iniciando migración de cursos académicos...")
            self.migrar_cursos_academicos()
            
            logger.info("Iniciando migración de usuarios...")
            self.migrar_usuarios()
            
            logger.info("Iniciando migración de cursos...")
            self.migrar_cursos()
            
            logger.info("Iniciando migración de matrículas...")
            self.migrar_matriculas()
            
            logger.info("Iniciando migración de calificaciones y notas...")
            self.migrar_calificaciones_y_notas()
            
            logger.info("Iniciando migración de asistencias...")
            self.migrar_asistencias()
            
            # Finalizar migración exitosa
            self.finalizar_migracion('completada')
            logger.info("Migración completada exitosamente")
            
            return self.migration_log
            
        except Exception as e:
            error_msg = f"Error durante la migración: {str(e)}"
            logger.error(error_msg)
            self.finalizar_migracion('error', error_msg)
            raise
        finally:
            self.desconectar_mariadb()
    
    def inspeccionar_y_migrar_automaticamente(self, usuario):
        """
        Inspecciona automáticamente la base de datos remota y migra todos los datos
        creando modelos dinámicos según sea necesario
        """
        try:
            # Iniciar migración
            self.iniciar_migracion(usuario)
            self.migration_log.estado = 'en_progreso'
            self.migration_log.save()
            
            # Conectar a MariaDB
            if not self.conectar_mariadb():
                raise Exception("No se pudo conectar a la base de datos MariaDB")
            
            # Crear inspector de base de datos
            self.inspector = InspectorBaseDatos(self.connection)
            
            # Inspeccionar toda la base de datos
            logger.info("Inspeccionando estructura de la base de datos...")
            modelos_dinamicos = self.inspector.inspeccionar_base_datos_completa()
            self.modelos_dinamicos = modelos_dinamicos
            
            # Migrar datos usando los modelos dinámicos
            total_registros_migrados = 0
            
            tablas_con_datos = 0
            tablas_vacias = 0
            registros_nuevos_migrados = 0
            
            for nombre_tabla, modelo_dinamico in modelos_dinamicos.items():
                try:
                    logger.info(f"Migrando datos de la tabla: {nombre_tabla}")
                    registros_en_origen = self.migrar_tabla_dinamica(nombre_tabla, modelo_dinamico)
                    
                    # Contar si la tabla tiene datos en el origen
                    if registros_en_origen > 0:
                        tablas_con_datos += 1
                        logger.info(f"✓ Tabla {nombre_tabla} tiene {registros_en_origen} registros")
                    else:
                        tablas_vacias += 1
                        logger.info(f"○ Tabla {nombre_tabla} está vacía")
                        
                except Exception as e:
                    logger.error(f"Error migrando tabla {nombre_tabla}: {e}")
                    tablas_vacias += 1  # Contar como vacía si hay error
                    continue
            
            # Contar registros realmente migrados (nuevos)
            from .models import DatoArchivadoDinamico
            registros_nuevos_migrados = DatoArchivadoDinamico.objects.filter(
                fecha_migracion__gte=self.migration_log.fecha_inicio
            ).count()
            
            # Actualizar log con totales
            self.migration_log.usuarios_migrados = registros_nuevos_migrados
            self.migration_log.tablas_inspeccionadas = len(modelos_dinamicos)
            self.migration_log.tablas_con_datos = tablas_con_datos
            self.migration_log.tablas_vacias = tablas_vacias
            self.migration_log.save()
            
            logger.info(f"Resumen: {len(modelos_dinamicos)} tablas inspeccionadas, {tablas_con_datos} con datos, {tablas_vacias} vacías")
            
            # Finalizar migración exitosa
            self.finalizar_migracion('completada')
            logger.info(f"Migración automática completada. Total de registros migrados: {total_registros_migrados}")
            
            return self.migration_log
            
        except Exception as e:
            error_msg = f"Error durante la migración automática: {str(e)}"
            logger.error(error_msg)
            self.finalizar_migracion('error', error_msg)
            raise
        finally:
            self.desconectar_mariadb()
    
    def migrar_tabla_dinamica(self, nombre_tabla, modelo_dinamico):
        """
        Migra los datos de una tabla específica usando un modelo dinámico
        """
        cursor = self.connection.cursor(dictionary=True)
        try:
            # Obtener todos los registros de la tabla
            query = f"SELECT * FROM {nombre_tabla} ORDER BY id DESC LIMIT 1000"  # Limitar para evitar sobrecarga
            cursor.execute(query)
            registros = cursor.fetchall()
            
            # Contar registros en la tabla origen (no solo los nuevos migrados)
            total_registros_origen = len(registros)
            migrados = 0
            
            for registro in registros:
                try:
                    # Crear modelo archivado dinámico
                    modelo_archivado = self.crear_modelo_archivado_dinamico(nombre_tabla, registro)
                    if modelo_archivado:
                        migrados += 1
                except Exception as e:
                    logger.error(f"Error migrando registro {registro.get('id', 'N/A')} de {nombre_tabla}: {e}")
                    continue
            
            # Retornar el total de registros en origen (para contar tablas con datos)
            # aunque no se hayan migrado nuevos registros en esta ejecución
            return total_registros_origen
            
        except Exception as e:
            logger.error(f"Error migrando tabla {nombre_tabla}: {e}")
            raise
        finally:
            cursor.close()
    
    def crear_modelo_archivado_dinamico(self, nombre_tabla, datos_registro):
        """
        Crea un registro archivado dinámico en la base de datos local
        """
        from .models import DatoArchivadoDinamico
        
        try:
            # Verificar si ya existe este registro
            id_original = datos_registro.get('id')
            if not id_original:
                return None
            
            # Verificar si ya existe
            if DatoArchivadoDinamico.objects.filter(
                tabla_origen=nombre_tabla, 
                id_original=id_original
            ).exists():
                return None
            
            # Convertir datos a JSON, manejando tipos especiales
            datos_json = self.convertir_datos_a_json(datos_registro)
            
            # Crear registro archivado
            modelo_archivado = DatoArchivadoDinamico.objects.create(
                tabla_origen=nombre_tabla,
                id_original=id_original,
                datos_originales=datos_json,
                estructura_tabla=json.dumps(self.inspector.tablas_inspeccionadas.get(nombre_tabla, {}))
            )
            
            return modelo_archivado
            
        except Exception as e:
            logger.error(f"Error creando modelo archivado para {nombre_tabla}: {e}")
            return None
    
    def convertir_datos_a_json(self, datos):
        """
        Convierte los datos del registro a formato JSON, manejando tipos especiales
        """
        from datetime import timedelta
        
        datos_convertidos = {}
        
        for clave, valor in datos.items():
            if valor is None:
                datos_convertidos[clave] = None
            elif isinstance(valor, (datetime, date)):
                datos_convertidos[clave] = valor.isoformat()
            elif isinstance(valor, timedelta):
                # Convertir timedelta a string en formato legible
                total_seconds = int(valor.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                datos_convertidos[clave] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            elif isinstance(valor, Decimal):
                datos_convertidos[clave] = float(valor)
            elif isinstance(valor, bytes):
                # Convertir bytes a string si es posible
                try:
                    datos_convertidos[clave] = valor.decode('utf-8')
                except:
                    datos_convertidos[clave] = str(valor)
            else:
                # Para cualquier otro tipo que no sea JSON serializable, convertir a string
                try:
                    # Intentar serializar para verificar si es JSON serializable
                    json.dumps(valor)
                    datos_convertidos[clave] = valor
                except (TypeError, ValueError):
                    # Si no es serializable, convertir a string
                    datos_convertidos[clave] = str(valor)
        
        return datos_convertidos
    
    def obtener_resumen_migracion(self):
        """
        Obtiene un resumen de la migración realizada
        """
        if not self.migration_log:
            return None
        
        resumen = {
            'id_migracion': self.migration_log.id,
            'estado': self.migration_log.estado,
            'fecha_inicio': self.migration_log.fecha_inicio,
            'fecha_fin': self.migration_log.fecha_fin,
            'host_origen': self.migration_log.host_origen,
            'base_datos_origen': self.migration_log.base_datos_origen,
            'total_registros': self.migration_log.usuarios_migrados,
            'errores': self.migration_log.errores
        }
        
        if hasattr(self, 'modelos_dinamicos'):
            resumen['tablas_procesadas'] = list(self.modelos_dinamicos.keys())
            resumen['total_tablas'] = len(self.modelos_dinamicos)
        
        return resumen