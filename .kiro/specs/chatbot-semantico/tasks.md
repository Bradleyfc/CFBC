# Implementation Plan - Chatbot Semántico

- [x] 1. Set up project structure and install dependencies



  - Create `chatbot` Django app with proper directory structure
  - Add required packages to requirements.txt: sentence-transformers, faiss-cpu, transformers, torch, hypothesis
  - Create directories for models storage and FAISS index
  - Configure environment variables for chatbot settings
  - _Requirements: 6.1_

- [x] 2. Create Django models for knowledge base



  - _Requirements: 4.1, 4.2, 9.1, 11.1_

- [x] 2.1 Implement CategoriaFAQ model


  - Create model with nombre, descripcion, slug, icono, orden fields
  - Add admin registration with list display and search
  - _Requirements: 11.2_

- [x] 2.2 Implement FAQ model


  - Create model with pregunta, respuesta, categoria, prioridad, destacada, activa fields
  - Add metrics fields: veces_usada, ultima_fecha_uso, tasa_exito
  - Add timestamps: fecha_creacion, fecha_actualizacion
  - _Requirements: 4.2, 10.1_

- [x] 2.3 Implement FAQVariation model


  - Create model with faq foreign key and texto_variacion field
  - Add admin inline for managing variations within FAQ admin
  - _Requirements: 9.1, 9.2_

- [x] 2.4 Implement ChatInteraction model


  - Create model with session_id, pregunta, respuesta, documentos_recuperados (JSONField)
  - Add intencion_detectada, confianza, fue_util, fecha, tiempo_respuesta fields
  - _Requirements: 8.1, 8.7_

- [x] 2.5 Implement DocumentEmbedding model


  - Create model with GenericForeignKey for content_type and object_id
  - Add texto_indexado, embedding_vector (BinaryField), categoria, fecha_indexacion fields
  - _Requirements: 4.5, 4.6_

- [ ]* 2.6 Write property test for FAQ model persistence
  - **Property 4: Index consistency on content changes (FAQ creation part)**
  - **Validates: Requirements 4.2, 4.5**

- [x] 3. Implement semantic search service



  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 3.1 Create SemanticSearchService class


  - Initialize sentence-transformer model (paraphrase-multilingual-MiniLM-L12-v2)
  - Implement generate_embedding() method to create embeddings from text
  - Add model caching to avoid reloading on each request
  - _Requirements: 2.1_

- [x] 3.2 Implement FAISS index management


  - Create initialize_index() method to create or load FAISS IndexFlatIP
  - Implement save_index() and load_index() methods for persistence
  - Add index_document() method to add single document to index
  - Implement rebuild_index() method to recreate index from all DocumentEmbeddings
  - _Requirements: 2.2, 4.4_

- [x] 3.3 Implement semantic search functionality


  - Create search() method that takes query text and returns top-k similar documents
  - Add category filtering parameter for intent-based search
  - Implement cosine similarity scoring using FAISS inner product
  - Return documents with scores and metadata
  - _Requirements: 2.3, 2.5, 11.4_

- [ ]* 3.4 Write property test for embedding generation
  - **Property 3: Embedding generation and search pipeline (embedding part)**
  - **Validates: Requirements 2.1**

- [ ]* 3.5 Write property test for search results ordering
  - **Property 3: Embedding generation and search pipeline (search part)**
  - **Validates: Requirements 2.3, 2.5**

- [x] 4. Implement content indexing service



  - _Requirements: 4.6, 4.7, 4.8_

- [x] 4.1 Create ContentIndexer class


  - Implement extract_text_from_curso() to extract relevant fields from Curso model
  - Implement extract_text_from_noticia() to extract fields from Noticia model
  - Implement extract_text_from_faq() to extract question, variations, and answer
  - _Requirements: 4.7, 4.8_

- [x] 4.2 Implement indexing methods for each content type


  - Create index_faqs() to index all active FAQs and their variations
  - Create index_cursos() to index all courses with status 'I', 'IT', or 'P'
  - Create index_noticias() to index all published blog posts
  - Create index_all() to index all content types
  - _Requirements: 4.6_

- [x] 4.3 Add Django signals for automatic indexing


  - Create post_save signal for FAQ model to trigger indexing on create/update
  - Create post_delete signal for FAQ model to remove from index
  - Create signals for FAQVariation model
  - Create signals for Curso and Noticia models
  - _Requirements: 4.3, 4.4, 9.4_

- [ ]* 4.4 Write property test for index consistency
  - **Property 4: Index consistency on content changes**
  - **Validates: Requirements 4.3, 4.4, 4.5, 9.4**

