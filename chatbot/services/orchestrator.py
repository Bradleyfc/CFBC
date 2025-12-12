"""
Chatbot Orchestrator Service
Coordinates all chatbot components to process user questions
"""
import logging
import time
from typing import Dict, List, Optional

from django.db.models import Count, Avg, Q

from .intent_classifier import IntentClassifier
from .semantic_search import SemanticSearchService
from ..models import ChatInteraction, FAQ
from ..config import (
    SEARCH_TOP_K, 
    RESPONSE_TIMEOUT_SECONDS,
    USE_MMR,
    SIMILARITY_THRESHOLD
)

logger = logging.getLogger(__name__)


class ChatbotOrchestrator:
    """
    Main orchestrator that coordinates all chatbot components
    """
    
    def __init__(self):
        """Initialize service components - only semantic search and intent classification"""
        self.intent_classifier = IntentClassifier()
        self.semantic_search = SemanticSearchService()
        # LLM generator removed - using only semantic search
        
        # Load FAISS index if not already loaded
        if not self.semantic_search.load_index():
            logger.warning("FAISS index not found, will need to rebuild")
    
    def process_question(self, pregunta: str, session_id: str) -> Dict:
        """
        Process a user question through the complete pipeline
        
        Args:
            pregunta: User's question
            session_id: Session identifier
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Classify intent
            should_filter, intent = self.intent_classifier.should_filter_by_intent(pregunta)
            primary_intent, confidence = self.intent_classifier.get_primary_intent(pregunta)
            
            # Enhanced intent detection for registration/login questions
            pregunta_lower = pregunta.lower()
            if any(word in pregunta_lower for word in ['registr', 'crear cuenta', 'login', 'iniciar sesión', 'entrar', 'acceder', 'usuario', 'contraseña', 'olvidé']):
                primary_intent = 'inscripciones'
                confidence = 1.0
                should_filter = True
                intent = 'inscripciones'
                logger.info(f"Enhanced detection: Registration/Login question detected")
            
            # Enhanced intent detection for word/phrase location questions (must come before location detection)
            elif any(pattern in pregunta_lower for pattern in ['dónde se menciona', 'donde se menciona', 'en qué lugar se menciona', 'en que lugar se menciona', 'dónde aparece', 'donde aparece']):
                primary_intent = 'eventos'  # Use eventos to access all content
                confidence = 1.0
                should_filter = False  # Don't filter by category, we need all content
                intent = None
                logger.info(f"Enhanced detection: Word/phrase location question detected")
            
            # Enhanced intent detection for location/direction questions
            elif any(word in pregunta_lower for word in ['dirección', 'direccion', 'ubicación', 'ubicacion', 'cómo llegar', 'como llegar', 'llegar', 'centro', 'sitio', 'localización']) and not any(pattern in pregunta_lower for pattern in ['dónde se menciona', 'donde se menciona']):
                primary_intent = 'ubicaciones'
                confidence = 1.0
                should_filter = True
                intent = 'ubicaciones'
                logger.info(f"Enhanced detection: Location/Direction question detected")
            
            # Enhanced intent detection for news/blog questions
            elif any(word in pregunta_lower for word in ['noticia', 'noticias', 'últimas noticias', 'ultimas noticias', 'blog', 'eventos', 'actividades', 'novedades', 'qué hay de nuevo', 'que hay de nuevo']):
                primary_intent = 'eventos'
                confidence = 1.0
                should_filter = True
                intent = 'eventos'
                logger.info(f"Enhanced detection: News/Blog question detected")
            
            logger.info(f"Intent classification: {primary_intent} (confidence: {confidence:.2f})")
            
            # Step 2: Semantic search with category mapping
            categoria = self._map_intent_to_category(intent) if should_filter else None
            logger.info(f"Intent '{intent}' mapped to category '{categoria}'")
            documents = self.semantic_search.search(
                query=pregunta,
                top_k=SEARCH_TOP_K,
                categoria=categoria
            )
            
            logger.info(f"Found {len(documents)} relevant documents")
            
            # Step 3: Generate response using semantic search only
            if documents:
                logger.info(f"Processing {len(documents)} documents in _generate_structured_response")
                response = self._generate_structured_response(documents, pregunta)
            else:
                # No documents found - provide helpful guidance
                logger.info("No documents found, using _handle_no_results")
                response = self._handle_no_results(pregunta)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Check if response time exceeded limit
            if response_time > RESPONSE_TIMEOUT_SECONDS:
                logger.warning(f"Response time exceeded limit: {response_time:.2f}s > {RESPONSE_TIMEOUT_SECONDS}s")
            
            # Prepare result
            result = {
                'respuesta': response,
                'confianza': confidence,
                'tiempo': response_time,
                'intencion': primary_intent,
                'documentos_recuperados': documents,
                'success': True
            }
            
            # Step 4: Log interaction
            self.log_interaction(
                session_id=session_id,
                pregunta=pregunta,
                respuesta=response,
                documentos=documents,
                intencion=primary_intent,
                confianza=confidence,
                tiempo_respuesta=response_time
            )
            
            # Step 5: Track FAQ usage if applicable
            self._track_faq_usage(documents)
            
            logger.info(f"Question processed successfully in {response_time:.2f}s")
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Error processing question: {e}")
            
            # Return error response
            error_response = {
                'respuesta': "Lo siento, ocurrió un error al procesar tu pregunta. Por favor, intenta de nuevo.",
                'confianza': 0.0,
                'tiempo': response_time,
                'intencion': 'general',
                'documentos_recuperados': [],
                'success': False,
                'error': str(e)
            }
            
            # Still log the interaction for debugging
            try:
                self.log_interaction(
                    session_id=session_id,
                    pregunta=pregunta,
                    respuesta=error_response['respuesta'],
                    documentos=[],
                    intencion='general',
                    confianza=0.0,
                    tiempo_respuesta=response_time
                )
            except Exception as log_error:
                logger.error(f"Error logging failed interaction: {log_error}")
            
            return error_response
    
    def _generate_structured_response(self, documents: List[Dict], pregunta: str) -> str:
        """
        Generate a structured response from documents using indexed content
        
        Args:
            documents: List of relevant documents
            pregunta: User's question
            
        Returns:
            Structured response text based on real content
        """
        pregunta_lower = pregunta.lower() if pregunta else ""
        
        # Check if asking where a word/phrase is mentioned
        if any(pattern in pregunta_lower for pattern in ['dónde se menciona', 'donde se menciona', 'en qué lugar se menciona', 'en que lugar se menciona', 'dónde aparece', 'donde aparece']):
            return self._generate_word_location_response(documents, pregunta)
        
        # Check if it's a single word search (no question words, just a term)
        elif self._is_single_word_search(pregunta):
            return self._generate_single_word_search_response(documents, pregunta)
        
        # Check if this is a general search query (site search functionality)
        elif self._is_site_search_query(pregunta):
            return self._generate_site_search_response(documents, pregunta)
        
        # First, validate if this is a question we can answer
        if not self._can_answer_question(pregunta):
            return self._get_restricted_response()
        
        if not documents:
            return self._handle_no_results(pregunta)
        
        # Filter documents to only include Spanish content
        spanish_documents = self._filter_spanish_documents(documents)
        logger.info(f"After Spanish filtering: {len(spanish_documents)} documents remain")
        
        if not spanish_documents:
            logger.info("No Spanish documents found, using _handle_no_spanish_content")
            return self._handle_no_spanish_content(pregunta)
        
        # Categorize documents by type
        faq_docs = [doc for doc in spanish_documents if doc.get('content_type') == 'chatbot.faq']
        course_docs = [doc for doc in spanish_documents if doc.get('content_type') == 'principal.curso']
        blog_docs = [doc for doc in spanish_documents if doc.get('content_type') == 'blog.noticia']
        contact_docs = [doc for doc in spanish_documents if doc.get('categoria') == 'contacto']
        
        # Generate response based on document type priority
        if faq_docs:
            # Look for FAQ chunks that contain answers first
            answer_docs = [doc for doc in faq_docs if 'Respuesta:' in doc.get('text', '') or '|' in doc.get('text', '')]
            if answer_docs:
                faq_response = self._generate_faq_response(answer_docs[0])
                # If FAQ response is too short or incomplete after professor filtering, try course docs
                if len(faq_response.strip()) < 50 or faq_response.endswith(':') or faq_response.endswith('|'):
                    if course_docs:
                        return self._generate_course_response(course_docs, pregunta)
                return faq_response
            else:
                # If no answer chunks found, try course docs first if available
                if course_docs:
                    return self._generate_course_response(course_docs, pregunta)
                else:
                    return self._generate_faq_response(faq_docs[0])
        
        elif course_docs:
            # Use course content to provide real information
            return self._generate_course_response(course_docs, pregunta)
        
        elif blog_docs:
            # Use blog content
            return self._generate_blog_response(blog_docs, pregunta)
        
        elif contact_docs:
            # Use contact/footer content
            return self._generate_contact_response(contact_docs[0])
        
        else:
            # Fallback to generic response
            return self._generate_generic_response(spanish_documents, pregunta)
    
    def _generate_faq_response(self, faq_doc: Dict) -> str:
        """Generate response from FAQ document"""
        faq_text = faq_doc.get('text', '').strip()
        
        # If this chunk doesn't contain a response, look for one that does
        if 'Respuesta:' not in faq_text and '|' not in faq_text:
            # This is just a question chunk, but still clean it before returning
            cleaned_text = self._remove_professor_mentions_improved(faq_text)
            cleaned_text = self._ensure_spanish_response(cleaned_text)
            return cleaned_text if cleaned_text else "Para información específica sobre cursos, visita la **página Nuestros Cursos**."
        
        clean_answer = self._extract_answer_from_faq(faq_text)
        clean_answer = self._remove_professor_mentions_improved(clean_answer)
        clean_answer = self._ensure_spanish_response(clean_answer)
        return clean_answer
    
    def _generate_course_response(self, course_docs: List[Dict], pregunta: str) -> str:
        """Generate response from course documents with real information"""
        course_doc = course_docs[0]
        course_text = course_doc.get('text', '').strip()
        
        # Extract course information from the indexed content
        pregunta_lower = pregunta.lower()
        
        # If asking about specific courses or areas
        if any(word in pregunta_lower for word in ['qué cursos', 'cuáles cursos', 'cursos disponibles']):
            # Collect course information from multiple documents
            course_info = []
            courses_by_area = {}
            
            for doc in course_docs[:5]:  # Top 5 course documents
                text = doc.get('text', '').strip()
                
                # Parse course information
                if '|' in text:
                    # Format: "Curso: Name | Área: Area"
                    parts = text.split('|')
                    course_name = ''
                    area_name = ''
                    
                    for part in parts:
                        part = part.strip()
                        if part.startswith('Curso:'):
                            course_name = part.replace('Curso:', '').strip()
                        elif part.startswith('Área:'):
                            area_name = part.replace('Área:', '').strip()
                    
                    if course_name and area_name:
                        if area_name not in courses_by_area:
                            courses_by_area[area_name] = []
                        if course_name not in courses_by_area[area_name]:
                            courses_by_area[area_name].append(course_name)
                
                elif text.startswith('Curso:'):
                    # Format: "Curso: Name"
                    course_name = text.replace('Curso:', '').strip()
                    if course_name:
                        if 'General' not in courses_by_area:
                            courses_by_area['General'] = []
                        if course_name not in courses_by_area['General']:
                            courses_by_area['General'].append(course_name)
                
                elif 'curso' in text.lower():
                    # Format: "Course name" (without prefix)
                    course_name = text.strip()
                    if course_name:
                        if 'General' not in courses_by_area:
                            courses_by_area['General'] = []
                        if course_name not in courses_by_area['General']:
                            courses_by_area['General'].append(course_name)
            
            if courses_by_area:
                response = "📚 **Cursos disponibles:**\n\n"
                
                for area, courses in courses_by_area.items():
                    response += f"**{area}:**\n"
                    for course in courses[:3]:  # Limit to 3 per area
                        response += f"• {course}\n"
                    response += "\n"
                
                response += "Para información completa sobre horarios, fechas de inscripción y requisitos, visita la **página Nuestros Cursos**."
                return response
        
        # If asking about registration or login process
        elif any(word in pregunta_lower for word in ['registrar', 'registro', 'crear cuenta', 'login', 'iniciar sesión', 'entrar', 'acceder', 'usuario', 'contraseña', 'olvidé']):
            # Look for registration/login information in documents
            reg_login_info = []
            
            for doc in course_docs:
                text = doc.get('text', '').strip()
                
                # Check if this document contains registration/login information
                if any(keyword in text.lower() for keyword in ['registro', 'login', 'iniciar sesión', 'crear cuenta', 'contraseña', 'formulario']):
                    reg_login_info.append(text)
            
            if reg_login_info:
                response = "📝 **Proceso de Registro e Inicio de Sesión:**\n\n"
                
                # Extract and format registration information
                for info in reg_login_info[:3]:  # Limit to 3 most relevant
                    if 'PASO 1' in info and 'REGISTRO' in info.upper():
                        response += "**1️⃣ REGISTRO DE USUARIO:**\n"
                        # Extract registration steps
                        lines = info.split('\n')
                        in_registro = False
                        for line in lines:
                            line = line.strip()
                            if 'PASO 1' in line and 'REGISTRO' in line.upper():
                                in_registro = True
                                continue
                            elif 'PASO 2' in line:
                                in_registro = False
                                break
                            elif in_registro and line and not line.startswith('PASO'):
                                if line.startswith('-') or line.startswith('•') or line.startswith('1.'):
                                    response += f"   {line}\n"
                                elif 'Cómo registrarse:' in line:
                                    response += f"   **{line}**\n"
                        response += "\n"
                    
                    elif 'PASO 2' in info and ('LOGIN' in info.upper() or 'INICIAR SESIÓN' in info.upper()):
                        response += "**2️⃣ INICIAR SESIÓN:**\n"
                        # Extract login steps
                        lines = info.split('\n')
                        in_login = False
                        for line in lines:
                            line = line.strip()
                            if 'PASO 2' in line and ('LOGIN' in line.upper() or 'INICIAR SESIÓN' in line.upper()):
                                in_login = True
                                continue
                            elif 'PASO 3' in line:
                                in_login = False
                                break
                            elif in_login and line and not line.startswith('PASO'):
                                if line.startswith('-') or line.startswith('•') or line.startswith('1.'):
                                    response += f"   {line}\n"
                                elif 'Cómo iniciar sesión:' in line:
                                    response += f"   **{line}**\n"
                        response += "\n"
                
                response += "**3️⃣ ACCESO A CURSOS:**\n"
                response += "   • Una vez con sesión iniciada, vaya a la página Nuestros Cursos\n"
                response += "   • Explore los programas disponibles\n"
                response += "   • Seleccione el curso de su interés\n"
                response += "   • Complete el proceso de inscripción\n\n"
                
                response += "⚠️ **IMPORTANTE:** Sin registro e inicio de sesión NO podrá acceder a ningún curso."
                return response
            else:
                # Fallback to general registration process
                response = "📝 **Proceso de Registro e Inscripción:**\n\n"
                response += "**1️⃣ REGISTRO (OBLIGATORIO):**\n"
                response += "   • Vaya al sitio web del Centro Fray Bartolomé de las Casas\n"
                response += "   • Busque y haga clic en 'Registrarse' o 'Crear Cuenta'\n"
                response += "   • Complete el formulario con sus datos personales\n"
                response += "   • Cree un nombre de usuario y contraseña segura\n"
                response += "   • Proporcione un email válido\n"
                response += "   • Haga clic en 'Registrarse'\n\n"
                
                response += "**2️⃣ INICIAR SESIÓN:**\n"
                response += "   • Vaya a la página de 'Iniciar Sesión' o 'Login'\n"
                response += "   • Ingrese su usuario/email y contraseña\n"
                response += "   • Haga clic en 'Iniciar Sesión'\n"
                response += "   • Si olvida su contraseña, use '¿Olvidó su contraseña?'\n\n"
                
                response += "**3️⃣ INSCRIPCIÓN A CURSOS:**\n"
                response += "   • Con sesión iniciada, vaya a la página Nuestros Cursos\n"
                response += "   • Seleccione el curso de su interés\n"
                response += "   • Complete el proceso de matrícula\n\n"
                
                response += "⚠️ **IMPORTANTE:** El registro es GRATUITO y solo toma unos minutos. Sin registro no podrá inscribirse a ningún curso."
                return response
        
        # Check for time-remaining queries first (more specific)
        elif any(pattern in pregunta_lower for pattern in ['cuánto tiempo me queda', 'cuanto tiempo me queda', 'cuánto tiempo queda', 'cuanto tiempo queda', 'tiempo restante', 'tiempo que queda', 'cuántos días quedan', 'cuantos dias quedan']):
            return self._create_inscription_time_response(course_docs, pregunta)
        
        # If asking about inscriptions, dates, or deadlines (expanded detection)
        elif any(word in pregunta_lower for word in ['inscripción', 'inscribir', 'matrícula', 'fecha', 'cuándo', 'hasta cuándo', 'límite', 'disponible', 'abierta', 'empieza', 'inicia', 'comienza', 'termina']):
            # Look for enrollment information in documents
            enrollment_info = []
            
            for doc in course_docs:
                text = doc.get('text', '').strip()
                
                # Check if this document contains enrollment information
                if 'Inscripciones para' in text and ('Fecha límite' in text or 'Estado actual' in text):
                    # Clean the text to remove professor mentions
                    cleaned_text = self._remove_professor_mentions_improved(text)
                    enrollment_info.append(cleaned_text)
            
            if enrollment_info:
                response = "📅 **Información de Inscripciones:**\n\n"
                
                for info in enrollment_info[:5]:  # Limit to 5 courses
                    # Parse the enrollment information
                    if 'Inscripciones para' in info:
                        # Extract course name
                        course_start = info.find('Inscripciones para') + len('Inscripciones para ')
                        course_end = info.find(':', course_start)
                        if course_end > course_start:
                            course_name = info[course_start:course_end].strip()
                            # Clean course name to remove any professor mentions
                            course_name = self._remove_professor_mentions_improved(course_name)
                            response += f"**{course_name}:**\n"
                            
                            # Extract status
                            if 'Estado actual:' in info:
                                status_start = info.find('Estado actual:') + len('Estado actual: ')
                                status_end = info.find('|', status_start)
                                if status_end == -1:
                                    status_end = len(info)
                                status = info[status_start:status_end].strip()
                                # Clean status to remove professor mentions
                                status = self._remove_professor_mentions_improved(status)
                                if status:  # Only add if there's content after cleaning
                                    response += f"• Estado: {status}\n"
                            
                            # Extract deadline
                            if 'Fecha límite de inscripción:' in info:
                                deadline_start = info.find('Fecha límite de inscripción:') + len('Fecha límite de inscripción: ')
                                deadline_end = info.find('|', deadline_start)
                                if deadline_end == -1:
                                    deadline_end = len(info)
                                deadline = info[deadline_start:deadline_end].strip()
                                # Clean deadline to remove professor mentions
                                deadline = self._remove_professor_mentions_improved(deadline)
                                if deadline:  # Only add if there's content after cleaning
                                    response += f"• Fecha límite: {deadline}\n"
                            
                            # Extract start date
                            if 'Fecha de inicio:' in info:
                                start_start = info.find('Fecha de inicio:') + len('Fecha de inicio: ')
                                start_end = info.find('|', start_start)
                                if start_end == -1:
                                    start_end = len(info)
                                start_date = info[start_start:start_end].strip()
                                # Clean start date to remove professor mentions
                                start_date = self._remove_professor_mentions_improved(start_date)
                                if start_date:  # Only add if there's content after cleaning
                                    response += f"• Fecha de inicio: {start_date}\n"
                            
                            # Extract availability
                            if '✅ Inscripciones abiertas' in info:
                                response += f"• ✅ **Inscripciones abiertas**\n"
                            elif '❌' in info:
                                response += f"• ❌ **Inscripciones cerradas**\n"
                            
                            response += "\n"
                
                response += "📝 **Proceso de Inscripción:**\n"
                response += "1. **Registro:** Crea una cuenta de usuario\n"
                response += "2. **Login:** Inicia sesión con tus credenciales\n"
                response += "3. **Inscripción:** Accede a la página Nuestros Cursos y completa tu inscripción\n\n"
                response += "⚠️ **IMPORTANTE:** Sin registro no podrás inscribirte a ningún curso."
                return response
            else:
                # Fallback to general inscription process
                response = "📝 **Proceso de Inscripción a Cursos:**\n\n"
                response += "**PASO 1: Registro de Usuario**\n"
                response += "• Vaya a la página de **Registro**\n"
                response += "• Complete todos los campos requeridos\n"
                response += "• Haga clic en 'Registrarse'\n\n"
                response += "**PASO 2: Iniciar Sesión**\n"
                response += "• Vaya a la página de **Iniciar Sesión**\n"
                response += "• Ingrese su usuario y contraseña\n"
                response += "• Haga clic en 'Iniciar Sesión'\n\n"
                response += "**PASO 3: Inscripción**\n"
                response += "• Acceda a la **página Nuestros Cursos**\n"
                response += "• Consulte fechas y requisitos\n"
                response += "• Complete su inscripción\n\n"
                response += "⚠️ **IMPORTANTE:** Sin registro no podrá inscribirse a ningún curso."
                return response
        
        # If asking about areas or specific subjects
        elif any(word in pregunta_lower for word in ['idiomas', 'inglés', 'alemán', 'teología', 'diseño']):
            area_mentioned = None
            if 'idiomas' in pregunta_lower or 'inglés' in pregunta_lower or 'alemán' in pregunta_lower:
                area_mentioned = 'Idiomas'
            elif 'teología' in pregunta_lower:
                area_mentioned = 'Teología'
            elif 'diseño' in pregunta_lower:
                area_mentioned = 'Diseño'
            
            # Check if asking about dates/times for specific courses
            if any(date_word in pregunta_lower for date_word in ['cuándo', 'fecha', 'empieza', 'inicia', 'límite']):
                # Look for enrollment information for courses in this area
                enrollment_info = []
                
                for doc in course_docs:
                    text = doc.get('text', '').strip()
                    
                    # Check if this document contains enrollment information for the area
                    if 'Inscripciones para' in text and area_mentioned and area_mentioned.lower() in text.lower():
                        enrollment_info.append(text)
                
                if enrollment_info:
                    response = f"📅 **Información de Inscripciones - {area_mentioned}:**\n\n"
                    
                    for info in enrollment_info[:3]:  # Limit to 3 courses
                        # Parse the enrollment information
                        if 'Inscripciones para' in info:
                            # Extract course name
                            course_start = info.find('Inscripciones para') + len('Inscripciones para ')
                            course_end = info.find(':', course_start)
                            if course_end > course_start:
                                course_name = info[course_start:course_end].strip()
                                response += f"**{course_name}:**\n"
                                
                                # Extract status
                                if 'Estado actual:' in info:
                                    status_start = info.find('Estado actual:') + len('Estado actual: ')
                                    status_end = info.find('|', status_start)
                                    if status_end == -1:
                                        status_end = len(info)
                                    status = info[status_start:status_end].strip()
                                    response += f"• Estado: {status}\n"
                                
                                # Extract deadline
                                if 'Fecha límite de inscripción:' in info:
                                    deadline_start = info.find('Fecha límite de inscripción:') + len('Fecha límite de inscripción: ')
                                    deadline_end = info.find('|', deadline_start)
                                    if deadline_end == -1:
                                        deadline_end = len(info)
                                    deadline = info[deadline_start:deadline_end].strip()
                                    response += f"• Fecha límite: {deadline}\n"
                                
                                # Extract start date
                                if 'Fecha de inicio:' in info:
                                    start_start = info.find('Fecha de inicio:') + len('Fecha de inicio: ')
                                    start_end = info.find('|', start_start)
                                    if start_end == -1:
                                        start_end = len(info)
                                    start_date = info[start_start:start_end].strip()
                                    response += f"• Fecha de inicio: {start_date}\n"
                                
                                # Extract availability
                                if '✅ Inscripciones abiertas' in info:
                                    response += f"• ✅ **Inscripciones abiertas**\n"
                                elif '❌' in info:
                                    response += f"• ❌ **Inscripciones cerradas**\n"
                                
                                response += "\n"
                    
                    return response
            
            if area_mentioned:
                # Look for courses in that area (general info)
                area_courses = []
                for doc in course_docs:
                    text = doc.get('text', '').strip()
                    
                    # Check if this document is for the requested area
                    if f'Área: {area_mentioned}' in text:
                        # Extract course name
                        if '|' in text:
                            parts = text.split('|')
                            for part in parts:
                                part = part.strip()
                                if part.startswith('Curso:'):
                                    course_name = part.replace('Curso:', '').strip()
                                    if course_name and course_name not in area_courses:
                                        area_courses.append(course_name)
                        elif text.startswith('Curso:'):
                            course_name = text.replace('Curso:', '').strip()
                            if course_name and course_name not in area_courses:
                                area_courses.append(course_name)
                
                if area_courses:
                    response = f"📖 **Cursos en {area_mentioned}:**\n\n"
                    for course in area_courses[:3]:  # Limit to 3
                        response += f"• {course}\n"
                    response += f"\nPara más detalles sobre estos cursos, horarios y fechas de inscripción, "
                    response += "visita la **página Nuestros Cursos**."
                    return response
        
        # Default course response with page reference
        return ("Para información completa sobre nuestros cursos, incluyendo horarios, fechas de inscripción, "
                "requisitos y detalles específicos, te recomiendo visitar la **página Nuestros Cursos** "
                "donde encontrarás toda la información actualizada.")
    
    def _generate_blog_response(self, blog_docs: List[Dict], pregunta: str = "") -> str:
        """Generate enhanced response from blog documents with search capabilities"""
        
        if not blog_docs:
            return ("Para las últimas noticias y eventos del centro, te recomiendo visitar nuestro "
                   "**blog de noticias** donde encontrarás información actualizada.")
        
        pregunta_lower = pregunta.lower() if pregunta else ""
        
        # Check if asking for latest news
        if any(word in pregunta_lower for word in ['últimas', 'ultimas', 'recientes', 'nuevas', 'qué hay de nuevo', 'que hay de nuevo']):
            return self._generate_latest_news_response(blog_docs)
        
        # Check if asking where a word/phrase is mentioned
        elif any(pattern in pregunta_lower for pattern in ['dónde se menciona', 'donde se menciona', 'en qué lugar se menciona', 'en que lugar se menciona', 'dónde aparece', 'donde aparece']):
            return self._generate_word_location_response(blog_docs, pregunta)
        
        # Check if asking specifically which news talks about a topic
        elif any(pattern in pregunta_lower for pattern in ['qué noticia habla sobre', 'que noticia habla sobre', 'cuál noticia habla sobre', 'cual noticia habla sobre', 'qué noticias hablan sobre', 'que noticias hablan sobre', 'cuáles noticias hablan sobre', 'cuales noticias hablan sobre']):
            return self._generate_specific_topic_news_response(blog_docs, pregunta)
        
        # Check if it's a single word search (no question words, just a term)
        elif self._is_single_word_search(pregunta):
            return self._generate_single_word_search_response(blog_docs, pregunta)
        
        # Check if searching for specific topic (general search)
        elif any(word in pregunta_lower for word in ['buscar', 'sobre', 'tema', 'habla de', 'habla sobre']):
            return self._generate_news_search_response(blog_docs, pregunta)
        
        # Default: show single news item
        else:
            return self._generate_single_news_response(blog_docs[0])
    
    def _generate_latest_news_response(self, blog_docs: List[Dict]) -> str:
        """Generate response showing latest news"""
        response = "📰 **Últimas Noticias del Centro:**\n\n"
        
        # Show up to 5 latest news
        for i, doc in enumerate(blog_docs[:5], 1):
            blog_text = doc.get('text', '').strip()
            title, summary, date = self._extract_blog_info(blog_text)
            
            if title:
                response += f"**{i}. {title}**\n"
                if date:
                    response += f"   📅 {date}\n"
                if summary:
                    # Limit summary to 100 characters
                    short_summary = summary[:100] + "..." if len(summary) > 100 else summary
                    response += f"   {short_summary}\n"
                response += "\n"
        
        response += "📖 **Para leer las noticias completas, visita nuestro blog de noticias.**"
        return response
    
    def _generate_specific_topic_news_response(self, blog_docs: List[Dict], pregunta: str) -> str:
        """Generate response for specific topic queries - returns only news titles that talk about the topic"""
        
        # Extract the topic from the question
        topic = self._extract_topic_from_question(pregunta)
        
        if not topic:
            return ("No pude identificar el tema específico sobre el que preguntas. "
                   "Por favor, reformula tu pregunta, por ejemplo: '¿qué noticia habla sobre cursos?'")
        
        # Search through ALL news content to find titles that mention the topic
        matching_news = []
        
        # Get all blog documents from the semantic search (not just the top results)
        all_blog_docs = self._get_all_blog_documents()
        
        for doc in all_blog_docs:
            blog_text = doc.get('text', '').strip()
            blog_text_lower = blog_text.lower()
            
            # Extract clean title and other info
            clean_title = self._extract_clean_title(blog_text)
            title, summary, date = self._extract_blog_info(blog_text)
            
            # Use clean title if available, otherwise use extracted title
            final_title = clean_title if clean_title else title
            
            # Check if the topic appears in the full text content (title, summary, or content)
            if final_title and self._topic_matches_content(topic, blog_text_lower):
                matching_news.append({
                    'title': final_title,
                    'date': date,
                    'summary': summary,
                    'relevance_score': self._calculate_topic_relevance(topic, blog_text_lower)
                })
        
        # Sort by relevance score (highest first)
        matching_news.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        if not matching_news:
            return (f"📰 **No encontré noticias que hablen específicamente sobre '{topic}'.**\n\n"
                   f"Para ver todas las noticias disponibles, visita nuestro **blog de noticias**.")
        
        # Build response with only titles
        response = f"📰 **Noticias que hablan sobre '{topic}':**\n\n"
        
        for i, news in enumerate(matching_news[:5], 1):  # Limit to top 5 most relevant
            response += f"**{i}. {news['title']}**"
            if news['date']:
                response += f" (📅 {news['date']})"
            response += "\n"
        
        response += f"\n📖 **Para leer estas noticias completas, visita nuestro blog de noticias.**"
        
        return response
    
    def _generate_news_search_response(self, blog_docs: List[Dict], pregunta: str) -> str:
        """Generate response for news search queries"""
        # Extract search terms from question
        search_terms = self._extract_search_terms(pregunta)
        
        response = f"🔍 **Noticias encontradas"
        if search_terms:
            response += f" sobre: {', '.join(search_terms)}"
        response += ":**\n\n"
        
        found_news = 0
        for doc in blog_docs[:5]:  # Limit to 5 results
            blog_text = doc.get('text', '').strip()
            title, summary, date = self._extract_blog_info(blog_text)
            
            if title:
                found_news += 1
                response += f"**{found_news}. {title}**\n"
                if date:
                    response += f"   📅 {date}\n"
                if summary:
                    # Show more summary for search results
                    short_summary = summary[:150] + "..." if len(summary) > 150 else summary
                    response += f"   {short_summary}\n"
                response += "\n"
        
        if found_news == 0:
            response = f"🔍 **No se encontraron noticias específicas"
            if search_terms:
                response += f" sobre: {', '.join(search_terms)}"
            response += ".**\n\n"
            response += "📰 Para ver todas las noticias disponibles, visita nuestro **blog de noticias**."
        else:
            response += "📖 **Para leer las noticias completas, visita nuestro blog de noticias.**"
        
        return response
    
    def _generate_single_news_response(self, blog_doc: Dict) -> str:
        """Generate response for a single news item"""
        blog_text = blog_doc.get('text', '').strip()
        title, summary, date = self._extract_blog_info(blog_text)
        
        if title and summary:
            response = f"📰 **{title}**\n\n"
            if date:
                response += f"📅 **Fecha:** {date}\n\n"
            response += f"{summary}\n\n"
            response += "📖 **Para leer la noticia completa y ver más noticias, visita nuestro blog de noticias.**"
            return response
        else:
            return ("Para las últimas noticias y eventos del centro, te recomiendo visitar nuestro "
                   "**blog de noticias** donde encontrarás información actualizada.")
    
    def _extract_blog_info(self, blog_text: str) -> tuple:
        """Extract title, summary, and date from blog text"""
        lines = blog_text.split('\n')
        title = ''
        summary = ''
        date = ''
        
        for line in lines:
            line = line.strip()
            if line.startswith('Título:'):
                title = line.replace('Título:', '').strip()
            elif line.startswith('Resumen:'):
                summary = line.replace('Resumen:', '').strip()
            elif line.startswith('Fecha:'):
                date = line.replace('Fecha:', '').strip()
            elif line.startswith('Contenido:'):
                # If no summary found, use first part of content
                if not summary:
                    content = line.replace('Contenido:', '').strip()
                    summary = content[:200] + "..." if len(content) > 200 else content
        
        return title, summary, date
    
    def _extract_clean_title(self, blog_text: str) -> str:
        """Extract only the clean title from blog text"""
        lines = blog_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Título:'):
                title = line.replace('Título:', '').strip()
                # Clean up any extra information that might be attached
                if ' Categoría:' in title:
                    title = title.split(' Categoría:')[0].strip()
                if ' Resumen:' in title:
                    title = title.split(' Resumen:')[0].strip()
                return title
        
        # If no title found with "Título:" pattern, try to extract from first meaningful line
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Categoría:', 'Resumen:', 'Contenido:', 'Autor:', 'Fecha:')):
                # This might be the title
                if len(line) > 10 and len(line) < 100:  # Reasonable title length
                    return line
        
        return ""
    
    def _extract_search_terms(self, pregunta: str) -> List[str]:
        """Extract search terms from a question"""
        pregunta_lower = pregunta.lower()
        
        # Remove common question words
        stop_words = ['qué', 'que', 'cuál', 'cual', 'cómo', 'como', 'dónde', 'donde', 
                     'cuándo', 'cuando', 'por qué', 'por que', 'para qué', 'para que',
                     'hay', 'tiene', 'sobre', 'de', 'del', 'la', 'el', 'un', 'una',
                     'noticia', 'noticias', 'blog', 'habla', 'tema', 'buscar', 'mostrar']
        
        # Split into words and filter
        words = pregunta_lower.split()
        search_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        return search_terms[:3]  # Return up to 3 search terms
    
    def _extract_topic_from_question(self, pregunta: str) -> str:
        """Extract the specific topic from questions like '¿qué noticia habla sobre [topic]?'"""
        pregunta_lower = pregunta.lower()
        
        # Patterns to identify the topic
        patterns = [
            'qué noticia habla sobre ',
            'que noticia habla sobre ',
            'cuál noticia habla sobre ',
            'cual noticia habla sobre ',
            'qué noticias hablan sobre ',
            'que noticias hablan sobre ',
            'cuáles noticias hablan sobre ',
            'cuales noticias hablan sobre ',
            'qué noticia habla de ',
            'que noticia habla de ',
            'cuál noticia habla de ',
            'cual noticia habla de '
        ]
        
        # Find the topic after the pattern
        for pattern in patterns:
            if pattern in pregunta_lower:
                # Extract everything after the pattern
                topic_start = pregunta_lower.find(pattern) + len(pattern)
                topic = pregunta_lower[topic_start:].strip()
                
                # Clean up the topic (remove question marks, etc.)
                topic = topic.replace('?', '').replace('¿', '').strip()
                
                # Remove common words at the end
                end_words = ['del centro', 'en el centro', 'del blog', 'en el blog']
                for end_word in end_words:
                    if topic.endswith(end_word):
                        topic = topic[:-len(end_word)].strip()
                
                if topic:
                    return topic
        
        return ""
    
    def _get_all_blog_documents(self) -> List[Dict]:
        """Get all blog documents from the semantic search index"""
        try:
            # Search for all blog documents with a very broad query
            all_docs = self.semantic_search.search(
                query="noticias blog contenido",
                top_k=50,  # Get more documents
                categoria='blog'
            )
            return all_docs
        except Exception as e:
            logger.error(f"Error getting all blog documents: {e}")
            return []
    
    def _topic_matches_content(self, topic: str, content: str) -> bool:
        """Check if a topic matches the content of a news article"""
        topic_lower = topic.lower()
        content_lower = content.lower()
        
        # Direct topic match
        if topic_lower in content_lower:
            return True
        
        # Check for related terms based on common topics
        topic_synonyms = {
            'cursos': ['curso', 'programa', 'estudios', 'educación', 'formación', 'clases'],
            'idiomas': ['idioma', 'inglés', 'alemán', 'italiano', 'francés', 'lenguas', 'language'],
            'eventos': ['evento', 'actividad', 'celebración', 'ceremonia', 'encuentro'],
            'graduación': ['graduación', 'promoción', 'egresados', 'titulación', 'ceremonia'],
            'teología': ['teología', 'religión', 'fe', 'espiritual', 'pastoral'],
            'diseño': ['diseño', 'gráfico', 'creativo', 'arte', 'visual'],
            'becas': ['beca', 'ayuda', 'financiamiento', 'apoyo económico', 'oportunidad'],
            'instalaciones': ['instalación', 'laboratorio', 'aula', 'espacio', 'renovación', 'mejora'],
            'actividades': ['actividad', 'taller', 'seminario', 'encuentro', 'programa']
        }
        
        # Check if topic has synonyms
        synonyms = topic_synonyms.get(topic_lower, [topic_lower])
        
        # Check if any synonym appears in content
        for synonym in synonyms:
            if synonym in content_lower:
                return True
        
        return False
    
    def _calculate_topic_relevance(self, topic: str, content: str) -> float:
        """Calculate how relevant a news article is to a specific topic"""
        topic_lower = topic.lower()
        content_lower = content.lower()
        
        relevance_score = 0.0
        
        # Direct topic mentions (highest score)
        topic_count = content_lower.count(topic_lower)
        relevance_score += topic_count * 3.0
        
        # Check for related terms
        topic_synonyms = {
            'cursos': ['curso', 'programa', 'estudios', 'educación', 'formación', 'clases'],
            'idiomas': ['idioma', 'inglés', 'alemán', 'italiano', 'francés', 'lenguas'],
            'eventos': ['evento', 'actividad', 'celebración', 'ceremonia', 'encuentro'],
            'graduación': ['graduación', 'promoción', 'egresados', 'titulación'],
            'teología': ['teología', 'religión', 'fe', 'espiritual', 'pastoral'],
            'diseño': ['diseño', 'gráfico', 'creativo', 'arte', 'visual'],
            'becas': ['beca', 'ayuda', 'financiamiento', 'apoyo económico'],
            'instalaciones': ['instalación', 'laboratorio', 'aula', 'espacio', 'renovación'],
            'actividades': ['actividad', 'taller', 'seminario', 'encuentro', 'programa']
        }
        
        synonyms = topic_synonyms.get(topic_lower, [])
        for synonym in synonyms:
            synonym_count = content_lower.count(synonym)
            relevance_score += synonym_count * 1.5
        
        # Bonus for topic appearing in title (extracted from content)
        if 'título:' in content_lower:
            title_section = content_lower.split('título:')[1].split('\n')[0] if 'título:' in content_lower else ""
            if topic_lower in title_section:
                relevance_score += 5.0
            
            # Check synonyms in title
            for synonym in synonyms:
                if synonym in title_section:
                    relevance_score += 3.0
        
        return relevance_score
    
    def _generate_word_location_response(self, blog_docs: List[Dict], pregunta: str) -> str:
        """Generate response showing where a specific word or phrase is mentioned"""
        
        # Extract the word/phrase from the question
        word_phrase = self._extract_word_phrase_from_question(pregunta)
        
        if not word_phrase:
            return ("No pude identificar la palabra o frase específica que buscas. "
                   "Por favor, reformula tu pregunta, por ejemplo: '¿dónde se menciona diseño gráfico?'")
        
        # Search through ALL content (not just blog) to find mentions
        all_locations = self._find_word_phrase_locations(word_phrase)
        
        if not all_locations:
            return (f"📍 **No encontré menciones de '{word_phrase}' en el contenido disponible.**\n\n"
                   f"Para buscar información más específica, visita nuestro sitio web.")
        
        # Build response showing locations
        response = f"📍 **Lugares donde se menciona '{word_phrase}':**\n\n"
        
        # Group by content type
        locations_by_type = {
            'noticias': [],
            'cursos': [],
            'contacto': [],
            'inscripciones': []
        }
        
        for location in all_locations:
            content_type = location.get('content_type', '')
            category = location.get('category', 'general')
            
            if 'blog' in content_type or category == 'blog':
                locations_by_type['noticias'].append(location)
            elif 'curso' in content_type or category == 'cursos':
                locations_by_type['cursos'].append(location)
            elif category == 'contacto':
                locations_by_type['contacto'].append(location)
            elif category == 'inscripciones':
                locations_by_type['inscripciones'].append(location)
        
        # Show results by category
        if locations_by_type['noticias']:
            response += "📰 **En Noticias:**\n"
            for i, loc in enumerate(locations_by_type['noticias'][:3], 1):
                response += f"{i}. {loc['title']} - {loc['context']}\n"
            response += "\n"
        
        if locations_by_type['cursos']:
            response += "📚 **En Cursos:**\n"
            for i, loc in enumerate(locations_by_type['cursos'][:3], 1):
                response += f"{i}. {loc['title']} - {loc['context']}\n"
            response += "\n"
        
        if locations_by_type['inscripciones']:
            response += "📝 **En Información de Inscripciones:**\n"
            for i, loc in enumerate(locations_by_type['inscripciones'][:2], 1):
                response += f"{i}. {loc['context']}\n"
            response += "\n"
        
        if locations_by_type['contacto']:
            response += "📞 **En Información de Contacto:**\n"
            for i, loc in enumerate(locations_by_type['contacto'][:2], 1):
                response += f"{i}. {loc['context']}\n"
            response += "\n"
        
        response += f"💡 **Para más detalles, visita las secciones correspondientes en nuestro sitio web.**"
        
        return response
    
    def _generate_single_word_search_response(self, blog_docs: List[Dict], pregunta: str) -> str:
        """Generate response for single word searches across the entire site"""
        
        search_word = pregunta.strip().lower()
        
        # Check if it's a relevant word (not too common)
        if self._is_relevant_search_word(search_word):
            # Search across all content
            all_locations = self._find_word_phrase_locations(search_word)
            
            if not all_locations:
                return (f"🔍 **No encontré referencias a '{search_word}' en el contenido disponible.**\n\n"
                       f"Para buscar información más específica, visita nuestro sitio web.")
            
            # Build comprehensive response
            response = f"🔍 **Búsqueda de '{search_word}' en todo el sitio:**\n\n"
            
            # Group and show results
            locations_by_type = {
                'noticias': [],
                'cursos': [],
                'contacto': [],
                'inscripciones': []
            }
            
            for location in all_locations:
                content_type = location.get('content_type', '')
                category = location.get('category', 'general')
                
                if 'blog' in content_type or category == 'blog':
                    locations_by_type['noticias'].append(location)
                elif 'curso' in content_type or category == 'cursos':
                    locations_by_type['cursos'].append(location)
                elif category == 'contacto':
                    locations_by_type['contacto'].append(location)
                elif category == 'inscripciones':
                    locations_by_type['inscripciones'].append(location)
            
            # Show results by category with more detail
            if locations_by_type['noticias']:
                response += "📰 **En Noticias y Blog:**\n"
                for i, loc in enumerate(locations_by_type['noticias'][:4], 1):
                    response += f"**{i}. {loc['title']}**\n"
                    response += f"   📍 {loc['context']}\n\n"
            
            if locations_by_type['cursos']:
                response += "📚 **En Cursos:**\n"
                for i, loc in enumerate(locations_by_type['cursos'][:4], 1):
                    response += f"**{i}. {loc['title']}**\n"
                    response += f"   📍 {loc['context']}\n\n"
            
            if locations_by_type['inscripciones']:
                response += "📝 **En Información de Inscripciones:**\n"
                for i, loc in enumerate(locations_by_type['inscripciones'][:3], 1):
                    response += f"{i}. {loc['context']}\n"
                response += "\n"
            
            if locations_by_type['contacto']:
                response += "📞 **En Información de Contacto:**\n"
                for i, loc in enumerate(locations_by_type['contacto'][:2], 1):
                    response += f"{i}. {loc['context']}\n"
                response += "\n"
            
            response += f"💡 **Para información completa, visita las páginas correspondientes en nuestro sitio web.**"
            
            return response
        else:
            # For common words, use regular search
            return self._generate_news_search_response(blog_docs, pregunta)
    
    def _extract_word_phrase_from_question(self, pregunta: str) -> str:
        """Extract the word or phrase from location questions"""
        pregunta_lower = pregunta.lower()
        
        # Patterns to identify the word/phrase
        patterns = [
            'dónde se menciona ',
            'donde se menciona ',
            'en qué lugar se menciona ',
            'en que lugar se menciona ',
            'dónde aparece ',
            'donde aparece ',
            'en qué parte se menciona ',
            'en que parte se menciona '
        ]
        
        # Find the word/phrase after the pattern
        for pattern in patterns:
            if pattern in pregunta_lower:
                # Extract everything after the pattern
                word_start = pregunta_lower.find(pattern) + len(pattern)
                word_phrase = pregunta_lower[word_start:].strip()
                
                # Clean up the word/phrase (remove question marks, etc.)
                word_phrase = word_phrase.replace('?', '').replace('¿', '').strip()
                
                # Remove common endings
                end_words = ['del centro', 'en el centro', 'del blog', 'en el blog', 'en el sitio', 'en la página']
                for end_word in end_words:
                    if word_phrase.endswith(end_word):
                        word_phrase = word_phrase[:-len(end_word)].strip()
                
                if word_phrase:
                    return word_phrase
        
        return ""
    
    def _find_word_phrase_locations(self, word_phrase: str) -> List[Dict]:
        """Find all locations where a word or phrase is mentioned"""
        locations = []
        
        try:
            # Search across all content types
            all_docs = self.semantic_search.search(
                query=word_phrase,
                top_k=20,  # Get more results for comprehensive search
                categoria=None  # Search all categories
            )
            
            for doc in all_docs:
                text = doc.get('text', '').strip()
                content_type = doc.get('content_type', '')
                category = doc.get('categoria', 'general')
                
                # Check if the word/phrase actually appears in the text
                if word_phrase.lower() in text.lower():
                    # Extract context around the word/phrase
                    context = self._extract_context_around_word(text, word_phrase)
                    
                    # Extract title if available
                    title = self._extract_title_from_content(text, content_type)
                    
                    locations.append({
                        'title': title,
                        'context': context,
                        'content_type': content_type,
                        'category': category,
                        'score': doc.get('score', 0)
                    })
            
            # Sort by relevance score
            locations.sort(key=lambda x: x['score'], reverse=True)
            
            return locations[:10]  # Return top 10 most relevant
            
        except Exception as e:
            logger.error(f"Error finding word/phrase locations: {e}")
            return []
    
    def _extract_context_around_word(self, text: str, word_phrase: str, context_length: int = 100) -> str:
        """Extract context around a word or phrase"""
        text_lower = text.lower()
        word_lower = word_phrase.lower()
        
        # Find the position of the word/phrase
        pos = text_lower.find(word_lower)
        if pos == -1:
            return text[:context_length] + "..." if len(text) > context_length else text
        
        # Extract context before and after
        start = max(0, pos - context_length // 2)
        end = min(len(text), pos + len(word_phrase) + context_length // 2)
        
        context = text[start:end].strip()
        
        # Add ellipsis if truncated
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context
    
    def _extract_title_from_content(self, text: str, content_type: str) -> str:
        """Extract title from content based on content type"""
        lines = text.split('\n')
        
        # For blog content
        if 'blog' in content_type:
            for line in lines:
                line = line.strip()
                if line.startswith('Título:'):
                    return line.replace('Título:', '').strip()
        
        # For course content
        elif 'curso' in content_type:
            for line in lines:
                line = line.strip()
                if line.startswith('Curso:'):
                    return line.replace('Curso:', '').strip()
        
        # For other content, try to find a meaningful title
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 100:
                # This might be a title
                if not line.startswith(('Categoría:', 'Resumen:', 'Contenido:', 'Autor:', 'Fecha:')):
                    return line
        
        return "Contenido del sitio"
    
    def _is_single_word_search(self, pregunta: str) -> bool:
        """Check if this is a single word search query"""
        pregunta = pregunta.strip()
        
        # Check if it's just one or two words without question indicators
        words = pregunta.split()
        if len(words) > 3:
            return False
        
        # Check if it doesn't contain question words
        question_words = ['qué', 'que', 'cuál', 'cual', 'cómo', 'como', 'dónde', 'donde', 
                         'cuándo', 'cuando', 'por qué', 'por que', '¿', '?']
        
        pregunta_lower = pregunta.lower()
        has_question_words = any(qword in pregunta_lower for qword in question_words)
        
        return not has_question_words and len(words) <= 3
    
    def _is_relevant_search_word(self, word: str) -> bool:
        """Check if a word is relevant enough for site-wide search"""
        # Words that are relevant for site search
        relevant_words = [
            # Course related
            'cursos', 'curso', 'idiomas', 'inglés', 'alemán', 'italiano', 'diseño', 'teología',
            'educación', 'formación', 'programa', 'clases',
            
            # Institution related
            'centro', 'fray', 'bartolomé', 'casas', 'institución',
            
            # Process related
            'inscripción', 'matrícula', 'registro', 'becas', 'graduación',
            
            # Facilities
            'laboratorio', 'instalaciones', 'aula', 'biblioteca',
            
            # Activities
            'eventos', 'actividades', 'talleres', 'seminarios', 'conferencias',
            
            # People (if specific names)
            'profesor', 'estudiante', 'director'
        ]
        
        # Check if word is in relevant list or is long enough to be a name/title
        return word in relevant_words or len(word) >= 5
    
    def _generate_contact_response(self, contact_doc: Dict) -> str:
        """Generate response from contact/footer document"""
        contact_text = contact_doc.get('text', '').strip()
        
        # Extract contact information from the text
        if 'Dirección:' in contact_text and ('Teléfono:' in contact_text or 'Email:' in contact_text):
            response = "📞 **Información de Contacto y Ubicación:**\n\n"
            
            # Extract address
            if 'Dirección:' in contact_text:
                # Find text between "Dirección:" and "Teléfono:"
                start = contact_text.find('Dirección:')
                end = contact_text.find('Teléfono:', start)
                if end == -1:
                    end = contact_text.find('Email:', start)
                if end == -1:
                    end = len(contact_text)
                
                address = contact_text[start:end].replace('Dirección:', '').strip()
                if address:
                    response += f"📍 **Dirección:** {address}\n"
                    response += f"🗺️ **Ubicación:** Centro Fray Bartolomé de las Casas\n"
                    response += f"🏢 **Zona:** Vedado, Plaza de la Revolución, La Habana\n\n"
                    
                    # Add directions information
                    response += "🚗 **Cómo llegar:**\n"
                    response += "• **En transporte público:** Consulta las rutas de guaguas que pasan por el Vedado\n"
                    response += "• **En taxi:** Indica la dirección: Calle 19 No 258 entre J e I, Vedado\n"
                    response += "• **Referencias:** Zona céntrica del Vedado, cerca de instituciones conocidas\n\n"
            
            # Extract phone
            if 'Teléfono:' in contact_text:
                start = contact_text.find('Teléfono:')
                end = contact_text.find('Email:', start)
                if end == -1:
                    # Look for next space or end of text
                    words = contact_text[start:].split()
                    if len(words) >= 3:  # "Teléfono:" + number + maybe more
                        phone = ' '.join(words[1:3])  # Take next 2 words
                    else:
                        phone = contact_text[start:].replace('Teléfono:', '').strip()
                else:
                    phone = contact_text[start:end].replace('Teléfono:', '').strip()
                
                if phone:
                    response += f"📱 **Teléfono:** {phone}\n"
            
            # Extract email
            if 'Email:' in contact_text:
                start = contact_text.find('Email:')
                # Find the email address (look for @ symbol)
                email_part = contact_text[start:].replace('Email:', '').strip()
                # Take first word that might be email
                email_words = email_part.split()
                if email_words:
                    email = email_words[0]
                    # Clean up common suffixes
                    if email.endswith('.'):
                        email = email[:-1]
                    response += f"📧 **Email:** {email}\n"
            
            response += "\n💡 **Tip:** Para indicaciones más específicas, puedes llamar al teléfono indicado."
            
            return response
        else:
            return ("📍 **Ubicación del Centro:**\n\n"
                   "**Dirección:** Calle 19 No 258 e/ J e I, Vedado, Plaza de la Revolución, La Habana\n"
                   "**Teléfono:** +53 59518075\n"
                   "**Email:** centrofraybartolomedelascasas@gmail.com\n\n"
                   "🚗 **Cómo llegar:** El centro está ubicado en el Vedado, una zona céntrica y accesible de La Habana. "
                   "Puedes llegar en transporte público o taxi indicando la dirección exacta.")
    
    def _generate_generic_response(self, documents: List[Dict], pregunta: str) -> str:
        """Generate generic response from any documents"""
        best_doc = documents[0]
        text = best_doc.get('text', '').strip()
        
        # Clean and ensure Spanish
        clean_text = self._ensure_spanish_response(text)
        clean_text = self._remove_professor_mentions_improved(clean_text)
        
        if clean_text:
            return self._add_page_reference(clean_text, pregunta)
        else:
            return self._handle_no_results(pregunta)





    def _handle_no_results(self, pregunta: str) -> str:
        """
        Handle case when no relevant documents are found
        
        Args:
            pregunta: User's question
            
        Returns:
            Appropriate response for no results with page references
        """
        logger.info("No relevant documents found")
        
        # Check if we can answer this type of question
        if not self._can_answer_question(pregunta):
            return self._get_restricted_response()
        
        # Provide specific page recommendations based on question content
        pregunta_lower = pregunta.lower()
        
        if any(word in pregunta_lower for word in ['curso', 'estudiar', 'programa', 'carrera']):
            return ("No encontré información específica sobre tu consulta de cursos. "
                   "Te recomiendo visitar la **página Nuestros Cursos** en nuestro sitio web para ver "
                   "toda la información detallada sobre programas disponibles.")
        
        elif any(word in pregunta_lower for word in ['inscripción', 'inscribir', 'matrícula', 'registro', 'registrar', 'crear cuenta', 'login', 'iniciar sesión']):
            return ("📝 **Proceso Completo de Inscripción:**\n\n"
                   "**1️⃣ REGISTRO DE USUARIO (OBLIGATORIO):**\n"
                   "   • Vaya al sitio web del Centro Fray Bartolomé de las Casas\n"
                   "   • Busque el botón 'Registrarse' o 'Crear Cuenta'\n"
                   "   • Complete el formulario con:\n"
                   "     - Nombre de usuario único\n"
                   "     - Contraseña segura\n"
                   "     - Email válido\n"
                   "     - Datos personales\n"
                   "   • Haga clic en 'Registrarse'\n\n"
                   "**2️⃣ INICIAR SESIÓN:**\n"
                   "   • Vaya a la página 'Iniciar Sesión' o 'Login'\n"
                   "   • Ingrese su usuario/email y contraseña\n"
                   "   • Haga clic en 'Iniciar Sesión'\n"
                   "   • Si olvida su contraseña, use '¿Olvidó su contraseña?'\n\n"
                   "**3️⃣ INSCRIPCIÓN A CURSOS:**\n"
                   "   • Con sesión iniciada, vaya a la página Nuestros Cursos\n"
                   "   • Explore los programas disponibles\n"
                   "   • Seleccione el curso de su interés\n"
                   "   • Complete el proceso de matrícula\n\n"
                   "⚠️ **IMPORTANTE:** El registro es GRATUITO y solo toma unos minutos. "
                   "Sin registro e inicio de sesión NO podrá acceder a ningún curso.")
        
        elif any(word in pregunta_lower for word in ['noticia', 'evento', 'actividad', 'nuevo', 'blog']):
            return ("Para las últimas noticias y eventos, te recomiendo visitar el **blog de noticias** "
                   "en nuestro sitio web. Actualmente no hay noticias publicadas, pero se actualiza regularmente.")
        
        elif any(word in pregunta_lower for word in ['contacto', 'teléfono', 'dirección', 'ubicación', 'centro']):
            return ("Para información de contacto y sobre el centro, puedes encontrar los datos "
                   "en la sección de contacto de nuestro sitio web.")
        
        else:
            return self._get_restricted_response()
    
    def get_pipeline_status(self) -> Dict:
        """
        Get status of all pipeline components
        
        Returns:
            Dictionary with component status
        """
        return {
            'intent_classifier': {
                'available': True,
                'threshold': self.intent_classifier.confidence_threshold,
                'intents': self.intent_classifier.get_all_intents()
            },
            'semantic_search': {
                'available': True,
                'index_stats': self.semantic_search.get_index_stats(),
                'model_dimension': self.semantic_search.get_embedding_dimension()
            },
            'mode': 'semantic_search_only',
            'llm_enabled': False,
            'hybrid_mode': False
        }
    
    def validate_question(self, pregunta: str) -> tuple[bool, str]:
        """
        Validate user question before processing
        
        Args:
            pregunta: User's question
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pregunta:
            return False, "La pregunta no puede estar vacía"
        
        pregunta = pregunta.strip()
        
        if len(pregunta) < 3:
            return False, "La pregunta es demasiado corta"
        
        if len(pregunta) > 1000:
            return False, "La pregunta es demasiado larga (máximo 1000 caracteres)"
        
        # Check for suspicious patterns (basic security)
        suspicious_patterns = ['<script', 'javascript:', 'eval(', 'exec(']
        pregunta_lower = pregunta.lower()
        
        for pattern in suspicious_patterns:
            if pattern in pregunta_lower:
                return False, "La pregunta contiene contenido no permitido"
        
        return True, ""
    
    def get_suggested_questions(self) -> List[str]:
        """
        Get a list of suggested questions for users
        
        Returns:
            List of suggested question strings
        """
        return [
            "¿Cuándo empiezan las inscripciones?",
            "¿Qué cursos están disponibles?",
            "¿Cuáles son los requisitos para inscribirme?",
            "¿Dónde puedo pagar la matrícula?",
            "¿Cuál es el horario de clases?",
            "¿Dónde está ubicado el centro?",
            "¿Hay becas disponibles?",
            "¿Qué documentos necesito para inscribirme?"
        ]
    
    def log_interaction(
        self,
        session_id: str,
        pregunta: str,
        respuesta: str,
        documentos: List[Dict],
        intencion: str,
        confianza: float,
        tiempo_respuesta: float
    ):
        """
        Log interaction to database with anonymization
        
        Args:
            session_id: Session identifier
            pregunta: User's question
            respuesta: Generated response
            documentos: Retrieved documents
            intencion: Detected intent
            confianza: Confidence score
            tiempo_respuesta: Response time in seconds
        """
        try:
            # Anonymize personal data in question and response
            pregunta_anonima = ChatInteraction.anonimizar_datos(pregunta or "")
            respuesta_anonima = ChatInteraction.anonimizar_datos(respuesta or "")
            
            # Determine if this should be a FAQ candidate
            es_candidata = self._should_be_faq_candidate(confianza, documentos)
            
            # Create interaction record
            interaction = ChatInteraction.objects.create(
                session_id=session_id,
                pregunta=pregunta_anonima,
                respuesta=respuesta_anonima,
                documentos_recuperados=documentos,
                intencion_detectada=intencion,
                confianza=confianza,
                tiempo_respuesta=tiempo_respuesta,
                es_candidata_faq=es_candidata
            )
            
            logger.debug(f"Interaction logged with ID {interaction.id}")
            
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            # Don't raise exception - logging failure shouldn't break the response
    
    def _should_be_faq_candidate(self, confianza: float, documentos: List[Dict]) -> bool:
        """
        Determine if an interaction should be marked as FAQ candidate
        
        Args:
            confianza: Confidence score
            documentos: Retrieved documents
            
        Returns:
            True if should be FAQ candidate
        """
        # Mark as candidate if:
        # 1. Low confidence (< 0.5)
        # 2. No documents found
        # 3. Low document scores
        
        if confianza < 0.5:
            return True
        
        if not documentos:
            return True
        
        # Check document scores
        if documentos:
            max_score = max(doc.get('score', 0) for doc in documentos)
            if max_score < 0.3:  # Low similarity scores
                return True
        
        return False
    
    def mark_low_confidence_as_candidates(self, threshold: float = 0.5) -> int:
        """
        Mark low-confidence questions as FAQ candidates
        
        Args:
            threshold: Confidence threshold below which to mark as candidates
            
        Returns:
            Number of interactions marked as candidates
        """
        try:
            # Mark interactions with low confidence as FAQ candidates
            updated = ChatInteraction.objects.filter(
                confianza__lt=threshold,
                es_candidata_faq=False
            ).update(es_candidata_faq=True)
            
            # Also mark interactions with negative feedback
            negative_feedback_updated = ChatInteraction.objects.filter(
                fue_util=False,
                es_candidata_faq=False
            ).update(es_candidata_faq=True)
            
            total_updated = updated + negative_feedback_updated
            
            logger.info(f"Marked {total_updated} interactions as FAQ candidates "
                       f"({updated} low confidence, {negative_feedback_updated} negative feedback)")
            
            return total_updated
            
        except Exception as e:
            logger.error(f"Error marking low-confidence questions as candidates: {e}")
            return 0
    
    def update_interaction_feedback(self, interaction_id: int, fue_util: bool) -> bool:
        """
        Update interaction with user feedback and update FAQ success rates
        
        Args:
            interaction_id: ID of the interaction
            fue_util: Whether the response was useful
            
        Returns:
            True if updated successfully
        """
        try:
            interaction = ChatInteraction.objects.get(id=interaction_id)
            interaction.fue_util = fue_util
            interaction.save(update_fields=['fue_util'])
            
            # Update FAQ success rates if FAQs were used
            self._update_faq_success_rates(interaction, fue_util)
            
            # If feedback is negative and confidence was reasonable, mark as FAQ candidate
            if not fue_util and interaction.confianza >= 0.5:
                interaction.es_candidata_faq = True
                interaction.save(update_fields=['es_candidata_faq'])
            
            logger.info(f"Updated interaction {interaction_id} feedback: {fue_util}")
            return True
            
        except ChatInteraction.DoesNotExist:
            logger.error(f"Interaction {interaction_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating interaction feedback: {e}")
            return False
    
    def _update_faq_success_rates(self, interaction: 'ChatInteraction', fue_util: bool):
        """
        Update success rates for FAQs that were used in the interaction
        
        Args:
            interaction: ChatInteraction instance
            fue_util: Whether the response was useful
        """
        try:
            # Get FAQs that were used in this interaction
            documentos = interaction.documentos_recuperados or []
            
            faq_ids = []
            for doc in documentos:
                if doc.get('content_type') == 'chatbot.faq':
                    faq_id = doc.get('object_id')
                    if faq_id and faq_id not in faq_ids:
                        faq_ids.append(faq_id)
            
            # Update success rate for each FAQ
            for faq_id in faq_ids:
                try:
                    faq = FAQ.objects.get(id=faq_id)
                    
                    # Calculate new success rate
                    # Get all feedback for this FAQ
                    faq_interactions = ChatInteraction.objects.filter(
                        documentos_recuperados__contains=[{'object_id': faq_id, 'content_type': 'chatbot.faq'}],
                        fue_util__isnull=False
                    )
                    
                    total_feedback = faq_interactions.count()
                    positive_feedback = faq_interactions.filter(fue_util=True).count()
                    
                    if total_feedback > 0:
                        new_success_rate = positive_feedback / total_feedback
                        faq.tasa_exito = new_success_rate
                        faq.save(update_fields=['tasa_exito'])
                        
                        logger.debug(f"Updated FAQ {faq_id} success rate: {new_success_rate:.2f} ({positive_feedback}/{total_feedback})")
                
                except FAQ.DoesNotExist:
                    logger.warning(f"FAQ {faq_id} not found for success rate update")
                    continue
                except Exception as e:
                    logger.error(f"Error updating FAQ {faq_id} success rate: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error updating FAQ success rates: {e}")
    
    def _track_faq_usage(self, documentos: List[Dict]):
        """
        Track usage of FAQs that were used in the response
        
        Args:
            documentos: List of retrieved documents
        """
        try:
            for doc in documentos:
                # Check if document is from FAQ
                if doc.get('content_type') == 'chatbot.faq':
                    faq_id = doc.get('object_id')
                    if faq_id:
                        self.track_faq_usage(faq_id)
        except Exception as e:
            logger.error(f"Error tracking FAQ usage: {e}")
    
    def track_faq_usage(self, faq_id: int):
        """
        Track usage of a specific FAQ
        
        Args:
            faq_id: ID of the FAQ to track
        """
        try:
            faq = FAQ.objects.get(id=faq_id)
            faq.incrementar_uso()
            logger.debug(f"Tracked usage for FAQ {faq_id}")
        except FAQ.DoesNotExist:
            logger.error(f"FAQ {faq_id} not found for usage tracking")
        except Exception as e:
            logger.error(f"Error tracking FAQ {faq_id} usage: {e}")
    
    def get_interaction_stats(self, days: int = 30) -> Dict:
        """
        Get interaction statistics for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with statistics
        """
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days)
            
            interactions = ChatInteraction.objects.filter(fecha__gte=cutoff_date)
            
            total_interactions = interactions.count()
            
            if total_interactions == 0:
                return {
                    'total_interactions': 0,
                    'avg_confidence': 0,
                    'avg_response_time': 0,
                    'intent_distribution': {},
                    'feedback_stats': {},
                    'faq_candidates': 0
                }
            
            # Calculate averages
            avg_confidence = interactions.aggregate(
                avg=Avg('confianza')
            )['avg'] or 0
            
            avg_response_time = interactions.aggregate(
                avg=Avg('tiempo_respuesta')
            )['avg'] or 0
            
            # Intent distribution
            intent_distribution = dict(
                interactions.values('intencion_detectada')
                .annotate(count=Count('id'))
                .values_list('intencion_detectada', 'count')
            )
            
            # Feedback stats
            feedback_interactions = interactions.exclude(fue_util__isnull=True)
            positive_feedback = feedback_interactions.filter(fue_util=True).count()
            total_feedback = feedback_interactions.count()
            
            feedback_stats = {
                'total_with_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': total_feedback - positive_feedback,
                'feedback_rate': total_feedback / total_interactions if total_interactions > 0 else 0
            }
            
            # FAQ candidates
            faq_candidates = interactions.filter(es_candidata_faq=True).count()
            
            return {
                'total_interactions': total_interactions,
                'avg_confidence': round(avg_confidence, 3),
                'avg_response_time': round(avg_response_time, 3),
                'intent_distribution': intent_distribution,
                'feedback_stats': feedback_stats,
                'faq_candidates': faq_candidates,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting interaction stats: {e}")
            return {
                'error': str(e),
                'total_interactions': 0
            }
    
    def get_unused_faqs(self, days_threshold: int = 90) -> List[Dict]:
        """
        Get FAQs that haven't been used in the specified number of days
        
        Args:
            days_threshold: Number of days to consider as "unused"
            
        Returns:
            List of unused FAQ information
        """
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days_threshold)
            
            # Get FAQs that are either never used or not used recently
            unused_faqs = FAQ.objects.filter(
                Q(ultima_fecha_uso__lt=cutoff_date) | Q(ultima_fecha_uso__isnull=True),
                activa=True
            ).select_related('categoria').order_by('fecha_creacion')
            
            results = []
            for faq in unused_faqs:
                days_since_use = None
                if faq.ultima_fecha_uso:
                    days_since_use = (timezone.now() - faq.ultima_fecha_uso).days
                
                results.append({
                    'id': faq.id,
                    'pregunta': faq.pregunta,
                    'categoria': faq.categoria.nombre,
                    'fecha_creacion': faq.fecha_creacion,
                    'ultima_fecha_uso': faq.ultima_fecha_uso,
                    'days_since_use': days_since_use,
                    'veces_usada': faq.veces_usada,
                    'tasa_exito': faq.tasa_exito
                })
            
            logger.info(f"Found {len(results)} unused FAQs (>{days_threshold} days)")
            return results
            
        except Exception as e:
            logger.error(f"Error getting unused FAQs: {e}")
            return []
    
    def group_similar_questions(self, similarity_threshold: float = 0.8) -> List[Dict]:
        """
        Group similar questions using semantic similarity
        
        Args:
            similarity_threshold: Minimum similarity score to group questions
            
        Returns:
            List of question groups with similarity information
        """
        try:
            # Get FAQ candidate questions
            candidates = ChatInteraction.objects.filter(
                es_candidata_faq=True
            ).values('pregunta').annotate(
                count=Count('id'),
                avg_confidence=Avg('confianza')
            ).order_by('-count')
            
            if not candidates:
                return []
            
            # Convert to list for processing
            questions = list(candidates)
            
            # Generate embeddings for all questions
            question_embeddings = {}
            for question_data in questions:
                question = question_data['pregunta']
                try:
                    embedding = self.semantic_search.generate_embedding(question)
                    question_embeddings[question] = embedding
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for question: {question[:50]}... Error: {e}")
                    continue
            
            # Group similar questions
            groups = []
            processed_questions = set()
            
            for question_data in questions:
                question = question_data['pregunta']
                
                if question in processed_questions or question not in question_embeddings:
                    continue
                
                # Find similar questions
                similar_questions = []
                question_embedding = question_embeddings[question]
                
                for other_question_data in questions:
                    other_question = other_question_data['pregunta']
                    
                    if (other_question == question or 
                        other_question in processed_questions or 
                        other_question not in question_embeddings):
                        continue
                    
                    # Calculate cosine similarity
                    other_embedding = question_embeddings[other_question]
                    similarity = self._calculate_cosine_similarity(question_embedding, other_embedding)
                    
                    if similarity >= similarity_threshold:
                        similar_questions.append({
                            'question': other_question,
                            'similarity': similarity,
                            'count': other_question_data['count'],
                            'avg_confidence': other_question_data['avg_confidence']
                        })
                        processed_questions.add(other_question)
                
                # Create group if we found similar questions or if this is a frequent question
                if similar_questions or question_data['count'] >= 3:
                    groups.append({
                        'main_question': {
                            'question': question,
                            'count': question_data['count'],
                            'avg_confidence': question_data['avg_confidence']
                        },
                        'similar_questions': similar_questions,
                        'total_count': question_data['count'] + sum(sq['count'] for sq in similar_questions),
                        'group_size': len(similar_questions) + 1
                    })
                
                processed_questions.add(question)
            
            # Sort groups by total count (most frequent first)
            groups.sort(key=lambda g: g['total_count'], reverse=True)
            
            logger.info(f"Grouped {len(questions)} questions into {len(groups)} groups")
            return groups
            
        except Exception as e:
            logger.error(f"Error grouping similar questions: {e}")
            return []
    
    def _calculate_cosine_similarity(self, embedding1, embedding2):
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            import numpy as np
            
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _extract_answer_from_faq(self, faq_text: str) -> str:
        """
        Extract only the answer part from FAQ text, removing the question
        
        Args:
            faq_text: Full FAQ text that may include question and answer
            
        Returns:
            Clean answer text
        """
        if not faq_text:
            return ""
        
        # Common patterns to split question from answer
        separators = [
            ' | Respuesta: ',
            ' | Respuesta:',
            '| Respuesta: ',
            '| Respuesta:',
            'Respuesta: ',
            'Respuesta:',
            '\nRespuesta: ',
            '\nRespuesta:'
        ]
        
        # Try to find and extract the answer part
        for separator in separators:
            if separator in faq_text:
                parts = faq_text.split(separator, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        # If no separator found, check if it starts with "Pregunta:"
        if faq_text.startswith('Pregunta:'):
            # Try to find where the answer starts
            lines = faq_text.split('\n')
            answer_lines = []
            found_answer = False
            
            for line in lines:
                if 'Respuesta:' in line:
                    found_answer = True
                    # Add the part after "Respuesta:"
                    if ':' in line:
                        answer_part = line.split(':', 1)[1].strip()
                        if answer_part:
                            answer_lines.append(answer_part)
                elif found_answer:
                    answer_lines.append(line.strip())
            
            if answer_lines:
                return '\n'.join(answer_lines).strip()
        
        # If still no clear answer found, return the original text
        # but try to clean it up
        cleaned = faq_text.strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            'Pregunta: ',
            'P: ',
            'Q: '
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        return cleaned
    
    def _filter_course_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Filter course documents to only include official page content
        
        Args:
            documents: List of documents
            
        Returns:
            Filtered list of documents with only official course info
        """
        filtered = []
        
        for doc in documents:
            text = doc.get('text', '').lower()
            
            # Exclude documents that mention specific professors or students
            exclude_keywords = [
                'profesor:', 'profesora:', 'docente:', 'instructor:',
                'estudiante:', 'alumno:', 'alumna:',
                'mateo vi', 'nombre del profesor', 'nombre del estudiante',
                'mateo', 'profesor mateo'
            ]
            
            # Check if document contains excluded content
            should_exclude = any(keyword in text for keyword in exclude_keywords)
            
            if not should_exclude:
                # Also filter the document text to remove professor info
                doc_copy = doc.copy()
                doc_copy['text'] = self._remove_professor_info(doc.get('text', ''))
                filtered.append(doc_copy)
        
        return filtered
    
    def _remove_professor_info(self, text: str) -> str:
        """
        Remove professor information from course text
        
        Args:
            text: Original course text
            
        Returns:
            Text with professor info removed
        """
        if not text:
            return text
        
        # Split by | and filter out professor-related parts
        parts = text.split('|')
        clean_parts = []
        
        for part in parts:
            part = part.strip()
            part_lower = part.lower()
            
            # Skip parts that mention professors
            skip_patterns = [
                'profesor:', 'profesora:', 'docente:', 'instructor:',
                'mateo vi', 'mateo', 'nombre del profesor'
            ]
            
            should_skip = any(pattern in part_lower for pattern in skip_patterns)
            
            if not should_skip and part:
                clean_parts.append(part)
        
        return ' | '.join(clean_parts) if clean_parts else text
    
    def _extract_course_info(self, course_text: str) -> str:
        """
        Extract clean course information, removing personal details
        
        Args:
            course_text: Raw course text
            
        Returns:
            Clean course information
        """
        if not course_text:
            return ""
        
        # Clean up the text first
        cleaned_text = course_text.strip()
        
        # Remove document references and metadata
        if 'Documento' in cleaned_text:
            parts = cleaned_text.split('Documento')
            cleaned_text = parts[0].strip()
        
        # Split by common separators and clean each part
        parts = cleaned_text.split('|')
        clean_parts = []
        
        for part in parts:
            part = part.strip()
            
            # Skip empty parts or parts with unwanted content
            if not part:
                continue
                
            # Skip parts that contain personal information or metadata
            skip_keywords = [
                'profesor:', 'profesora:', 'docente:', 'instructor:',
                'mateo vi', 'mateo', 'nombre del profesor', 'pregunta:', 'nicamente:',
                'cantidad de clases:', 'ao académico:', 'activo'
            ]
            
            part_lower = part.lower()
            should_skip = any(keyword in part_lower for keyword in skip_keywords)
            
            if not should_skip and part:
                # Clean up the part
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Only include relevant course information
                    relevant_keys = [
                        'curso', 'área', 'tipo', 'descripción', 
                        'fecha de inicio', 'duración', 'modalidad',
                        'requisitos', 'costo', 'horario', 'estado'
                    ]
                    
                    if any(rel_key in key.lower() for rel_key in relevant_keys) and value:
                        clean_parts.append(f"{key}: {value}")
                else:
                    # For parts without colons, check if they contain useful course info
                    useful_patterns = [
                        'curso de', 'idiomas', 'diseño', 'teología',
                        'inscripción', 'disponible', 'etapa'
                    ]
                    
                    if any(pattern in part_lower for pattern in useful_patterns):
                        clean_parts.append(part)
        
        if clean_parts:
            return ' | '.join(clean_parts)
        else:
            # If no clean parts found, try to extract basic course name
            if 'curso' in cleaned_text.lower():
                lines = cleaned_text.split('\n')
                for line in lines:
                    if 'curso' in line.lower() and ':' in line:
                        return line.strip()
            
            return "Información de curso disponible"
    
    def _extract_clean_course_info(self, course_text: str) -> str:
        """
        Extract clean course information with aggressive filtering of personal data
        
        Args:
            course_text: Raw course text
            
        Returns:
            Clean course information without personal details
        """
        if not course_text:
            return ""
        
        # First, remove any document references
        text = course_text.strip()
        if 'Documento' in text:
            parts = text.split('Documento')
            text = parts[0].strip()
        
        # Split by | and process each part
        parts = text.split('|')
        course_name = ""
        course_area = ""
        course_status = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            part_lower = part.lower()
            
            # Skip any part that mentions professors or personal info
            if any(skip in part_lower for skip in ['profesor', 'mateo', 'docente', 'instructor']):
                continue
                
            # Extract course name
            if 'curso:' in part_lower or part_lower.startswith('curso'):
                course_name = part.replace('Curso:', '').replace('curso:', '').strip()
            
            # Extract area
            elif 'área:' in part_lower or 'area:' in part_lower:
                course_area = part.replace('Área:', '').replace('área:', '').replace('Area:', '').replace('area:', '').strip()
            
            # Extract status
            elif 'estado:' in part_lower or 'etapa' in part_lower:
                if 'inscripción' in part_lower:
                    course_status = "En etapa de inscripción"
                else:
                    course_status = part.replace('Estado:', '').replace('estado:', '').strip()
        
        # Build clean course description
        if course_name:
            result = course_name
            if course_area:
                result += f" (Área: {course_area})"
            if course_status:
                result += f" - {course_status}"
            return result
        
        # If no structured info found, try to extract basic course name
        for part in parts:
            part = part.strip()
            if 'curso' in part.lower() and not any(skip in part.lower() for skip in ['profesor', 'mateo', 'docente']):
                return part
        
        return ""
        if 'Documento' in text:
            parts = text.split('Documento')
            text = parts[0].strip()
        
        # Initialize course info
        course_info = {
            'name': '',
            'area': '',
            'status': 'Disponible'
        }
        
        # Split by | and process each part
        parts = text.split('|')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            part_lower = part.lower()
            
            # Skip any internal information
            skip_keywords = [
                'profesor', 'mateo', 'docente', 'instructor',
                'cantidad de clases', 'ao académico', 'activo',
                'pregunta:', 'nicamente:', 'documento'
            ]
            
            if any(skip in part_lower for skip in skip_keywords):
                continue
            
            # Extract course name
            if 'curso:' in part_lower:
                course_name = part.replace('Curso:', '').replace('curso:', '').strip()
                if course_name:
                    course_info['name'] = course_name
            
            # Extract area
            elif 'área:' in part_lower or 'area:' in part_lower:
                area = part.replace('Área:', '').replace('área:', '').replace('Area:', '').replace('area:', '').strip()
                if area:
                    course_info['area'] = area
            
            # Extract status
            elif 'estado:' in part_lower or 'etapa' in part_lower:
                if 'inscripción' in part_lower:
                    course_info['status'] = 'En etapa de inscripción'
                elif 'disponible' in part_lower:
                    course_info['status'] = 'Disponible'
        
        # If no structured name found, try to extract from unstructured text
        if not course_info['name']:
            for part in parts:
                part = part.strip()
                if 'curso' in part.lower() and not any(skip in part.lower() for skip in ['profesor', 'mateo', 'docente']):
                    # Clean up the course name
                    name = part.replace('Curso:', '').replace('curso:', '').replace('Curso de', '').replace('curso de', '').strip()
                    if name and len(name) > 2:
                        course_info['name'] = name
                        break
        
        # Return only if we have a valid course name
        if course_info['name']:
            return course_info
        else:
            return {}
    
    def _add_page_reference(self, answer: str, pregunta: str) -> str:
        """
        Add appropriate page reference to answers based on question content
        
        Args:
            answer: Original answer
            pregunta: User's question
            
        Returns:
            Enhanced answer with page reference
        """
        if not answer:
            return answer
        
        pregunta_lower = pregunta.lower()
        
        # Add specific page references based on question topic
        if any(word in pregunta_lower for word in ['curso', 'estudiar', 'programa', 'carrera', 'idioma', 'diseño', 'teología']):
            if 'página Nuestros Cursos' not in answer and 'sitio web' not in answer:
                answer += "\n\n📚 Para información completa y actualizada, visita la **página Nuestros Cursos** en nuestro sitio web."
        
        elif any(word in pregunta_lower for word in ['inscripción', 'inscribir', 'matrícula', 'registro', 'requisito']):
            if 'página Nuestros Cursos' not in answer and 'sitio web' not in answer:
                answer += "\n\n📝 Para el proceso completo de inscripción y fechas de inscripción, visita la **página Nuestros Cursos** en nuestro sitio web."
        
        elif any(word in pregunta_lower for word in ['horario', 'hora', 'cuándo', 'fecha']):
            if 'sitio web' not in answer:
                answer += "\n\n🕒 Para horarios y fechas de inscripción actualizadas, consulta la **página Nuestros Cursos** en nuestro sitio web."
        
        elif any(word in pregunta_lower for word in ['costo', 'precio', 'pago', 'matrícula']):
            if 'sitio web' not in answer:
                answer += "\n\n💰 Para información de costos actualizada, consulta nuestro sitio web o contacta directamente al centro."
        
        elif any(word in pregunta_lower for word in ['contacto', 'teléfono', 'dirección', 'ubicación']):
            if 'página de Contacto' not in answer and 'sitio web' not in answer:
                answer += "\n\n📞 Para información de contacto completa, visita la **página de Contacto** en nuestro sitio web."
        
        return answer
    
    def _can_answer_question(self, pregunta: str) -> bool:
        """
        Validate if this is a question we can answer based on our restricted scope
        
        Args:
            pregunta: User's question
            
        Returns:
            True if we can answer, False otherwise
        """
        pregunta_lower = pregunta.lower()
        
        # Topics we CAN answer about
        allowed_topics = {
            # Cursos
            'cursos': ['curso', 'estudiar', 'programa', 'carrera', 'idioma', 'inglés', 'alemán', 'italiano', 'diseño', 'teología'],
            # Noticias
            'noticias': ['noticia', 'evento', 'actividad', 'nuevo', 'blog'],
            # Centro (información del footer)
            'centro': ['centro', 'institución', 'organización', 'misión', 'visión', 'historia', 'fray bartolomé', 'contacto', 'dirección', 'teléfono', 'ubicación'],
            # Inscripciones (relacionado con cursos)
            'inscripciones': ['inscripción', 'inscribir', 'matrícula', 'registro', 'requisito', 'documento']
        }
        
        # Check if question is about allowed topics
        for topic, keywords in allowed_topics.items():
            if any(keyword in pregunta_lower for keyword in keywords):
                return True
        
        # Questions we explicitly CANNOT answer
        forbidden_topics = [
            'profesor', 'docente', 'maestro', 'instructor',
            'estudiante', 'alumno', 'compañero',
            'calificación', 'nota', 'examen', 'tarea',
            'horario específico', 'calendario académico',
            'precio exacto', 'costo específico',
            'personal', 'empleado', 'staff'
        ]
        
        # Check if question contains forbidden topics
        if any(forbidden in pregunta_lower for forbidden in forbidden_topics):
            return False
        
        # If it's a very general question, we can try to answer
        general_questions = ['qué', 'cómo', 'cuándo', 'dónde', 'por qué', 'cuál']
        if any(q in pregunta_lower for q in general_questions):
            return True
        
        return False
    
    def _get_restricted_response(self) -> str:
        """
        Get standard response for questions outside our scope
        
        Returns:
            Standard restricted response
        """
        return ("Lo siento, no puedo proporcionar esa información en este momento. "
               "Puedo ayudarte con información sobre:\n\n"
               "• **Cursos** disponibles en el centro\n"
               "• **Noticias y eventos** del blog\n"
               "• **Información general** del Centro Fray Bartolomé de las Casas\n\n"
               "Para otras consultas, te recomiendo contactar directamente al centro.")
    
    def _remove_all_professor_mentions(self, text: str) -> str:
        """
        Remove all mentions of professors and personal information
        
        Args:
            text: Original text
            
        Returns:
            Text with professor mentions removed
        """
        if not text:
            return text
        
        # Patterns to remove
        remove_patterns = [
            r'profesor[^|]*\|?',
            r'profesora[^|]*\|?',
            r'docente[^|]*\|?',
            r'instructor[^|]*\|?',
            r'mateo[^|]*\|?',
            r'nombre del profesor[^|]*\|?',
            r'\|\s*profesor[^|]*',
            r'\|\s*profesora[^|]*',
            r'\|\s*docente[^|]*',
            r'\|\s*instructor[^|]*',
            r'\|\s*mateo[^|]*'
        ]
        
        import re
        
        cleaned_text = text
        for pattern in remove_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up extra pipes and spaces
        cleaned_text = re.sub(r'\|\s*\|', '|', cleaned_text)
        cleaned_text = re.sub(r'^\s*\|\s*', '', cleaned_text)
        cleaned_text = re.sub(r'\s*\|\s*$', '', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    def _remove_professor_mentions_improved(self, text: str) -> str:
        """
        Improved method to remove all mentions of professors and personal information
        
        Args:
            text: Original text
            
        Returns:
            Text with professor mentions completely removed
        """
        if not text:
            return text
        
        import re
        
        # More comprehensive patterns to remove professor information
        remove_patterns = [
            # Direct professor mentions with colons
            r'profesor:\s*[^|]*\|?',
            r'profesora:\s*[^|]*\|?',
            r'docente:\s*[^|]*\|?',
            r'instructor:\s*[^|]*\|?',
            r'maestro:\s*[^|]*\|?',
            r'maestra:\s*[^|]*\|?',
            
            # Specific names that are professors
            r'mateo\s+vi[^|]*\|?',
            r'mateo[^|]*\|?',
            
            # Professor mentions without colons
            r'profesor[^|]*\|?',
            r'profesora[^|]*\|?',
            r'docente[^|]*\|?',
            r'instructor[^|]*\|?',
            
            # Pipe-separated professor information
            r'\|\s*profesor:\s*[^|]*',
            r'\|\s*profesora:\s*[^|]*',
            r'\|\s*docente:\s*[^|]*',
            r'\|\s*instructor:\s*[^|]*',
            r'\|\s*maestro:\s*[^|]*',
            r'\|\s*maestra:\s*[^|]*',
            
            # Any pipe section containing professor names
            r'\|\s*[^|]*mateo[^|]*',
            r'\|\s*[^|]*profesor[^|]*',
            r'\|\s*[^|]*profesora[^|]*',
            r'\|\s*[^|]*docente[^|]*',
            r'\|\s*[^|]*instructor[^|]*',
            
            # Lines or sections starting with professor info
            r'^profesor[^|]*\|?',
            r'^profesora[^|]*\|?',
            r'^docente[^|]*\|?',
            r'^instructor[^|]*\|?',
            
            # General professor-related phrases
            r'nombre del profesor[^|]*\|?',
            r'impartido por[^|]*\|?',
            r'a cargo de[^|]*\|?'
        ]
        
        cleaned_text = text
        
        # Apply all removal patterns
        for pattern in remove_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up formatting issues
        cleaned_text = re.sub(r'\|\s*\|', '|', cleaned_text)  # Remove double pipes
        cleaned_text = re.sub(r'^\s*\|\s*', '', cleaned_text)  # Remove leading pipes
        cleaned_text = re.sub(r'\s*\|\s*$', '', cleaned_text)  # Remove trailing pipes
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text)  # Remove empty lines
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize spaces
        
        # Final cleanup: remove any remaining isolated professor names
        isolated_names = ['mateo', 'mateo vi']
        for name in isolated_names:
            cleaned_text = re.sub(rf'\b{re.escape(name)}\b', '', cleaned_text, flags=re.IGNORECASE)
        
        # Final space cleanup
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    def _remove_professor_mentions_selective(self, text: str) -> str:
        """
        More selective professor removal that preserves course information
        """
        if not text:
            return text
        
        import re
        
        # Split by common separators to work with chunks
        chunks = []
        
        # Split by pipes first
        if '|' in text:
            parts = text.split('|')
        else:
            # Split by common patterns if no pipes
            parts = re.split(r'(?=Curso|Estado|Fecha|Diplomado)', text)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Skip parts that are primarily about professors
            part_lower = part.lower()
            if any(prof_word in part_lower for prof_word in ['profesor:', 'profesora:', 'docente:', 'instructor:']):
                # Skip this entire part
                continue
            
            # Remove isolated professor names
            part = re.sub(r'\bmateo\s+vi\b', '', part, flags=re.IGNORECASE)
            part = re.sub(r'\bmateo\b', '', part, flags=re.IGNORECASE)
            
            # Clean up and add if it has useful content
            part = part.strip()
            if part and len(part) > 3:
                chunks.append(part)
        
        # Reconstruct the text
        if chunks:
            result = ' | '.join(chunks)
            # Final cleanup
            result = re.sub(r'\s+', ' ', result)
            result = re.sub(r'\|\s*\|', '|', result)
            return result.strip()
        
        return text
    
    def _create_inscription_time_response(self, course_docs: List[Dict], pregunta: str) -> str:
        """
        Create a proper response for inscription time queries
        """
        if not course_docs:
            return ("Para información sobre fechas de inscripción, visita la **página Nuestros Cursos** "
                   "donde encontrarás toda la información actualizada.")
        
        # Extract course information from documents - prefer active inscriptions
        course_info = ""
        fallback_info = ""
        
        for doc in course_docs[:3]:  # Check top 3 documents
            text = doc.get('text', '').strip()
            if 'italiano' in text.lower() and ('fecha' in text.lower() or 'inscripción' in text.lower()):
                # Prefer documents that show active inscriptions (not terminated)
                if 'en etapa de inscripción' in text.lower() and 'terminado' not in text.lower():
                    course_info = text
                    break
                elif not fallback_info:  # Store as fallback
                    fallback_info = text
        
        # Use fallback if no active inscription found
        if not course_info:
            course_info = fallback_info
        
        if not course_info:
            course_info = course_docs[0].get('text', '')
        
        # Clean the course info
        cleaned_info = self._remove_professor_mentions_selective(course_info)
        
        # Extract key information
        course_name = ""
        state = ""
        deadline = ""
        start_date = ""
        
        # Extract course name
        if 'curso de italiano' in cleaned_info.lower():
            course_name = "Curso de Italiano"
        elif 'diplomado de italiano' in cleaned_info.lower():
            course_name = "Diplomado de Italiano"
        elif 'italiano' in cleaned_info.lower():
            course_name = "Curso de Italiano"
        else:
            course_name = "Curso solicitado"
        
        # Extract state
        if 'en etapa de inscripción' in cleaned_info.lower():
            state = "En etapa de inscripción"
        elif 'disponible' in cleaned_info.lower():
            state = "Disponible"
        elif 'abierta' in cleaned_info.lower():
            state = "Inscripciones abiertas"
        
        # Extract dates - handle multiple formats
        import re
        
        # Look for YYYY-MM-DD format first
        dates_iso = re.findall(r'(\d{4}-\d{2}-\d{2})', cleaned_info)
        
        # Look for "DD de Month de YYYY" format
        dates_spanish = re.findall(r'(\d{1,2} de \w+ de \d{4})', cleaned_info)
        
        # Extract specific deadline and start dates from text
        deadline = ""
        start_date = ""
        
        # Look for deadline specifically
        deadline_match = re.search(r'Fecha límite de inscripción:\s*([^|]+)', cleaned_info)
        if deadline_match:
            deadline = deadline_match.group(1).strip()
        
        # Look for start date specifically
        start_match = re.search(r'Fecha de inicio:\s*([^|]+)', cleaned_info)
        if start_match:
            start_date = start_match.group(1).strip()
        
        # If no specific matches, use the found dates
        if not deadline and dates_iso:
            deadline = dates_iso[0]
        elif not deadline and dates_spanish:
            deadline = dates_spanish[0]
        
        if not start_date and len(dates_iso) >= 2:
            start_date = dates_iso[1]
        elif not start_date and len(dates_spanish) >= 2:
            start_date = dates_spanish[1]
        
        # Build response for time remaining query
        response = f"⏰ **Información de Inscripción - {course_name}:**\n\n"
        
        if state:
            response += f"📊 **Estado actual:** {state}\n"
        
        if deadline:
            response += f"📅 **Fecha límite de inscripción:** {deadline}\n"
            
            # Calculate time remaining
            try:
                from datetime import datetime
                
                # Try to parse different date formats
                deadline_date = None
                
                # Try ISO format first (YYYY-MM-DD)
                try:
                    deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
                except:
                    pass
                
                # Try Spanish format (DD de Month de YYYY)
                if not deadline_date:
                    try:
                        # Convert Spanish month names to English
                        spanish_months = {
                            'enero': 'January', 'febrero': 'February', 'marzo': 'March',
                            'abril': 'April', 'mayo': 'May', 'junio': 'June',
                            'julio': 'July', 'agosto': 'August', 'septiembre': 'September',
                            'octubre': 'October', 'noviembre': 'November', 'diciembre': 'December',
                            'december': 'December'  # Handle English month names too
                        }
                        
                        deadline_lower = deadline.lower()
                        for spanish, english in spanish_months.items():
                            if spanish in deadline_lower:
                                english_date = deadline_lower.replace(spanish, english)
                                # Parse format like "16 de December de 2025"
                                deadline_date = datetime.strptime(english_date, '%d de %B de %Y')
                                break
                    except:
                        pass
                
                if deadline_date:
                    today = datetime.now()
                    days_remaining = (deadline_date - today).days
                    
                    if days_remaining > 0:
                        response += f"⏳ **Tiempo restante:** {days_remaining} días\n"
                    elif days_remaining == 0:
                        response += f"⚠️ **¡Último día para inscribirse!**\n"
                    else:
                        response += f"❌ **Fecha límite vencida** (hace {abs(days_remaining)} días)\n"
                else:
                    response += f"⏳ **Revisa la fecha límite:** {deadline}\n"
            except Exception as e:
                response += f"⏳ **Revisa la fecha límite:** {deadline}\n"
        
        if start_date:
            response += f"🚀 **Fecha de inicio del curso:** {start_date}\n"
        
        response += f"\n📝 **Para inscribirte:**\n"
        response += f"1. **Regístrate** en el sitio web del centro\n"
        response += f"2. **Inicia sesión** con tus credenciales\n"
        response += f"3. Ve a la **página Nuestros Cursos**\n"
        response += f"4. Busca el {course_name} y completa tu inscripción\n"
        response += f"\n💡 **Importante:** Sin registro no podrás inscribirte."
        
        return response
    
    def _is_site_search_query(self, pregunta: str) -> bool:
        """
        Determine if this is a general site search query
        
        Args:
            pregunta: User's question
            
        Returns:
            True if this appears to be a site search query
        """
        pregunta_lower = pregunta.lower()
        
        # Keywords that indicate a search query
        search_indicators = [
            'buscar', 'busco', 'encontrar', 'información sobre',
            'qué hay sobre', 'que hay sobre', 'mostrar', 'ver',
            'contenido sobre', 'datos sobre', 'detalles sobre'
        ]
        
        # Check if it's a search-like query
        is_search = any(indicator in pregunta_lower for indicator in search_indicators)
        
        # Also consider short queries (1-3 words) as potential searches
        words = pregunta.strip().split()
        is_short_query = len(words) <= 3 and len(pregunta.strip()) > 2
        
        return is_search or is_short_query
    
    def _generate_site_search_response(self, documents: List[Dict], pregunta: str) -> str:
        """
        Generate a site search response showing relevant content
        
        Args:
            documents: List of relevant documents
            pregunta: User's search query
            
        Returns:
            Search results response
        """
        if not documents:
            return self._handle_no_results(pregunta)
        
        # Group documents by type
        results_by_type = {
            'cursos': [],
            'blog': [],
            'contacto': [],
            'inscripciones': [],
            'general': []
        }
        
        for doc in documents[:10]:  # Limit to top 10 results
            categoria = doc.get('categoria', 'general')
            content_type = doc.get('content_type', '')
            text = doc.get('text', '').strip()
            
            if categoria in results_by_type:
                results_by_type[categoria].append({
                    'text': text[:200] + '...' if len(text) > 200 else text,
                    'content_type': content_type,
                    'score': doc.get('score', 0)
                })
            else:
                results_by_type['general'].append({
                    'text': text[:200] + '...' if len(text) > 200 else text,
                    'content_type': content_type,
                    'score': doc.get('score', 0)
                })
        
        # Build search results response
        response = f"🔍 **Resultados de búsqueda para:** \"{pregunta}\"\n\n"
        
        # Show results by category
        if results_by_type['cursos']:
            response += "📚 **Cursos:**\n"
            for i, result in enumerate(results_by_type['cursos'][:3], 1):
                response += f"{i}. {result['text']}\n"
            response += "\n"
        
        if results_by_type['inscripciones']:
            response += "📝 **Inscripciones:**\n"
            for i, result in enumerate(results_by_type['inscripciones'][:3], 1):
                response += f"{i}. {result['text']}\n"
            response += "\n"
        
        if results_by_type['blog']:
            response += "📰 **Noticias:**\n"
            for i, result in enumerate(results_by_type['blog'][:2], 1):
                response += f"{i}. {result['text']}\n"
            response += "\n"
        
        if results_by_type['contacto']:
            response += "📞 **Contacto:**\n"
            for i, result in enumerate(results_by_type['contacto'][:2], 1):
                response += f"{i}. {result['text']}\n"
            response += "\n"
        
        if results_by_type['general']:
            response += "ℹ️ **Información General:**\n"
            for i, result in enumerate(results_by_type['general'][:2], 1):
                response += f"{i}. {result['text']}\n"
            response += "\n"
        
        # Add navigation help
        response += "💡 **Para más información específica:**\n"
        response += "• Visita la **página Nuestros Cursos** para detalles de programas\n"
        response += "• Consulta la sección de **Contacto** para ubicación y datos\n"
        response += "• Revisa el **blog de noticias** para eventos y actividades"
        
        return response
    
    def _generate_restricted_course_response(self, documents: List[Dict], pregunta: str) -> str:
        """
        Generate course response with strict filtering - only official page info
        
        Args:
            documents: List of course documents
            pregunta: User's question
            
        Returns:
            Restricted course response
        """
        # Extract only basic course information
        courses = []
        
        for doc in documents:
            course_name = self._extract_basic_course_name(doc.get('text', ''))
            if course_name and course_name not in courses:
                courses.append(course_name)
        
        if not courses:
            return ("La información sobre nuestros cursos está disponible en la **página Nuestros Cursos** "
                   "de nuestro sitio web, donde encontrarás todos los detalles actualizados.")
        
        # Group courses by type
        idiomas = [c for c in courses if any(lang in c.lower() for lang in ['inglés', 'alemán', 'italiano', 'francés', 'idioma'])]
        diseño = [c for c in courses if 'diseño' in c.lower()]
        teologia = [c for c in courses if 'teología' in c.lower()]
        otros = [c for c in courses if c not in idiomas + diseño + teologia]
        
        response = "**Cursos disponibles:**\n\n"
        
        if idiomas:
            response += "**Idiomas:**\n"
            for curso in idiomas:
                response += f"• {curso}\n"
            response += "\n"
        
        if diseño:
            response += "**Diseño:**\n"
            for curso in diseño:
                response += f"• {curso}\n"
            response += "\n"
        
        if teologia:
            response += "**Teología:**\n"
            for curso in teologia:
                response += f"• {curso}\n"
            response += "\n"
        
        if otros:
            response += "**Otros:**\n"
            for curso in otros:
                response += f"• {curso}\n"
            response += "\n"
        
        response += ("📚 **Para información completa sobre horarios, requisitos, costos y proceso de inscripción, "
                    "visita la página Nuestros Cursos en nuestro sitio web.**")
        
        return response
    
    def _map_intent_to_category(self, intent: str) -> str:
        """
        Map intent classifier categories to database categories
        
        Args:
            intent: Intent from classifier
            
        Returns:
            Mapped category for database search
        """
        # Mapping from intent classifier to database categories
        intent_to_category_map = {
            'cursos': 'cursos',
            'inscripciones': 'inscripciones',  # Registration and inscription info
            'pagos': 'cursos',  # Payment info is usually in course docs
            'ubicaciones': 'contacto',  # Location info is in contact docs
            'requisitos': 'inscripciones',  # Requirements are in inscription docs
            'eventos': 'blog',  # Events and news in blog category
            'noticias': 'blog',  # News in blog category
            'horarios': 'cursos',  # Schedule info in course docs
            'registro': 'inscripciones',  # Registration process
            'login': 'inscripciones',  # Login process
            'acceso': 'inscripciones'  # Access and authentication
        }
        
        return intent_to_category_map.get(intent, intent)
    
    def _extract_basic_course_name(self, text: str) -> str:
        """
        Extract only the basic course name, nothing else
        
        Args:
            text: Course text
            
        Returns:
            Clean course name or empty string
        """
        if not text:
            return ""
        
        # Remove all professor and internal information first
        cleaned = self._remove_professor_mentions_improved(text)
        
        # Look for course name patterns
        import re
        
        # Pattern 1: "Curso: Name"
        match = re.search(r'curso:\s*([^|]+)', cleaned, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name and len(name) > 2:
                return name
        
        # Pattern 2: "Curso de Name"
        match = re.search(r'curso\s+de\s+([^|]+)', cleaned, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name and len(name) > 2:
                return name
        
        # Pattern 3: Just "Name" if it contains course-related words
        parts = cleaned.split('|')
        for part in parts:
            part = part.strip()
            if any(word in part.lower() for word in ['inglés', 'alemán', 'italiano', 'diseño', 'teología']) and len(part) < 50:
                return part
        
        return ""
    
    def _format_area_response(self, area_name: str, courses: List[Dict]) -> str:
        """
        Format response for a specific course area
        
        Args:
            area_name: Name of the course area
            courses: List of courses in this area
            
        Returns:
            Formatted response for the area
        """
        if not courses:
            return (f"No encontré cursos específicos de {area_name} en este momento. "
                   f"Te recomiendo visitar la **página Nuestros Cursos** en nuestro sitio web "
                   f"para ver toda la información actualizada.")
        
        response = f"**Cursos de {area_name}:**\n\n"
        
        for course in courses:
            status = course.get('status', 'Disponible')
            response += f"• {course['name']} - {status}\n"
        
        response += (f"\n📚 **Para información completa sobre horarios, requisitos y proceso de inscripción "
                    f"de estos cursos de {area_name}, visita la página Nuestros Cursos en nuestro sitio web.**")
        
        return response
    
    def _format_all_courses_response(self, courses_by_area: Dict[str, List[Dict]]) -> str:
        """
        Format response showing all available courses
        
        Args:
            courses_by_area: Dictionary of courses organized by area
            
        Returns:
            Formatted response with all courses
        """
        response = "**Cursos disponibles en el Centro Fray Bartolomé de las Casas:**\n\n"
        
        # Add courses by category
        for area, courses in courses_by_area.items():
            if courses:
                response += f"**{area}:**\n"
                for course in courses:
                    status = course.get('status', 'Disponible')
                    response += f"• {course['name']} - {status}\n"
                response += "\n"
        
        # Add specific page reference
        if any(courses for courses in courses_by_area.values()):
            response += "📚 **Para información completa y detallada sobre cada curso, visita nuestra página Nuestros Cursos en el sitio web.**\n\n"
            response += "📞 Para inscripciones y consultas específicas, contacta al Centro Fray Bartolomé de las Casas."
        else:
            response = "La información completa sobre nuestros cursos está disponible en la página Nuestros Cursos de nuestro sitio web.\n\n"
            response += "Para más detalles sobre programas, horarios, costos y requisitos, te recomendamos visitar la sección de Cursos en nuestro sitio."
        
        return response
    
    def _filter_spanish_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Filter documents to only include Spanish content
        
        Args:
            documents: List of documents to filter
            
        Returns:
            List of documents with Spanish content only
        """
        spanish_documents = []
        
        for doc in documents:
            text = doc.get('text', '').strip()
            if self._is_spanish_content(text):
                spanish_documents.append(doc)
        
        return spanish_documents
    
    def _is_spanish_content(self, text: str) -> bool:
        """
        Check if text content is in Spanish
        
        Args:
            text: Text to check
            
        Returns:
            True if content appears to be in Spanish
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Common English phrases that indicate English content
        english_indicators = [
            'what is the', 'when is the', 'where is the', 'how to',
            'contact the event organizer', 'contact our secretariat',
            'the event is open to all ages', 'for details',
            'date:', 'time:', 'location:', 'contact:',
            'event organizer', 'secretariat for details'
        ]
        
        # If text contains multiple English indicators, it's likely English
        english_count = sum(1 for indicator in english_indicators if indicator in text_lower)
        if english_count >= 2:
            return False
        
        # Spanish indicators
        spanish_indicators = [
            'curso', 'inscripción', 'matrícula', 'centro', 'fray bartolomé',
            'información', 'disponible', 'requisitos', 'horario', 'fecha',
            'contacto', 'teléfono', 'dirección', 'área', 'diseño', 'teología',
            'idiomas', 'inglés', 'alemán', 'italiano', 'francés'
        ]
        
        # Count Spanish indicators
        spanish_count = sum(1 for indicator in spanish_indicators if indicator in text_lower)
        
        # If we have Spanish indicators and no strong English indicators, it's Spanish
        return spanish_count > 0
    
    def _ensure_spanish_response(self, text: str) -> str:
        """
        Ensure response is in Spanish, translate common English phrases
        
        Args:
            text: Original text
            
        Returns:
            Text with English phrases translated to Spanish
        """
        if not text:
            return text
        
        # Common English to Spanish translations
        translations = {
            'Date:': 'Fecha:',
            'Time:': 'Hora:',
            'Location:': 'Ubicación:',
            'Contact:': 'Contacto:',
            'What is the date in which the event is held?': '¿Cuál es la fecha del evento?',
            'The event is open to all ages': 'El evento está abierto para todas las edades',
            'Contact the event organizer': 'Contacta al organizador del evento',
            'Contact our secretariat for details': 'Contacta nuestra secretaría para más detalles',
            'for details': 'para más detalles',
            'event organizer': 'organizador del evento',
            'secretariat': 'secretaría'
        }
        
        # Apply translations
        translated_text = text
        for english, spanish in translations.items():
            translated_text = translated_text.replace(english, spanish)
        
        return translated_text
    
    def _handle_no_spanish_content(self, pregunta: str) -> str:
        """
        Handle case when no Spanish content is found
        
        Args:
            pregunta: User's question
            
        Returns:
            Spanish response directing to courses page
        """
        pregunta_lower = pregunta.lower()
        
        if any(word in pregunta_lower for word in ['curso', 'estudiar', 'programa', 'carrera', 'inscripción']):
            return ("La información sobre cursos, fechas de inscripción y requisitos está disponible "
                   "en la **página Nuestros Cursos** de nuestro sitio web. Allí encontrarás todos los "
                   "detalles actualizados sobre programas, horarios y proceso de inscripción.")
        
        elif any(word in pregunta_lower for word in ['evento', 'actividad', 'fecha']):
            return ("Para información sobre eventos y actividades, te recomiendo visitar la "
                   "**página Nuestros Cursos** donde encontrarás las fechas de inscripción y detalles "
                   "de todos nuestros programas.")
        
        else:
            return ("Para obtener información detallada y actualizada, te recomiendo visitar "
                   "la **página Nuestros Cursos** en nuestro sitio web donde encontrarás toda la "
                   "información disponible sobre el Centro Fray Bartolomé de las Casas.")
    
    def _get_simple_course_response(self, pregunta: str) -> str:
        """
        Get simple, direct response for course-related questions
        
        Args:
            pregunta: User's question
            
        Returns:
            Simple response directing to courses page
        """
        pregunta_lower = pregunta.lower()
        
        if any(word in pregunta_lower for word in ['inscripción', 'inscribir', 'matrícula', 'registro']):
            return ("📝 **Para información sobre inscripciones y fechas de inscripción**, "
                   "visita la **página Nuestros Cursos** en nuestro sitio web donde encontrarás "
                   "todos los detalles actualizados.")
        
        elif any(word in pregunta_lower for word in ['horario', 'hora', 'cuándo', 'fecha']):
            return ("🕒 **Para horarios y fechas de inscripción**, "
                   "visita la **página Nuestros Cursos** en nuestro sitio web donde está "
                   "toda la información actualizada.")
        
        elif any(word in pregunta_lower for word in ['costo', 'precio', 'pago', 'matrícula']):
            return ("💰 **Para información sobre costos y pagos**, "
                   "visita la **página Nuestros Cursos** en nuestro sitio web o "
                   "contacta directamente al centro.")
        
        elif any(word in pregunta_lower for word in ['idioma', 'inglés', 'alemán', 'italiano', 'francés']):
            return ("🌍 **Para información sobre cursos de idiomas**, "
                   "visita la **página Nuestros Cursos** en nuestro sitio web donde "
                   "encontrarás todos los programas disponibles.")
        
        elif any(word in pregunta_lower for word in ['diseño']):
            return ("🎨 **Para información sobre cursos de diseño**, "
                   "visita la **página Nuestros Cursos** en nuestro sitio web donde "
                   "encontrarás todos los detalles del programa.")
        
        elif any(word in pregunta_lower for word in ['teología']):
            return ("📖 **Para información sobre cursos de teología**, "
                   "visita la **página Nuestros Cursos** en nuestro sitio web donde "
                   "encontrarás todos los detalles del programa.")
        
        else:
            return ("📚 **Para información completa sobre cursos**, "
                   "visita la **página Nuestros Cursos** en nuestro sitio web donde "
                   "encontrarás programas, horarios, costos, fechas de inscripción y requisitos.")