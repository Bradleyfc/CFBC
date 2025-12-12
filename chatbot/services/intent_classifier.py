"""
Intent Classification Service
Classifies user questions into predefined categories using keyword matching
"""
import logging
import re
from typing import List, Tuple, Dict

from ..config import INTENT_THRESHOLD

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Service for classifying user intent based on keywords
    """
    
    # Intent categories with their associated keywords
    INTENT_KEYWORDS = {
        'cursos': [
            'curso', 'cursos', 'clase', 'clases', 'materia', 'materias', 
            'asignatura', 'asignaturas', 'programa', 'programas', 'estudiar',
            'carrera', 'carreras', 'diplomado', 'diplomados', 'grado', 'grados',
            'taller', 'talleres', 'capacitación', 'capacitaciones', 'formación',
            'enseñanza', 'aprender', 'educación', 'académico', 'académica'
        ],
        'inscripciones': [
            'inscribir', 'inscribirme', 'inscripción', 'inscripciones', 
            'matricular', 'matricularme', 'matrícula', 'matrículas',
            'registrar', 'registrarme', 'registro', 'registros',
            'aplicar', 'aplicación', 'solicitar', 'solicitud',
            'admisión', 'admisiones', 'ingreso', 'ingresos'
        ],
        'pagos': [
            'pagar', 'pago', 'pagos', 'costo', 'costos', 'precio', 'precios',
            'tarifa', 'tarifas', 'pensión', 'pensiones', 'arancel', 'aranceles',
            'cuota', 'cuotas', 'mensualidad', 'mensualidades', 'dinero',
            'efectivo', 'tarjeta', 'transferencia', 'banco', 'bancario',
            'financiamiento', 'beca', 'becas', 'descuento', 'descuentos'
        ],
        'ubicaciones': [
            'dónde', 'donde', 'ubicación', 'ubicaciones', 'dirección', 'direcciones',
            'lugar', 'lugares', 'edificio', 'edificios', 'aula', 'aulas',
            'salón', 'salones', 'campus', 'sede', 'sedes', 'local', 'locales',
            'oficina', 'oficinas', 'secretaría', 'secretaria', 'administración',
            'biblioteca', 'cafetería', 'cacho', 'baño', 'baños', 'parqueo'
        ],
        'requisitos': [
            'requisito', 'requisitos', 'necesitar', 'necesito', 'requerir', 'requiero',
            'condición', 'condiciones', 'documento', 'documentos', 'papel', 'papeles',
            'certificado', 'certificados', 'título', 'títulos', 'diploma', 'diplomas',
            'bachillerato', 'universidad', 'universitario', 'secundaria',
            'experiencia', 'conocimiento', 'conocimientos', 'habilidad', 'habilidades'
        ],
        'eventos': [
            'evento', 'eventos', 'actividad', 'actividades', 'ceremonia', 'ceremonias',
            'celebración', 'celebraciones', 'conferencia', 'conferencias',
            'seminario', 'seminarios', 'taller', 'talleres', 'charla', 'charlas',
            'graduación', 'graduaciones', 'acto', 'actos', 'festival', 'festivales'
        ],
        'horarios': [
            'horario', 'horarios', 'hora', 'horas', 'cuándo', 'cuando', 'tiempo',
            'fecha', 'fechas', 'día', 'días', 'calendario', 'calendarios',
            'cronograma', 'cronogramas', 'programa', 'programación',
            'mañana', 'tarde', 'noche', 'lunes', 'martes', 'miércoles',
            'jueves', 'viernes', 'sábado', 'domingo', 'semana', 'mes'
        ]
    }
    
    def __init__(self, confidence_threshold: float = INTENT_THRESHOLD):
        """
        Initialize the intent classifier
        
        Args:
            confidence_threshold: Minimum confidence to consider intent valid
        """
        self.confidence_threshold = confidence_threshold
    
    def classify(self, pregunta: str) -> Tuple[str, float]:
        """
        Classify the intent of a question
        
        Args:
            pregunta: User question text
            
        Returns:
            Tuple of (intent, confidence)
        """
        if not pregunta or not pregunta.strip():
            return 'general', 0.0
        
        # Normalize text
        pregunta_lower = self._normalize_text(pregunta)
        
        # Calculate scores for each intent
        scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = self._calculate_intent_score(pregunta_lower, keywords)
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return 'general', 0.5
        
        # Get intent with highest score
        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]
        
        # Calculate confidence (normalize based on question length and keyword density)
        question_words = len(pregunta_lower.split())
        confidence = min(max_score / max(question_words * 0.3, 1.0), 1.0)
        
        logger.debug(f"Intent classification: '{pregunta[:50]}...' -> {max_intent} ({confidence:.2f})")
        
        return max_intent, confidence
    
    def classify_multiple(self, pregunta: str) -> List[Tuple[str, float]]:
        """
        Classify multiple intents in a question
        
        Args:
            pregunta: User question text
            
        Returns:
            List of (intent, confidence) tuples sorted by confidence
        """
        if not pregunta or not pregunta.strip():
            return [('general', 0.0)]
        
        # Normalize text
        pregunta_lower = self._normalize_text(pregunta)
        
        # Calculate scores for each intent
        intent_scores = []
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = self._calculate_intent_score(pregunta_lower, keywords)
            if score > 0:
                # Calculate confidence
                question_words = len(pregunta_lower.split())
                confidence = min(score / max(question_words * 0.3, 1.0), 1.0)
                
                # Only include if above threshold
                if confidence >= self.confidence_threshold:
                    intent_scores.append((intent, confidence))
        
        if not intent_scores:
            return [('general', 0.5)]
        
        # Sort by confidence (highest first)
        intent_scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Multi-intent classification: '{pregunta[:50]}...' -> {intent_scores}")
        
        return intent_scores
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for better matching
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents and special characters
        text = self._remove_accents(text)
        
        # Remove punctuation except spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _remove_accents(self, text: str) -> str:
        """
        Remove Spanish accents from text
        
        Args:
            text: Input text with accents
            
        Returns:
            Text without accents
        """
        accent_map = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'Ñ': 'N', 'Ü': 'U'
        }
        
        for accented, unaccented in accent_map.items():
            text = text.replace(accented, unaccented)
        
        return text
    
    def _calculate_intent_score(self, text: str, keywords: List[str]) -> float:
        """
        Calculate score for an intent based on keyword matches
        
        Args:
            text: Normalized question text
            keywords: List of keywords for the intent
            
        Returns:
            Score for the intent
        """
        text_words = text.split()
        score = 0.0
        
        for keyword in keywords:
            # Exact word match
            if keyword in text_words:
                score += 1.0
            # Partial match (keyword is part of a word)
            elif any(keyword in word for word in text_words):
                score += 0.5
        
        return score
    
    def get_keywords_for_intent(self, intent: str) -> List[str]:
        """
        Get keywords associated with an intent
        
        Args:
            intent: Intent name
            
        Returns:
            List of keywords
        """
        return self.INTENT_KEYWORDS.get(intent, [])
    
    def get_all_intents(self) -> List[str]:
        """
        Get all available intent categories
        
        Returns:
            List of intent names
        """
        return list(self.INTENT_KEYWORDS.keys()) + ['general']
    
    def has_multiple_intents(self, pregunta: str) -> bool:
        """
        Check if a question has multiple intents
        
        Args:
            pregunta: User question text
            
        Returns:
            True if multiple intents detected above threshold
        """
        intents = self.classify_multiple(pregunta)
        return len(intents) > 1
    
    def get_primary_intent(self, pregunta: str) -> Tuple[str, float]:
        """
        Get the primary (highest confidence) intent
        
        Args:
            pregunta: User question text
            
        Returns:
            Tuple of (primary_intent, confidence)
        """
        intents = self.classify_multiple(pregunta)
        if intents:
            return intents[0]  # First item is highest confidence
        return 'general', 0.5
    
    def should_filter_by_intent(self, pregunta: str) -> Tuple[bool, str]:
        """
        Determine if search should be filtered by intent
        
        Args:
            pregunta: User question text
            
        Returns:
            Tuple of (should_filter, intent_to_use)
        """
        primary_intent, confidence = self.get_primary_intent(pregunta)
        
        # Only filter if confidence is above threshold and not general
        should_filter = (
            confidence >= self.confidence_threshold and 
            primary_intent != 'general'
        )
        
        return should_filter, primary_intent if should_filter else None
    
    def explain_classification(self, pregunta: str) -> Dict:
        """
        Get detailed explanation of intent classification
        
        Args:
            pregunta: User question text
            
        Returns:
            Dictionary with classification details
        """
        normalized = self._normalize_text(pregunta)
        all_intents = self.classify_multiple(pregunta)
        primary_intent, primary_confidence = self.get_primary_intent(pregunta)
        
        # Find matched keywords for primary intent
        matched_keywords = []
        if primary_intent in self.INTENT_KEYWORDS:
            keywords = self.INTENT_KEYWORDS[primary_intent]
            text_words = normalized.split()
            
            for keyword in keywords:
                if keyword in text_words:
                    matched_keywords.append(keyword)
                elif any(keyword in word for word in text_words):
                    matched_keywords.append(f"{keyword}*")  # Partial match
        
        return {
            'original_question': pregunta,
            'normalized_question': normalized,
            'primary_intent': primary_intent,
            'primary_confidence': primary_confidence,
            'all_intents': all_intents,
            'matched_keywords': matched_keywords,
            'should_filter': primary_confidence >= self.confidence_threshold,
            'threshold': self.confidence_threshold
        }