# Requirements Document

## Introduction

Este documento define los requisitos para un sistema de chatbot inteligente que se integrará en la página de inicio del sitio web. El chatbot utilizará búsqueda por similitud semántica mediante sentence-transformers para encontrar información relevante y un modelo de lenguaje local pequeño (LLM) para generar respuestas naturales a las preguntas de los usuarios sobre el contenido y funcionalidades del sitio.

## Glossary

- **Chatbot**: Sistema de conversación automatizado que interactúa con usuarios mediante texto
- **Sistema de Búsqueda Semántica**: Componente que utiliza embeddings vectoriales para encontrar contenido similar por significado
- **Sentence-Transformers**: Biblioteca de Python para generar embeddings de texto usando modelos pre-entrenados
- **LLM Local**: Modelo de lenguaje grande ejecutado localmente en el servidor sin dependencias de APIs externas
- **Embeddings**: Representaciones vectoriales de texto que capturan significado semántico
- **Base de Conocimiento**: Colección de documentos indexados que contienen información sobre el sitio
- **Índice Vectorial**: Estructura de datos que almacena embeddings para búsqueda eficiente
- **Widget de Chat**: Componente de interfaz de usuario que permite la interacción con el chatbot
- **FAQ**: Modelo de Django que almacena preguntas frecuentes y sus respuestas en la base de datos
- **Aprendizaje del Chatbot**: Proceso mediante el cual el sistema mejora sus respuestas basándose en interacciones previas

## Requirements

### Requirement 1

**User Story:** Como visitante del sitio, quiero interactuar con un chatbot en la página de inicio, para que pueda obtener respuestas rápidas sobre el sitio sin navegar por múltiples páginas.

#### Acceptance Criteria

1. WHEN un usuario visita la página de inicio THEN el Sistema SHALL mostrar un widget de chat visible y accesible
2. WHEN un usuario escribe una pregunta y presiona enviar THEN el Sistema SHALL procesar la pregunta y mostrar una respuesta en menos de 5 segundos
3. WHEN un usuario envía múltiples mensajes THEN el Sistema SHALL mantener el historial de conversación durante la sesión
4. WHEN un usuario cierra el widget de chat THEN el Sistema SHALL preservar el historial de conversación si el usuario lo reabre durante la misma sesión
5. WHILE el chatbot está procesando una respuesta THEN el Sistema SHALL mostrar un indicador visual de carga

### Requirement 2

**User Story:** Como administrador del sistema, quiero que el chatbot utilice búsqueda semántica con sentence-transformers, para que pueda encontrar información relevante basándose en el significado de las preguntas y no solo en palabras clave exactas.

#### Acceptance Criteria

1. WHEN el Sistema recibe una pregunta del usuario THEN el Sistema SHALL generar embeddings usando un modelo de sentence-transformers
2. WHEN el Sistema genera embeddings de la pregunta THEN el Sistema SHALL buscar en el Índice Vectorial los documentos más similares semánticamente
3. WHEN el Sistema busca documentos similares THEN el Sistema SHALL retornar los 3 documentos más relevantes basándose en similitud coseno
4. WHEN el Sistema indexa contenido nuevo THEN el Sistema SHALL generar y almacenar embeddings para ese contenido automáticamente
5. WHEN el Sistema compara embeddings THEN el Sistema SHALL utilizar similitud coseno como métrica de relevancia

### Requirement 3

**User Story:** Como administrador del sistema, quiero que el chatbot use un modelo LLM local y pequeño, para que las respuestas sean generadas sin depender de servicios externos y manteniendo la privacidad de los datos.

#### Acceptance Criteria

1. WHEN el Sistema genera una respuesta THEN el Sistema SHALL utilizar un modelo LLM ejecutado localmente en el servidor
2. WHEN el Sistema selecciona un modelo LLM THEN el Sistema SHALL usar un modelo con menos de 3GB de tamaño para optimizar recursos
3. WHEN el Sistema genera respuestas THEN el Sistema SHALL combinar el contexto recuperado de la búsqueda semántica con la pregunta del usuario
4. WHEN el Sistema invoca el modelo LLM THEN el Sistema SHALL limitar la longitud de respuesta a un máximo de 300 tokens
5. WHEN el modelo LLM no está disponible THEN el Sistema SHALL retornar las respuestas recuperadas de la búsqueda semántica sin generación adicional

### Requirement 4

**User Story:** Como administrador del sistema, quiero gestionar una base de conocimiento FAQ en Django, para que pueda crear, editar y organizar preguntas frecuentes desde el admin de Django.

#### Acceptance Criteria

