"""
Cached versions of course documents views using Redis caching.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, CreateView, View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db import transaction, models as db_models
from django.core.files.storage import default_storage
from django.conf import settings
import os
import mimetypes

from principal.models import Curso, Matriculas
from .models import DocumentFolder, CourseDocument, DocumentAccess, NewContentNotification, AuditLog
from .permissions import TeacherPermissionMixin, StudentPermissionMixin
from .forms import DocumentFolderForm, CourseDocumentForm
from .services import NotificationService
from .indicator_service import ContentIndicatorService
from cfbc.cache_utils import (
    get_cached_folders_for_curso,
    invalidate_folders_cache_for_curso,
    invalidate_all_folders_cache,
    CacheMetrics,
    cached_with_metrics,
    generate_cache_key
)


class TeacherDashboardCachedView(LoginRequiredMixin, TeacherPermissionMixin, DetailView):
    """
    Cached version of TeacherDashboardView with Redis caching for document folders.
    
    Validates: Requirements 2.1, 2.2, 2.5, 2.6, 2.8
    """
    model = Curso
    template_name = 'course_documents/teacher_dashboard.html'
    context_object_name = 'curso'
    pk_url_kwarg = 'curso_id'
    
    @cached_with_metrics(timeout=300, key_prefix='course_docs:teacher_dashboard_stats')
    def get_course_stats(self, curso):
        """
        Get course statistics with caching.
        
        Args:
            curso: Course object
            
        Returns:
            Dictionary with course statistics
        """
        from django.db.models import Count, Sum
        
        # Get cached folders for the course
        folders = get_cached_folders_for_curso(curso.id)
        
        # Get aggregated statistics
        folder_stats = DocumentFolder.objects.filter(curso=curso).aggregate(
            total_folders=Count('id'),
            total_documents=Count('documents'),
            total_document_size=Sum('documents__file_size')
        )
        
        # Count active students
        total_students = Matriculas.objects.filter(
            course=curso, 
            activo=True
        ).count()
        
        # Calculate average documents per folder
        average_docs_per_folder = folder_stats['total_documents'] / folder_stats['total_folders'] if folder_stats['total_folders'] > 0 else 0
        
        return {
            'total_folders': folder_stats['total_folders'],
            'total_documents': folder_stats['total_documents'],
            'total_students': total_students,
            'average_docs_per_folder': average_docs_per_folder,
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = self.get_object()
        
        # Get cached folders
        folders = get_cached_folders_for_curso(curso.id)
        
        # Get cached statistics
        stats = self.get_course_stats(curso)
        
        context['folders'] = folders
        context['stats'] = stats
        
        # Forms for creating folder and uploading document
        context['folder_form'] = DocumentFolderForm()
        context['document_form'] = CourseDocumentForm()
        
        # Record cache metrics
        CacheMetrics.record_hit('course_docs:teacher_dashboard_view')
        
        return context


class StudentDashboardCachedView(LoginRequiredMixin, StudentPermissionMixin, DetailView):
    """
    Cached version of StudentDashboardView with Redis caching.
    
    Validates: Requirements 2.1, 2.2, 2.5, 2.6, 2.8
    """
    model = Curso
    template_name = 'course_documents/student_dashboard.html'
    context_object_name = 'curso'
    pk_url_kwarg = 'curso_id'
    
    @cached_with_metrics(timeout=300, key_prefix='course_docs:student_dashboard_data')
    def get_student_dashboard_data(self, curso, user):
        """
        Get student dashboard data with caching.
        
        Args:
            curso: Course object
            user: Current user
            
        Returns:
            Tuple of (folders, stats, has_new_content)
        """
        from django.db.models import Count, Prefetch
        
        # Get cached folders with prefetched documents
        folders = get_cached_folders_for_curso(curso.id)
        
        # Get statistics
        stats = DocumentFolder.objects.filter(curso=curso, documents__isnull=False).aggregate(
            total_folders=Count('id', distinct=True),
            total_documents=Count('documents', distinct=True)
        )
        
        # Check for new content
        has_new_content = ContentIndicatorService.has_new_content(curso, user)
        
        return folders, stats, has_new_content
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = self.get_object()
        
        # Get cached dashboard data
        folders, stats, has_new_content = self.get_student_dashboard_data(curso, self.request.user)
        
        context['folders'] = folders
        context['stats'] = {
            'total_folders': stats['total_folders'],
            'total_documents': stats['total_documents'],
            'has_new_content': has_new_content,
        }
        
        # Record cache metrics
        CacheMetrics.record_hit('course_docs:student_dashboard_view')
        
        return context
    
    def get(self, request, *args, **kwargs):
        """Override get to mark content as seen and record metrics."""
        response = super().get(request, *args, **kwargs)
        
        curso = self.get_object()
        if ContentIndicatorService.deactivate_indicator_for_student(curso, request.user):
            # Register in audit log
            AuditLog.log_action(
                user=request.user,
                action='content_viewed',
                curso=curso,
                details=f'Estudiante accedió al dashboard del curso "{curso.name}"'
            )
        
        return response


# Cache-aware folder operations
class CreateFolderCachedView(LoginRequiredMixin, TeacherPermissionMixin, CreateView):
    """
    Create folder view with cache invalidation.
    """
    model = DocumentFolder
    form_class = DocumentFolderForm
    template_name = 'course_documents/create_folder.html'
    
    def get_curso(self):
        """Get course from URL."""
        return get_object_or_404(Curso, id=self.kwargs['curso_id'])
    
    def form_valid(self, form):
        """Process valid form with cache invalidation."""
        curso = self.get_curso()
        
        # Verify user is course teacher
        if curso.teacher != self.request.user:
            raise PermissionDenied("No tienes permisos para crear carpetas en este curso")
        
        # Assign course and user
        form.instance.curso = curso
        form.instance.created_by = self.request.user
        
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                
                # Invalidate cache for this course
                invalidate_folders_cache_for_curso(curso.id)
                
                # Register in audit log
                AuditLog.log_action(
                    user=self.request.user,
                    action='folder_created',
                    curso=curso,
                    folder=self.object,
                    details=f'Carpeta "{self.object.name}" creada'
                )
                
                messages.success(
                    self.request, 
                    f'Carpeta "{self.object.name}" creada exitosamente.'
                )
                
                return response
                
        except Exception as e:
            messages.error(
                self.request, 
                f'Error al crear la carpeta: {str(e)}'
            )
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redirect URL after creating folder."""
        return reverse('course_documents:teacher_dashboard', kwargs={'curso_id': self.kwargs['curso_id']})


