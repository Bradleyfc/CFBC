# Design Document - Chatbot Semántico

## Overview

El sistema de chatbot semántico es una arquitectura híbrida que combina búsqueda por similitud semántica (Retrieval) con generación de lenguaje natural (Generation) para proporcionar respuestas precisas y contextualizadas a las preguntas de los usuarios sobre el sitio web.

El sistema sigue el patrón RAG (Retrieval-Augmented Generation):
1. **Retriever**: Usa sentence-transformers para encontrar documentos relevantes mediante embeddings vectoriales
2. **Intent Classifier**: Clasifica la intención de la pregunta para filtrar resultados
3. **Reader/Generator**: Usa un LLM local pequeño para generar respuestas naturales basadas en el contexto recuperado

Esta arquitectura garantiza que las respuestas estén fundamentadas en información real del sitio, evitando alucinaciones del modelo.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Widget)                         │
│  - Chat UI (HTML/CSS/JS)                                        │
│  - Session Management                                            │
│  - Real-time Updates                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Django Backend (Views)                       │
│  - API Endpoints                                                 │
│  - Session Management                                            │
│  - Request Validation                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Chatbot Service Layer                         │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ Intent Classifier│  │  Semantic Search │  │  LLM Generator│ │
│  │                  │  │                  │  │               │ │
│  │ - Categorization │  │ - Embeddings     │  │ - Context     │ │
│  │ - Confidence     │  │ - Similarity     │  │ - Generation  │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│           │                     │                      │         │
│           └─────────────────────┼──────────────────────┘         │
│                                 │                                │
└─────────────────────────────────┼────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Knowledge Base Layer                        │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  FAQ Model   │  │  Curso Model │  │ Noticia Model│          │
│  │              │  │              │  │              │          │
│  │ - Questions  │  │ - Content    │  │ - Content    │          │
│  │ - Answers    │  │ - Metadata   │  │ - Metadata   │          │
│  │ - Variations │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Vector Store (FAISS)                        │
│  - Embeddings Storage                                            │
│  - Fast Similarity Search                                        │
│  - Index Management                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Django 4.x (Framework principal)
- sentence-transformers (Embeddings)
- FAISS (Vector similarity search)
- transformers (LLM local)
- torch (Deep learning backend)

**Frontend:**
- HTML5/CSS3
- JavaScript (Vanilla o Alpine.js para reactividad)
- WebSocket o AJAX para comunicación en tiempo real

**Storage:**
- PostgreSQL/SQLite (Base de datos relacional)
- FAISS Index (Almacenamiento vectorial en disco)

**Models:**
- Sentence-Transformer: `paraphrase-multilingual-MiniLM-L12-v2` (118MB, multilingüe)
- LLM Local: `google/flan-t5-small` (308MB) o `facebook/opt-350m` (700MB)

## Components and Interfaces

### 1. Django Models

#### FAQ Model
```python
class FAQ(models.Model):
    """Modelo para preguntas frecuentes"""
    pregunta = models.CharField(max_length=500)
    respuesta = models.TextField()
    categoria = models.ForeignKey('CategoriaFAQ', on_delete=models.CASCADE)
    prioridad = models.IntegerField(default=0)
    destacada = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Métricas
    veces_usada = models.IntegerField(default=0)
    ultima_fecha_uso = models.DateTimeField(null=True, blank=True)
    tasa_exito = models.FloatField(default=0.0)
```

#### FAQVariation Model
```python
class FAQVariation(models.Model):
    """Variaciones de preguntas para una FAQ"""
    faq = models.ForeignKey(FAQ, on_delete=models.CASCADE, related_name='variaciones')
    texto_variacion = models.CharField(max_length=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
```

#### CategoriaFAQ Model
```python
class CategoriaFAQ(models.Model):
    """Categorías para organizar FAQs"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    icono = models.CharField(max_length=50, blank=True)
    orden = models.IntegerField(default=0)
```

#### ChatInteraction Model
```python
class ChatInteraction(models.Model):
    """Registro de interacciones del chatbot"""
    session_id = models.CharField(max_length=100)
    pregunta = models.TextField()
    respuesta = models.TextField()
    documentos_recuperados = models.JSONField()
    intencion_detectada = models.CharField(max_length=50, null=True)
    confianza = models.FloatField()
    fue_util = models.BooleanField(null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    tiempo_respuesta = models.FloatField()  # en segundos
```

