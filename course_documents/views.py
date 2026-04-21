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


class TeacherDashboardView(LoginRequiredMixin, TeacherPermissionMixin, DetailView):
    """
    Dashboard del profesor para gestionar documentos de un curso específico
    """
    model = Curso
    template_name = 'course_documents/teacher_dashboard.html'
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
        
        # Asignar carpeta y usuario
        form.instance.folder = folder
        form.instance.uploaded_by = self.request.user
        
        # Calcular tamaño del archivo
        if form.instance.file:
            form.instance.file_size = form.instance.file.size
        
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                
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
                    f'Documento "{self.object.name}" subido exitosamente.'
                )
                
                return response
                
        except Exception as e:
            messages.error(
                self.request, 
                f'Error al subir el documento: {str(e)}'
            )
            return redirect('course_documents:teacher_dashboard', curso_id=curso.id)

    def form_invalid(self, form):
        """Manejar formulario inválido - mostrar errores específicos"""
        curso = self.get_curso()
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect('course_documents:teacher_dashboard', curso_id=curso.id)

    def get_success_url(self):
        """URL de redirección después de subir documento"""
        return reverse('course_documents:teacher_dashboard', kwargs={'curso_id': self.kwargs['curso_id']})


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
        
        # Marcar contenido como visto usando el servicio
        curso = self.get_object()
        if ContentIndicatorService.deactivate_indicator_for_student(curso, request.user):
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
            # Ignorar prefetch requests
            is_prefetch = (
                request.META.get('HTTP_PURPOSE', '').lower() == 'prefetch' or
                request.META.get('HTTP_SEC_PURPOSE', '').lower() == 'prefetch' or
                request.META.get('HTTP_X_PURPOSE', '').lower() == 'prefetch'
            )
            if is_prefetch:
                return HttpResponse(status=204)

            # Verificar que el archivo existe
            if not document.file or not default_storage.exists(document.file.name):
                messages.error(request, 'El archivo no está disponible.')
                return redirect('course_documents:student_dashboard', curso_id=curso.id)

            # Determinar el tipo MIME
            content_type, _ = mimetypes.guess_type(document.file.name)
            if not content_type:
                content_type = 'application/octet-stream'

            # Leer el archivo
            with default_storage.open(document.file.name, 'rb') as file:
                file_content = file.read()

            # Usar token de sesión para evitar registros duplicados por antivirus/extensiones.
            # Solo la primera request en un intervalo de 5 segundos registra la descarga.
            import time
            session_key = f'dl_token_{request.user.id}_{document_id}'
            last_registered = request.session.get(session_key, 0)
            now = time.time()
            should_register = (now - last_registered) > 5

            if should_register:
                request.session[session_key] = now
                DocumentAccess.objects.create(
                    document=document,
                    student=request.user
                )
                AuditLog.log_action(
                    user=request.user,
                    action='document_downloaded',
                    curso=curso,
                    folder=document.folder,
                    document=document,
                    details=f'Documento "{document.name}" descargado por estudiante'
                )

            response = HttpResponse(file_content, content_type=content_type)
            filename = os.path.basename(document.file.name)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = document.file_size or len(file_content)
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
            response['X-Robots-Tag'] = 'noindex'

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
        # IMPORTANTE: {% regroup %} requiere que los datos estén ordenados por el campo de agrupación.
        # Agrupamos por accessed_at.date, así que ordenamos por fecha descendente y luego por hora.
        from django.db.models.functions import TruncDate
        downloads = DocumentAccess.objects.filter(
            document__folder__curso=curso,
            student=self.request.user
        ).select_related('document', 'document__folder').annotate(
            download_date=TruncDate('accessed_at')
        ).order_by('-download_date', '-accessed_at')
        
        context['downloads'] = downloads
        
        # Estadísticas del estudiante
        total_downloads = downloads.count()
        unique_documents = downloads.values('document').distinct().count()
        
        context['stats'] = {
            'total_downloads': total_downloads,
            'unique_documents': unique_documents,
        }
        
        return context


