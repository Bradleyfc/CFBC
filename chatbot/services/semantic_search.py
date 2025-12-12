"""
Semantic Search Service using sentence-transformers and FAISS
"""
import numpy as np
import pickle
import logging
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss

from ..config import (
    SENTENCE_TRANSFORMER_MODEL,
    FAISS_INDEX_PATH,
    FAISS_METADATA_PATH,
    SEARCH_TOP_K,
    SIMILARITY_THRESHOLD,
    USE_MMR,
    MMR_DIVERSITY_LAMBDA
)

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Service for semantic search using sentence-transformers and FAISS
    """
    
    _instance = None
    _model = None
    _index = None
    _id_to_metadata = None
    
    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the semantic search service"""
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        import os
        
        try:
            logger.info(f"Loading sentence-transformer model: {SENTENCE_TRANSFORMER_MODEL}")
            
            # Configure for offline mode
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['HF_DATASETS_OFFLINE'] = '1'
            
            # Try loading from HuggingFace cache directory first (most likely to work)
            hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
            model_folder_name = f"models--sentence-transformers--{SENTENCE_TRANSFORMER_MODEL.replace('/', '--')}"
            model_cache_path = os.path.join(hf_cache, model_folder_name)
            
            if os.path.exists(model_cache_path):
                logger.info(f"Found model in HuggingFace cache: {model_cache_path}")
                # Find the actual model directory (usually has snapshots subdirectory)
                snapshots_dir = os.path.join(model_cache_path, "snapshots")
                if os.path.exists(snapshots_dir):
                    # Get the first (and usually only) snapshot
                    snapshot_dirs = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
                    if snapshot_dirs:
                        actual_model_path = os.path.join(snapshots_dir, snapshot_dirs[0])
                        logger.info(f"Loading from snapshot: {actual_model_path}")
                        self._model = SentenceTransformer(actual_model_path)
                        logger.info("Model loaded successfully from HuggingFace cache")
                        return
                
                # If no snapshots, try direct path
                try:
                    self._model = SentenceTransformer(model_cache_path)
                    logger.info("Model loaded successfully from HuggingFace cache (direct)")
                    return
                except Exception as direct_error:
                    logger.warning(f"Direct cache loading failed: {direct_error}")
            
            # Try to load model with local_files_only to prevent internet access
            try:
                logger.info("Attempting offline model loading with local_files_only...")
                self._model = SentenceTransformer(
                    SENTENCE_TRANSFORMER_MODEL,
                    local_files_only=True,
                    use_auth_token=False
                )
                logger.info("Model loaded successfully in offline mode")
                return
            except Exception as offline_error:
                logger.warning(f"Offline model loading failed: {offline_error}")
            
            # Check torch sentence_transformers cache
            torch_cache_dir = os.path.expanduser("~/.cache/torch/sentence_transformers")
            torch_model_path = os.path.join(torch_cache_dir, SENTENCE_TRANSFORMER_MODEL.replace('/', '_'))
            
            if os.path.exists(torch_model_path):
                logger.info(f"Loading model from torch cache: {torch_model_path}")
                self._model = SentenceTransformer(torch_model_path)
                logger.info("Model loaded successfully from torch cache")
                return
            
            # Try loading from venv site-packages
            try:
                import site
                
                # Look for model in site-packages
                for site_dir in site.getsitepackages():
                    model_path = os.path.join(site_dir, "sentence_transformers", "models", SENTENCE_TRANSFORMER_MODEL.replace('/', '_'))
                    if os.path.exists(model_path):
                        logger.info(f"Loading model from site-packages: {model_path}")
                        self._model = SentenceTransformer(model_path)
                        logger.info("Model loaded successfully from site-packages")
                        return
                        
            except Exception as site_error:
                logger.warning(f"Site-packages loading failed: {site_error}")
            
            # If all offline methods fail, try with internet as last resort
            logger.info("All offline methods failed, attempting to load model with internet access...")
            # Temporarily remove offline environment variables
            os.environ.pop('TRANSFORMERS_OFFLINE', None)
            os.environ.pop('HF_HUB_OFFLINE', None)
            os.environ.pop('HF_DATASETS_OFFLINE', None)
            
            self._model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            logger.info("Model loaded successfully with internet access")
                
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer model: {e}")
            raise RuntimeError(f"Could not load model {SENTENCE_TRANSFORMER_MODEL}. "
                             f"Please ensure the model is downloaded locally or internet connection is available. "
                             f"Error: {e}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a text
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            numpy array with the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            # Generate embedding
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            # Normalize for cosine similarity (FAISS IndexFlatIP expects normalized vectors)
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        return self._model.get_sentence_embedding_dimension()
    
    @property
    def model(self):
        """Get the sentence transformer model"""
        if self._model is None:
            self._load_model()
        return self._model

    
    def initialize_index(self, dimension: Optional[int] = None):
        """
        Initialize or create a new FAISS index
        
        Args:
            dimension: Dimension of the embedding vectors (uses model dimension if not provided)
        """
        if dimension is None:
            dimension = self.get_embedding_dimension()
        
        logger.info(f"Initializing FAISS index with dimension {dimension}")
        
        # Create IndexFlatIP for inner product (cosine similarity with normalized vectors)
        self._index = faiss.IndexFlatIP(dimension)
        self._id_to_metadata = {}
        
        logger.info("FAISS index initialized")
    
    def save_index(self):
        """Save the FAISS index and metadata to disk"""
        if self._index is None:
            logger.warning("No index to save")
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self._index, FAISS_INDEX_PATH)
            logger.info(f"FAISS index saved to {FAISS_INDEX_PATH}")
            
            # Save metadata
            with open(FAISS_METADATA_PATH, 'wb') as f:
                pickle.dump(self._id_to_metadata, f)
            logger.info(f"Metadata saved to {FAISS_METADATA_PATH}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def load_index(self) -> bool:
        """
        Load the FAISS index and metadata from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            import os
            
            if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(FAISS_METADATA_PATH):
                logger.warning("Index files not found")
                return False
            
            # Load FAISS index
            self._index = faiss.read_index(FAISS_INDEX_PATH)
            logger.info(f"FAISS index loaded from {FAISS_INDEX_PATH}")
            
            # Load metadata
            with open(FAISS_METADATA_PATH, 'rb') as f:
                self._id_to_metadata = pickle.load(f)
            logger.info(f"Metadata loaded from {FAISS_METADATA_PATH}")
            
            logger.info(f"Index contains {self._index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def index_document(self, doc_id: int, text: str, metadata: dict):
        """
        Index a single document
        
        Args:
            doc_id: Unique ID for the document in the index
            text: Text to index
            metadata: Metadata to store (type, object_id, categoria, etc.)
        """
        if self._index is None:
            self.initialize_index()
        
        try:
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Add to FAISS index
            embedding_2d = embedding.reshape(1, -1).astype('float32')
            self._index.add(embedding_2d)
            
            # Store metadata
            current_id = self._index.ntotal - 1
            self._id_to_metadata[current_id] = {
                'doc_id': doc_id,
                'text': text[:500],  # Store first 500 chars for reference
                **metadata
            }
            
            logger.debug(f"Indexed document {doc_id} at position {current_id}")
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
            raise
    
    def rebuild_index(self):
        """
        Rebuild the entire index from DocumentEmbedding model
        This will be implemented in the content indexer service
        """
        from ..models import DocumentEmbedding
        
        logger.info("Rebuilding FAISS index from database")
        
        # Initialize new index
        self.initialize_index()
        
        # Get all embeddings from database
        embeddings = DocumentEmbedding.objects.all()
        
        if not embeddings.exists():
            logger.warning("No embeddings found in database")
            return
        
        # Add all embeddings to index
        for idx, emb in enumerate(embeddings):
            try:
                # Deserialize embedding vector
                embedding_vector = pickle.loads(emb.embedding_vector)
                
                # Add to FAISS index
                embedding_2d = embedding_vector.reshape(1, -1).astype('float32')
                self._index.add(embedding_2d)
                
                # Store metadata
                self._id_to_metadata[idx] = {
                    'doc_id': emb.id,
                    'content_type': str(emb.content_type),
                    'object_id': emb.object_id,
                    'categoria': emb.categoria,
                    'text': emb.texto_indexado[:500]
                }
            except Exception as e:
                logger.error(f"Error adding embedding {emb.id} to index: {e}")
                continue
        
        # Save index to disk
        self.save_index()
        
        logger.info(f"Index rebuilt with {self._index.ntotal} vectors")
    
    def get_index_stats(self) -> dict:
        """Get statistics about the current index"""
        if self._index is None:
            return {'total_vectors': 0, 'dimension': 0}
        
        return {
            'total_vectors': self._index.ntotal,
            'dimension': self._index.d,
            'metadata_count': len(self._id_to_metadata)
        }

    
    def search(
        self, 
        query: str, 
        top_k: int = SEARCH_TOP_K, 
        categoria: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar documents with priority-based ordering
        
        Args:
            query: Query text
            top_k: Number of results to return
            categoria: Optional category filter
            
        Returns:
            List of documents with scores and metadata, ordered by priority
        """
        # Load index if not loaded
        if self._index is None:
            if not self.load_index():
                logger.warning("Index is empty or not loaded")
                return []
        
        if self._index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            query_embedding_2d = query_embedding.reshape(1, -1).astype('float32')
            
            # Search in FAISS index
            # We search for more results if filtering by category (increased factor)
            search_k = top_k * 10 if categoria else top_k
            scores, indices = self._index.search(query_embedding_2d, min(search_k, self._index.ntotal))
            
            # Process results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for empty slots
                    continue
                
                metadata = self._id_to_metadata.get(int(idx))
                if metadata is None:
                    continue
                
                # Filter by category if specified
                if categoria and metadata.get('categoria') != categoria:
                    continue
                
                # Get additional metadata for priority ordering
                result = {
                    'doc_id': metadata['doc_id'],
                    'score': float(score),
                    'text': metadata.get('text', ''),
                    'categoria': metadata.get('categoria', ''),
                    'content_type': metadata.get('content_type', ''),
                    'object_id': metadata.get('object_id', 0),
                    'destacada': False,
                    'prioridad': 0
                }
                
                # Get FAQ-specific metadata for priority ordering
                if metadata.get('content_type') == 'chatbot.faq':
                    faq_data = self._get_faq_priority_data(metadata.get('object_id'))
                    if faq_data:
                        result.update(faq_data)
                
                results.append(result)
                
                # Stop if we have enough results (before ordering)
                if len(results) >= top_k * 2:  # Get more for better ordering
                    break
            
            # Apply priority-based ordering
            ordered_results = self._apply_priority_ordering(results)
            
            # Apply deduplication with MMR if enabled
            deduplicated_results = self._deduplicate_results(ordered_results, query_embedding)
            
            # Return top_k results
            final_results = deduplicated_results[:top_k]
            
            logger.info(f"Search returned {len(final_results)} results for query: {query[:50]}... (deduplicated: {len(results)} -> {len(final_results)})")
            return final_results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def _get_faq_priority_data(self, faq_id: int) -> Optional[Dict]:
        """
        Get priority data for a FAQ
        
        Args:
            faq_id: FAQ object ID
            
        Returns:
            Dictionary with priority data or None
        """
        try:
            from ..models import FAQ
            
            faq = FAQ.objects.get(id=faq_id, activa=True)
            return {
                'destacada': faq.destacada,
                'prioridad': faq.prioridad,
                'veces_usada': faq.veces_usada,
                'tasa_exito': faq.tasa_exito
            }
        except Exception:
            return None
    
    def _apply_priority_ordering(self, results: List[Dict]) -> List[Dict]:
        """
        Apply priority-based ordering to search results
        
        Order by:
        1. Destacada flag (highlighted FAQs first)
        2. Prioridad value (higher priority first)
        3. Similarity score (higher score first)
        4. Usage count (more used first)
        
        Args:
            results: List of search results
            
        Returns:
            Ordered list of results
        """
        def sort_key(result):
            return (
                -int(result.get('destacada', False)),  # Destacada first (negative for desc)
                -result.get('prioridad', 0),           # Higher priority first
                -result.get('score', 0),               # Higher similarity first
                -result.get('veces_usada', 0)          # More used first
            )
        
        return sorted(results, key=sort_key)
    
    def clear_index(self):
        """Clear the current index"""
        self._index = None
        self._id_to_metadata = {}
        logger.info("Index cleared")
    
    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Normalize vectors
            vec1_norm = vec1 / np.linalg.norm(vec1)
            vec2_norm = vec2 / np.linalg.norm(vec2)
            
            # Calculate cosine similarity
            similarity = np.dot(vec1_norm, vec2_norm)
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, float(similarity)))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _deduplicate_results(self, results: List[Dict], query_embedding: np.ndarray) -> List[Dict]:
        """
        Remove duplicate or very similar results
        
        Args:
            results: List of search results
            query_embedding: Original query embedding for MMR calculation
            
        Returns:
            Deduplicated list of results
        """
        if len(results) <= 1:
            return results
        
        if USE_MMR:
            return self._max_marginal_relevance_search(results, query_embedding)
        else:
            return self._simple_deduplication(results)
    
    def _simple_deduplication(self, results: List[Dict]) -> List[Dict]:
        """
        Simple deduplication based on text similarity
        
        Args:
            results: List of search results
            
        Returns:
            Deduplicated results
        """
        deduplicated = []
        
        for result in results:
            is_duplicate = False
            result_text = result.get('text', '').lower().strip()
            
            if not result_text:
                continue
            
            # Check against already selected results
            for selected in deduplicated:
                selected_text = selected.get('text', '').lower().strip()
                
                # Simple text similarity check
                if self._text_similarity(result_text, selected_text) > SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    # Keep the one with higher score
                    if result.get('score', 0) > selected.get('score', 0):
                        deduplicated.remove(selected)
                        deduplicated.append(result)
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
        
        logger.debug(f"Deduplication: {len(results)} -> {len(deduplicated)} results")
        return deduplicated
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using simple metrics
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _max_marginal_relevance_search(self, results: List[Dict], query_embedding: np.ndarray) -> List[Dict]:
        """
        Apply Maximum Marginal Relevance to balance relevance and diversity
        
        Args:
            results: List of search results with embeddings
            query_embedding: Original query embedding
            
        Returns:
            Reordered results with better diversity
        """
        if len(results) <= 1:
            return results
        
        # Generate embeddings for all result texts
        result_embeddings = []
        valid_results = []
        
        for result in results:
            text = result.get('text', '').strip()
            if text:
                try:
                    embedding = self.generate_embedding(text)
                    result_embeddings.append(embedding)
                    valid_results.append(result)
                except Exception as e:
                    logger.warning(f"Could not generate embedding for result: {e}")
                    continue
        
        if len(valid_results) <= 1:
            return valid_results
        
        # MMR algorithm
        selected_indices = []
        remaining_indices = list(range(len(valid_results)))
        
        # Select first result (highest relevance)
        if remaining_indices:
            best_idx = 0  # Already sorted by relevance
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        # Select remaining results using MMR
        while remaining_indices and len(selected_indices) < len(valid_results):
            best_score = -1
            best_idx = None
            
            for idx in remaining_indices:
                # Relevance score (similarity to query)
                relevance = self._calculate_cosine_similarity(
                    query_embedding, 
                    result_embeddings[idx]
                )
                
                # Diversity score (minimum similarity to selected results)
                if selected_indices:
                    max_similarity = max(
                        self._calculate_cosine_similarity(
                            result_embeddings[idx],
                            result_embeddings[selected_idx]
                        )
                        for selected_idx in selected_indices
                    )
                    diversity = 1 - max_similarity
                else:
                    diversity = 1.0
                
                # MMR score: balance between relevance and diversity
                mmr_score = (MMR_DIVERSITY_LAMBDA * relevance + 
                           (1 - MMR_DIVERSITY_LAMBDA) * diversity)
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx
            
            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)
        
        # Return results in MMR order
        mmr_results = [valid_results[idx] for idx in selected_indices]
        
        logger.debug(f"MMR reordering: {len(results)} -> {len(mmr_results)} results")
        return mmr_results