#### DocumentEmbedding Model
```python
class DocumentEmbedding(models.Model):
    """Almacena embeddings y metadatos de documentos indexados"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    texto_indexado = models.TextField()
    embedding_vector = models.BinaryField()  # Serializado con pickle/numpy
    categoria = models.CharField(max_length=50)
    fecha_indexacion = models.DateTimeField(auto_now=True)
```

### 2. Service Layer Components

#### IntentClassifier
```python
class IntentClassifier:
    """Clasifica la intención de las preguntas"""
    
    INTENCIONES = [
        'cursos', 'inscripciones', 'pagos', 'ubicaciones',
        'requisitos', 'eventos', 'horarios', 'general'
    ]
    
    def classify(self, pregunta: str) -> tuple[str, float]:
        """
        Clasifica la intención de una pregunta
        Returns: (intencion, confianza)
        """
        pass
    
    def get_keywords_for_intent(self, intencion: str) -> list[str]:
        """Retorna palabras clave asociadas a una intención"""
        pass
```

#### SemanticSearchService
```python
class SemanticSearchService:
    """Servicio de búsqueda semántica"""
    
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = None  # FAISS index
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Genera embedding para un texto"""
        pass
    
    def search(self, query: str, top_k: int = 3, categoria: str = None) -> list[dict]:
        """
        Busca documentos similares
        Returns: Lista de documentos con scores
        """
        pass
    
    def index_document(self, doc_id: int, text: str, metadata: dict):
        """Indexa un nuevo documento"""
        pass
    
    def rebuild_index(self):
        """Reconstruye el índice completo"""
        pass
```

#### LLMGeneratorService
```python
class LLMGeneratorService:
    """Servicio de generación con LLM local"""
    
    def __init__(self, model_name: str = 'google/flan-t5-small'):
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def generate_response(
        self, 
        pregunta: str, 
        contexto: list[str], 
        max_tokens: int = 300
    ) -> str:
        """
        Genera una respuesta basada en el contexto
        """
        pass
    
    def build_prompt(self, pregunta: str, contexto: list[str]) -> str:
        """Construye el prompt para el LLM"""
        pass
```

#### ChatbotOrchestrator
```python
class ChatbotOrchestrator:
    """Orquesta todos los componentes del chatbot"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.semantic_search = SemanticSearchService()
        self.llm_generator = LLMGeneratorService()
    
    def process_question(self, pregunta: str, session_id: str) -> dict:
        """
        Procesa una pregunta y retorna la respuesta
        Returns: {
            'respuesta': str,
            'confianza': float,
            'documentos': list,
            'intencion': str
        }
        """
        pass
    
    def log_interaction(self, interaction_data: dict):
        """Registra la interacción en la base de datos"""
        pass
```

### 3. Indexing Service

#### ContentIndexer
```python
class ContentIndexer:
    """Indexa contenido de diferentes fuentes"""
    
    def index_faqs(self):
        """Indexa todas las FAQs activas"""
        pass
    
    def index_cursos(self):
        """Indexa información de cursos"""
        pass
    
    def index_noticias(self):
        """Indexa noticias del blog"""
        pass
    
    def index_all(self):
        """Indexa todo el contenido"""
        pass
    
    def extract_text_from_curso(self, curso: Curso) -> str:
        """Extrae texto relevante de un curso"""
        pass
    
    def extract_text_from_noticia(self, noticia: Noticia) -> str:
        """Extrae texto relevante de una noticia"""
        pass
```

### 4. API Endpoints

```python
# views.py

def chatbot_widget(request):
    """Renderiza el widget del chatbot"""
    pass

def chatbot_ask(request):
    """
    POST /chatbot/ask/
    Body: {
        "pregunta": str,
        "session_id": str
    }
    Response: {
        "respuesta": str,
        "confianza": float,
        "tiempo": float
    }
    """
    pass

def chatbot_feedback(request):
    """
    POST /chatbot/feedback/
    Body: {
        "interaction_id": int,
        "fue_util": bool
    }
    """
    pass

def admin_suggested_faqs(request):
    """Vista admin para FAQs sugeridas"""
    pass
```

