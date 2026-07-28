package com.cfbc.app.presentation.model

/**
 * UI-friendly models that ViewModels expose to screens.
 * These transform repository DTOs into clean, display-ready objects
 * with formatted strings and computed properties.
 */

// =============================================================================
// Auth
// =============================================================================

data class AuthUiState(
    val isAuthenticated: Boolean = false,
    val username: String? = null,
    val groups: List<String> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

// =============================================================================
// Courses
// =============================================================================

data class CourseUiModel(
    val id: Int,
    val name: String,
    val description: String?,
    val area: String,
    val areaDisplay: String,
    val tipo: String,
    val tipoDisplay: String,
    val teacherName: String,
    val status: String,
    val statusDisplay: String,
    val dynamicStatus: String,
    val dynamicStatusDisplay: String,
    val startDate: String?,
    val enrollmentDeadline: String?,
    val imageUrl: String?,
    val cursoAcademicoNombre: String?
)

data class HomePageUiModel(
    val availableCourses: List<CourseUiModel>,
    val latestNews: List<BlogPostListItemUiModel>
)

data class CourseListUiState(
    val courses: List<CourseUiModel> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val selectedArea: String? = null,
    val selectedTipo: String? = null
)

data class CourseDetailUiState(
    val course: CourseUiModel? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

data class HomePageUiState(
    val data: HomePageUiModel? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

// =============================================================================
// Blog
// =============================================================================

data class BlogPostListItemUiModel(
    val id: Int,
    val titulo: String,
    val slug: String,
    val resumen: String,
    val imagenPrincipalUrl: String?,
    val categoria: String,
    val autorUsername: String,
    val fechaPublicacion: String?,
    val destacada: Boolean
)

data class BlogPostDetailUiModel(
    val id: Int,
    val titulo: String,
    val slug: String,
    val resumen: String,
    val contenido: String,
    val imagenPrincipalUrl: String?,
    val categoria: String,
    val autorUsername: String,
    val estado: String,
    val fechaPublicacion: String?,
    val fechaCreacion: String?,
    val fechaActualizacion: String?,
    val destacada: Boolean,
    val metaDescripcion: String?,
    val notasEditor: String?
)

data class CategoryUiModel(
    val id: Int,
    val nombre: String,
    val descripcion: String?,
    val slug: String
)

data class BlogListUiState(
    val posts: List<BlogPostListItemUiModel> = emptyList(),
    val categories: List<CategoryUiModel> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val selectedCategoryId: Int? = null,
    val searchQuery: String = ""
)

data class BlogPostDetailUiState(
    val post: BlogPostDetailUiModel? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

// =============================================================================
// Profile
// =============================================================================

data class StudentProfileUiModel(
    val username: String,
    val email: String,
    val firstName: String,
    val lastName: String,
    val fullName: String, // Computed: "$firstName $lastName"
    val nacionalidad: String?,
    val carnet: String?,
    val sexo: String,
    val imageUrl: String?,
    val address: String?,
    val location: String?,
    val provincia: String?,
    val telephone: String?,
    val movil: String?
)

data class EnrollmentUiModel(
    val id: Int,
    val courseName: String,
    val courseArea: String,
    val courseAreaDisplay: String,
    val courseTipo: String,
    val courseTipoDisplay: String,
    val courseTeacherName: String,
    val estado: String,
    val estadoDisplay: String,
    val cursoAcademicoNombre: String?,
    val fechaMatricula: String?,
    val activo: Boolean
)

data class ProfileUiState(
    val profile: StudentProfileUiModel? = null,
    val enrollments: List<EnrollmentUiModel> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val isSaving: Boolean = false,
    val saveError: String? = null,
    val saveSuccess: Boolean = false
)

// =============================================================================
// Course Applications
// =============================================================================

data class CourseApplicationUiModel(
    val id: Int,
    val courseName: String,
    val courseArea: String,
    val courseAreaDisplay: String,
    val courseTeacherName: String?,
    val status: String,
    val statusDisplay: String,
    val submissionDate: String?,
    val notes: String?
)

data class ApplicationListUiState(
    val applications: List<CourseApplicationUiModel> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val isSubmitting: Boolean = false,
    val submitError: String? = null,
    val submitSuccess: Boolean = false
)

// =============================================================================
// Author Dashboard
// =============================================================================

data class AuthorDashboardUiState(
    val posts: List<BlogPostDetailUiModel> = emptyList(),
    val borradorCount: Int = 0,
    val pendienteRevisionCount: Int = 0,
    val publicadoCount: Int = 0,
    val archivadoCount: Int = 0,
    val selectedStatus: String? = null,
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null
)

// =============================================================================
// Moderator Dashboard
// =============================================================================

data class ReportUiModel(
    val id: Int,
    val comentarioContenido: String,
    val comentarioAutor: String,
    val reportadoPorUsername: String,
    val motivo: String,
    val fechaReporte: String?
)

data class SanctionUiModel(
    val id: Int,
    val usuarioUsername: String,
    val tipoSancion: String,
    val motivo: String,
    val fechaInicio: String?,
    val fechaFin: String?,
    val activa: Boolean
)

data class CommunityMetricsUiModel(
    val totalReportes: Int = 0,
    val totalComentarios: Int = 0,
    val totalSanciones: Int = 0,
    val usuarioMasActivoUsername: String? = null
)

data class ModeratorDashboardUiState(
    val reports: List<ReportUiModel> = emptyList(),
    val sanctions: List<SanctionUiModel> = emptyList(),
    val metrics: CommunityMetricsUiModel = CommunityMetricsUiModel(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val processingReportId: Int? = null
)

// =============================================================================
// Editor Dashboard
// =============================================================================

data class EditorDashboardUiState(
    val pendingReviewPosts: List<BlogPostDetailUiModel> = emptyList(),
    val recentlyPublishedPosts: List<BlogPostDetailUiModel> = emptyList(),
    val pendingReviewCount: Int = 0,
    val recentlyPublishedCount: Int = 0,
    val searchQuery: String = "",
    val searchResults: List<BlogPostDetailUiModel> = emptyList(),
    val isSearching: Boolean = false,
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null,
    val publishingPostId: Int? = null,
    val rejectingPostId: Int? = null
)

/** Convert a [BlogPostDetailUiModel] to a [BlogPostListItemUiModel] for list display. */
fun BlogPostDetailUiModel.toListItem(): BlogPostListItemUiModel = BlogPostListItemUiModel(
    id = id,
    titulo = titulo,
    slug = slug,
    resumen = resumen,
    imagenPrincipalUrl = imagenPrincipalUrl,
    categoria = categoria,
    autorUsername = autorUsername,
    fechaPublicacion = fechaPublicacion,
    destacada = destacada
)

// =============================================================================
// One-time Events (for navigation, snackbar, etc.)
// =============================================================================

sealed class UiEvent {
    data class ShowSnackbar(val message: String) : UiEvent()
    data class ShowErrorSnackbar(val message: String) : UiEvent()
    data class NavigateTo(val route: String) : UiEvent()
    object NavigateBack : UiEvent()
    data class NavigateToCourse(val courseId: Int) : UiEvent()
    data class NavigateToPost(val slug: String) : UiEvent()
    object NavigateToHome : UiEvent()
    object NavigateToLogin : UiEvent()
    object NavigateToApplications : UiEvent()
}
