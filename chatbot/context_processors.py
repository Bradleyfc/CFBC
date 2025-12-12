"""
Context processors for chatbot
"""
import uuid
from django.middleware.csrf import get_token
from .services.orchestrator import ChatbotOrchestrator


def chatbot_context(request):
    """
    Add chatbot context variables to all templates
    """
    # Generate or get session ID
    if not request.session.session_key:
        request.session.create()
    
    session_id = request.session.session_key or str(uuid.uuid4())
    
    # Get CSRF token
    csrf_token = get_token(request)
    
    # Get conversation history from session
    history = request.session.get('chatbot_history', [])
    
    # Get suggested questions
    orchestrator = ChatbotOrchestrator()
    suggestions = orchestrator.get_suggested_questions()[:4]  # Limit to 4 suggestions
    
    return {
        'chatbot_session_id': session_id,
        'chatbot_csrf_token': csrf_token,
        'chatbot_history': history,
        'chatbot_suggestions': suggestions,
    }