"""
LLM Generator Service using local transformers model
"""
import logging
from typing import List, Optional
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

from ..config import LLM_MODEL, LLM_ENABLED, MAX_TOKENS

logger = logging.getLogger(__name__)


class LLMGeneratorService:
    """
    Service for generating responses using a local LLM
    """
    
    _instance = None
    _model = None
    _tokenizer = None
    _model_loaded = False
    
    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the LLM generator service"""
        if not self._model_loaded and LLM_ENABLED:
            self._load_model()
    
    def _load_model(self):
        """Load the LLM model and tokenizer with optimizations"""
        try:
            logger.info(f"Loading LLM model: {LLM_MODEL}")
            logger.info("⏳ Esta operación puede tomar varios minutos la primera vez...")
            
            # Optimized loading with progress and caching
            import time
            start_time = time.time()
            
            # Load tokenizer first (smaller, faster)
            logger.info("📥 Descargando tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                LLM_MODEL,
                cache_dir=None,  # Use default cache
                local_files_only=False,
                resume_download=True  # Resume if interrupted
            )
            tokenizer_time = time.time() - start_time
            logger.info(f"✅ Tokenizer cargado en {tokenizer_time:.1f}s")
            
            # Load model with optimizations
            logger.info("📥 Descargando modelo principal (~308 MB)...")
            model_start = time.time()
            
            self._model = AutoModelForSeq2SeqLM.from_pretrained(
                LLM_MODEL,
                torch_dtype=torch.float32,  # Use float32 for CPU compatibility
                device_map="auto" if torch.cuda.is_available() else None,
                cache_dir=None,  # Use default cache
                local_files_only=False,
                resume_download=True,  # Resume if interrupted
                low_cpu_mem_usage=True,  # Reduce memory usage during loading
                use_safetensors=True  # Use safer tensor format if available
            )
            
            model_time = time.time() - model_start
            logger.info(f"✅ Modelo cargado en {model_time:.1f}s")
            
            # Set to evaluation mode
            self._model.eval()
            
            # Move to CPU if needed (for consistency)
            if not torch.cuda.is_available():
                self._model = self._model.to('cpu')
            
            self._model_loaded = True
            total_time = time.time() - start_time
            logger.info(f"🎉 LLM completamente cargado en {total_time:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Error loading LLM model: {e}")
            logger.info("💡 Sugerencias:")
            logger.info("   1. Verificar conexión a internet")
            logger.info("   2. Verificar espacio en disco")
            logger.info("   3. Reintentar la descarga")
            self._model_loaded = False
            raise
    
    def is_available(self) -> bool:
        """
        Check if the LLM is available for use
        
        Returns:
            True if model is loaded and enabled
        """
        return LLM_ENABLED and self._model_loaded and self._model is not None
    
    @property
    def model(self):
        """Get the LLM model"""
        if not self._model_loaded and LLM_ENABLED:
            self._load_model()
        return self._model
    
    @property
    def tokenizer(self):
        """Get the tokenizer"""
        if not self._model_loaded and LLM_ENABLED:
            self._load_model()
        return self._tokenizer
    
    def build_prompt(self, pregunta: str, contexto: List[str]) -> str:
        """
        Build a prompt for the LLM combining context and question
        
        Args:
            pregunta: User's question
            contexto: List of context documents
            
        Returns:
            Formatted prompt for the LLM
        """
        # Template for the prompt
        prompt_template = """Eres un asistente virtual del Centro Fray Bartolomé de las Casas (CFBC). 
Tu tarea es responder preguntas basándote ÚNICAMENTE en el contexto proporcionado.

Contexto:
{context}

Pregunta: {question}

Instrucciones:
- Responde de manera clara y concisa en español
- Usa solo información del contexto proporcionado
- Si el contexto no contiene la respuesta, di "No tengo información específica sobre ese tema en este momento"
- Sé útil y amigable
- Máximo 2-3 párrafos
- Si hay fechas o información específica, inclúyela

