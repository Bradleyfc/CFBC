from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, CreateView, View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, Http404
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db import transaction
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


class TeacherDashboardView(LoginRequiredMixin, TeacherPermissionMixin, DetailView):
    """
    Dashboard del profesor para gestionar documentos de un curso específico
    """
    model = Curso
    template_name = 'course_documents/teacher_dashboard.html'  # Template principal corregido
    context_object_name = 'curso'
    pk_url_kwarg = 'curso_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = self.get_object()

        # Obtener todas las carpetas del curso
        folders = DocumentFolder.objects.filter(curso=curso).order_by('name')
        context['folders'] = folders

        # Obtener estadísticas
        total_documents = CourseDocument.objects.filter(folder__curso=curso).count()
        total_folders = folders.count()
        # Contar estudiantes matriculados activos
        total_students = Matriculas.objects.filter(
            course=curso,
            activo=True
        ).count()

        # Calcular promedio de documentos por carpeta
        average_docs_per_folder = total_documents / total_folders if total_folders > 0 else 0

        context['stats'] = {
            'total_folders': total_folders,
            'total_documents': total_documents,
            'total_students': total_students,
            'average_docs_per_folder': average_docs_per_folder,
        }

        # Formularios para crear carpeta y subir documento
        context['folder_form'] = DocumentFolderForm()
        context['document_form'] = CourseDocumentForm()

        return context


class CreateFolderView(LoginRequiredMixin, TeacherPermissionMixin, CreateView):
    """
    Vista para crear nuevas carpetas de documentos
    """
    model = DocumentFolder
    form_class = DocumentFolderForm
    template_name = 'course_documents/create_folder.html'

    def get_curso(self):
        """Obtener el curso desde la URL"""
        return get_object_or_404(Curso, id=self.kwargs['curso_id'])

    def form_valid(self, form):
        """Procesar formulario válido"""
        curso = self.get_curso()

        # Verificar que el usuario es el profesor del curso
        if curso.teacher != self.request.user:
            raise PermissionDenied("No tienes permisos para crear carpetas en este curso")

        # Asignar curso y usuario
        form.instance.curso = curso
        form.instance.created_by = self.request.user

        try:
            with transaction.atomic():
                response = super().form_valid(form)

                # Registrar en audit log
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

    def form_invalid(self, form):
        """Manejar formulario inválido"""
        curso = self.get_curso()
        messages.error(
            self.request,
            'Error al crear la carpeta. Verifica que el nombre sea válido.'
        )
        return redirect('course_documents:teacher_dashboard', curso_id=curso.id)

    def get_success_url(self):
        """URL de redirección después de crear carpeta"""
        return reverse('course_documents:teacher_dashboard', kwargs={'curso_id': self.kwargs['curso_id']})