# ─────────────────────────────────────────────────────────────────────────────
# Vistas de administración: gestión de documentos por curso académico
# ─────────────────────────────────────────────────────────────────────────────

class AdminDiagnosticoView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vista de diagnóstico: muestra el estado real de BD vs disco."""

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['Administración', 'Secretaría']
        ).exists()

    def get(self, request):
        from principal.models import CursoAcademico
        from django.conf import settings as dj_settings
        import os

        lineas = []

        # ── 1. Cursos académicos ─────────────────────────────────────────────
        lineas.append("=== CURSOS ACADÉMICOS EN BD ===")
        for ca in CursoAcademico.objects.all().order_by('id'):
            lineas.append(f"  ID={ca.id}  nombre='{ca.nombre}'  activo={ca.activo}  archivado={ca.archivado}")

        # ── 2. DocumentFolder en BD ──────────────────────────────────────────
        lineas.append("")
        lineas.append("=== CARPETAS (DocumentFolder) EN BD ===")
        folders = DocumentFolder.objects.select_related('curso__curso_academico').all()
        lineas.append(f"  Total carpetas: {folders.count()}")
        for f in folders:
            ca = f.curso.curso_academico
            ca_info = f"CA_ID={ca.id} '{ca.nombre}'" if ca else "sin CursoAcademico"
            lineas.append(f"  Folder ID={f.id}  nombre='{f.name}'  curso_id={f.curso_id}  {ca_info}")

        # ── 3. CourseDocument en BD ──────────────────────────────────────────
        lineas.append("")
        lineas.append("=== DOCUMENTOS (CourseDocument) EN BD ===")
        docs = CourseDocument.objects.select_related('folder__curso__curso_academico').all()
        lineas.append(f"  Total documentos: {docs.count()}")
        for d in docs:
            ca = d.folder.curso.curso_academico
            ca_info = f"CA='{ca.nombre}'" if ca else "CA=NULL"
            lineas.append(
                f"  Doc ID={d.id}  '{d.name}'  "
                f"folder_id={d.folder_id}  curso_id={d.folder.curso_id}  "
                f"{ca_info}  file='{d.file}'"
            )

        # ── 4. Archivos en disco ─────────────────────────────────────────────
        lineas.append("")
        lineas.append("=== ARCHIVOS EN media/course_documents/ ===")
        media_base = os.path.join(dj_settings.MEDIA_ROOT, 'course_documents')
        if os.path.exists(media_base):
            for cdir in sorted(os.listdir(media_base)):
                cpath = os.path.join(media_base, cdir)
                if not os.path.isdir(cpath):
                    continue
                for fdir in sorted(os.listdir(cpath)):
                    fpath = os.path.join(cpath, fdir)
                    if not os.path.isdir(fpath):
                        continue
                    archivos = [f for f in os.listdir(fpath) if os.path.isfile(os.path.join(fpath, f))]
                    for fname in archivos:
                        rel = f'course_documents/{cdir}/{fdir}/{fname}'
                        en_bd = CourseDocument.objects.filter(file=rel).exists()
                        lineas.append(
                            f"  curso_id={cdir}  folder_id={fdir}  "
                            f"archivo='{fname}'  en_BD={en_bd}"
                        )
        else:
            lineas.append("  Directorio no existe")

        # ── 5. Cursos 163, 166, 168 ──────────────────────────────────────────
        lineas.append("")
        lineas.append("=== CURSOS CON ARCHIVOS EN DISCO (163, 166, 168) ===")
        from principal.models import Curso
        for cid in [163, 166, 168]:
            try:
                c = Curso.objects.select_related('curso_academico').get(id=cid)
                ca = c.curso_academico
                ca_info = f"CA_ID={ca.id} '{ca.nombre}' archivado={ca.archivado}" if ca else "curso_academico=NULL"
                lineas.append(f"  Curso ID={cid}  '{c.name}'  {ca_info}")
            except Curso.DoesNotExist:
                lineas.append(f"  Curso ID={cid}  NO EXISTE EN BD")

        texto = "\n".join(lineas)
        from django.http import HttpResponse
        return HttpResponse(f"<pre style='font-family:monospace;padding:20px'>{texto}</pre>")


class AdminDocumentosView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Vista para que el administrador gestione documentos de cursos académicos.
    Usa DocumentFolder.curso_academico como fuente de verdad, que se preserva
    aunque el Curso sea eliminado al archivar.
    Para carpetas antiguas sin curso_academico en BD, cae al escaneo de disco.
    """
    template_name = 'course_documents/admin_documentos.html'

    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name__in=['Administración', 'Secretaría']).exists()
        )

    def get(self, request):
        from principal.models import CursoAcademico, Curso as CursoModel
        from collections import defaultdict

        # Todos los cursos académicos para el selector
        cursos_academicos = CursoAcademico.objects.all().order_by('-fecha_creacion')

        # Contar documentos reales por CA
        for ca in cursos_academicos:
            folders = DocumentFolder.objects.filter(curso_academico=ca)
            ca.total_documentos = CourseDocument.objects.filter(folder__in=folders).count()

        # Filtro seleccionado
        curso_academico_id = request.GET.get('curso_academico')
        curso_academico_sel = None
        cursos_con_docs = []
        total_docs_sel = 0
        total_size_sel = 0

        if curso_academico_id:
            curso_academico_sel = get_object_or_404(CursoAcademico, id=curso_academico_id)

            # Carpetas vinculadas a este CA en BD
            folders_qs = (
                DocumentFolder.objects
                .filter(curso_academico=curso_academico_sel)
                .prefetch_related('documents__uploaded_by')
                .select_related('curso__teacher')
                .order_by('curso_id', 'name')
            )

            # Agrupar por curso (puede ser NULL si el curso fue eliminado al archivar)
            grupos = defaultdict(list)
            for folder in folders_qs:
                grupos[folder.curso_id].append(folder)

            for curso_id_key, folders in grupos.items():
                if curso_id_key:
                    try:
                        curso_obj = CursoModel.objects.select_related('teacher').get(id=curso_id_key)
                        curso_nombre = curso_obj.name
                        profesor_nombre = curso_obj.teacher.get_full_name() or curso_obj.teacher.username
                    except CursoModel.DoesNotExist:
                        curso_obj = None
                        curso_nombre = f'Curso #{curso_id_key} (archivado)'
                        profesor_nombre = '—'
                else:
                    curso_obj = None
                    first_folder = folders[0]
                    profesor_nombre = (
                        first_folder.created_by.get_full_name() or first_folder.created_by.username
                        if first_folder.created_by else '—'
                    )
                    curso_nombre = f'Curso archivado'

                carpetas_lista = []
                for folder in folders:
                    docs_list = list(folder.documents.all())
                    if docs_list:
                        carpetas_lista.append({
                            'folder': folder,
                            'folder_id': folder.id,
                            'folder_nombre': folder.name,
                            'documentos': docs_list,
                            'cantidad': len(docs_list),
                            'desde_disco': False,
                        })

                if not carpetas_lista:
                    continue

                total_docs_curso = sum(c['cantidad'] for c in carpetas_lista)
                total_size_curso = sum(
                    doc.file_size or 0
                    for c in carpetas_lista
                    for doc in c['documentos']
                )

                cursos_con_docs.append({
                    'curso_id': curso_id_key or 0,
                    'curso_obj': curso_obj,
                    'curso_nombre': curso_nombre,
                    'profesor_nombre': profesor_nombre,
                    'carpetas': carpetas_lista,
                    'total_docs': total_docs_curso,
                    'total_size': total_size_curso,
                    'desde_disco': False,
                })
                total_docs_sel += total_docs_curso
                total_size_sel += total_size_curso

        return render(request, self.template_name, {
            'cursos_academicos': cursos_academicos,
            'curso_academico_sel': curso_academico_sel,
            'cursos_con_docs': cursos_con_docs,
            'total_docs_sel': total_docs_sel,
            'total_size_sel': total_size_sel,
        })