Respuesta:"""
        
        # Format context documents
        if contexto:
            context_text = "\n\n".join([
                f"Documento {i+1}:\n{doc}"
                for i, doc in enumerate(contexto)
            ])
        else:
            context_text = "No se encontró información relevante en la base de conocimiento."
        
        # Build final prompt
        prompt = prompt_template.format(
            context=context_text,
            question=pregunta
        )
        
        return prompt
    
    def _truncate_prompt_if_needed(self, prompt: str, max_input_tokens: int = 512) -> str:
        """
        Truncate prompt if it exceeds token limit
        
        Args:
            prompt: Input prompt
            max_input_tokens: Maximum tokens for input
            
        Returns:
            Truncated prompt if necessary
        """
        if not self.tokenizer:
            return prompt
        
        # Tokenize to check length
        tokens = self.tokenizer.encode(prompt, add_special_tokens=True)
        
        if len(tokens) <= max_input_tokens:
            return prompt
        
        # If too long, truncate the context part
        logger.warning(f"Prompt too long ({len(tokens)} tokens), truncating...")
        
        # Find the context section and truncate it
        lines = prompt.split('\n')
        context_start = -1
        question_start = -1
        
        for i, line in enumerate(lines):
            if line.startswith('Contexto:'):
                context_start = i
            elif line.startswith('Pregunta:'):
                question_start = i
                break
        
        if context_start != -1 and question_start != -1:
            # Keep everything except truncate context
            before_context = '\n'.join(lines[:context_start+1])
            after_context = '\n'.join(lines[question_start:])
            
            # Calculate available tokens for context
            other_tokens = len(self.tokenizer.encode(before_context + after_context))
            available_tokens = max_input_tokens - other_tokens - 50  # Safety margin
            
            # Truncate context to fit
            context_lines = lines[context_start+1:question_start]
            context_text = '\n'.join(context_lines)
            
            # Truncate context text
            context_tokens = self.tokenizer.encode(context_text)
            if len(context_tokens) > available_tokens:
                truncated_tokens = context_tokens[:available_tokens]
                context_text = self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
                context_text += "\n[... contexto truncado ...]"
            
            # Rebuild prompt
            prompt = before_context + '\n' + context_text + '\n' + after_context
        
        return prompt
    
    def generate_response(
        self, 
        pregunta: str, 
        contexto: List[str], 
        max_tokens: int = MAX_TOKENS
    ) -> str:
        """
        Generate a response based on question and context
        
        Args:
            pregunta: User's question
            contexto: List of context documents
            max_tokens: Maximum tokens for response
            
        Returns:
            Generated response text
        """
        if not self.is_available():
            logger.warning("LLM not available, returning fallback response")
            return self._generate_fallback_response(contexto)
        
        try:
            # Build prompt
            prompt = self.build_prompt(pregunta, contexto)
            
            # Truncate if needed
            prompt = self._truncate_prompt_if_needed(prompt)
            
            # Tokenize input
            inputs = self.tokenizer.encode(
                prompt, 
                return_tensors="pt", 
                add_special_tokens=True,
                truncation=True,
                max_length=512
            )
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_tokens,
                    min_length=10,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=3,
                    early_stopping=True
                )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0], 
                skip_special_tokens=True
            )
            
            # Clean up response
            cleaned_response = self._clean_response(response)
            
            # If cleaning returned None (problematic response), use fallback
            if cleaned_response is None:
                logger.warning("LLM generated problematic response, using fallback")
                return self._generate_fallback_response(contexto)
            
            response = cleaned_response
            
            # Verify token count
            response_tokens = len(self.tokenizer.encode(response))
            if response_tokens > max_tokens:
                logger.warning(f"Response exceeds token limit: {response_tokens} > {max_tokens}")
                # Truncate response
                tokens = self.tokenizer.encode(response)[:max_tokens-10]
                response = self.tokenizer.decode(tokens, skip_special_tokens=True)
                response += "..."
            
            logger.info(f"Generated response ({response_tokens} tokens)")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(contexto)
    
    def _clean_response(self, response: str) -> str:
        """
        Clean and format the generated response
        
        Args:
            response: Raw response from model
            
        Returns:
            Cleaned response
        """
        # Remove extra whitespace
        response = ' '.join(response.split())
        
        # Check if response contains prompt instructions (problematic response)
        problematic_phrases = [
            "Responde de manera clara y concisa",
            "Usa solo información del contexto",
            "Si el contexto no contiene la respuesta",
            "Sé útil y amigable",
            "Máximo 2-3 párrafos",
            "si hay fechas ou informaciones",
            "Instrucciones:",
            "Contexto:",
            "Pregunta:",
            "Eres un asistente virtual"
        ]
        
        # If response contains any problematic phrase, it's returning the prompt
        response_lower = response.lower()
        for phrase in problematic_phrases:
            if phrase.lower() in response_lower:
                logger.warning("LLM returned prompt instructions instead of response, using fallback")
                # Return None to trigger fallback
                return None
        
        # Remove common artifacts
        response = response.replace("Respuesta:", "").strip()
        response = response.replace("Respuesta :", "").strip()
        
        # Remove any remaining prompt fragments
        if response.startswith("Eres un asistente"):
            return None
        
        # Ensure it starts with capital letter
        if response and response[0].islower():
            response = response[0].upper() + response[1:]
        
        # Ensure it ends with punctuation
        if response and response[-1] not in '.!?':
            response += '.'
        
        return response
    
    def _generate_fallback_response(self, contexto: List[str]) -> str:
        """
        Generate a fallback response when LLM is not available
        
        Args:
            contexto: List of context documents
            
        Returns:
            Fallback response based on context
        """
        if not contexto:
            return ("Lo siento, no encontré información específica sobre tu pregunta. "
                   "Te recomiendo contactar directamente al Centro Fray Bartolomé de las Casas "
                   "para obtener información más detallada.")
        
        # Return formatted context
        response = "Basándome en la información disponible:\n\n"
        
        for i, doc in enumerate(contexto[:2]):  # Limit to 2 documents
            # Clean and truncate document
            doc_clean = doc.replace('|', ' - ').strip()
            if len(doc_clean) > 200:
                doc_clean = doc_clean[:200] + "..."
            
            response += f"• {doc_clean}\n\n"
        
        response += ("Para información más específica, te recomiendo contactar "
                    "al Centro Fray Bartolomé de las Casas.")
        
        return response
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        if not self.tokenizer:
            # Rough estimate: ~4 characters per token
            return len(text) // 4
        
        return len(self.tokenizer.encode(text, add_special_tokens=True))
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': LLM_MODEL,
            'enabled': LLM_ENABLED,
            'loaded': self._model_loaded,
            'available': self.is_available(),
            'max_tokens': MAX_TOKENS,
            'device': str(self.model.device) if self.model else None
        }