- [ ]* 4.5 Write property test for universal content indexing
  - **Property 5: Universal content indexing**
  - **Validates: Requirements 2.4, 4.6, 4.7, 4.8**

- [x] 5. Implement intent classification service



  - _Requirements: 12.1, 12.2, 12.3_

- [x] 5.1 Create IntentClassifier class


  - Define INTENT_KEYWORDS dictionary with keywords for each category
  - Implement classify() method using keyword matching
  - Return intent and confidence score (0-1)
  - Set confidence threshold at 0.6 for filtering
  - _Requirements: 12.1, 12.2_

- [x] 5.2 Add support for multi-intent detection


  - Modify classify() to detect multiple intents in a single question
  - Return list of intents with confidence scores
  - _Requirements: 12.6_

- [ ]* 5.3 Write property test for intent classification
  - **Property 15: Intent classification**
  - **Validates: Requirements 12.1, 12.2**

- [ ]* 5.4 Write property test for multi-intent handling
  - **Property 17: Multi-intent handling**
  - **Validates: Requirements 12.6**

- [x] 6. Implement LLM generation service



  - _Requirements: 3.1, 3.3, 3.4_

- [x] 6.1 Create LLMGeneratorService class


  - Initialize flan-t5-small model and tokenizer
  - Implement model caching to keep in memory
  - Add error handling for model loading failures
  - _Requirements: 3.1_

- [x] 6.2 Implement prompt building


  - Create build_prompt() method that combines context documents and question
  - Use template that instructs model to answer only from context
  - Format context documents clearly with numbering
  - _Requirements: 3.3_

- [x] 6.3 Implement response generation


  - Create generate_response() method that takes question and context
  - Set max_tokens parameter to 300
  - Add token counting to verify length constraint
  - Implement fallback to return raw context if LLM fails
  - _Requirements: 3.4, 3.5_

- [ ]* 6.4 Write property test for context inclusion
  - **Property 6: Context-based response generation**
  - **Validates: Requirements 3.3, 5.1**

- [ ]* 6.5 Write property test for response length
  - **Property 7: Response length constraint**
  - **Validates: Requirements 3.4**

- [x] 7. Implement chatbot orchestrator



  - _Requirements: 1.2, 5.1, 5.2, 8.1, 8.2_

- [x] 7.1 Create ChatbotOrchestrator class


  - Initialize all service components (intent, search, LLM)
  - Create process_question() method as main entry point
  - Implement pipeline: classify intent → search → generate → log
  - _Requirements: 1.2_

- [x] 7.2 Implement question processing pipeline


  - Call IntentClassifier to detect intent and confidence
  - Call SemanticSearchService with category filter if confidence > 0.6
  - Retrieve top 3 documents from search results
  - Call LLMGeneratorService to generate response from context
  - Handle empty search results with polite message
  - _Requirements: 5.1, 5.2, 12.3_

- [x] 7.3 Implement interaction logging


  - Create log_interaction() method to save ChatInteraction record
  - Anonymize any personal data before saving
  - Calculate and store response time
  - Store retrieved documents as JSON
  - Mark low-confidence interactions as FAQ candidates
  - _Requirements: 8.1, 8.2, 8.7_

- [x] 7.4 Implement FAQ usage tracking


  - Create track_faq_usage() method to increment veces_usada counter
  - Update ultima_fecha_uso timestamp
  - _Requirements: 10.1_

- [ ]* 7.5 Write property test for response time
  - **Property 1: Response time constraint**
  - **Validates: Requirements 1.2**

- [ ]* 7.6 Write property test for interaction logging
  - **Property 11: Interaction logging with anonymization**
  - **Validates: Requirements 8.1, 8.7, 6.5**

- [ ]* 7.7 Write property test for FAQ usage tracking
  - **Property 10: FAQ usage tracking**
  - **Validates: Requirements 10.1**

- [x] 8. Create API endpoints and views



  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 8.1 Create chatbot_ask API endpoint


  - Create POST endpoint at /chatbot/ask/
  - Accept JSON with pregunta and session_id
  - Call ChatbotOrchestrator.process_question()
  - Return JSON with respuesta, confianza, tiempo
  - Add error handling for all error types from design doc
  - _Requirements: 1.2_

- [x] 8.2 Create chatbot_feedback API endpoint


  - Create POST endpoint at /chatbot/feedback/
  - Accept JSON with interaction_id and fue_util boolean
  - Update ChatInteraction record with feedback
  - Update FAQ tasa_exito if FAQ was used
  - _Requirements: 10.3_

- [x] 8.3 Implement session management


  - Store conversation history in Django session
  - Create helper to add message to session history
  - Create helper to retrieve session history
  - Preserve history when widget is closed and reopened
  - _Requirements: 1.3, 1.4_

