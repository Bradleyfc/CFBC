# Chatbot Semántico - Centro Fray Bartolomé de las Casas

Sistema de chatbot inteligente con búsqueda semántica y generación de respuestas usando LLM local.

## Arquitectura

- **Búsqueda Semántica**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Vector Store**: FAISS para búsqueda rápida por similitud
- **LLM Local**: google/flan-t5-small para generación de respuestas
- **Clasificador de Intención**: Sistema basado en keywords para categorizar preguntas

## Estructura del Proyecto

```
chatbot/
├── models.py              # Modelos Django (FAQ, ChatInteraction, etc.)
├── services/              # Servicios de negocio
│   ├── semantic_search.py # Búsqueda semántica con FAISS
│   ├── llm_generator.py   # Generación con LLM
│   ├── intent_classifier.py # Clasificación de intención
│   ├── content_indexer.py # Indexación de contenido
│   └── orchestrator.py    # Orquestador principal
├── views.py               # API endpoints
├── admin.py               # Configuración del admin
├── management/commands/   # Comandos de gestión
└── config.py              # Configuración y variables de entorno
```

## Variables de Entorno

Puedes configurar el chatbot mediante variables de entorno en tu archivo `.env`:

```bash
# Directorios
CHATBOT_DATA_DIR=/path/to/chatbot_data
CHATBOT_MODEL_PATH=/path/to/models
CHATBOT_INDEX_PATH=/path/to/faiss_index.bin

# Modelos
SENTENCE_TRANSFORMER_MODEL=paraphrase-multilingual-MiniLM-L12-v2
LLM_MODEL=google/flan-t5-small
CHATBOT_ENABLE_LLM=true

# Parámetros de búsqueda
CHATBOT_SEARCH_TOP_K=3
CHATBOT_MAX_TOKENS=300
CHATBOT_INTENT_THRESHOLD=0.6

# Sesión
CHATBOT_SESSION_TIMEOUT=30
```

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar migraciones:
```bash
python manage.py makemigrations chatbot
python manage.py migrate
```

3. Construir el índice inicial:
```bash
python manage.py rebuild_index
```

## Requisitos del Sistema

- **CPU**: 4+ cores recomendado
- **RAM**: 4GB mínimo (2GB para modelos, 2GB para Django + FAISS)
- **Almacenamiento**: 2GB para modelos + índice
- **GPU**: Opcional (acelera inferencia 5-10x)

## Uso

### Desde el Frontend

El widget de chat se mostrará automáticamente en la página de inicio.

### API Endpoints

**POST /chatbot/ask/**
```json
{
  "pregunta": "¿Cuándo empiezan las inscripciones?",
  "session_id": "abc123"
}
```

Respuesta:
```json
{
  "respuesta": "Las inscripciones empiezan el 15 de enero...",
  "confianza": 0.85,
  "tiempo": 1.2
}
```

**POST /chatbot/feedback/**
```json
{
  "interaction_id": 123,
  "fue_util": true
}
```

## Comandos de Gestión

### Reconstruir índice completo
```bash
python manage.py rebuild_index
```

### Exportar métricas
```bash
python manage.py export_metrics --output metrics.csv
```

## Administración

Accede al admin de Django para:
- Gestionar FAQs y sus variaciones
- Ver preguntas sugeridas para nuevas FAQs
- Revisar métricas de uso
- Configurar categorías

## Monitoreo

El sistema registra:
- Todas las interacciones (anonimizadas)
- Tiempos de respuesta
- Errores y excepciones
- Uso de FAQs
- Feedback de usuarios

## Troubleshooting

### Los modelos no se descargan
Los modelos se descargan automáticamente la primera vez. Asegúrate de tener conexión a internet.

### Error de memoria
Reduce el tamaño del batch o usa un modelo más pequeño.

### Respuestas lentas
- Verifica que los modelos estén cargados en memoria
- Considera usar GPU
- Revisa el tamaño del índice FAISS

## Desarrollo

Para ejecutar tests:
```bash
python manage.py test chatbot
```

Para ejecutar property tests:
```bash
pytest chatbot/tests/ -v
```
