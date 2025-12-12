"""
Custom admin views for chatbot management
"""
from django.contrib import admin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import ChatInteraction, FAQ, CategoriaFAQ
from .services.orchestrator import ChatbotOrchestrator


@staff_member_required
def suggested_faqs_view(request):
    """
    View for managing suggested FAQs based on user interactions
    """
    # Use the orchestrator to get grouped similar questions
    orchestrator = ChatbotOrchestrator()
    
    # Mark low-confidence questions as candidates first
    newly_marked = orchestrator.mark_low_confidence_as_candidates()
    if newly_marked > 0:
        messages.info(request, f'{newly_marked} nuevas interacciones marcadas como candidatas para FAQ.')
    
    # Get grouped similar questions
    grouped_candidates = orchestrator.group_similar_questions(similarity_threshold=0.8)
    
    # Get recent interactions for context
    recent_interactions = ChatInteraction.objects.filter(
        es_candidata_faq=True
    ).order_by('-fecha')[:20]
    
    # Get categories for the form
    categories = CategoriaFAQ.objects.all().order_by('orden', 'nombre')
    
    context = {
        'title': 'FAQs Sugeridas',
        'grouped_candidates': grouped_candidates,
        'recent_interactions': recent_interactions,
        'categories': categories,
        'total_candidates': sum(g['total_count'] for g in grouped_candidates),
        'total_groups': len(grouped_candidates)
    }
    
    return render(request, 'admin/chatbot/suggested_faqs.html', context)


@staff_member_required
def create_faq_from_suggestion(request):
    """
    Create a new FAQ from a suggested question
    """
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        answer = request.POST.get('answer', '').strip()
        category_id = request.POST.get('category')
        variations = request.POST.getlist('variations')
        
        if not question or not answer:
            messages.error(request, 'Pregunta y respuesta son requeridas.')
            return redirect('admin:chatbot_suggested_faqs')
        
        try:
            # Get category
            category = get_object_or_404(CategoriaFAQ, id=category_id)
            
            # Create FAQ
            faq = FAQ.objects.create(
                pregunta=question,
                respuesta=answer,
                categoria=category,
                activa=True
            )
            
            # Add variations
            from .models import FAQVariation
            for variation_text in variations:
                if variation_text.strip():
                    FAQVariation.objects.create(
                        faq=faq,
                        texto_variacion=variation_text.strip()
                    )
            
            # Mark related interactions as processed
            ChatInteraction.objects.filter(
                pregunta__icontains=question[:50]  # Partial match
            ).update(es_candidata_faq=False)
            
            messages.success(request, f'FAQ creada exitosamente: {question[:50]}...')
            return redirect('admin:chatbot_faq_change', faq.id)
            
        except Exception as e:
            messages.error(request, f'Error creando FAQ: {str(e)}')
    
    return redirect('admin:chatbot_suggested_faqs')


@staff_member_required
def faq_metrics_view(request):
    """
    View for FAQ metrics and statistics
    """
    # Get FAQ statistics
    total_faqs = FAQ.objects.count()
    active_faqs = FAQ.objects.filter(activa=True).count()
    highlighted_faqs = FAQ.objects.filter(destacada=True).count()
    
    # Most used FAQs
    most_used = FAQ.objects.filter(
        veces_usada__gt=0
    ).order_by('-veces_usada')[:10]
    
    # Least used FAQs (potential for removal)
    from django.utils import timezone
    from datetime import timedelta
    
    ninety_days_ago = timezone.now() - timedelta(days=90)
    unused_faqs = FAQ.objects.filter(
        Q(ultima_fecha_uso__lt=ninety_days_ago) | Q(ultima_fecha_uso__isnull=True),
        activa=True
    ).order_by('fecha_creacion')
    
    # FAQs with low success rate
    low_success_faqs = FAQ.objects.filter(
        veces_usada__gt=5,  # Only consider FAQs used more than 5 times
        tasa_exito__lt=0.5,
        activa=True
    ).order_by('tasa_exito')
    
    # Category distribution
    category_stats = CategoriaFAQ.objects.annotate(
        faq_count=Count('faqs'),
        active_faq_count=Count('faqs', filter=Q(faqs__activa=True))
    ).order_by('-faq_count')
    
    # Recent interaction stats
    orchestrator = ChatbotOrchestrator()
    interaction_stats = orchestrator.get_interaction_stats(30)
    
    context = {
        'title': 'Métricas de FAQs',
        'total_faqs': total_faqs,
        'active_faqs': active_faqs,
        'highlighted_faqs': highlighted_faqs,
        'most_used': most_used,
        'unused_faqs': unused_faqs,
        'low_success_faqs': low_success_faqs,
        'category_stats': category_stats,
        'interaction_stats': interaction_stats
    }
    
    return render(request, 'admin/chatbot/faq_metrics.html', context)