class AdminEliminarDocumentoView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Elimina un documento individual desde el panel de administración.
    """

    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name__in=['Administración', 'Secretaría']).exists()
        )

    def post(self, request, document_id):
        document = get_object_or_404(CourseDocument, id=document_id)
        curso = document.folder.curso
        curso_academico_id = document.folder.curso_academico_id  # Usar curso_academico de la carpeta

        try:
            with transaction.atomic():
                doc_name = document.name
                # Eliminar archivo físico
                if document.file and default_storage.exists(document.file.name):
                    default_storage.delete(document.file.name)
                document.delete()

                curso_nombre = curso.name if curso else f'Curso archivado'
                AuditLog.log_action(
                    user=request.user,
                    action='document_deleted',
                    curso=curso,
                    folder=document.folder,
                    details=f'[Admin] Documento "{doc_name}" eliminado del curso "{curso_nombre}"'
                )

            messages.success(request, f'Documento "{doc_name}" eliminado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el documento: {str(e)}')

        # Redirigir al curso académico correcto
        if curso_academico_id:
            return redirect(
                f"{reverse('course_documents:admin_documentos')}?curso_academico={curso_academico_id}"
            )
        else:
            return redirect(reverse('course_documents:admin_documentos'))


class AdminEliminarCarpetaView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Elimina una carpeta completa (y todos sus documentos) desde el panel de administración.
    """

    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name__in=['Administración', 'Secretaría']).exists()
        )

    def post(self, request, folder_id):
        folder = get_object_or_404(DocumentFolder, id=folder_id)
        curso = folder.curso
        curso_academico_id = folder.curso_academico_id  # Usar curso_academico de la carpeta directamente

        try:
            with transaction.atomic():
                folder_name = folder.name
                total = folder.documents.count()
                # Eliminar archivos físicos
                for doc in folder.documents.all():
                    if doc.file and default_storage.exists(doc.file.name):
                        default_storage.delete(doc.file.name)
                folder.delete()

                curso_nombre = curso.name if curso else f'Curso archivado (carpeta {folder_id})'
                AuditLog.log_action(
                    user=request.user,
                    action='folder_deleted',
                    curso=curso,
                    details=f'[Admin] Carpeta "{folder_name}" con {total} documentos eliminada del curso "{curso_nombre}"'
                )

            messages.success(
                request,
                f'Carpeta "{folder_name}" y sus {total} documento(s) eliminados correctamente.'
            )
        except Exception as e:
            messages.error(request, f'Error al eliminar la carpeta: {str(e)}')

        # Redirigir al curso académico correcto
        if curso_academico_id:
            return redirect(
                f"{reverse('course_documents:admin_documentos')}?curso_academico={curso_academico_id}"
            )
        else:
            return redirect(reverse('course_documents:admin_documentos'))


