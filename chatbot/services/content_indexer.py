"""
Content Indexer Service
Indexes content from courses, blog posts, and footer for semantic search
"""
import logging
from typing import List, Dict, Optional
from django.contrib.contenttypes.models import ContentType

from .semantic_search import SemanticSearchService
from .text_chunker import TextChunker
from ..models import DocumentEmbedding
from principal.models import Curso
from blog.models import Noticia

logger = logging.getLogger(__name__)


class ContentIndexerService:
    """
    Service for indexing website content (courses, blog, footer) for semantic search
    """
    
    def __init__(self):
        """Initialize the content indexer service"""
        self.semantic_search = SemanticSearchService()
        self.text_chunker = TextChunker()
    
    def index_all_content(self):
        """
        Index all website content: courses, blog posts, and footer
        """
        logger.info("Starting full content indexing...")
        
        total_chunks = 0
        
        # Index courses
        course_chunks = self.index_courses()
        total_chunks += course_chunks
        logger.info(f"Indexed {course_chunks} course chunks")
        
        # Index blog posts
        blog_chunks = self.index_blog_posts()
        total_chunks += blog_chunks
        logger.info(f"Indexed {blog_chunks} blog chunks")
        
        # Index footer content
        footer_chunks = self.index_footer_content()
        total_chunks += footer_chunks
        logger.info(f"Indexed {footer_chunks} footer chunks")
        
        # Index authentication process
        auth_chunks = self.index_auth_process()
        total_chunks += auth_chunks
        logger.info(f"Indexed {auth_chunks} authentication process chunks")
        
        # Index registration and login pages
        reg_login_chunks = self.index_registration_and_login_pages()
        total_chunks += reg_login_chunks
        logger.info(f"Indexed {reg_login_chunks} registration/login chunks")
        
        # Save the updated index
        self.semantic_search.save_index()
        
        logger.info(f"Content indexing completed. Total chunks: {total_chunks}")
        return total_chunks
    
    def index_courses(self) -> int:
        """
        Index all active courses
        
        Returns:
            Number of chunks created
        """
        logger.info("Indexing courses...")
        
        courses = Curso.objects.all()
        chunks_created = 0
        
        for course in courses:
            try:
                # Prepare course data with detailed information
                course_data = {
                    'nombre': course.name,
                    'descripcion': course.description or '',
                    'area': course.get_area_display(),
                    'tipo': course.get_tipo_display(),
                    'estado': course.get_dynamic_status_display(),
                    'profesor': f"{course.teacher.first_name} {course.teacher.last_name}".strip() or course.teacher.username,
                    'fecha_limite': course.enrollment_deadline.strftime('%Y-%m-%d') if course.enrollment_deadline else '',
                    'fecha_inicio': course.start_date.strftime('%Y-%m-%d') if course.start_date else '',
                    'cantidad_clases': course.class_quantity,
                    'curso_academico': str(course.curso_academico) if course.curso_academico else '',
                    'disponible': course.get_dynamic_status() in ['I'],  # 'I' = En etapa de inscripción
                    'estado_codigo': course.get_dynamic_status()
                }
                
                # Create chunks for this course
                chunks = self.text_chunker.chunk_course_content(
                    course_data,
                    {
                        'content_type': 'principal.curso',
                        'object_id': course.id,
                        'categoria': 'cursos',
                        'area': course.area,
                        'estado': course.get_dynamic_status()
                    }
                )
                
                # Index each chunk
                for chunk in chunks:
                    try:
                        # Generate embedding
                        embedding_vector = self.semantic_search.generate_embedding(chunk['text'])
                        
                        # Create embedding in database
                        embedding_obj = DocumentEmbedding.objects.create(
                            content_type=ContentType.objects.get_for_model(Curso),
                            object_id=course.id,
                            texto_indexado=chunk['text'],
                            categoria='cursos',
                            chunk_index=chunk.get('chunk_index', 0),
                            chunk_type=chunk.get('chunk_type', 'course_content')
                        )
                        
                        # Save embedding
                        embedding_obj.save_embedding(embedding_vector)
                        
                        # Index in FAISS
                        self.semantic_search.index_document(
                            embedding_obj.id,
                            chunk['text'],
                            {
                                'content_type': 'principal.curso',
                                'object_id': course.id,
                                'categoria': 'cursos',
                                'chunk_type': chunk.get('chunk_type', 'course_content'),
                                'area': course.area,
                                'estado': course.get_dynamic_status()
                            }
                        )
                        
                        chunks_created += 1
                        
                    except Exception as e:
                        logger.error(f"Error indexing chunk for course {course.id}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing course {course.id}: {e}")
                continue
        
        return chunks_created
    
    def index_blog_posts(self) -> int:
        """
        Index all published blog posts
        
        Returns:
            Number of chunks created
        """
        logger.info("Indexing blog posts...")
        
        # Only index published posts
        posts = Noticia.objects.filter(estado='publicado')
        chunks_created = 0
        
        for post in posts:
            try:
                # Create comprehensive text for the blog post
                blog_content = f"""
                Título: {post.titulo}
                Categoría: {post.categoria.nombre}
                Resumen: {post.resumen}
                Contenido: {post.contenido}
                Autor: {post.autor.get_full_name() or post.autor.username}
                Fecha: {post.fecha_publicacion.strftime('%Y-%m-%d')}
                """.strip()
                
                # Create chunks for this blog post
                chunks = self.text_chunker.chunk_text(
                    blog_content,
                    {
                        'content_type': 'blog.noticia',
                        'object_id': post.id,
                        'categoria': 'blog',
                        'blog_categoria': post.categoria.nombre,
                        'destacada': post.destacada
                    }
                )
                
                # Index each chunk
                for chunk in chunks:
                    try:
                        # Generate embedding
                        embedding_vector = self.semantic_search.generate_embedding(chunk['text'])
                        
                        # Create embedding in database
                        embedding_obj = DocumentEmbedding.objects.create(
                            content_type=ContentType.objects.get_for_model(Noticia),
                            object_id=post.id,
                            texto_indexado=chunk['text'],
                            categoria='blog',
                            chunk_index=chunk.get('chunk_index', 0),
                            chunk_type=chunk.get('chunk_type', 'blog_content')
                        )
                        
                        # Save embedding
                        embedding_obj.save_embedding(embedding_vector)
                        
                        # Index in FAISS
                        self.semantic_search.index_document(
                            embedding_obj.id,
                            chunk['text'],
                            {
                                'content_type': 'blog.noticia',
                                'object_id': post.id,
                                'categoria': 'blog',
                                'chunk_type': chunk.get('chunk_type', 'blog_content'),
                                'blog_categoria': post.categoria.nombre,
                                'destacada': post.destacada
                            }
                        )
                        
                        chunks_created += 1
                        
                    except Exception as e:
                        logger.error(f"Error indexing chunk for blog post {post.id}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing blog post {post.id}: {e}")
                continue
        
        return chunks_created
    
    def index_footer_content(self) -> int:
        """
        Index footer content (contact info, links, etc.)
        
        Returns:
            Number of chunks created
        """
        logger.info("Indexing footer content...")
        
        # Footer content extracted from the template with enhanced location info
        footer_content = """
        Centro Fray Bartolomé de las Casas
        Formación integral y educación de calidad para el desarrollo personal y profesional.
        
        Ubicación y Contacto:
        Dirección: Calle 19 No 258 e/ J e I, Vedado, Plaza de la Revolución, La Habana
        Ubicación: Centro Fray Bartolomé de las Casas, Vedado, La Habana
        Zona: Vedado, Plaza de la Revolución, La Habana
        Teléfono: +53 59518075
        Email: centrofraybartolomedelascasas@gmail.com
        
        Cómo llegar al centro:
        - En transporte público: Consulta las rutas de guaguas que pasan por el Vedado
        - En taxi: Indica la dirección Calle 19 No 258 entre J e I, Vedado
        - Referencias: Zona céntrica del Vedado, cerca de instituciones conocidas
        - El centro está ubicado en una zona accesible de la ciudad
        
        Enlaces disponibles:
        - Página de Inicio
        - Página Nuestros Cursos
        - Información sobre Nosotros
        - Información de Contacto
        
        Redes sociales: Facebook, Twitter, Instagram, LinkedIn
        """
        
        chunks_created = 0
        
        try:
            # Create chunks for footer content
            chunks = self.text_chunker.chunk_text(
                footer_content,
                {
                    'content_type': 'footer',
                    'object_id': 1,  # Single footer
                    'categoria': 'contacto',
                    'tipo': 'footer'
                }
            )
            
            # Index each chunk
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding_vector = self.semantic_search.generate_embedding(chunk['text'])
                    
                    # Create embedding in database (using a special content type for footer)
                    embedding_obj = DocumentEmbedding.objects.create(
                        content_type=ContentType.objects.get_for_model(DocumentEmbedding),  # Self-reference for footer
                        object_id=1,  # Single footer ID
                        texto_indexado=chunk['text'],
                        categoria='contacto',
                        chunk_index=chunk.get('chunk_index', 0),
                        chunk_type='footer_content'
                    )
                    
                    # Save embedding
                    embedding_obj.save_embedding(embedding_vector)
                    
                    # Index in FAISS
                    self.semantic_search.index_document(
                        embedding_obj.id,
                        chunk['text'],
                        {
                            'content_type': 'footer',
                            'object_id': 1,
                            'categoria': 'contacto',
                            'chunk_type': 'footer_content'
                        }
                    )
                    
                    chunks_created += 1
                    
                except Exception as e:
                    logger.error(f"Error indexing footer chunk: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing footer content: {e}")
        
        return chunks_created
    
    def index_auth_process(self) -> int:
        """
        Index authentication process content (registration and login info)
        
        Returns:
            Number of chunks created
        """
        logger.info("Indexing authentication process...")
        
        # Detailed authentication process content
        auth_content = """
        Proceso Completo de Inscripción a Cursos:
        
        PASO 1: REGISTRO DE USUARIO (OBLIGATORIO)
        Para acceder a cualquier curso, primero debe registrarse en el sitio web.
        
        Cómo registrarse:
        1. Vaya al sitio web del Centro Fray Bartolomé de las Casas
        2. Busque y haga clic en el botón "Registrarse" o "Crear Cuenta"
        3. Complete el formulario de registro con:
           - Nombre de usuario (único)
           - Contraseña segura
           - Confirmar contraseña
           - Dirección de email válida
           - Nombre completo
           - Datos personales adicionales si se requieren
        4. Acepte los términos y condiciones
        5. Haga clic en "Registrarse" o "Crear Cuenta"
        6. Verifique su email si es necesario
        
        PASO 2: INICIAR SESIÓN
        Una vez registrado, debe iniciar sesión para acceder a los cursos.
        
        Cómo iniciar sesión:
        1. Vaya al sitio web del Centro
        2. Busque y haga clic en "Iniciar Sesión" o "Login"
        3. Ingrese sus credenciales:
           - Nombre de usuario o email
           - Contraseña
        4. Haga clic en "Iniciar Sesión"
        5. Si olvida su contraseña, use "¿Olvidó su contraseña?"
        
        PASO 3: ACCESO A CURSOS Y MATRÍCULA
        Con su sesión iniciada, ya puede inscribirse a cursos.
        
        Cómo inscribirse:
        1. Navegue a la página de "Cursos" o "Programas"
        2. Explore los cursos disponibles por área:
           - Idiomas (Inglés, Alemán, etc.)
           - Diseño
           - Teología
        3. Seleccione el curso de su interés
        4. Revise la información del curso:
           - Fechas de inscripción
           - Fecha de inicio
           - Requisitos
           - Costo (si aplica)
        5. Haga clic en "Inscribirse" o "Matricularse"
        6. Complete el proceso de matrícula
        
        IMPORTANTE: 
        - Sin registro NO puede acceder a ningún curso
        - Sin iniciar sesión NO puede ver la información completa
        - El registro es GRATUITO y toma solo unos minutos
        - Mantenga sus credenciales seguras
        """
        
        chunks_created = 0
        
        try:
            # Create chunks for auth process content
            chunks = self.text_chunker.chunk_text(
                auth_content,
                {
                    'content_type': 'auth_process',
                    'object_id': 1,  # Single auth process
                    'categoria': 'inscripciones',
                    'tipo': 'proceso_registro'
                }
            )
            
            # Index each chunk
            for chunk in chunks:
                try:
                    # Generate embedding
                    embedding_vector = self.semantic_search.generate_embedding(chunk['text'])
                    
                    # Create embedding in database
                    embedding_obj = DocumentEmbedding.objects.create(
                        content_type=ContentType.objects.get_for_model(DocumentEmbedding),  # Self-reference for auth process
                        object_id=2,  # Auth process ID (different from footer)
                        texto_indexado=chunk['text'],
                        categoria='inscripciones',
                        chunk_index=chunk.get('chunk_index', 0),
                        chunk_type='auth_process'
                    )
                    
                    # Save embedding
                    embedding_obj.save_embedding(embedding_vector)
                    
                    # Index in FAISS
                    self.semantic_search.index_document(
                        embedding_obj.id,
                        chunk['text'],
                        {
                            'content_type': 'auth_process',
                            'object_id': 1,
                            'categoria': 'inscripciones',
                            'chunk_type': 'auth_process'
                        }
                    )
                    
                    chunks_created += 1
                    
                except Exception as e:
                    logger.error(f"Error indexing auth process chunk: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing auth process content: {e}")
        
        return chunks_created
    
    def index_registration_and_login_pages(self) -> int:
        """
        Index detailed information about registration and login pages
        
        Returns:
            Number of chunks created
        """
        logger.info("Indexing registration and login page information...")
        
        # Registration page information
        registration_content = """
        Página de Registro - Información Detallada:
        
        UBICACIÓN: Busque el enlace "Registrarse" o "Crear Cuenta" en el sitio web
        
        CAMPOS DEL FORMULARIO DE REGISTRO:
        - Nombre de usuario: Debe ser único, sin espacios
        - Email: Dirección de correo electrónico válida
        - Contraseña: Mínimo 8 caracteres, se recomienda incluir números y símbolos
        - Confirmar contraseña: Debe coincidir exactamente
        - Nombre completo: Su nombre real para certificados
        - Teléfono: Número de contacto (opcional)
        - Dirección: Información de residencia (si se requiere)
        
        PROCESO DE REGISTRO:
        1. Complete todos los campos obligatorios (marcados con *)
        2. Asegúrese de que las contraseñas coincidan
        3. Use un email al que tenga acceso
        4. Lea y acepte los términos y condiciones
        5. Haga clic en "Registrarse"
        6. Recibirá confirmación por email (revise spam/correo no deseado)
        
        CONSEJOS PARA EL REGISTRO:
        - Use una contraseña segura que pueda recordar
        - Anote sus credenciales en un lugar seguro
        - Use su email principal para recibir notificaciones
        - Complete su perfil después del registro
        """
        
        # Login page information
        login_content = """
        Página de Iniciar Sesión - Información Detallada:
        
        UBICACIÓN: Busque el enlace "Iniciar Sesión", "Login" o "Entrar" en el sitio web
        
        CAMPOS DEL FORMULARIO DE LOGIN:
        - Usuario/Email: Su nombre de usuario o dirección de email registrada
        - Contraseña: La contraseña que creó durante el registro
        
        PROCESO DE INICIO DE SESIÓN:
        1. Ingrese su nombre de usuario o email
        2. Ingrese su contraseña exactamente como la creó
        3. Haga clic en "Iniciar Sesión" o "Entrar"
        4. Si es correcto, será redirigido a su panel de usuario
        
        PROBLEMAS COMUNES Y SOLUCIONES:
        - "Usuario no encontrado": Verifique que escribió correctamente su usuario/email
        - "Contraseña incorrecta": Asegúrese de usar la contraseña correcta
        - "Cuenta bloqueada": Contacte al administrador del sitio
        
        ¿OLVIDÓ SU CONTRASEÑA?
        1. Haga clic en "¿Olvidó su contraseña?" en la página de login
        2. Ingrese su email registrado
        3. Revise su correo electrónico (incluya spam)
        4. Siga las instrucciones del email para restablecer
        5. Cree una nueva contraseña segura
        
        DESPUÉS DEL LOGIN:
        - Podrá acceder a la página de Cursos
        - Verá información completa de cada programa
        - Podrá realizar inscripciones
        - Tendrá acceso a su perfil de usuario
        """
        
        chunks_created = 0
        
        try:
            # Index registration content
            reg_chunks = self.text_chunker.chunk_text(
                registration_content,
                {
                    'content_type': 'registration_page',
                    'object_id': 1,
                    'categoria': 'inscripciones',
                    'tipo': 'pagina_registro'
                }
            )
            
            for chunk in reg_chunks:
                try:
                    # Generate embedding
                    embedding_vector = self.semantic_search.generate_embedding(chunk['text'])
                    
                    # Create embedding in database
                    embedding_obj = DocumentEmbedding.objects.create(
                        content_type=ContentType.objects.get_for_model(DocumentEmbedding),
                        object_id=3,  # Registration page ID
                        texto_indexado=chunk['text'],
                        categoria='inscripciones',
                        chunk_index=chunk.get('chunk_index', 0),
                        chunk_type='registration_page'
                    )
                    
                    # Save embedding
                    embedding_obj.save_embedding(embedding_vector)
                    
                    # Index in FAISS
                    self.semantic_search.index_document(
                        embedding_obj.id,
                        chunk['text'],
                        {
                            'content_type': 'registration_page',
                            'object_id': 1,
                            'categoria': 'inscripciones',
                            'chunk_type': 'registration_page'
                        }
                    )
                    
                    chunks_created += 1
                    
                except Exception as e:
                    logger.error(f"Error indexing registration chunk: {e}")
                    continue
            
            # Index login content
            login_chunks = self.text_chunker.chunk_text(
                login_content,
                {
                    'content_type': 'login_page',
                    'object_id': 1,
                    'categoria': 'inscripciones',
                    'tipo': 'pagina_login'
                }
            )
            
            for chunk in login_chunks:
                try:
                    # Generate embedding
                    embedding_vector = self.semantic_search.generate_embedding(chunk['text'])
                    
                    # Create embedding in database
                    embedding_obj = DocumentEmbedding.objects.create(
                        content_type=ContentType.objects.get_for_model(DocumentEmbedding),
                        object_id=4,  # Login page ID
                        texto_indexado=chunk['text'],
                        categoria='inscripciones',
                        chunk_index=chunk.get('chunk_index', 0),
                        chunk_type='login_page'
                    )
                    
                    # Save embedding
                    embedding_obj.save_embedding(embedding_vector)
                    
                    # Index in FAISS
                    self.semantic_search.index_document(
                        embedding_obj.id,
                        chunk['text'],
                        {
                            'content_type': 'login_page',
                            'object_id': 1,
                            'categoria': 'inscripciones',
                            'chunk_type': 'login_page'
                        }
                    )
                    
                    chunks_created += 1
                    
                except Exception as e:
                    logger.error(f"Error indexing login chunk: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error processing registration/login content: {e}")
        
        return chunks_created
    
    def clear_content_index(self, content_type: Optional[str] = None):
        """
        Clear indexed content
        
        Args:
            content_type: Optional content type to clear ('cursos', 'blog', 'contacto')
                         If None, clears all content
        """
        logger.info(f"Clearing content index for: {content_type or 'all content'}")
        
        if content_type:
            # Clear specific content type
            DocumentEmbedding.objects.filter(categoria=content_type).delete()
        else:
            # Clear all content (except FAQs)
            DocumentEmbedding.objects.exclude(categoria='general').delete()
        
        # Rebuild FAISS index
        self.semantic_search.rebuild_index()
        
        logger.info("Content index cleared and rebuilt")
    
    def get_indexing_stats(self) -> Dict:
        """
        Get statistics about indexed content
        
        Returns:
            Dictionary with indexing statistics
        """
        stats = {
            'total_embeddings': DocumentEmbedding.objects.count(),
            'faqs': DocumentEmbedding.objects.filter(categoria='general').count(),
            'cursos': DocumentEmbedding.objects.filter(categoria='cursos').count(),
            'blog': DocumentEmbedding.objects.filter(categoria='blog').count(),
            'contacto': DocumentEmbedding.objects.filter(categoria='contacto').count(),
        }
        
        # Get chunk type distribution
        chunk_types = {}
        for emb in DocumentEmbedding.objects.all():
            chunk_type = emb.chunk_type
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        stats['chunk_types'] = chunk_types
        
        return stats