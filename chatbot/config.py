"""
Chatbot configuration settings
"""
import os
from pathlib import Path

# Base directory for chatbot data
BASE_DIR = Path(__file__).resolve().parent.parent
CHATBOT_DATA_DIR = os.getenv('CHATBOT_DATA_DIR', str(BASE_DIR / 'chatbot_data'))

# Model paths
CHATBOT_MODEL_PATH = os.getenv('CHATBOT_MODEL_PATH', str(BASE_DIR / 'chatbot_data' / 'models'))

# Sentence transformer model
SENTENCE_TRANSFORMER_MODEL = os.getenv(
    'SENTENCE_TRANSFORMER_MODEL',
    'paraphrase-multilingual-MiniLM-L12-v2'
)

# LLM model - DESACTIVADO
LLM_MODEL = os.getenv('LLM_MODEL', 'google/flan-t5-small')
LLM_ENABLED = False  # Desactivado - solo búsquedas semánticas

# Hybrid system settings - DESACTIVADO
HYBRID_MODE_ENABLED = False  # Desactivado - solo respuestas estructuradas
COMPLEX_QUESTION_THRESHOLD = float(os.getenv('CHATBOT_COMPLEX_THRESHOLD', '0.5'))  # Umbral más bajo para usar LLM más frecuentemente
SIMPLE_RESPONSE_MAX_TIME = float(os.getenv('CHATBOT_SIMPLE_MAX_TIME', '3.0'))  # Tiempo máximo para respuestas simples
LLM_MAX_TIME = float(os.getenv('CHATBOT_LLM_MAX_TIME', '8.0'))  # Tiempo máximo para LLM antes de fallback

# FAISS index path
FAISS_INDEX_PATH = os.getenv(
    'CHATBOT_INDEX_PATH',
    str(BASE_DIR / 'chatbot_data' / 'faiss_index.bin')
)
FAISS_METADATA_PATH = os.getenv(
    'CHATBOT_METADATA_PATH',
    str(BASE_DIR / 'chatbot_data' / 'id_to_metadata.json')
)

# Search parameters
SEARCH_TOP_K = int(os.getenv('CHATBOT_SEARCH_TOP_K', '3'))
MAX_TOKENS = int(os.getenv('CHATBOT_MAX_TOKENS', '300'))

# Chunking parameters for better semantic search
CHUNK_SIZE = int(os.getenv('CHATBOT_CHUNK_SIZE', '250'))  # 150-300 caracteres
CHUNK_OVERLAP = int(os.getenv('CHATBOT_CHUNK_OVERLAP', '50'))  # Solapamiento entre chunks

# Deduplication parameters
SIMILARITY_THRESHOLD = float(os.getenv('CHATBOT_SIMILARITY_THRESHOLD', '0.85'))  # Umbral para considerar duplicados
USE_MMR = os.getenv('CHATBOT_USE_MMR', 'true').lower() == 'true'  # Usar Max Marginal Relevance
MMR_DIVERSITY_LAMBDA = float(os.getenv('CHATBOT_MMR_LAMBDA', '0.7'))  # Balance relevancia vs diversidad

# Intent classification
INTENT_THRESHOLD = float(os.getenv('CHATBOT_INTENT_THRESHOLD', '0.6'))

# Session settings
SESSION_TIMEOUT_MINUTES = int(os.getenv('CHATBOT_SESSION_TIMEOUT', '30'))

# Performance settings
RESPONSE_TIMEOUT_SECONDS = 5.0

# Create directories if they don't exist
os.makedirs(CHATBOT_DATA_DIR, exist_ok=True)
os.makedirs(CHATBOT_MODEL_PATH, exist_ok=True)