class AdminEliminarTodosCursoView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Elimina todos los documentos de un curso específico desde el panel de administración.
    """

    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name__in=['Administración', 'Secretaría']).exists()
        )

    def post(self, request, curso_id):
        # curso_id=0 significa "todos los archivos del disco para ese path"
        # pero esta vista solo aplica cuando el Curso existe en BD
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            messages.error(request, f'Curso #{curso_id} no encontrado en BD. Usa la eliminación por disco.')
            return redirect(reverse('course_documents:admin_documentos'))

        curso_academico_id = curso.curso_academico_id
        # También buscar en DocumentFolder por si el curso ya fue desvinculado
        if not curso_academico_id:
            folder = DocumentFolder.objects.filter(curso=curso).first()
            if folder:
                curso_academico_id = folder.curso_academico_id

        try:
            with transaction.atomic():
                total = 0
                for folder in curso.document_folders.all():
                    for doc in folder.documents.all():
                        if doc.file and default_storage.exists(doc.file.name):
                            default_storage.delete(doc.file.name)
                        doc.delete()
                        total += 1

                AuditLog.log_action(
                    user=request.user,
                    action='document_deleted',
                    curso=curso,
                    details=f'[Admin] {total} documentos eliminados del curso "{curso.name}"'
                )

            messages.success(
                request,
                f'Se eliminaron {total} documento(s) del curso "{curso.name}".'
            )
        except Exception as e:
            messages.error(request, f'Error al eliminar documentos: {str(e)}')

        return redirect(
            f"{reverse('course_documents:admin_documentos')}?curso_academico={curso_academico_id}"
        )


class AdminEliminarArchivoDiscoView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Elimina un archivo físico directamente desde disco (sin registro en BD).
    Recibe rel_path y curso_academico_id por POST.
    """

    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name__in=['Administración', 'Secretaría']).exists()
        )

    def post(self, request):
        import os
        from django.conf import settings as dj_settings

        rel_path = request.POST.get('rel_path', '').strip()
        curso_academico_id = request.POST.get('curso_academico_id', '')

        if not rel_path:
            messages.error(request, 'Ruta de archivo no especificada.')
            return redirect(reverse('course_documents:admin_documentos'))

        # Seguridad: solo permitir rutas dentro de course_documents/
        if not rel_path.startswith('course_documents/') or '..' in rel_path:
            messages.error(request, 'Ruta de archivo no válida.')
            return redirect(reverse('course_documents:admin_documentos'))

        abs_path = os.path.join(dj_settings.MEDIA_ROOT, rel_path)
        nombre = os.path.basename(abs_path)

        try:
            if os.path.isfile(abs_path):
                os.remove(abs_path)
                messages.success(request, f'Archivo "{nombre}" eliminado correctamente.')
            else:
                messages.warning(request, f'El archivo "{nombre}" no existe en disco.')
        except Exception as e:
            messages.error(request, f'Error al eliminar "{nombre}": {str(e)}')

        redirect_url = reverse('course_documents:admin_documentos')
        if curso_academico_id:
            redirect_url += f'?curso_academico={curso_academico_id}'
        return redirect(redirect_url)