class UploadDocumentView(LoginRequiredMixin, TeacherPermissionMixin, CreateView):
    """
    Vista para subir documentos a una carpeta específica
    """
    model = CourseDocument
    form_class = CourseDocumentForm
    template_name = 'course_documents/upload_document.html'

    def get_curso(self):
        """Obtener el curso desde la URL"""
        return get_object_or_404(Curso, id=self.kwargs['curso_id'])

    def get_folder(self):
        """Obtener la carpeta desde la URL"""
        return get_object_or_404(
            DocumentFolder,
            id=self.kwargs['folder_id'],
            curso_id=self.kwargs['curso_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curso'] = self.get_curso()
        context['folder'] = self.get_folder()
        return context

    def form_valid(self, form):
        """Procesar formulario válido"""
        curso = self.get_curso()
        folder = self.get_folder()

        # Verificar que el usuario es el profesor del curso
        if curso.teacher != self.request.user:
            raise PermissionDenied("No tienes permisos para subir documentos en este curso")

        # Verificar duplicados antes de guardar
        try:
            form.check_duplicate_document(folder)
        except ValidationError as e:
            # Agregar el error específico de duplicado
            messages.error(
                self.request,
                f'⚠️ Documento duplicado: {e.message}'
            )
            return self.form_invalid(form)

        # Asignar carpeta y usuario ANTES de guardar
        document = form.save(commit=False)
        document.folder = folder
        document.uploaded_by = self.request.user

        # Calcular tamaño del archivo
        if document.file:
            document.file_size = document.file.size

        try:
            with transaction.atomic():
                # Guardar el documento
                document.save()
                self.object = document

                # Registrar en audit log
                AuditLog.log_action(
                    user=self.request.user,
                    action='document_uploaded',
                    curso=curso,
                    folder=folder,
                    document=self.object,
                    details=f'Documento "{self.object.name}" subido a carpeta "{folder.name}"'
                )

                # Enviar notificaciones a estudiantes
                NotificationService.notify_new_document(self.object)

                # Actualizar indicadores de contenido nuevo
                NotificationService.update_content_indicators(curso)

                messages.success(
                    self.request,
                    f'✅ Documento "{self.object.name}" subido exitosamente.'
                )

                return redirect(self.get_success_url())

        except ValidationError as e:
            # Error de validación del modelo (duplicado a nivel de BD)
            error_msg = str(e.message_dict.get('name', ['Error de validación'])[0]) if hasattr(e, 'message_dict') else str(e)
            messages.error(
                self.request,
                f'⚠️ {error_msg}'
            )
            return self.form_invalid(form)
        except Exception as e:
            messages.error(
                self.request,
                f'❌ Error al subir el documento: {str(e)}'
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Manejar formulario inválido"""
        curso = self.get_curso()
        folder = self.get_folder()
        
        # Si no hay mensajes específicos, agregar uno genérico
        if not messages.get_messages(self.request):
            messages.error(
                self.request,
                '❌ Error al subir el documento. Verifica el archivo y el nombre.'
            )
        
        # Redirigir de vuelta a la página de la carpeta (no al formulario de subida)
        return redirect('course_documents:folder_detail', curso_id=curso.id, folder_id=folder.id)

    def get_success_url(self):
        """URL de redirección después de subir documento"""
        return reverse('course_documents:folder_detail', kwargs={
            'curso_id': self.kwargs['curso_id'],
            'folder_id': self.kwargs['folder_id']
        })


class FolderDetailView(LoginRequiredMixin, TeacherPermissionMixin, DetailView):
    """
    Vista detallada de una carpeta para el profesor
    """
    model = DocumentFolder
    template_name = 'course_documents/folder_detail.html'
    context_object_name = 'folder'
    pk_url_kwarg = 'folder_id'

    def get_queryset(self):
        """Filtrar carpetas por curso"""
        return DocumentFolder.objects.filter(curso_id=self.kwargs['curso_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder = self.get_object()

        # Obtener documentos de la carpeta
        documents = CourseDocument.objects.filter(folder=folder).order_by('-uploaded_at')
        context['documents'] = documents
        context['curso'] = folder.curso

        # Formulario para subir documento
        context['document_form'] = CourseDocumentForm()

        return context


class DeleteFolderView(LoginRequiredMixin, TeacherPermissionMixin, View):
    """
    Vista para eliminar una carpeta (AJAX)
    """

    def post(self, request, curso_id, folder_id):
        """Eliminar carpeta"""
        curso = get_object_or_404(Curso, id=curso_id)
        folder = get_object_or_404(DocumentFolder, id=folder_id, curso=curso)

        # Verificar permisos
        if curso.teacher != request.user:
            return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

        try:
            with transaction.atomic():
                folder_name = folder.name

                # Eliminar archivos físicos de los documentos
                for document in folder.documents.all():
                    if document.file and default_storage.exists(document.file.name):
                        default_storage.delete(document.file.name)

                # Eliminar carpeta (cascade eliminará documentos)
                folder.delete()

                # Registrar en audit log
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


class DeleteDocumentView(LoginRequiredMixin, TeacherPermissionMixin, View):
    """
    Vista para eliminar un documento (AJAX)
    """

    def post(self, request, curso_id, document_id):
        """Eliminar documento"""
        curso = get_object_or_404(Curso, id=curso_id)
        document = get_object_or_404(CourseDocument, id=document_id, folder__curso=curso)

        # Verificar permisos
        if curso.teacher != request.user:
            return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)

        try:
            with transaction.atomic():
                document_name = document.name
                folder_name = document.folder.name

                # Eliminar archivo físico
                if document.file and default_storage.exists(document.file.name):
                    default_storage.delete(document.file.name)

                # Eliminar documento
                document.delete()

                # Registrar en audit log
                AuditLog.log_action(
                    user=request.user,
                    action='document_deleted',
                    curso=curso,
                    folder=document.folder,
                    details=f'Documento "{document_name}" eliminado de carpeta "{folder_name}"'
                )

                return JsonResponse({
                    'success': True,
                    'message': f'Documento "{document_name}" eliminado exitosamente.'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al eliminar documento: {str(e)}'
            }, status=500)


class StudentDashboardView(LoginRequiredMixin, StudentPermissionMixin, DetailView):
    """
    Dashboard del estudiante para acceder a documentos de un curso específico
    """
    model = Curso
    template_name = 'course_documents/student_dashboard.html'
    context_object_name = 'curso'
    pk_url_kwarg = 'curso_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = self.get_object()

        # Obtener todas las carpetas del curso que tienen documentos
        folders = DocumentFolder.objects.filter(
            curso=curso,
            documents__isnull=False
        ).distinct().order_by('name')

        # Agregar información de documentos a cada carpeta
        for folder in folders:
            folder.document_list = CourseDocument.objects.filter(
                folder=folder
            ).order_by('-uploaded_at')
            
            # Calcular documentos nuevos para este estudiante
            folder.new_documents_count = folder.get_new_documents_count(self.request.user)

        context['folders'] = folders

        # Obtener estadísticas para el estudiante
        total_documents = CourseDocument.objects.filter(folder__curso=curso).count()
        total_folders = folders.count()

        # Verificar si hay contenido nuevo usando el servicio
        has_new_content = ContentIndicatorService.has_new_content(curso, self.request.user)

        context['stats'] = {
            'total_folders': total_folders,
            'total_documents': total_documents,
            'has_new_content': has_new_content,
        }

        return context

    def get(self, request, *args, **kwargs):
        """Override get to mark content as seen"""
        response = super().get(request, *args, **kwargs)

        # Actualizar la fecha de última verificación del estudiante
        curso = self.get_object()
        ContentIndicatorService.update_last_checked(curso, request.user)
        
        # Registrar en audit log
        AuditLog.log_action(
            user=request.user,
            action='content_viewed',
            curso=curso,
            details=f'Estudiante accedió al dashboard del curso "{curso.name}"'
        )

        return response


class DownloadDocumentView(LoginRequiredMixin, StudentPermissionMixin, View):
    """
    Vista para descargar documentos con control de acceso y logging
    """

    def get(self, request, curso_id, document_id):
        """Descargar documento"""
        curso = get_object_or_404(Curso, id=curso_id)
        document = get_object_or_404(
            CourseDocument,
            id=document_id,
            folder__curso=curso
        )

        # Verificar que el estudiante esté inscrito en el curso
        if not Matriculas.objects.filter(
            course=curso,
            student=request.user,
            activo=True
        ).exists():
            raise PermissionDenied("No tienes acceso a este documento")

        try:
            # Registrar acceso al documento
            DocumentAccess.objects.create(
                document=document,
                student=request.user
            )

            # Registrar en audit log
            AuditLog.log_action(
                user=request.user,
                action='document_downloaded',
                curso=curso,
                folder=document.folder,
                document=document,
                details=f'Documento "{document.name}" descargado por estudiante'
            )

            # Verificar que el archivo existe
            if not document.file or not default_storage.exists(document.file.name):
                messages.error(request, 'El archivo no está disponible.')
                return redirect('course_documents:student_dashboard', curso_id=curso.id)

            # Obtener el archivo
            file_path = document.file.path if hasattr(document.file, 'path') else document.file.name

            # Determinar el tipo MIME
            content_type, _ = mimetypes.guess_type(document.file.name)
            if not content_type:
                content_type = 'application/octet-stream'

            # Crear respuesta HTTP con el archivo
            with default_storage.open(document.file.name, 'rb') as file:
                response = HttpResponse(file.read(), content_type=content_type)

                # Configurar headers para descarga
                filename = os.path.basename(document.file.name)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Content-Length'] = document.file_size or document.file.size

                return response

        except Exception as e:
            # Registrar error en audit log
            AuditLog.log_action(
                user=request.user,
                action='download_error',
                curso=curso,
                document=document,
                details=f'Error al descargar documento "{document.name}": {str(e)}'
            )

            messages.error(request, f'Error al descargar el archivo: {str(e)}')
            return redirect('course_documents:student_dashboard', curso_id=curso.id)


class StudentFolderDetailView(LoginRequiredMixin, StudentPermissionMixin, DetailView):
    """
    Vista detallada de una carpeta para el estudiante
    """
    model = DocumentFolder
    template_name = 'course_documents/student_folder_detail.html'
    context_object_name = 'folder'
    pk_url_kwarg = 'folder_id'

    def get_queryset(self):
        """Filtrar carpetas por curso"""
        return DocumentFolder.objects.filter(curso_id=self.kwargs['curso_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        folder = self.get_object()

        # Obtener documentos de la carpeta
        documents = CourseDocument.objects.filter(folder=folder).order_by('-uploaded_at')
        context['documents'] = documents
        context['curso'] = folder.curso

        # Obtener estadísticas de acceso del estudiante
        user_downloads = DocumentAccess.objects.filter(
            document__folder=folder,
            student=self.request.user
        ).count()

        context['user_stats'] = {
            'downloads_count': user_downloads,
        }

        return context

    def get(self, request, *args, **kwargs):
        """Override get to update folder access"""
        response = super().get(request, *args, **kwargs)
        
        # Actualizar el acceso a la carpeta
        folder = self.get_object()
        from .models import FolderAccess
        
        folder_access, created = FolderAccess.objects.get_or_create(
            folder=folder,
            student=request.user
        )
        
        # Si no es la primera vez, actualizar last_accessed (se hace automáticamente por auto_now=True)
        if not created:
            folder_access.save()  # Esto actualiza last_accessed
        
        # Actualizar el indicador global del curso
        ContentIndicatorService.update_last_checked(folder.curso, request.user)
        
        # Registrar en audit log
        AuditLog.log_action(
            user=request.user,
            action='folder_accessed',
            curso=folder.curso,
            folder=folder,
            details=f'Estudiante accedió a la carpeta "{folder.name}"'
        )
        
        return response


class StudentDocumentHistoryView(LoginRequiredMixin, StudentPermissionMixin, DetailView):
    """
    Vista del historial de descargas del estudiante para un curso
    """
    model = Curso
    template_name = 'course_documents/student_history.html'
    context_object_name = 'curso'
    pk_url_kwarg = 'curso_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curso = self.get_object()

        # Obtener historial de descargas del estudiante en este curso
        downloads = DocumentAccess.objects.filter(
            document__folder__curso=curso,
            student=self.request.user
        ).select_related('document', 'document__folder').order_by('-accessed_at')

        context['downloads'] = downloads

        # Estadísticas del estudiante
        total_downloads = downloads.count()
        unique_documents = downloads.values('document').distinct().count()

        context['stats'] = {
            'total_downloads': total_downloads,
            'unique_documents': unique_documents,
        }

        return context