@staff_member_required
def chatbot_dashboard(request):
    """
    Main chatbot dashboard
    """
    # Get system status
    orchestrator = ChatbotOrchestrator()
    system_status = orchestrator.get_pipeline_status()
    
    # Get recent stats
    stats = orchestrator.get_interaction_stats(7)  # Last 7 days
    
    # Get recent interactions
    recent_interactions = ChatInteraction.objects.order_by('-fecha')[:10]
    
    # Get FAQ candidates count
    faq_candidates_count = ChatInteraction.objects.filter(
        es_candidata_faq=True
    ).count()
    
    context = {
        'title': 'Dashboard del Chatbot',
        'system_status': system_status,
        'stats': stats,
        'recent_interactions': recent_interactions,
        'faq_candidates_count': faq_candidates_count
    }
    
    return render(request, 'admin/chatbot/dashboard.html', context)


def _questions_similar(q1, q2, threshold=0.6):
    """
    Simple similarity check between two questions
    Can be improved with semantic similarity using embeddings
    """
    # Convert to lowercase and split into words
    words1 = set(q1.lower().split())
    words2 = set(q2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return False
    
    similarity = intersection / union
    return similarity >= threshold

@staff_member_required
def export_metrics(request):
    """
    Export FAQ metrics to CSV
    """
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="faq_metrics_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Pregunta', 'Categoria', 'Activa', 'Destacada', 'Prioridad',
        'Veces Usada', 'Ultima Fecha Uso', 'Tasa Exito', 'Fecha Creacion',
        'Variaciones Count'
    ])
    
    faqs = FAQ.objects.select_related('categoria').prefetch_related('variaciones')
    
    for faq in faqs:
        writer.writerow([
            faq.id,
            faq.pregunta,
            faq.categoria.nombre,
            'Sí' if faq.activa else 'No',
            'Sí' if faq.destacada else 'No',
            faq.prioridad,
            faq.veces_usada,
            faq.ultima_fecha_uso.strftime('%Y-%m-%d %H:%M') if faq.ultima_fecha_uso else '',
            f'{faq.tasa_exito:.2f}' if faq.tasa_exito else '0.00',
            faq.fecha_creacion.strftime('%Y-%m-%d'),
            faq.variaciones.count()
        ])
    
    return response


@staff_member_required
def bulk_approve_faqs(request):
    """
    Bulk approve multiple FAQ suggestions
    """
    if request.method == 'POST':
        import json
        
        try:
            data = json.loads(request.body)
            suggestions = data.get('suggestions', [])
            
            approved_count = 0
            
            for suggestion in suggestions:
                question = suggestion.get('question', '').strip()
                answer = suggestion.get('answer', '').strip()
                category_id = suggestion.get('category_id')
                
                if question and answer and category_id:
                    try:
                        category = CategoriaFAQ.objects.get(id=category_id)
                        
                        # Create FAQ
                        faq = FAQ.objects.create(
                            pregunta=question,
                            respuesta=answer,
                            categoria=category,
                            activa=True
                        )
                        
                        # Mark related interactions as processed
                        ChatInteraction.objects.filter(
                            pregunta__icontains=question[:50]
                        ).update(es_candidata_faq=False)
                        
                        approved_count += 1
                        
                    except Exception as e:
                        continue
            
            return JsonResponse({
                'success': True,
                'approved_count': approved_count,
                'message': f'{approved_count} FAQs creadas exitosamente.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@staff_member_required
def dismiss_suggestion(request):
    """
    Dismiss a FAQ suggestion
    """
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        
        if question:
            # Mark interactions as not FAQ candidates
            updated = ChatInteraction.objects.filter(
                pregunta__icontains=question[:50],
                es_candidata_faq=True
            ).update(es_candidata_faq=False)
            
            messages.success(request, f'Sugerencia descartada. {updated} interacciones marcadas.')
        else:
            messages.error(request, 'Pregunta no válida.')
    
    return redirect('admin:chatbot_suggested_faqs')


@staff_member_required
def rebuild_search_index(request):
    """
    Manually rebuild the search index
    """
    if request.method == 'POST':
        try:
            from .services.content_indexer import ContentIndexer
            
            indexer = ContentIndexer()
            results = indexer.index_all()
            
            total_indexed = sum(results.values())
            
            messages.success(
                request, 
                f'Índice reconstruido exitosamente. '
                f'Documentos indexados: {results["faqs"]} FAQs, '
                f'{results["cursos"]} cursos, {results["noticias"]} noticias. '
                f'Total: {total_indexed}'
            )
            
        except Exception as e:
            messages.error(request, f'Error reconstruyendo índice: {str(e)}')
    
    return redirect('admin:chatbot_dashboard')