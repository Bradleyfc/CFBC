# Configuración del Chatbot Semántico

## Variables de Entorno

El chatbot utiliza las siguientes variables de entorno que deben configurarse:

### Variables Requeridas

```bash
# Configuración del LLM
LLM_ENABLED=True
LLM_MODEL=google/flan-t5-small
MAX_TOKENS=300

# Configuración de búsqueda semántica
SEARCH_TOP_K=3
RESPONSE_TIMEOUT_SECONDS=30

# Configuración del modelo de embeddings
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384

# Configuración de FAISS
FAISS_INDEX_PATH=chatbot_data/faiss_index
MODELS_PATH=chatbot_data/models
```

### Variables Opcionales

```bash
# Configuración de logging
CHATBOT_LOG_LEVEL=INFO

# Configuración de cache
CHATBOT_CACHE_TIMEOUT=3600
```

## Instalación de Dependencias

### Opción 1: Instalación Automática Completa (Recomendado)

```bash
# Instalación completa con un solo comando
python install_chatbot.py
```

O usando Make:
```bash
make install
```

### Opción 2: Instalación Manual Paso a Paso

#### 1. Instalar paquetes Python

```bash
pip install -r requirements.txt
```

#### 2. Descargar modelos de Hugging Face

**IMPORTANTE**: El chatbot requiere descargar ~800 MB de modelos de IA.

#### Opción A: Comando Django (Recomendado)
```bash
python manage.py download_models --verbose
```

#### Opción B: Script directo
```bash
python chatbot/download_models.py
```

#### Opción C: Descarga automática
Los modelos se descargan automáticamente al usar el chatbot por primera vez.

**Modelos que se descargan**:
- `paraphrase-multilingual-MiniLM-L12-v2` (~470 MB) - Embeddings semánticos
- `google/flan-t5-small` (~308 MB) - Generación de texto

**Ubicación**: `~/.cache/huggingface/` (Windows: `C:\Users\[usuario]\.cache\huggingface\`)

## Configuración de la Base de Datos

### 1. Aplicar migraciones

```bash
python manage.py migrate
```

### 2. Cargar datos iniciales

```bash
# Cargar categorías FAQ
python manage.py loaddata chatbot/fixtures/categorias_faq.json

# Cargar FAQs de ejemplo
python manage.py loaddata chatbot/fixtures/faqs_iniciales.json

# Cargar variaciones de FAQs
python manage.py loaddata chatbot/fixtures/faq_variaciones.json
```

### 3. Construir índice inicial

```bash
python manage.py rebuild_index
```

## Configuración del Servidor Web

### 1. Archivos estáticos

Asegúrate de que los archivos estáticos del chatbot estén servidos correctamente:

```bash
python manage.py collectstatic
```

### 2. Context Processor

El context processor del chatbot debe estar habilitado en `settings.py`:

```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... otros context processors
                'chatbot.context_processors.chatbot_context',
            ],
        },
    },
]
```

## Comandos de Mantenimiento

### Reconstruir índice

```bash
# Reconstruir todo el índice
python manage.py rebuild_index

# Reconstruir solo FAQs
python manage.py rebuild_index --content-type=faqs

# Reconstruir con información detallada
python manage.py rebuild_index --verbose
```

### Exportar métricas

```bash
# Exportar métricas de los últimos 30 días
python manage.py export_metrics

# Exportar métricas de los últimos 7 días
python manage.py export_metrics --days=7

# Exportar a directorio específico
python manage.py export_metrics --output-dir=/ruta/exportacion
```
## Estructura de Directorios

```
chatbot/
├── fixtures/                 # Datos iniciales
├── management/commands/       # Comandos de Django
├── services/                  # Servicios del chatbot
├── static/chatbot/           # Archivos estáticos
├── templates/chatbot/        # Templates HTML
├── migrations/               # Migraciones de base de datos
└── chatbot_data/            # Datos del chatbot (creado automáticamente)
    ├── faiss_index/         # Índice FAISS
    └── models/              # Modelos descargados
```

## Requisitos del Sistema

### Hardware Mínimo

- RAM: 4GB (recomendado 8GB)
- Almacenamiento: 2GB libres para modelos
- CPU: Procesador de 64 bits

### Software

- Python 3.8+
- PostgreSQL 12+ (o SQLite para desarrollo)
- Sistema operativo: Windows, Linux, o macOS

## Solución de Problemas

### Error: "No module named 'sentence_transformers'"

```bash
pip install sentence-transformers
```

### Error: "FAISS index not found"

```bash
python manage.py rebuild_index
```

### Error: "Model download failed"

**Solución rápida - Deshabilitar LLM**:
```bash
# Usar solo embeddings (más rápido)
python manage.py manage_models --disable-llm
```

**Solución completa**:
```bash
# Verificar estado
python manage.py manage_models --action=check

# Descargar con reintentos
python manage.py manage_models --action=download --force

# Verificar conexión
python manage.py shell -c "
from chatbot.services.semantic_search import SemanticSearchService
search = SemanticSearchService()
"
```

### Descarga muy lenta

**Acelerar descarga**:
```bash
# Solo descargar embeddings (omitir LLM)
python manage.py manage_models --model=embeddings

# Verificar si ya está en cache
python manage.py manage_models --action=check
```

### Rendimiento lento

1. **Deshabilitar LLM para acelerar**:
   ```bash
   # En variables de entorno
   LLM_ENABLED=false
   
   # O usando comando
   python manage.py manage_models --disable-llm
   ```

2. **Verificar modelos en cache**:
   ```bash
   python manage.py manage_models --action=check
   ```

3. **Descargar solo embeddings**:
   ```bash
   python manage.py manage_models --action=download --model=embeddings
   ```

4. **Optimizar configuración**:
   - Ajustar SEARCH_TOP_K para reducir resultados
   - Usar GPU si está disponible
   - Verificar que los modelos estén cargados en memoria

## Monitoreo

### Logs del sistema

Los logs del chatbot se escriben usando el logger de Django:

```python
import logging
logger = logging.getLogger('chatbot')
```

### Métricas disponibles

- Número de interacciones por día
- Tiempo promedio de respuesta
- Tasa de éxito de FAQs
- Preguntas candidatas para nuevas FAQs

## Despliegue en Producción

### 1. Variables de entorno

Configura todas las variables requeridas en el servidor de producción.

### 2. Seguridad

- Desactiva DEBUG en settings.py
- Configura ALLOWED_HOSTS apropiadamente
- Usa HTTPS para las APIs del chatbot

### 3. Rendimiento

- Considera usar un servidor de aplicaciones como Gunicorn
- Configura un proxy reverso (nginx)
- Implementa cache para respuestas frecuentes