## Data Models

### Database Schema

```sql
-- FAQ Table
CREATE TABLE faq (
    id SERIAL PRIMARY KEY,
    pregunta VARCHAR(500) NOT NULL,
    respuesta TEXT NOT NULL,
    categoria_id INTEGER REFERENCES categoria_faq(id),
    prioridad INTEGER DEFAULT 0,
    destacada BOOLEAN DEFAULT FALSE,
    activa BOOLEAN DEFAULT TRUE,
    veces_usada INTEGER DEFAULT 0,
    ultima_fecha_uso TIMESTAMP,
    tasa_exito FLOAT DEFAULT 0.0,
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP DEFAULT NOW()
);

-- FAQ Variations Table
CREATE TABLE faq_variation (
    id SERIAL PRIMARY KEY,
    faq_id INTEGER REFERENCES faq(id) ON DELETE CASCADE,
    texto_variacion VARCHAR(500) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Categoria FAQ Table
CREATE TABLE categoria_faq (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    slug VARCHAR(100) UNIQUE NOT NULL,
    icono VARCHAR(50),
    orden INTEGER DEFAULT 0
);

-- Chat Interaction Table
CREATE TABLE chat_interaction (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    documentos_recuperados JSONB,
    intencion_detectada VARCHAR(50),
    confianza FLOAT,
    fue_util BOOLEAN,
    fecha TIMESTAMP DEFAULT NOW(),
    tiempo_respuesta FLOAT
);

-- Document Embedding Table
CREATE TABLE document_embedding (
    id SERIAL PRIMARY KEY,
    content_type_id INTEGER,
    object_id INTEGER,
    texto_indexado TEXT NOT NULL,
    embedding_vector BYTEA,
    categoria VARCHAR(50),
    fecha_indexacion TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_faq_categoria ON faq(categoria_id);
CREATE INDEX idx_faq_activa ON faq(activa);
CREATE INDEX idx_chat_session ON chat_interaction(session_id);
CREATE INDEX idx_chat_fecha ON chat_interaction(fecha);
CREATE INDEX idx_embedding_content ON document_embedding(content_type_id, object_id);
```

### FAISS Index Structure