- [x] 8.4 Create chatbot widget view


  - Create view to render chatbot widget HTML
  - Include session_id generation
  - _Requirements: 1.1_

- [ ]* 8.5 Write property test for session history persistence
  - **Property 2: Session history persistence**
  - **Validates: Requirements 1.3, 1.4**

- [x] 9. Implement frontend chat widget



  - _Requirements: 1.1, 1.5, 7.1, 7.3, 7.5_

- [x] 9.1 Create HTML structure for chat widget


  - Create collapsible chat widget container
  - Add header with title and close button
  - Add messages container with scroll
  - Add input field and send button
  - Add loading indicator
  - _Requirements: 1.1, 1.5_

- [x] 9.2 Add CSS styling for chat widget


  - Style widget to be fixed position in bottom-right corner
  - Make widget responsive for mobile (max 90% width on small screens)
  - Style messages with user/bot differentiation
  - Add smooth animations for open/close
  - Ensure scroll works within widget without affecting page
  - _Requirements: 7.1, 7.3, 7.5_

- [x] 9.3 Implement JavaScript for chat functionality


  - Handle send button click and Enter key press
  - Make AJAX POST request to /chatbot/ask/
  - Display loading indicator while waiting for response
  - Append user message and bot response to chat
  - Store messages in sessionStorage for persistence
  - Restore messages when widget is reopened
  - Handle errors and display user-friendly messages
  - _Requirements: 1.2, 1.3, 1.4, 1.5_


- [x] 9.4 Add feedback buttons to responses

  - Add thumbs up/down buttons to each bot response
  - Send feedback to /chatbot/feedback/ endpoint
  - Disable buttons after feedback is given
  - _Requirements: 10.3_

- [x] 10. Implement admin interface for FAQ management



  - _Requirements: 4.1, 8.3, 8.4, 10.2, 11.2_

- [x] 10.1 Create FAQ admin with inline variations


  - Register FAQ model in admin with custom ModelAdmin
  - Add FAQVariation as inline
  - Add list display with pregunta, categoria, prioridad, destacada, veces_usada
  - Add list filters for categoria, destacada, activa
  - Add search fields for pregunta and respuesta
  - _Requirements: 4.1, 9.1_

- [x] 10.2 Create admin view for suggested FAQs


  - Create custom admin view to show FAQ candidates
  - Query ChatInteraction for low-confidence or negative feedback
  - Group similar questions using semantic similarity
  - Display with frequency count and sample questions
  - Add action button to create FAQ from suggestion
  - _Requirements: 8.3, 8.4_

- [x] 10.3 Create admin view for FAQ metrics


  - Create custom admin view to display FAQ statistics
  - Show table with FAQ, veces_usada, ultima_fecha_uso, tasa_exito
  - Add filter for unused FAQs (>90 days)
  - Add export to CSV functionality
  - _Requirements: 10.2, 10.4_

- [x] 10.4 Implement FAQ approval workflow


  - Add approve_suggested_faq() method to create FAQ from suggestion
  - Automatically index new FAQ after creation
  - Mark source interactions as processed
  - _Requirements: 8.6_

- [ ]* 10.5 Write property test for FAQ approval and indexing
  - **Property 14: FAQ approval and indexing**
  - **Validates: Requirements 8.6**

- [ ] 11. Implement FAQ suggestion and grouping
  - _Requirements: 8.2, 8.5, 9.5_

- [ ] 11.1 Create method to mark low-confidence questions as candidates
  - Implement logic in ChatbotOrchestrator to check confidence threshold
  - Mark ChatInteraction as FAQ candidate if confidence < 0.5 or negative feedback
  - _Requirements: 8.2_

- [ ] 11.2 Implement similar question grouping
  - Create group_similar_questions() method using semantic similarity
  - Use sentence-transformers to compare question embeddings
  - Group questions with similarity > 0.8
  - Store grouping results for admin display
  - _Requirements: 8.5, 9.5_

- [ ]* 11.3 Write property test for low-confidence FAQ suggestion
  - **Property 12: Low-confidence FAQ suggestion**
  - **Validates: Requirements 8.2**

- [ ]* 11.4 Write property test for similar question grouping
  - **Property 13: Similar question grouping**
  - **Validates: Requirements 8.5, 9.5**

- [ ] 12. Implement result ordering and filtering
  - _Requirements: 11.3, 11.4, 11.5_

- [ ] 12.1 Add priority-based result ordering
  - Modify SemanticSearchService.search() to apply ordering
  - Order by: (1) destacada flag, (2) prioridad value, (3) similarity score
  - _Requirements: 11.3, 11.5_

