"""
Chatbot API Views
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .services.orchestrator import ChatbotOrchestrator
from .models import ChatInteraction

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_ask(request):
    """
    API endpoint for asking questions to the chatbot
    
    POST /chatbot/ask/
    Body: {
        "pregunta": str,
        "session_id": str
    }
    Response: {
        "respuesta": str,
        "confianza": float,
        "tiempo": float,
        "success": bool,
        "interaction_id": int (optional)
    }
    """
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            }, status=400)
        
        # Extract parameters
        pregunta = data.get('pregunta', '').strip()
        session_id = data.get('session_id', '').strip()
        
        # Validate required parameters
        if not pregunta:
            return JsonResponse({
                'success': False,
                'error': 'Pregunta is required'
            }, status=400)
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID is required'
            }, status=400)
        
        # Initialize orchestrator
        orchestrator = ChatbotOrchestrator()
        
        # Validate question
        is_valid, error_message = orchestrator.validate_question(pregunta)
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=400)
        
        # Process question
        result = orchestrator.process_question(pregunta, session_id)
        
        # Get interaction ID for feedback
        try:
            # Get the most recent interaction for this session
            interaction = ChatInteraction.objects.filter(
                session_id=session_id
            ).order_by('-fecha').first()
            
            if interaction:
                result['interaction_id'] = interaction.id
        except Exception as e:
            logger.warning(f"Could not get interaction ID: {e}")
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in chatbot_ask: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'respuesta': 'Lo siento, ocurrió un error interno. Por favor, intenta de nuevo.',
            'confianza': 0.0,
            'tiempo': 0.0
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def chatbot_status(request):
    """
    API endpoint to check chatbot status
    
    GET /chatbot/status/
    Response: {
        "status": "ok" | "error",
        "components": {...},
        "suggestions": [...]
    }
    """
    try:
        orchestrator = ChatbotOrchestrator()
        
        # Get component status
        pipeline_status = orchestrator.get_pipeline_status()
        
        # Get suggested questions
        suggestions = orchestrator.get_suggested_questions()
        
        # Determine overall status
        llm_available = pipeline_status['llm_generator']['available']
        search_available = pipeline_status['semantic_search']['index_stats']['total_vectors'] > 0
        
        overall_status = "ok" if (llm_available or search_available) else "degraded"
        
        return JsonResponse({
            'status': overall_status,
            'components': pipeline_status,
            'suggestions': suggestions,
            'message': 'Chatbot is ready' if overall_status == 'ok' else 'Chatbot running in fallback mode'
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot_status: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def chatbot_stats(request):
    """
    API endpoint to get chatbot statistics
    
    GET /chatbot/stats/?days=30
    Response: {
        "stats": {...}
    }
    """
    try:
        # Get days parameter
        days = int(request.GET.get('days', 30))
        if days < 1 or days > 365:
            days = 30
        
        orchestrator = ChatbotOrchestrator()
        stats = orchestrator.get_interaction_stats(days)
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot_stats: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_feedback(request):
    """
    API endpoint for submitting feedback on chatbot responses
    
    POST /chatbot/feedback/
    Body: {
        "interaction_id": int,
        "fue_util": bool
    }
    Response: {
        "success": bool,
        "message": str
    }
    """
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            }, status=400)
        
        # Extract parameters
        interaction_id = data.get('interaction_id')
        fue_util = data.get('fue_util')
        
        # Validate parameters
        if interaction_id is None:
            return JsonResponse({
                'success': False,
                'error': 'interaction_id is required'
            }, status=400)
        
        if fue_util is None:
            return JsonResponse({
                'success': False,
                'error': 'fue_util is required'
            }, status=400)
        
        if not isinstance(fue_util, bool):
            return JsonResponse({
                'success': False,
                'error': 'fue_util must be a boolean'
            }, status=400)
        
        # Update feedback
        orchestrator = ChatbotOrchestrator()
        success = orchestrator.update_interaction_feedback(interaction_id, fue_util)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Feedback recorded successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Interaction not found'
            }, status=404)
        
    except Exception as e:
        logger.error(f"Error in chatbot_feedback: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

# Session Management Utilities

def get_or_create_session_id(request):
    """
    Get or create a session ID for the chatbot
    
    Args:
        request: Django request object
        
    Returns:
        Session ID string
    """
    import uuid
    
    session_id = request.session.get('chatbot_session_id')
    
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['chatbot_session_id'] = session_id
        request.session['chatbot_history'] = []
        request.session['chatbot_start_time'] = str(timezone.now())
    
    return session_id


def add_message_to_session(request, pregunta, respuesta, interaction_id=None):
    """
    Add a message to the session history
    
    Args:
        request: Django request object
        pregunta: User's question
        respuesta: Bot's response
        interaction_id: Optional interaction ID
    """
    from django.utils import timezone
    
    if 'chatbot_history' not in request.session:
        request.session['chatbot_history'] = []
    
    message = {
        'pregunta': pregunta,
        'respuesta': respuesta,
        'timestamp': str(timezone.now()),
        'interaction_id': interaction_id
    }
    
    request.session['chatbot_history'].append(message)
    
    # Limit history to last 50 messages
    if len(request.session['chatbot_history']) > 50:
        request.session['chatbot_history'] = request.session['chatbot_history'][-50:]
    
    request.session.modified = True


def get_session_history(request):
    """
    Get the chat history for the current session
    
    Args:
        request: Django request object
        
    Returns:
        List of messages
    """
    return request.session.get('chatbot_history', [])


@csrf_exempt
@require_http_methods(["GET"])
def chatbot_history(request):
    """
    API endpoint to get chat history for current session
    
    GET /chatbot/history/
    Response: {
        "success": bool,
        "history": [...],
        "session_id": str
    }
    """
    try:
        session_id = get_or_create_session_id(request)
        history = get_session_history(request)
        
        return JsonResponse({
            'success': True,
            'history': history,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot_history: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_clear_history(request):
    """
    API endpoint to clear chat history for current session
    
    POST /chatbot/clear-history/
    Response: {
        "success": bool,
        "message": str
    }
    """
    try:
        request.session['chatbot_history'] = []
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'message': 'Chat history cleared'
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot_clear_history: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def chatbot_widget(request):
    """
    Render the chatbot widget
    
    GET /chatbot/widget/
    """
    try:
        session_id = get_or_create_session_id(request)
        history = get_session_history(request)
        
        # Get suggested questions
        orchestrator = ChatbotOrchestrator()
        suggestions = orchestrator.get_suggested_questions()
        
        context = {
            'session_id': session_id,
            'history': history,
            'suggestions': suggestions
        }
        
        return render(request, 'chatbot/widget.html', context)
        
    except Exception as e:
        logger.error(f"Error in chatbot_widget: {e}")
        return render(request, 'chatbot/error.html', {
            'error': 'Error loading chatbot widget'
        })