1. WHEN un administrador accede al admin de Django THEN el Sistema SHALL mostrar un modelo FAQ para gestionar preguntas y respuestas
2. WHEN un administrador crea una nueva entrada FAQ THEN el Sistema SHALL almacenar la pregunta, respuesta, categoría y estado de publicación en la base de datos
3. WHEN un administrador edita una entrada FAQ THEN el Sistema SHALL regenerar los embeddings de esa entrada y actualizar el Índice Vectorial
4. WHEN un administrador elimina una entrada FAQ THEN el Sistema SHALL remover la entrada y sus embeddings del Índice Vectorial
5. WHEN un administrador guarda una entrada FAQ THEN el Sistema SHALL indexar automáticamente el contenido generando embeddings para búsqueda semántica
6. WHEN el Sistema indexa contenido THEN el Sistema SHALL generar embeddings automáticamente de cursos, noticias del blog, páginas estáticas, FAQs y cualquier contenido relevante del sitio
7. WHEN el Sistema indexa un curso THEN el Sistema SHALL extraer y almacenar embeddings del título, descripción, requisitos, objetivos y contenido del curso
8. WHEN el Sistema indexa una noticia del blog THEN el Sistema SHALL extraer y almacenar embeddings del título, contenido, resumen y categoría de la noticia

### Requirement 5

**User Story:** Como usuario del chatbot, quiero recibir respuestas precisas y contextualizadas, para que pueda obtener información útil sobre cursos, inscripciones, requisitos y otros temas del sitio.

#### Acceptance Criteria

1. WHEN el Sistema genera una respuesta THEN el Sistema SHALL incluir información específica del contexto recuperado de la Base de Conocimiento
2. WHEN el Sistema no encuentra información relevante THEN el Sistema SHALL informar al usuario que no tiene información sobre ese tema y sugerir contactar al administrador
3. WHEN el Sistema genera una respuesta THEN el Sistema SHALL formatear la respuesta de manera clara y legible
4. WHEN la pregunta del usuario es ambigua THEN el Sistema SHALL generar una respuesta que solicite clarificación o proporcione información general
5. WHEN el Sistema responde sobre cursos THEN el Sistema SHALL incluir información actualizada sobre disponibilidad, fechas y requisitos

### Requirement 6

**User Story:** Como desarrollador del sistema, quiero que el chatbot tenga una arquitectura modular y escalable, para que pueda mantener y mejorar el sistema fácilmente en el futuro.

#### Acceptance Criteria

1. WHEN se implementa el Sistema THEN el Sistema SHALL separar la lógica de búsqueda semántica, generación LLM y gestión de base de conocimiento en módulos independientes
2. WHEN se actualiza el modelo de embeddings THEN el Sistema SHALL permitir el cambio sin modificar otros componentes
3. WHEN se actualiza el modelo LLM THEN el Sistema SHALL permitir el cambio sin modificar la lógica de búsqueda
4. WHEN se añaden nuevas fuentes de datos THEN el Sistema SHALL permitir la integración mediante una interfaz común de indexación
5. WHEN el Sistema procesa solicitudes THEN el Sistema SHALL registrar métricas de rendimiento y errores para monitoreo

### Requirement 7

**User Story:** Como usuario del sitio, quiero que el chatbot sea responsivo y funcione en dispositivos móviles, para que pueda acceder a la ayuda desde cualquier dispositivo.

#### Acceptance Criteria

1. WHEN un usuario accede desde un dispositivo móvil THEN el Sistema SHALL adaptar el Widget de Chat al tamaño de pantalla
2. WHEN un usuario interactúa con el chatbot en móvil THEN el Sistema SHALL mantener la funcionalidad completa sin degradación
3. WHEN el Widget de Chat se muestra en pantallas pequeñas THEN el Sistema SHALL ocupar un máximo del 90% del ancho de pantalla
4. WHEN un usuario escribe en móvil THEN el Sistema SHALL mostrar el teclado sin ocultar el área de conversación
5. WHEN el chatbot muestra respuestas largas en móvil THEN el Sistema SHALL permitir scroll dentro del widget sin afectar la página principal

### Requirement 8

**User Story:** Como administrador del sistema, quiero que el chatbot aprenda de las interacciones y sugiera nuevas FAQs, para que pueda mejorar continuamente la base de conocimiento basándose en preguntas reales de usuarios.

#### Acceptance Criteria