class DeleteFolderCachedView(LoginRequiredMixin, TeacherPermissionMixin, View):
    """
    Delete folder view with cache invalidation.
    """
    
    def post(self, request, curso_id, folder_id):
        """Delete folder with cache invalidation."""
        curso = get_object_or_404(Curso, id=curso_id)
        folder = get_object_or_404(DocumentFolder, id=folder_id, curso=curso)
        
        # Verify permissions
        if curso.teacher != request.user:
            return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
        
        try:
            with transaction.atomic():
                folder_name = folder.name
                
                # Delete physical files of documents
                for document in folder.documents.all():
                    if document.file and default_storage.exists(document.file.name):
                        default_storage.delete(document.file.name)
                
                # Delete folder (cascade will delete documents)
                folder.delete()
                
                # Invalidate cache for this course
                invalidate_folders_cache_for_curso(curso.id)
                
                # Register in audit log
                AuditLog.log_action(
                    user=request.user,
                    action='folder_deleted',
                    curso=curso,
                    details=f'Carpeta "{folder_name}" eliminada'
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Carpeta "{folder_name}" eliminada exitosamente.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error al eliminar carpeta: {str(e)}'
            }, status=500)


# Cache invalidation signal handlers
def invalidate_cache_on_document_folder_save(sender, instance, **kwargs):
    """
    Signal handler to invalidate cache when a DocumentFolder is saved.
    """
    if instance.curso_id:
        invalidate_folders_cache_for_curso(instance.curso_id)


def invalidate_cache_on_course_document_save(sender, instance, **kwargs):
    """
    Signal handler to invalidate cache when a CourseDocument is saved.
    """
    if instance.folder and instance.folder.curso_id:
        invalidate_folders_cache_for_curso(instance.folder.curso_id)


def invalidate_cache_on_document_access_save(sender, instance, **kwargs):
    """
    Signal handler to invalidate cache when a DocumentAccess is saved.
    """
    # Document access doesn't affect folder listings, so we don't need to invalidate
    # But we could invalidate student-specific cache if needed
    pass


# Cache monitoring and management utilities
def clear_course_documents_cache():
    """
    Clear all course documents related cache.
    
    Returns:
        Number of cache keys deleted
    """
    return invalidate_all_folders_cache()


def get_course_documents_cache_stats(curso_id=None):
    """
    Get cache statistics for course documents.
    
    Args:
        curso_id: Optional specific course ID
        
    Returns:
        Dictionary with cache statistics
    """
    base_stats = CacheMetrics.get_stats()
    
    if curso_id:
        # Get cache hit rate for specific course
        cache_key = generate_cache_key('cfbc:folders_curso', curso_id)
        # In a real implementation, you might track per-key metrics
        pass
    
    return {
        **base_stats,
        'course_specific': curso_id is not None,
    }