- [ ] 12.2 Implement category-based filtering
  - Add category parameter to search() method
  - Filter DocumentEmbeddings by categoria before search
  - Apply filtering only when intent confidence > 0.6
  - _Requirements: 11.4, 12.3_

- [ ]* 12.3 Write property test for result ordering
  - **Property 9: Result ordering by priority and category**
  - **Validates: Requirements 11.3, 11.4, 11.5**

- [ ]* 12.4 Write property test for intent-based filtering
  - **Property 16: Intent-based search filtering**
  - **Validates: Requirements 12.3**

- [ ] 13. Implement FAQ variation indexing
  - _Requirements: 9.2, 9.3, 9.4_

- [ ] 13.1 Update indexing to include all variations
  - Modify extract_text_from_faq() to include all variation texts
  - Create separate DocumentEmbedding for each variation
  - Link all variations to same FAQ via metadata
  - _Requirements: 9.2_

- [ ] 13.2 Ensure variations are included in search
  - Verify that search() returns results from variations
  - Map variation results back to parent FAQ
  - _Requirements: 9.3_

- [ ]* 13.3 Write property test for variation indexing
  - **Property 8: FAQ variation indexing**
  - **Validates: Requirements 9.2, 9.3**

- [ ] 14. Add course information completeness
  - _Requirements: 5.5_

- [ ] 14.1 Enhance curso text extraction
  - Ensure extract_text_from_curso() includes availability, dates, requisitos
  - Add logic to include dynamic status from get_dynamic_status()
  - Format dates in readable Spanish format
  - _Requirements: 5.5_

- [ ]* 14.2 Write property test for course information completeness
  - **Property 20: Course information completeness**
  - **Validates: Requirements 5.5**

- [ ] 15. Implement feedback tracking
  - _Requirements: 10.3_

- [ ] 15.1 Add feedback recording to ChatInteraction
  - Update chatbot_feedback endpoint to set fue_util field
  - Calculate and update FAQ tasa_exito based on feedback
  - _Requirements: 10.3_

- [ ]* 15.2 Write property test for feedback tracking
  - **Property 18: Feedback tracking**
  - **Validates: Requirements 10.3**

- [ ] 16. Implement unused FAQ identification
  - _Requirements: 10.4_

- [ ] 16.1 Create query method for unused FAQs
  - Add method to filter FAQs where ultima_fecha_uso is None or > 90 days ago
  - Display in admin metrics view
  - _Requirements: 10.4_

- [ ]* 16.2 Write property test for unused FAQ identification
  - **Property 19: Unused FAQ identification**
  - **Validates: Requirements 10.4**

- [x] 17. Create management commands for maintenance


  - _Requirements: 4.6_


- [x] 17.1 Create rebuild_index management command

  - Create Django management command to rebuild entire FAISS index
  - Call ContentIndexer.index_all()
  - Display progress and statistics
  - _Requirements: 4.6_



- [x] 17.2 Create export_metrics management command

  - Create command to export FAQ metrics to CSV
  - Include all statistics from requirements

  - _Requirements: 10.5_

- [x] 18. Add error handling and fallbacks
  - _Requirements: 3.5, 5.2_


- [x] 18.1 Implement LLM fallback mechanism

  - Add try-except in generate_response() to catch model errors
  - Return formatted search results if LLM fails
  - Log error for monitoring
  - _Requirements: 3.5_




- [x] 18.2 Implement empty results handling
  - Add check in process_question() for empty search results
  - Return polite "no information" message
  - Suggest contacting administrator
  - _Requirements: 5.2_

- [x] 19. Checkpoint - Ensure all tests pass




  - Run all unit tests and verify they pass
  - Run all property tests with 100 iterations
  - Fix any failing tests
  - Ask user if questions arise



- [ ] 20. Integration and deployment preparation
  - _Requirements: 1.1_



- [ ] 20.1 Integrate widget into homepage template
  - Add chatbot widget HTML to base template or homepage
  - Include JavaScript and CSS files



  - Test widget visibility and functionality
  - _Requirements: 1.1_



- [ ] 20.2 Create initial data fixtures
  - Create fixture with sample CategoriaFAQ records
  - Create fixture with sample FAQ records for testing


  - Create fixture with intent keywords configuration
  - _Requirements: 11.2, 12.5_

- [ ] 20.3 Add configuration documentation
  - Document environment variables
  - Document model download and setup
  - Document index rebuild process
  - Document deployment requirements

- [x] 21. Final checkpoint - Ensure all tests pass


  - Run full test suite including all property tests
  - Verify all 20 correctness properties pass
  - Test end-to-end user workflows manually
  - Ask user if questions arise
