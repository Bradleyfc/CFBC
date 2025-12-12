"""
Text Chunking Service for better semantic search
Splits text into smaller, more precise chunks for better search results
"""
import re
import logging
from typing import List, Dict, Tuple
from ..config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Service for splitting text into optimal chunks for semantic search
    """
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize the text chunker
        
        Args:
            chunk_size: Target size for each chunk (characters)
            chunk_overlap: Overlap between consecutive chunks (characters)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into optimized chunks
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text or not text.strip():
            return []
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Try sentence-based chunking first
        chunks = self._sentence_based_chunking(cleaned_text)
        
        # If chunks are too large, use character-based chunking
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
            else:
                # Split large chunks further
                sub_chunks = self._character_based_chunking(chunk)
                final_chunks.extend(sub_chunks)
        
        # Create chunk dictionaries with metadata
        chunk_dicts = []
        for i, chunk_text in enumerate(final_chunks):
            if chunk_text.strip():  # Only include non-empty chunks
                chunk_dict = {
                    'text': chunk_text.strip(),
                    'chunk_index': i,
                    'chunk_size': len(chunk_text),
                    **(metadata or {})
                }
                chunk_dicts.append(chunk_dict)
        
        logger.debug(f"Text chunked into {len(chunk_dicts)} chunks (avg size: {sum(len(c['text']) for c in chunk_dicts) / len(chunk_dicts):.0f} chars)")
        return chunk_dicts
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for better chunking
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with chunking
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'áéíóúñüÁÉÍÓÚÑÜ]', ' ', text)
        
        # Clean up multiple spaces again
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _sentence_based_chunking(self, text: str) -> List[str]:
        """
        Split text into chunks based on sentences
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        # Split by sentence endings
        sentences = re.split(r'[.!?]+\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed chunk size
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Start new chunk with current sentence
                if len(sentence) <= self.chunk_size:
                    current_chunk = sentence
                else:
                    # Sentence is too long, will be handled by character-based chunking
                    chunks.append(sentence)
                    current_chunk = ""
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _character_based_chunking(self, text: str) -> List[str]:
        """
        Split text into chunks based on character count with smart boundaries
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunks.append(text[start:])
                break
            
            # Try to find a good breaking point (space, punctuation)
            break_point = self._find_break_point(text, start, end)
            
            if break_point > start:
                chunks.append(text[start:break_point])
                start = break_point - self.chunk_overlap
            else:
                # No good break point found, use hard cut
                chunks.append(text[start:end])
                start = end - self.chunk_overlap
            
            # Ensure we don't go backwards
            start = max(start, 0)
        
        return chunks
    
    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """
        Find a good breaking point for text chunking
        
        Args:
            text: Full text
            start: Start position
            end: Desired end position
            
        Returns:
            Best breaking point position
        """
        # Look for sentence endings first
        for i in range(end - 1, start, -1):
            if text[i] in '.!?':
                return i + 1
        
        # Look for clause endings
        for i in range(end - 1, start, -1):
            if text[i] in ',;:':
                return i + 1
        
        # Look for word boundaries
        for i in range(end - 1, start, -1):
            if text[i] == ' ':
                return i + 1
        
        # No good break point found
        return -1
    
    def chunk_faq(self, pregunta: str, respuesta: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk FAQ content optimally
        
        Args:
            pregunta: FAQ question
            respuesta: FAQ answer
            metadata: Additional metadata
            
        Returns:
            List of optimized chunks
        """
        chunks = []
        
        # Create question chunk
        if pregunta and pregunta.strip():
            question_chunk = {
                'text': f"Pregunta: {pregunta.strip()}",
                'chunk_type': 'question',
                'chunk_index': 0,
                **(metadata or {})
            }
            chunks.append(question_chunk)
        
        # Create answer chunks
        if respuesta and respuesta.strip():
            answer_chunks = self.chunk_text(
                f"Respuesta: {respuesta.strip()}", 
                {**(metadata or {}), 'chunk_type': 'answer'}
            )
            
            # Update chunk indices
            for i, chunk in enumerate(answer_chunks):
                chunk['chunk_index'] = len(chunks) + i
            
            chunks.extend(answer_chunks)
        
        # Create combined chunk for FAQs (always create one for better search)
        if pregunta and respuesta:
            combined_text = f"{pregunta.strip()} | Respuesta: {respuesta.strip()}"
            
            # If it's short enough, use as is
            if len(combined_text) <= self.chunk_size:
                combined_chunk = {
                    'text': combined_text,
                    'chunk_type': 'combined',
                    'chunk_index': len(chunks),
                    **(metadata or {})
                }
                chunks.append(combined_chunk)
            else:
                # For long FAQs, create a summary chunk with question + first part of answer
                answer_preview = respuesta.strip()[:150] + "..." if len(respuesta.strip()) > 150 else respuesta.strip()
                summary_text = f"{pregunta.strip()} | Respuesta: {answer_preview}"
                
                summary_chunk = {
                    'text': summary_text,
                    'chunk_type': 'summary',
                    'chunk_index': len(chunks),
                    **(metadata or {})
                }
                chunks.append(summary_chunk)
        
        return chunks
    
    def chunk_course_content(self, course_data: Dict, metadata: Dict = None) -> List[Dict]:
        """
        Chunk course content optimally with detailed information
        
        Args:
            course_data: Dictionary with course information
            metadata: Additional metadata
            
        Returns:
            List of optimized chunks
        """
        chunks = []
        
        # Extract key course information
        course_name = course_data.get('nombre', '')
        course_area = course_data.get('area', '')
        course_description = course_data.get('descripcion', '')
        course_type = course_data.get('tipo', '')
        course_status = course_data.get('estado', '')
        enrollment_deadline = course_data.get('fecha_limite', '')
        start_date = course_data.get('fecha_inicio', '')
        
        # Create comprehensive course info chunk
        if course_name:
            course_info = f"Curso: {course_name}"
            if course_area:
                course_info += f" | Área: {course_area}"
            if course_type:
                course_info += f" | Tipo: {course_type}"
            if course_status:
                course_info += f" | Estado: {course_status}"
            
            info_chunk = {
                'text': course_info,
                'chunk_type': 'course_info',
                'chunk_index': 0,
                **(metadata or {})
            }
            chunks.append(info_chunk)
        
        # Create enrollment information chunk
        if enrollment_deadline or start_date or course_status:
            enrollment_info = []
            
            if course_name:
                enrollment_info.append(f"Inscripciones para {course_name}:")
            
            if course_status:
                enrollment_info.append(f"Estado actual: {course_status}")
            
            if enrollment_deadline:
                from datetime import datetime
                try:
                    deadline_date = datetime.strptime(enrollment_deadline, '%Y-%m-%d')
                    enrollment_info.append(f"Fecha límite de inscripción: {deadline_date.strftime('%d de %B de %Y')}")
                except:
                    enrollment_info.append(f"Fecha límite de inscripción: {enrollment_deadline}")
            
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                    enrollment_info.append(f"Fecha de inicio: {start_date_obj.strftime('%d de %B de %Y')}")
                except:
                    enrollment_info.append(f"Fecha de inicio: {start_date}")
            
            # Add availability status
            if course_status:
                if 'inscripción' in course_status.lower():
                    enrollment_info.append("✅ Inscripciones abiertas")
                elif 'terminado' in course_status.lower():
                    enrollment_info.append("❌ Plazo de inscripción terminado")
                elif 'progreso' in course_status.lower():
                    enrollment_info.append("🔄 Curso en progreso")
                elif 'finalizado' in course_status.lower():
                    enrollment_info.append("✅ Curso finalizado")
            
            if enrollment_info:
                enrollment_chunk = {
                    'text': ' | '.join(enrollment_info),
                    'chunk_type': 'course_enrollment',
                    'chunk_index': len(chunks),
                    **(metadata or {})
                }
                chunks.append(enrollment_chunk)
        
        # Create area-specific chunk
        if course_area:
            area_chunk = {
                'text': f"Área: {course_area}",
                'chunk_type': 'course_area',
                'chunk_index': len(chunks),
                **(metadata or {})
            }
            chunks.append(area_chunk)
        
        # Create description chunks
        if course_description:
            desc_chunks = self.chunk_text(
                course_description,
                {**(metadata or {}), 'chunk_type': 'course_description'}
            )
            
            # Update chunk indices
            for i, chunk in enumerate(desc_chunks):
                chunk['chunk_index'] = len(chunks) + i
            
            chunks.extend(desc_chunks)
        
        # Create combined chunk for basic info
        basic_info = []
        if course_name:
            basic_info.append(f"Curso: {course_name}")
        if course_area:
            basic_info.append(f"Área: {course_area}")
        
        if basic_info:
            combined_text = " | ".join(basic_info)
            if len(combined_text) <= self.chunk_size:
                combined_chunk = {
                    'text': combined_text,
                    'chunk_type': 'course_summary',
                    'chunk_index': len(chunks),
                    **(metadata or {})
                }
                chunks.append(combined_chunk)
        
        return chunks