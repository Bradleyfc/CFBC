"""
Django REST Framework API views for Blog app.

Provides public and authenticated endpoints for blog content,
comment moderation, and editorial workflows.

Validates Requirements: 3.1-3.6, 7.1-7.11, 8.1-8.12, 9.1-9.12, 10.1, 10.11-10.13, 10.19-10.22
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from .models import (
    Noticia,
    Categoria,
    ReporteComentario,
    SancionUsuario,
    MetricaComunidad,
)
from .serializers import (
    BlogPostSerializer,
    BlogPostListSerializer,
    CategorySerializer,
    CommentReportSerializer,
    UserSanctionSerializer,
    CommunityMetricsSerializer,
)


# ===== Pagination =====

class BlogPostPagination(PageNumberPagination):
    """Pagination for blog posts - 20 items per page."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ===== Permission Classes =====

class IsBlogAuthor(IsAuthenticated):
    """Permission class to check if user is a Blog Author."""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(name='Blog Autor').exists()


class IsBlogModerator(IsAuthenticated):
    """Permission class to check if user is a Blog Moderator."""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(name='Blog Moderador').exists()


class IsEditor(IsAuthenticated):
    """Permission class to check if user is an Editor."""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(name='Editor').exists()


# ===== Public Blog Endpoints =====
# Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 10.1