```python
# Estructura del índice FAISS
{
    'index': faiss.IndexFlatIP,  # Inner Product (cosine similarity)
    'id_to_metadata': {
        0: {
            'doc_id': 1,
            'type': 'faq',
            'categoria': 'cursos',
            'text': '...'
        },
        1: {
            'doc_id': 5,
            'type': 'curso',
            'categoria': 'cursos',
            'text': '...'
        }
    }
}
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Response time constraint
*For any* valid user question, the system should process and return a response in less than 5 seconds.
**Validates: Requirements 1.2**

### Property 2: Session history persistence
*For any* chat session and sequence of messages, the conversation history should be maintained throughout the session, including after closing and reopening the widget.
**Validates: Requirements 1.3, 1.4**

### Property 3: Embedding generation and search pipeline
*For any* user question, the system should generate embeddings using sentence-transformers and perform a similarity search in the vector index, returning the top 3 most relevant documents based on cosine similarity.
**Validates: Requirements 2.1, 2.2, 2.3, 2.5**

### Property 4: Index consistency on content changes
*For any* content modification (create, update, delete) on FAQs, courses, or blog posts, the system should automatically regenerate embeddings and update the vector index to maintain consistency.
**Validates: Requirements 4.3, 4.4, 4.5, 9.4**

### Property 5: Universal content indexing
*For any* content type (FAQ, course, blog post, static page), the system should automatically generate and store embeddings that include all relevant fields (title, description, content, metadata).
**Validates: Requirements 2.4, 4.6, 4.7, 4.8**

### Property 6: Context-based response generation
*For any* generated response, the system should combine the retrieved context from semantic search with the user's question, and the response should contain information from the retrieved documents.
**Validates: Requirements 3.3, 5.1**

### Property 7: Response length constraint
*For any* LLM-generated response, the output should not exceed 300 tokens.
**Validates: Requirements 3.4**

### Property 8: FAQ variation indexing
*For any* FAQ with multiple question variations, each variation should be indexed with separate embeddings that all point to the same answer, and all variations should be considered during semantic search.
**Validates: Requirements 9.2, 9.3**

### Property 9: Result ordering by priority and category
*For any* search query with detected intent, results should be filtered by category and ordered by: (1) highlighted FAQs first, (2) priority value, (3) similarity score.
**Validates: Requirements 11.3, 11.4, 11.5**

### Property 10: FAQ usage tracking
*For any* FAQ used in a response, the system should increment its usage counter by 1 and update the last usage date.
**Validates: Requirements 10.1**

### Property 11: Interaction logging with anonymization
*For any* user question processed, the system should log the question, generated response, retrieved documents, detected intent, confidence score, and response time, while anonymizing any personal user data.
**Validates: Requirements 8.1, 8.7, 6.5**

### Property 12: Low-confidence FAQ suggestion
*For any* interaction with low confidence score or negative user feedback, the system should mark the question as a candidate for a new FAQ.
**Validates: Requirements 8.2**

### Property 13: Similar question grouping
*For any* set of repeated similar questions, the system should group them together and suggest them as variations of a common FAQ.
**Validates: Requirements 8.5, 9.5**

### Property 14: FAQ approval and indexing
*For any* suggested FAQ approved by an administrator, the system should create the FAQ entry and automatically index it with embeddings.
**Validates: Requirements 8.6**

### Property 15: Intent classification
*For any* user question, the system should classify the intent into one of the predefined categories (cursos, inscripciones, pagos, ubicaciones, requisitos, eventos, horarios, general) before performing semantic search.
**Validates: Requirements 12.1, 12.2**

### Property 16: Intent-based search filtering
*For any* question with a detected intent above confidence threshold, the semantic search should prioritize FAQs from that category; otherwise, search without category filters.
**Validates: Requirements 12.3**

### Property 17: Multi-intent handling
*For any* question with multiple detected intents, the system should consider all relevant intents when performing the semantic search.
**Validates: Requirements 12.6**

### Property 18: Feedback tracking
*For any* response generated using a FAQ, the system should record whether the response was useful based on user feedback.
**Validates: Requirements 10.3**

### Property 19: Unused FAQ identification
*For any* query for underutilized FAQs, the system should correctly identify and return FAQs that have not been used in the last 90 days.
**Validates: Requirements 10.4**

### Property 20: Course information completeness
*For any* response about courses, the system should include updated information about availability, dates, and requirements from the indexed course data.
**Validates: Requirements 5.5**



## Error Handling

### Error Categories and Handling Strategies

#### 1. Model Loading Errors
**Scenario**: Sentence-transformer or LLM model fails to load
- **Handling**: 
  - Log error with full stack trace
  - Return HTTP 503 Service Unavailable
  - Display user-friendly message: "El chatbot está temporalmente fuera de servicio"
  - Fallback: If only LLM fails, return raw search results (Requirement 3.5)

#### 2. Embedding Generation Errors
**Scenario**: Failed to generate embeddings for user question
- **Handling**:
  - Log error with question text (anonymized)
  - Retry once with exponential backoff
  - If retry fails, return error message to user
  - Suggest alternative: "Por favor, intenta reformular tu pregunta"

#### 3. Vector Search Errors
**Scenario**: FAISS index is corrupted or unavailable
- **Handling**:
  - Log critical error
  - Attempt to rebuild index from database
  - If rebuild fails, return fallback response
  - Notify administrators via logging system

#### 4. Empty Search Results
**Scenario**: No relevant documents found (Requirement 5.2)
- **Handling**:
  - Return polite message: "Lo siento, no tengo información sobre ese tema en este momento"
  - Suggest: "Por favor, contacta al administrador o intenta con otra pregunta"
  - Log as potential FAQ candidate

#### 5. Timeout Errors
**Scenario**: Response generation exceeds 5 seconds (Requirement 1.2)
- **Handling**:
  - Cancel LLM generation
  - Return partial results from semantic search
  - Log timeout event with query details
  - Display: "La respuesta está tomando más tiempo del esperado. Aquí está la información que encontré..."

#### 6. Database Errors
**Scenario**: Failed to save interaction log or update FAQ metrics
- **Handling**:
  - Log error but don't fail the user request
  - Queue for retry with background task
  - Continue serving the response to user

#### 7. Invalid Input
**Scenario**: Empty question, too long question (>1000 chars), or malicious input
- **Handling**:
  - Validate input before processing
  - Return HTTP 400 Bad Request
  - Log suspicious patterns for security monitoring

#### 8. Session Errors
**Scenario**: Invalid or expired session_id
- **Handling**:
  - Create new session automatically
  - Return response normally
  - Log session creation

### Error Response Format

```json
{
    "success": false,
    "error": {
        "code": "EMBEDDING_GENERATION_FAILED",
        "message": "No pudimos procesar tu pregunta en este momento",
        "user_message": "Por favor, intenta reformular tu pregunta o contacta al administrador",
        "retry_allowed": true
    }
}
```

## Testing Strategy

### Overview
The testing strategy combines unit tests for specific components and property-based tests for universal correctness properties. This dual approach ensures both concrete functionality and general correctness across all inputs.

### Property-Based Testing

**Framework**: Hypothesis (Python)
**Configuration**: Minimum 100 iterations per property test

All property-based tests will be tagged with the format: `**Feature: chatbot-semantico, Property {number}: {property_text}**`

#### Property Test Examples

**Property 1: Response time constraint**
```python
@given(question=st.text(min_size=1, max_size=500))
@settings(max_examples=100)
def test_response_time_constraint(question):
    """Feature: chatbot-semantico, Property 1: Response time constraint"""
    start_time = time.time()
    response = chatbot.process_question(question, session_id="test")
    elapsed = time.time() - start_time
    assert elapsed < 5.0, f"Response took {elapsed}s, exceeds 5s limit"
