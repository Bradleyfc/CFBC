package com.cfbc.app.data.remote

import com.cfbc.app.data.model.Result
import com.cfbc.app.infrastructure.network.CfbcApiService
import com.cfbc.app.infrastructure.network.dto.*
import retrofit2.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Network Data Source — wraps all CfbcApiService calls with consistent error handling.
 *
 * Every method returns [Result]<T> so the caller never has to worry about exceptions.
 * Network errors (IOException), auth errors (401), and server errors (5xx) are all
 * caught and mapped to [Result.Error].
 *
 * Requirements: 10.1-10.22
 */
@Singleton
class NetworkDataSource @Inject constructor(
    private val api: CfbcApiService
) {

    // =========================================================================
    // Helpers
    // =========================================================================

    /**
     * Safely execute a suspend API call and wrap the result.
     * Handles HTTP errors, network exceptions, and unexpected errors.
     */
    private suspend fun <T> safeApiCall(
        call: suspend () -> Response<T>
    ): Result<T> {
        return try {
            val response = call()
            if (response.isSuccessful) {
                val body = response.body()
                if (body != null) {
                    Result.Success(body)
                } else {
                    Result.Error(
                        Exception("Respuesta vacía del servidor"),
                        "El servidor devolvió una respuesta vacía."
                    )
                }
            } else {
                val errorBody = response.errorBody()?.string() ?: "Error desconocido"
                val statusCode = response.code()
                val message = when (statusCode) {
                    400 -> "Solicitud inválida: $errorBody"
                    401 -> "No autorizado. Verifica tus credenciales."
                    403 -> "No tienes permiso para realizar esta acción."
                    404 -> "El recurso solicitado no fue encontrado."
                    429 -> "Demasiadas solicitudes. Intenta de nuevo más tarde."
                    in 500..599 -> "Error del servidor ($statusCode). Intenta de nuevo."
                    else -> "Error $statusCode: $errorBody"
                }
                Result.Error(
                    Exception("HTTP $statusCode: $errorBody"),
                    message
                )
            }
        } catch (e: java.io.IOException) {
            Result.Error(e, "No hay conexión a Internet. Verifica tu red.")
        } catch (e: Exception) {
            Result.Error(e, "Ocurrió un error inesperado: ${e.localizedMessage}")
        }
    }

    // =========================================================================
    // Authentication
    // =========================================================================

    /** POST /api/v1/auth/login/ */
    suspend fun login(username: String, password: String): Result<LoginResponse> {
        return safeApiCall { api.login(LoginRequest(username, password)) }
    }

    /** POST /api/v1/auth/logout/ */
    suspend fun logout(): Result<DetailResponse> {
        return safeApiCall { api.logout() }
    }

    // =========================================================================
    // Profile
    // =========================================================================

    /** GET /api/v1/profile/ */
    suspend fun getProfile(): Result<StudentProfileResponse> {
        return safeApiCall { api.getProfile() }
    }

    /** PATCH /api/v1/profile/ */
    suspend fun updateProfile(updates: StudentProfileUpdateRequest): Result<StudentProfileResponse> {
        return safeApiCall { api.updateProfile(updates) }
    }

    // =========================================================================
    // Home Page
    // =========================================================================

    /** GET /api/v1/home/ */
    suspend fun getHomePage(): Result<HomePageResponse> {
        return safeApiCall { api.getHomePage() }
    }

    // =========================================================================
    // Courses
    // =========================================================================

    /** GET /api/v1/courses/ */
    suspend fun getCourses(
        area: String? = null,
        tipo: String? = null,
        page: Int? = null
    ): Result<PaginatedResponse<CourseResponse>> {
        return safeApiCall { api.getCourses(area, tipo, page) }
    }

    /** GET /api/v1/courses/{id}/ */
    suspend fun getCourseById(courseId: Int): Result<CourseResponse> {
        return safeApiCall { api.getCourseById(courseId) }
    }

    // =========================================================================
    // Enrollments
    // =========================================================================

    /** GET /api/v1/enrollments/ */
    suspend fun getEnrollments(
        activo: String? = null,
        page: Int? = null
    ): Result<PaginatedResponse<EnrollmentResponse>> {
        return safeApiCall { api.getEnrollments(activo, page) }
    }

    /** GET /api/v1/enrollments/{id}/ */
    suspend fun getEnrollmentById(enrollmentId: Int): Result<EnrollmentResponse> {
        return safeApiCall { api.getEnrollmentById(enrollmentId) }
    }

    // =========================================================================
    // Blog — Public
    // =========================================================================

    /** GET /api/v1/blog/posts/ */
    suspend fun getBlogPosts(
        categoryId: Int? = null,
        featured: Boolean? = null,
        search: String? = null,
        page: Int? = null
    ): Result<PaginatedResponse<BlogPostListResponse>> {
        return safeApiCall { api.getBlogPosts(categoryId, featured, search, page) }
    }

    /** GET /api/v1/blog/posts/{slug}/ */
    suspend fun getBlogPostBySlug(slug: String): Result<BlogPostDetailResponse> {
        return safeApiCall { api.getBlogPostBySlug(slug) }
    }

    /** GET /api/v1/blog/categories/ */
    suspend fun getCategories(): Result<List<CategoryResponse>> {
        return safeApiCall { api.getCategories() }
    }

    // =========================================================================
    // Blog — Author
    // =========================================================================

    /** GET /api/v1/blog/author/posts/ */
    suspend fun getAuthorPosts(page: Int? = null): Result<PaginatedResponse<BlogPostDetailResponse>> {
        return safeApiCall { api.getAuthorPosts(page) }
    }

    /** GET /api/v1/blog/author/posts/by-status/{estado}/ */
    suspend fun getAuthorPostsByStatus(
        estado: String
    ): Result<PaginatedResponse<BlogPostDetailResponse>> {
        return safeApiCall { api.getAuthorPostsByStatus(estado) }
    }

    /** POST /api/v1/blog/author/posts/ */
    suspend fun createPost(post: CreatePostRequest): Result<BlogPostDetailResponse> {
        return safeApiCall { api.createPost(post) }
    }

    /** PATCH /api/v1/blog/author/posts/{id}/ */
    suspend fun updatePost(
        postId: Int,
        updates: UpdatePostRequest
    ): Result<BlogPostDetailResponse> {
        return safeApiCall { api.updatePost(postId, updates) }
    }

    /** DELETE /api/v1/blog/author/posts/{id}/ */
    suspend fun deletePost(postId: Int): Result<DetailResponse> {
        return safeApiCall { api.deletePost(postId) }
    }

    // =========================================================================
    // Blog — Moderator
    // =========================================================================

    /** GET /api/v1/blog/moderator/reports/ */
    suspend fun getModeratorReports(
        page: Int? = null
    ): Result<PaginatedResponse<CommentReportResponse>> {
        return safeApiCall { api.getModeratorReports(page) }
    }

    /** POST /api/v1/blog/moderator/reports/{id}/approve/ */
    suspend fun approveReport(reportId: Int): Result<CommentReportResponse> {
        return safeApiCall { api.approveReport(reportId) }
    }

    /** POST /api/v1/blog/moderator/reports/{id}/reject/ */
    suspend fun rejectReport(reportId: Int): Result<CommentReportResponse> {
        return safeApiCall { api.rejectReport(reportId) }
    }

    /** GET /api/v1/blog/moderator/sanctions/ */
    suspend fun getModeratorSanctions(
        page: Int? = null
    ): Result<PaginatedResponse<SanctionResponse>> {
        return safeApiCall { api.getModeratorSanctions(page) }
    }

    /** GET /api/v1/blog/moderator/metrics/ */
    suspend fun getCommunityMetrics(): Result<CommunityMetricsResponse> {
        return safeApiCall { api.getCommunityMetrics() }
    }

    // =========================================================================
    // Blog — Editor
    // =========================================================================

    /** GET /api/v1/blog/editor/posts/ */
    suspend fun getEditorPosts(
        search: String? = null,
        page: Int? = null
    ): Result<PaginatedResponse<BlogPostDetailResponse>> {
        return safeApiCall { api.getEditorPosts(search, page) }
    }

    /** GET /api/v1/blog/editor/posts/pending_review/ */
    suspend fun getPendingReviewPosts(
        page: Int? = null
    ): Result<PaginatedResponse<BlogPostDetailResponse>> {
        return safeApiCall { api.getPendingReviewPosts(page) }
    }

    /** GET /api/v1/blog/editor/posts/recently_published/ */
    suspend fun getRecentlyPublishedPosts(
        page: Int? = null
    ): Result<PaginatedResponse<BlogPostDetailResponse>> {
        return safeApiCall { api.getRecentlyPublishedPosts(page) }
    }

    /** POST /api/v1/blog/editor/posts/{id}/publish/ */
    suspend fun publishPost(postId: Int): Result<BlogPostDetailResponse> {
        return safeApiCall { api.publishPost(postId) }
    }

    /** POST /api/v1/blog/editor/posts/{id}/reject/ */
    suspend fun rejectPost(
        postId: Int,
        notasEditor: String
    ): Result<BlogPostDetailResponse> {
        return safeApiCall { api.rejectPost(postId, RejectPostRequest(notasEditor)) }
    }

    /** PATCH /api/v1/blog/editor/posts/{id}/update_notes/ */
    suspend fun updateEditorNotes(
        postId: Int,
        notasEditor: String
    ): Result<BlogPostDetailResponse> {
        return safeApiCall { api.updateEditorNotes(postId, UpdateNotesRequest(notasEditor)) }
    }

    // =========================================================================
    // Course Applications
    // =========================================================================

    /** POST /api/v1/applications/ */
    suspend fun createApplication(courseId: Int): Result<CourseApplicationResponse> {
        return safeApiCall { api.createApplication(CreateApplicationRequest(courseId)) }
    }

    /** GET /api/v1/applications/ */
    suspend fun getApplications(
        page: Int? = null
    ): Result<PaginatedResponse<CourseApplicationResponse>> {
        return safeApiCall { api.getApplications(page) }
    }

    /** GET /api/v1/applications/{id}/ */
    suspend fun getApplicationById(id: Int): Result<CourseApplicationResponse> {
        return safeApiCall { api.getApplicationById(id) }
    }

    /** POST /api/v1/applications/{id}/cancel/ */
    suspend fun cancelApplication(id: Int): Result<DetailResponse> {
        return safeApiCall { api.cancelApplication(id) }
    }
}
