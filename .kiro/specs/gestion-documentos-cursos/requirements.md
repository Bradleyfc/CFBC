# Requirements Document

## Introduction

Sistema de gestión de documentos para cursos que permite a los profesores organizar y compartir materiales educativos con sus estudiantes de manera estructurada, con notificaciones automáticas y acceso controlado por curso.

## Glossary

- **Sistema**: El sistema de gestión de documentos para cursos
- **Profesor**: Usuario con rol de profesor que puede subir documentos
- **Estudiante**: Usuario con rol de estudiante que puede descargar documentos
- **Dashboard_Curso**: Interfaz específica para gestionar documentos de un curso
- **Carpeta_Documento**: Contenedor organizacional creado por el profesor para agrupar documentos
- **Documento**: Archivo subido por el profesor para compartir con estudiantes
- **Notificacion_Email**: Mensaje automático enviado al correo del estudiante
- **Indicador_Nuevo**: Icono visual que señala contenido nuevo disponible

## Requirements

### Requirement 1

**User Story:** Como profesor, quiero acceder a un dashboard específico para cada curso que enseño, para poder gestionar los documentos de manera organizada por curso.

#### Acceptance Criteria

1. WHEN un profesor accede a su perfil THEN el Sistema SHALL mostrar un botón de acceso al dashboard por cada curso que atiende
2. WHEN un profesor hace clic en el botón de dashboard de un curso THEN el Sistema SHALL mostrar la interfaz de gestión de documentos específica para ese curso
3. WHEN un profesor accede al Dashboard_Curso THEN el Sistema SHALL mostrar todas las Carpeta_Documento existentes para ese curso
4. WHEN un profesor no tiene cursos asignados THEN el Sistema SHALL mostrar un mensaje indicando que no hay cursos disponibles
5. WHERE un profesor tiene múltiples cursos THEN el Sistema SHALL mostrar botones claramente identificados con el nombre de cada curso

### Requirement 2

**User Story:** Como profesor, quiero crear carpetas personalizadas en el dashboard del curso, para organizar los documentos según mi criterio pedagógico.

#### Acceptance Criteria

1. WHEN un profesor está en el Dashboard_Curso THEN el Sistema SHALL proporcionar una opción para crear nueva Carpeta_Documento
2. WHEN un profesor crea una Carpeta_Documento THEN el Sistema SHALL permitir asignar un nombre personalizado a la carpeta
3. WHEN un profesor intenta crear una Carpeta_Documento con nombre vacío THEN el Sistema SHALL rechazar la creación y mantener el estado actual
4. WHEN una Carpeta_Documento es creada THEN el Sistema SHALL mostrar la carpeta inmediatamente en el Dashboard_Curso
5. WHILE un profesor está creando una Carpeta_Documento THEN el Sistema SHALL validar que el nombre no contenga caracteres especiales no permitidos

### Requirement 3

**User Story:** Como profesor, quiero subir documentos dentro de las carpetas que he creado, para compartir material educativo organizado con mis estudiantes.

#### Acceptance Criteria

1. WHEN un profesor selecciona una Carpeta_Documento THEN el Sistema SHALL mostrar la opción para subir Documento
2. WHEN un profesor sube un Documento THEN el Sistema SHALL almacenar el archivo dentro de la Carpeta_Documento seleccionada
3. WHEN un Documento es subido exitosamente THEN el Sistema SHALL mostrar confirmación de la operación
4. WHEN un profesor intenta subir un archivo con formato no permitido THEN el Sistema SHALL rechazar la subida y mostrar mensaje de error
5. WHILE se está subiendo un Documento THEN el Sistema SHALL mostrar el progreso de la operación

### Requirement 4

**User Story:** Como estudiante, quiero acceder a un dashboard específico para cada curso en el que estoy inscrito, para poder descargar los documentos compartidos por el profesor.

#### Acceptance Criteria