```

**Property 3: Embedding generation and search pipeline**
```python
@given(question=st.text(min_size=1, max_size=500))
@settings(max_examples=100)
def test_embedding_search_pipeline(question):
    """Feature: chatbot-semantico, Property 3: Embedding generation and search pipeline"""
    result = chatbot.process_question(question, session_id="test")
    
    # Should have generated embeddings
    assert 'embedding' in result['debug_info']
    assert len(result['debug_info']['embedding']) == 384  # MiniLM dimension
    
    # Should have retrieved documents
    assert 'retrieved_docs' in result
    assert len(result['retrieved_docs']) <= 3
    
    # Should be ordered by similarity
    if len(result['retrieved_docs']) > 1:
        scores = [doc['score'] for doc in result['retrieved_docs']]
        assert scores == sorted(scores, reverse=True)
```

**Property 4: Index consistency on content changes**
```python
@given(
    faq_data=st.fixed_dictionaries({
        'pregunta': st.text(min_size=10, max_size=200),
        'respuesta': st.text(min_size=20, max_size=500),
        'categoria': st.sampled_from(['cursos', 'pagos', 'inscripciones'])
    })
)
@settings(max_examples=100)
def test_index_consistency(faq_data):
    """Feature: chatbot-semantico, Property 4: Index consistency on content changes"""
    # Create FAQ
    faq = FAQ.objects.create(**faq_data)
    
    # Check embedding was created
    embedding = DocumentEmbedding.objects.filter(
        content_type=ContentType.objects.get_for_model(FAQ),
        object_id=faq.id
    ).first()
    assert embedding is not None
    
    # Update FAQ
    faq.pregunta = "Updated: " + faq.pregunta
    faq.save()
    
    # Check embedding was updated
    updated_embedding = DocumentEmbedding.objects.get(id=embedding.id)
    assert updated_embedding.fecha_indexacion > embedding.fecha_indexacion
    
    # Delete FAQ
    faq_id = faq.id
    faq.delete()
    
    # Check embedding was deleted
    assert not DocumentEmbedding.objects.filter(
        content_type=ContentType.objects.get_for_model(FAQ),
        object_id=faq_id
    ).exists()