1. WHEN un usuario hace una pregunta THEN el Sistema SHALL registrar la pregunta, respuesta generada, documentos recuperados y nivel de confianza
2. WHEN el Sistema registra una pregunta sin respuesta satisfactoria THEN el Sistema SHALL marcarla como candidata para nueva FAQ
3. WHEN un administrador accede al panel de aprendizaje THEN el Sistema SHALL mostrar preguntas frecuentes sin FAQ correspondiente ordenadas por frecuencia
4. WHEN un administrador revisa preguntas candidatas THEN el Sistema SHALL permitir crear una nueva entrada FAQ directamente desde esa pregunta
5. WHEN el Sistema detecta preguntas similares repetidas THEN el Sistema SHALL agruparlas y sugerir una FAQ común
6. WHEN un administrador aprueba una FAQ sugerida THEN el Sistema SHALL crear la entrada FAQ e indexarla automáticamente
7. WHEN el Sistema registra interacciones THEN el Sistema SHALL anonimizar datos personales del usuario


### Requirement 9

**User Story:** Como administrador del sistema, quiero agregar múltiples variaciones de cada pregunta FAQ incluyendo sinónimos y jerga local, para que el chatbot pueda entender diferentes formas en que los estudiantes hacen la misma pregunta.

#### Acceptance Criteria

1. WHEN un administrador crea una FAQ THEN el Sistema SHALL permitir agregar múltiples variaciones de la pregunta principal
2. WHEN un administrador agrega variaciones THEN el Sistema SHALL indexar cada variación generando embeddings separados que apunten a la misma respuesta
3. WHEN el Sistema busca respuestas THEN el Sistema SHALL considerar todas las variaciones de pregunta en la búsqueda semántica
4. WHEN un administrador edita variaciones THEN el Sistema SHALL regenerar los embeddings de las variaciones modificadas
5. WHEN el Sistema sugiere nuevas FAQs THEN el Sistema SHALL agrupar preguntas similares como posibles variaciones de una misma FAQ

### Requirement 11

**User Story:** Como administrador del sistema, quiero organizar las FAQs por categorías y prioridades, para que el chatbot pueda proporcionar respuestas más relevantes y organizadas.

#### Acceptance Criteria

1. WHEN un administrador crea una FAQ THEN el Sistema SHALL permitir asignar una o múltiples categorías
2. WHEN un administrador gestiona categorías THEN el Sistema SHALL permitir crear, editar y eliminar categorías de FAQ desde el admin de Django
3. WHEN un administrador asigna prioridad a una FAQ THEN el Sistema SHALL usar ese valor para ordenar resultados cuando múltiples FAQs son relevantes
4. WHEN el Sistema busca FAQs relevantes THEN el Sistema SHALL considerar la categoría de la pregunta si está disponible
5. WHEN un administrador marca una FAQ como destacada THEN el Sistema SHALL priorizar esa FAQ en los resultados de búsqueda

### Requirement 10

**User Story:** Como administrador del sistema, quiero ver métricas de efectividad de cada FAQ, para que pueda identificar cuáles son más útiles y cuáles necesitan mejorarse.

#### Acceptance Criteria

1. WHEN una FAQ es utilizada en una respuesta THEN el Sistema SHALL incrementar el contador de uso de esa FAQ
2. WHEN un administrador accede a las estadísticas de FAQ THEN el Sistema SHALL mostrar número de usos, última fecha de uso y tasa de éxito
3. WHEN el Sistema genera una respuesta usando una FAQ THEN el Sistema SHALL registrar si la respuesta fue útil basándose en feedback del usuario
4. WHEN un administrador revisa FAQs poco utilizadas THEN el Sistema SHALL identificar FAQs que no han sido usadas en los últimos 90 días
5. WHEN un administrador exporta métricas THEN el Sistema SHALL generar un reporte con estadísticas de uso por FAQ y categoría

### Requirement 12

**User Story:** Como administrador del sistema, quiero que el chatbot clasifique la intención de las preguntas antes de buscar, para que pueda filtrar y priorizar resultados más relevantes según el tipo de consulta.

#### Acceptance Criteria

1. WHEN el Sistema recibe una pregunta del usuario THEN el Sistema SHALL clasificar la intención en categorías predefinidas antes de realizar la búsqueda semántica
2. WHEN el Sistema clasifica una intención THEN el Sistema SHALL identificar al menos estas categorías: cursos, inscripciones, pagos, ubicaciones, requisitos, eventos, horarios y general
3. WHEN el Sistema identifica una intención específica THEN el Sistema SHALL filtrar la búsqueda semántica para priorizar FAQs de esa categoría
4. WHEN el Sistema no puede determinar la intención con confianza THEN el Sistema SHALL realizar una búsqueda semántica sin filtros de categoría
5. WHEN un administrador configura el clasificador THEN el Sistema SHALL permitir agregar, editar o eliminar categorías de intención desde el admin de Django
6. WHEN el Sistema clasifica múltiples intenciones en una pregunta THEN el Sistema SHALL considerar todas las intenciones relevantes en la búsqueda