1. WHEN un estudiante accede a su perfil THEN el Sistema SHALL mostrar un botón de acceso al dashboard por cada curso en el que está inscrito
2. WHEN un estudiante hace clic en el botón de dashboard de un curso THEN el Sistema SHALL mostrar la interfaz de descarga de documentos específica para ese curso
3. WHEN un estudiante accede al Dashboard_Curso THEN el Sistema SHALL mostrar todas las Carpeta_Documento con documentos disponibles para ese curso
4. WHEN un estudiante no está inscrito en ningún curso THEN el Sistema SHALL mostrar un mensaje indicando que no hay cursos disponibles
5. WHERE un estudiante está inscrito en múltiples cursos THEN el Sistema SHALL mostrar botones claramente identificados con el nombre de cada curso

### Requirement 5

**User Story:** Como estudiante, quiero descargar documentos de las carpetas del curso, para acceder al material educativo compartido por el profesor.

#### Acceptance Criteria

1. WHEN un estudiante selecciona una Carpeta_Documento THEN el Sistema SHALL mostrar todos los Documento disponibles en esa carpeta
2. WHEN un estudiante hace clic en un Documento THEN el Sistema SHALL iniciar la descarga del archivo
3. WHEN un Documento se descarga exitosamente THEN el Sistema SHALL registrar la descarga para fines de seguimiento
4. WHEN un estudiante intenta acceder a documentos de un curso no inscrito THEN el Sistema SHALL denegar el acceso y mostrar mensaje de error
5. WHILE se está descargando un Documento THEN el Sistema SHALL mostrar el progreso de la descarga

### Requirement 6

**User Story:** Como estudiante, quiero recibir notificaciones por correo electrónico cuando se suban nuevos documentos, para estar informado de material nuevo disponible.

#### Acceptance Criteria

1. WHEN un profesor sube un nuevo Documento THEN el Sistema SHALL enviar Notificacion_Email a todos los estudiantes inscritos en ese curso
2. WHEN se envía una Notificacion_Email THEN el Sistema SHALL incluir el nombre del curso, la carpeta y el documento subido
3. WHEN un estudiante recibe una Notificacion_Email THEN el Sistema SHALL incluir un enlace directo al Dashboard_Curso correspondiente
4. WHEN el envío de Notificacion_Email falla THEN el Sistema SHALL registrar el error y reintentar el envío
5. WHERE un curso tiene múltiples estudiantes THEN el Sistema SHALL enviar Notificacion_Email individual a cada estudiante inscrito

### Requirement 7

**User Story:** Como estudiante, quiero ver un indicador visual junto al botón de acceso al dashboard del curso, para saber rápidamente si hay contenido nuevo disponible.

#### Acceptance Criteria

1. WHEN hay nuevos documentos subidos en un curso THEN el Sistema SHALL mostrar Indicador_Nuevo junto al botón de dashboard de ese curso
2. WHEN un estudiante accede al Dashboard_Curso con contenido nuevo THEN el Sistema SHALL remover el Indicador_Nuevo para ese curso
3. WHEN no hay contenido nuevo en un curso THEN el Sistema SHALL mantener el botón sin Indicador_Nuevo
4. WHEN se sube un nuevo Documento THEN el Sistema SHALL activar inmediatamente el Indicador_Nuevo para todos los estudiantes del curso
5. WHILE el Indicador_Nuevo está activo THEN el Sistema SHALL mantener una apariencia visual distintiva que llame la atención del estudiante

### Requirement 8

**User Story:** Como administrador del sistema, quiero que el acceso a los documentos esté controlado por inscripción en cursos, para mantener la seguridad y privacidad de los materiales educativos.

#### Acceptance Criteria

1. WHEN un usuario intenta acceder a documentos THEN el Sistema SHALL verificar que tenga el rol apropiado (profesor o estudiante)
2. WHEN un profesor intenta acceder al Dashboard_Curso THEN el Sistema SHALL verificar que esté asignado como profesor de ese curso
3. WHEN un estudiante intenta acceder al Dashboard_Curso THEN el Sistema SHALL verificar que esté inscrito en ese curso
4. WHEN un usuario no autorizado intenta acceder THEN el Sistema SHALL denegar el acceso y registrar el intento
5. WHILE se realizan operaciones de documentos THEN el Sistema SHALL mantener logs de auditoría de todas las acciones realizadas