```

**Property 7: Response length constraint**
```python
@given(
    question=st.text(min_size=10, max_size=200),
    context=st.lists(st.text(min_size=50, max_size=500), min_size=1, max_size=3)
)
@settings(max_examples=100)
def test_response_length_constraint(question, context):
    """Feature: chatbot-semantico, Property 7: Response length constraint"""
    llm_service = LLMGeneratorService()
    response = llm_service.generate_response(question, context, max_tokens=300)
    
    # Count tokens
    tokenizer = llm_service.tokenizer
    token_count = len(tokenizer.encode(response))
    
    assert token_count <= 300, f"Response has {token_count} tokens, exceeds 300 limit"
```

**Property 10: FAQ usage tracking**
```python
@given(
    faq_data=st.fixed_dictionaries({
        'pregunta': st.text(min_size=10, max_size=200),
        'respuesta': st.text(min_size=20, max_size=500),
    })
)
@settings(max_examples=100)
def test_faq_usage_tracking(faq_data):
    """Feature: chatbot-semantico, Property 10: FAQ usage tracking"""
    faq = FAQ.objects.create(**faq_data, veces_usada=0)
    initial_count = faq.veces_usada
    initial_date = faq.ultima_fecha_uso
    
    # Simulate FAQ being used in response
    chatbot.track_faq_usage(faq.id)
    
    faq.refresh_from_db()
    assert faq.veces_usada == initial_count + 1
    assert faq.ultima_fecha_uso > initial_date or initial_date is None
```

### Unit Testing

Unit tests focus on specific examples, edge cases, and integration points.

#### Core Component Tests

**SemanticSearchService Tests**
- Test embedding generation for Spanish text
- Test cosine similarity calculation accuracy
- Test FAISS index save/load operations
- Test handling of empty index
- Test handling of duplicate documents

**LLMGeneratorService Tests**
- Test prompt construction with context
- Test handling of empty context (edge case from Requirement 3.5)
- Test token counting accuracy
- Test response truncation at 300 tokens
- Test model loading and initialization

**IntentClassifier Tests**
- Test classification for each intent category
- Test handling of ambiguous questions (low confidence)
- Test multi-intent detection
- Test Spanish language patterns and keywords

**ChatbotOrchestrator Tests**
- Test end-to-end question processing
- Test interaction logging
- Test error handling and fallbacks
- Test session management

#### Django Model Tests

**FAQ Model Tests**
- Test FAQ creation with all fields
- Test FAQ update triggers embedding regeneration
- Test FAQ deletion removes embeddings
- Test usage counter increment
- Test priority ordering

**FAQVariation Model Tests**
- Test variation creation and linking to FAQ
- Test variation indexing
- Test variation search inclusion

**ChatInteraction Model Tests**
- Test interaction logging with all fields
- Test anonymization of personal data
- Test feedback recording

#### Integration Tests

**Indexing Pipeline Tests**
- Test indexing all FAQs
- Test indexing all courses
- Test indexing all blog posts
- Test incremental indexing on content update
- Test full index rebuild

**Search Pipeline Tests**
- Test search with intent filtering
- Test search without intent filtering
- Test search result ordering (priority, similarity)
- Test search with no results (edge case from Requirement 5.2)

**Admin Interface Tests**
- Test FAQ CRUD operations
- Test suggested FAQ approval workflow
- Test metrics dashboard display
- Test category management

### Test Data Generators

For property-based testing, we'll create smart generators that produce realistic test data:

```python
# Spanish text generator
spanish_text = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
        whitelist_characters='áéíóúñÁÉÍÓÚÑ¿?¡!'
    ),
    min_size=10,
    max_size=500
)

# FAQ question generator
faq_questions = st.sampled_from([
    "¿Cuándo empiezan las inscripciones?",
    "¿Dónde puedo pagar la matrícula?",
    "¿Qué requisitos necesito para el curso de inglés?",
    "¿Cuál es el horario de clases?",
    # ... more realistic questions
])