class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only ViewSet for published blog posts.
    
    Features:
    - Pagination (20 posts per page)
    - Category filtering
    - Search by title/content
    - Ordering by date
    
    Validates Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    
    permission_classes = [AllowAny]
    pagination_class = BlogPostPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'destacada']
    search_fields = ['titulo', 'contenido', 'resumen']
    ordering_fields = ['fecha_publicacion', 'fecha_creacion']
    ordering = ['-fecha_publicacion']
    
    def get_queryset(self):
        """Return only published posts with public visibility."""
        return Noticia.objects.filter(
            estado='publicado',
            visibilidad__in=['publico', 'indexable']
        ).select_related('categoria', 'autor')
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve, list serializer for list."""
        if self.action == 'retrieve':
            return BlogPostSerializer
        return BlogPostListSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single blog post by slug or ID.
        Uses slug in URL path.
        """
        # Try to get by slug first, then by pk
        slug = kwargs.get('pk')
        try:
            instance = self.get_queryset().get(slug=slug)
        except (Noticia.DoesNotExist, ValueError):
            try:
                instance = self.get_queryset().get(pk=slug)
            except (Noticia.DoesNotExist, ValueError):
                return Response(
                    {'detail': 'No se encontró la noticia.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only ViewSet for blog categories.
    
    Validates Requirements: 3.3
    """
    
    queryset = Categoria.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None  # No pagination for categories


# ===== Blog Author Endpoints =====
# Requirements: 7.1, 7.2, 7.3, 7.4, 7.6, 7.7, 7.8, 7.9, 7.11, 10.11, 10.17, 10.18

class AuthorPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog authors to manage their posts.
    
    Features:
    - List posts by authenticated author
    - Filter by status (borrador, pendiente_revision, publicado, archivado)
    - Create new posts
    - Edit own posts
    - Delete own draft posts
    
    Validates Requirements: 7.1, 7.2, 7.3, 7.4, 7.6, 7.7, 7.8, 7.9, 7.11
    """
    
    serializer_class = BlogPostSerializer
    permission_classes = [IsBlogAuthor]
    pagination_class = BlogPostPagination
    
    def get_queryset(self):
        """Return posts authored by the authenticated user."""
        return Noticia.objects.filter(
            autor=self.request.user
        ).select_related('categoria', 'autor')
    
    @action(detail=False, methods=['get'], url_path='by-status/(?P<estado>[^/.]+)')
    def by_status(self, request, estado=None):
        """
        Get posts filtered by status.
        URL: /api/author/posts/by-status/{estado}/
        
        Validates Requirements: 7.3, 7.4
        """
        valid_estados = ['borrador', 'pendiente_revision', 'publicado', 'archivado']
        
        if estado not in valid_estados:
            return Response(
                {'detail': f'Estado inválido. Opciones: {", ".join(valid_estados)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        posts = self.get_queryset().filter(estado=estado)
        page = self.paginate_queryset(posts)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Set the author to the authenticated user when creating a post."""
        serializer.save(autor=self.request.user, estado='borrador')
    
    def perform_update(self, serializer):
        """Only allow authors to edit their own posts."""
        if serializer.instance.autor != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No puedes editar posts de otros autores.")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only allow deletion of draft posts by the author."""
        if instance.autor != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No puedes eliminar posts de otros autores.")
        
        if instance.estado != 'borrador':
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Solo puedes eliminar borradores.")
        
        instance.delete()


# ===== Blog Moderator Endpoints =====
# Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.12, 10.12, 10.21, 10.22

class ModeratorReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for blog moderators to view and manage comment reports.
    
    Features:
    - List pending reports
    - View report details
    - Approve/reject reports
    
    Validates Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
    """
    
    serializer_class = CommentReportSerializer
    permission_classes = [IsBlogModerator]
    pagination_class = BlogPostPagination
    
    def get_queryset(self):
        """Return pending reports."""
        return ReporteComentario.objects.filter(
            estado='pendiente'
        ).select_related('comentario', 'reportado_por', 'comentario__noticia')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a report and hide the comment.
        
        Validates Requirements: 8.7
        """
        report = self.get_object()
        
        if report.estado != 'pendiente':
            return Response(
                {'detail': 'Este reporte ya fue procesado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update report
        report.estado = 'resuelto_retirado'
        report.resuelto_por = request.user
        report.fecha_resolucion = timezone.now()
        report.save()
        
        # Hide comment
        report.comentario.activo = False
        report.comentario.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a report and keep the comment active.
        
        Validates Requirements: 8.7
        """
        report = self.get_object()
        
        if report.estado != 'pendiente':
            return Response(
                {'detail': 'Este reporte ya fue procesado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update report
        report.estado = 'resuelto_mantenido'
        report.resuelto_por = request.user
        report.fecha_resolucion = timezone.now()
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)


class ModeratorSanctionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for blog moderators to view active sanctions.
    
    Validates Requirements: 8.2, 8.8, 8.9, 8.10
    """
    
    serializer_class = UserSanctionSerializer
    permission_classes = [IsBlogModerator]
    pagination_class = BlogPostPagination
    
    def get_queryset(self):
        """Return active sanctions."""
        return SancionUsuario.objects.filter(
            activa=True
        ).select_related('usuario', 'aplicada_por')


@api_view(['GET'])
@permission_classes([IsBlogModerator])
def moderator_metrics_view(request):
    """
    Get community metrics for the current month.
    
    Validates Requirements: 8.3, 8.12, 10.22
    """
    # Get or create metrics for current month
    today = timezone.now().date()
    first_day = today.replace(day=1)
    
    metrics, created = MetricaComunidad.objects.get_or_create(
        fecha=first_day,
        defaults={
            'total_reportes': ReporteComentario.objects.filter(
                fecha_reporte__year=today.year,
                fecha_reporte__month=today.month
            ).count(),
            'total_comentarios': 0,  # Would need to track this
            'total_sanciones': SancionUsuario.objects.filter(
                fecha_inicio__year=today.year,
                fecha_inicio__month=today.month
            ).count(),
        }
    )
    
    serializer = CommunityMetricsSerializer(metrics, context={'request': request})
    return Response(serializer.data)


# ===== Editor Endpoints =====
# Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.8, 9.9, 9.10, 9.12, 10.13, 10.19, 10.20

class EditorPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for editors to review and manage posts.
    
    Features:
    - View posts pending review
    - View recently published posts
    - Search posts by author
    - Update post status and notas_editor
    - Publish or reject posts
    
    Validates Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.8, 9.9, 9.10, 9.12
    """
    
    serializer_class = BlogPostSerializer
    permission_classes = [IsEditor]
    pagination_class = BlogPostPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['autor__username', 'autor__first_name', 'autor__last_name']
    
    def get_queryset(self):
        """Return posts for editorial review."""
        return Noticia.objects.select_related('categoria', 'autor')
    
    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """
        Get posts pending review (estado = pendiente_revision).
        
        Validates Requirements: 9.1, 9.4
        """
        posts = self.get_queryset().filter(estado='pendiente_revision')
        page = self.paginate_queryset(posts)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recently_published(self, request):
        """
        Get recently published posts (last 7 days).
        
        Validates Requirements: 9.2, 9.5
        """
        seven_days_ago = timezone.now() - timedelta(days=7)
        posts = self.get_queryset().filter(
            estado='publicado',
            fecha_publicacion__gte=seven_days_ago
        )
        page = self.paginate_queryset(posts)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish a post (change estado to publicado).
        
        Validates Requirements: 9.8, 9.10
        """
        post = self.get_object()
        
        if post.estado == 'publicado':
            return Response(
                {'detail': 'Este post ya está publicado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        post.estado = 'publicado'
        post.fecha_publicacion = timezone.now()
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a post and send it back to the author with notes.
        
        Validates Requirements: 9.9, 9.10
        """
        post = self.get_object()
        notes = request.data.get('notas_editor', '')
        
        if not notes:
            return Response(
                {'detail': 'Debes proporcionar notas del editor al rechazar un post.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        post.estado = 'borrador'
        post.notas_editor = notes
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_notes(self, request, pk=None):
        """
        Update notas_editor field.
        
        Validates Requirements: 9.6, 9.10
        """
        post = self.get_object()
        notes = request.data.get('notas_editor', '')
        
        post.notas_editor = notes
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)