class AdminEliminarCarpetaDiscoView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Elimina una carpeta completa o todos los archivos de un curso desde disco.
    - Si recibe folder_id en POST: elimina solo esa subcarpeta.
    - Si no: elimina toda la carpeta del curso (curso_id).
    """

    def test_func(self):
        return (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name__in=['Administración', 'Secretaría']).exists()
        )

    def post(self, request, curso_id):
        import os
        import shutil
        from django.conf import settings as dj_settings

        folder_id = request.POST.get('folder_id', '').strip()
        curso_academico_id = request.POST.get('curso_academico_id', '')

        # Obtener curso_academico_id desde la URL si no viene en POST
        if not curso_academico_id:
            curso_academico_id = request.GET.get('curso_academico', '')

        media_base = os.path.join(dj_settings.MEDIA_ROOT, 'course_documents')

        try:
            if folder_id:
                # Eliminar solo la subcarpeta específica
                target = os.path.join(media_base, str(curso_id), str(folder_id))
                if os.path.isdir(target):
                    shutil.rmtree(target)
                    messages.success(request, f'Carpeta {folder_id} del curso #{curso_id} eliminada.')
                else:
                    messages.warning(request, f'La carpeta no existe en disco.')
            else:
                # Eliminar toda la carpeta del curso
                target = os.path.join(media_base, str(curso_id))
                if os.path.isdir(target):
                    shutil.rmtree(target)
                    messages.success(request, f'Todos los archivos del curso #{curso_id} eliminados.')
                else:
                    messages.warning(request, f'No hay archivos en disco para el curso #{curso_id}.')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')

        redirect_url = reverse('course_documents:admin_documentos')
        if curso_academico_id:
            redirect_url += f'?curso_academico={curso_academico_id}'
        return redirect(redirect_url)