# Course data generator
course_data = st.fixed_dictionaries({
    'name': st.text(min_size=10, max_size=90),
    'description': st.text(min_size=50, max_size=500),
    'area': st.sampled_from(['idiomas', 'humanidades', 'computacion']),
    'status': st.sampled_from(['I', 'IT', 'P', 'F'])
})
```

### Test Coverage Goals

- **Unit Tests**: 80% code coverage minimum
- **Property Tests**: All 20 correctness properties must have corresponding tests
- **Integration Tests**: Cover all major user workflows
- **Edge Cases**: All identified edge cases must have explicit tests

### Continuous Testing

- Run unit tests on every commit
- Run property tests (100 iterations) on every PR
- Run full property tests (1000 iterations) nightly
- Run integration tests before deployment



## Implementation Details

### Model Selection Rationale

#### Sentence-Transformer Model
**Selected**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Size**: 118MB
- **Embedding Dimension**: 384
- **Languages**: Supports Spanish and 50+ languages
- **Performance**: Fast inference (~10ms per sentence)
- **Quality**: Good balance between size and accuracy for semantic search

**Alternative**: `distiluse-base-multilingual-cased-v2` (larger, 480MB, better quality)

#### LLM Model
**Selected**: `google/flan-t5-small`
- **Size**: 308MB
- **Parameters**: 80M
- **Strengths**: Good instruction following, multilingual support
- **Inference**: ~500ms for 100 tokens on CPU

**Alternative**: `facebook/opt-350m` (700MB, better Spanish but larger)

### Vector Store: FAISS

**Index Type**: `IndexFlatIP` (Inner Product for cosine similarity)
- Simple, accurate, no training required
- Good for datasets up to 100K vectors
- Can upgrade to `IndexIVFFlat` if dataset grows

**Storage Strategy**:
- Save index to disk: `chatbot_data/faiss_index.bin`
- Save metadata mapping: `chatbot_data/id_to_metadata.json`
- Rebuild index on server startup if files missing
- Incremental updates for single document changes

### Intent Classification Implementation

**Approach**: Keyword-based classification with confidence scoring

```python
INTENT_KEYWORDS = {
    'cursos': ['curso', 'clase', 'materia', 'asignatura', 'programa', 'estudiar'],
    'inscripciones': ['inscribir', 'matricular', 'registrar', 'inscripción', 'matrícula'],
    'pagos': ['pagar', 'pago', 'costo', 'precio', 'tarifa', 'pensión', 'arancel'],
    'ubicaciones': ['dónde', 'ubicación', 'dirección', 'lugar', 'edificio', 'aula'],
    'requisitos': ['requisito', 'necesitar', 'requerir', 'condición', 'documento'],
    'eventos': ['evento', 'actividad', 'ceremonia', 'celebración', 'conferencia'],
    'horarios': ['horario', 'hora', 'cuándo', 'fecha', 'día', 'calendario'],
    'general': []  # default fallback
}

def classify_intent(question: str) -> tuple[str, float]:
    question_lower = question.lower()
    scores = {}
    
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent == 'general':
            continue
        score = sum(1 for kw in keywords if kw in question_lower)
        if score > 0:
            scores[intent] = score
    
    if not scores:
        return 'general', 0.5
    
    max_intent = max(scores, key=scores.get)
    max_score = scores[max_intent]
    confidence = min(max_score / 3.0, 1.0)  # Normalize to 0-1
    
    return max_intent, confidence
```

**Confidence Threshold**: 0.6
- Above 0.6: Use intent filtering
- Below 0.6: Search without filters

### Prompt Engineering for LLM

**Template**:
```python
PROMPT_TEMPLATE = """Eres un asistente virtual del Centro de Formación Bíblica Católica. 
Tu tarea es responder preguntas basándote ÚNICAMENTE en el contexto proporcionado.

Contexto:
{context}

Pregunta: {question}

Instrucciones:
- Responde de manera clara y concisa
- Usa solo información del contexto
- Si el contexto no contiene la respuesta, di "No tengo información sobre ese tema"
- Responde en español
- Máximo 2-3 párrafos

Respuesta:"""

def build_prompt(question: str, documents: list[dict]) -> str:
    context = "\n\n".join([
        f"Documento {i+1}:\n{doc['text']}"
        for i, doc in enumerate(documents)
    ])
    return PROMPT_TEMPLATE.format(context=context, question=question)
```

### Content Extraction Strategies

#### From Curso Model
```python
def extract_curso_text(curso: Curso) -> str:
    parts = [
        f"Curso: {curso.name}",
        f"Área: {curso.get_area_display()}",
        f"Tipo: {curso.get_tipo_display()}",
    ]
    
    if curso.description:
        parts.append(f"Descripción: {curso.description}")
    
    if curso.teacher:
        parts.append(f"Profesor: {curso.teacher.get_full_name()}")
    
    if curso.start_date:
        parts.append(f"Fecha de inicio: {curso.start_date}")
    
    if curso.enrollment_deadline:
        parts.append(f"Fecha límite de inscripción: {curso.enrollment_deadline}")
    
    parts.append(f"Estado: {curso.get_dynamic_status_display()}")
    
    return " | ".join(parts)
```

#### From Noticia Model
```python
def extract_noticia_text(noticia: Noticia) -> str:
    parts = [
        f"Noticia: {noticia.titulo}",
        f"Categoría: {noticia.categoria.nombre}",
    ]
    
    if noticia.resumen:
        parts.append(f"Resumen: {noticia.resumen}")
    
    if noticia.contenido:
        # Limit content to first 500 chars to avoid huge embeddings
        content = noticia.contenido[:500]
        parts.append(f"Contenido: {content}")
    
    parts.append(f"Fecha: {noticia.fecha_publicacion.strftime('%Y-%m-%d')}")
    
    return " | ".join(parts)
```

#### From FAQ Model
```python
def extract_faq_text(faq: FAQ) -> str:
    # Main question
    texts = [f"Pregunta: {faq.pregunta}"]
    
    # Add variations
    for variation in faq.variaciones.all():
        texts.append(f"Variación: {variation.texto_variacion}")
    
    # Add answer
    texts.append(f"Respuesta: {faq.respuesta}")
    
    return " | ".join(texts)
```

### Session Management

**Storage**: Django sessions (database-backed)
**Session Data Structure**:
```python
{
    'chatbot_history': [
        {
            'question': str,
            'response': str,
            'timestamp': datetime,
            'interaction_id': int
        }
    ],
    'session_start': datetime,
    'message_count': int
}
```

**Session Timeout**: 30 minutes of inactivity

### Performance Optimizations

1. **Model Caching**: Load models once at server startup, keep in memory
2. **Index Caching**: Keep FAISS index in memory, only reload on updates
3. **Batch Indexing**: When rebuilding index, process documents in batches of 100
4. **Async Processing**: Use Celery for background tasks (index rebuilding, metrics calculation)
5. **Query Caching**: Cache frequent queries for 5 minutes using Django cache
6. **Connection Pooling**: Use database connection pooling for high concurrency

### Deployment Considerations

**Hardware Requirements**:
- **CPU**: 4+ cores recommended
- **RAM**: 4GB minimum (2GB for models, 2GB for Django + FAISS)
- **Storage**: 2GB for models + index
- **GPU**: Optional, would speed up inference 5-10x

**Environment Variables**:
```bash
CHATBOT_MODEL_PATH=/path/to/models
CHATBOT_INDEX_PATH=/path/to/faiss_index
CHATBOT_MAX_TOKENS=300
CHATBOT_SEARCH_TOP_K=3
CHATBOT_INTENT_THRESHOLD=0.6
CHATBOT_ENABLE_LLM=true
```

**Scaling Strategy**:
- Start with single server deployment
- If traffic grows, separate chatbot service from main Django app
- Use load balancer for multiple chatbot instances
- Share FAISS index via network file system or Redis
- Consider GPU instances for LLM if response time becomes issue

### Monitoring and Metrics

**Key Metrics to Track**:
- Average response time
- 95th percentile response time
- Questions per minute
- Cache hit rate
- FAQ usage distribution
- Intent classification accuracy (via manual review)
- User feedback rate (useful vs not useful)
- Error rate by type

**Logging Strategy**:
- Log all errors with full context
- Log slow queries (>3 seconds)
- Log all user feedback
- Log intent classification results
- Anonymize user data in logs

**Alerting**:
- Alert if error rate > 5%
- Alert if average response time > 4 seconds
- Alert if model fails to load
- Alert if index becomes corrupted

