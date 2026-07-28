package com.cfbc.app.infrastructure.network

import com.cfbc.app.infrastructure.network.dto.*
import retrofit2.Response
import retrofit2.http.*

/**
 * CFBC API Service - Retrofit interface for Django REST API endpoints.
 *
 * Base URL: Configured via BuildConfig.API_BASE_URL (e.g. http://10.0.2.2:8000/api/v1/)
 * Authentication: Token-based via AuthInterceptor
 *
 * All endpoints mapped from Django REST Framework views:
 * - principal/api_urls.py → /api/v1/
 * - blog/api_urls.py     → /api/v1/blog/
 *
 * Requirements: 10.1-10.22
 */
interface CfbcApiService {

    // =========================================================================
    // Authentication
    // Base: /api/v1/auth/
    // =========================================================================

    /** POST /api/v1/auth/login/ - Authenticate and get token */
    @POST("auth/login/")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    /** POST /api/v1/auth/logout/ - Invalidate token */
    @POST("auth/logout/")
    suspend fun logout(): Response<DetailResponse>

    // =========================================================================
    // Student Profile
    // Base: /api/v1/profile/
    // =========================================================================

    /** GET /api/v1/profile/ - Get authenticated user's profile */
    @GET("profile/")
    suspend fun getProfile(): Response<StudentProfileResponse>

    /** PATCH /api/v1/profile/ - Update own profile fields */
    @PATCH("profile/")
    suspend fun updateProfile(@Body updates: StudentProfileUpdateRequest): Response<StudentProfileResponse>

    // =========================================================================
    // Home Page
    // Base: /api/v1/home/
    // =========================================================================

    /** GET /api/v1/home/ - Get available courses (10) + latest news (5) */
    @GET("home/")
    suspend fun getHomePage(): Response<HomePageResponse>

    // =========================================================================
    // Courses
    // Base: /api/v1/courses/
    // =========================================================================

    /**
     * GET /api/v1/courses/ - List available courses (paginated).
     * Query params: ?area=idiomas&tipo=curso&page=1&page_size=20
     */
    @GET("courses/")
    suspend fun getCourses(
        @Query("area") area: String? = null,
        @Query("tipo") tipo: String? = null,
        @Query("page") page: Int? = null,
        @Query("page_size") pageSize: Int? = null
    ): Response<PaginatedResponse<CourseResponse>>

    /** GET /api/v1/courses/{id}/ - Get course details */
    @GET("courses/{id}/")
    suspend fun getCourseById(@Path("id") courseId: Int): Response<CourseResponse>

    // =========================================================================
    // Enrollments
    // Base: /api/v1/enrollments/
    // =========================================================================

    /**
     * GET /api/v1/enrollments/ - List own enrollments (paginated).
     * Query params: ?activo=1&page=1
     */
    @GET("enrollments/")
    suspend fun getEnrollments(
        @Query("activo") activo: String? = null,
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<EnrollmentResponse>>

    /** GET /api/v1/enrollments/{id}/ - Get enrollment detail */
    @GET("enrollments/{id}/")
    suspend fun getEnrollmentById(@Path("id") enrollmentId: Int): Response<EnrollmentResponse>

    // =========================================================================
    // Blog - Public Posts & Categories
    // Base: /api/v1/blog/
    // =========================================================================

    /**
     * GET /api/v1/blog/posts/ - List published blog posts (paginated).
     * Query params: ?categoria=1&destacada=true&search=keyword&page=1
     */
    @GET("blog/posts/")
    suspend fun getBlogPosts(
        @Query("categoria") categoryId: Int? = null,
        @Query("destacada") featured: Boolean? = null,
        @Query("search") search: String? = null,
        @Query("page") page: Int? = null,
        @Query("page_size") pageSize: Int? = null
    ): Response<PaginatedResponse<BlogPostListResponse>>

    /**
     * GET /api/v1/blog/posts/{slug}/ - Get blog post by slug (or ID).
     * Uses slug as path parameter (Django view resolves slug or id).
     */
    @GET("blog/posts/{slug}/")
    suspend fun getBlogPostBySlug(@Path("slug") slug: String): Response<BlogPostDetailResponse>

    /** GET /api/v1/blog/categories/ - List all categories */
    @GET("blog/categories/")
    suspend fun getCategories(): Response<List<CategoryResponse>>

    // =========================================================================
    // Blog - Author Posts
    // Base: /api/v1/blog/author/posts/
    // =========================================================================

    /** GET /api/v1/blog/author/posts/ - List own posts (paginated) */
    @GET("blog/author/posts/")
    suspend fun getAuthorPosts(
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<BlogPostDetailResponse>>

    /**
     * GET /api/v1/blog/author/posts/by-status/{estado}/ - Filter own posts by status.
     * Estados: borrador, pendiente_revision, publicado, archivado
     */
    @GET("blog/author/posts/by-status/{estado}/")
    suspend fun getAuthorPostsByStatus(
        @Path("estado") estado: String
    ): Response<PaginatedResponse<BlogPostDetailResponse>>

    /** POST /api/v1/blog/author/posts/ - Create new draft post */
    @POST("blog/author/posts/")
    suspend fun createPost(@Body post: CreatePostRequest): Response<BlogPostDetailResponse>

    /** PATCH /api/v1/blog/author/posts/{id}/ - Update own post */
    @PATCH("blog/author/posts/{id}/")
    suspend fun updatePost(
        @Path("id") postId: Int,
        @Body updates: UpdatePostRequest
    ): Response<BlogPostDetailResponse>

    /** DELETE /api/v1/blog/author/posts/{id}/ - Delete own draft post */
    @DELETE("blog/author/posts/{id}/")
    suspend fun deletePost(@Path("id") postId: Int): Response<DetailResponse>

    // =========================================================================
    // Blog - Moderator Reports & Sanctions
    // Base: /api/v1/blog/moderator/
    // =========================================================================

    /** GET /api/v1/blog/moderator/reports/ - List pending comment reports */
    @GET("blog/moderator/reports/")
    suspend fun getModeratorReports(
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<CommentReportResponse>>

    /** POST /api/v1/blog/moderator/reports/{id}/approve/ - Approve report and hide comment */
    @POST("blog/moderator/reports/{id}/approve/")
    suspend fun approveReport(@Path("id") reportId: Int): Response<CommentReportResponse>

    /** POST /api/v1/blog/moderator/reports/{id}/reject/ - Reject report and keep comment */
    @POST("blog/moderator/reports/{id}/reject/")
    suspend fun rejectReport(@Path("id") reportId: Int): Response<CommentReportResponse>

    /** GET /api/v1/blog/moderator/sanctions/ - List active user sanctions */
    @GET("blog/moderator/sanctions/")
    suspend fun getModeratorSanctions(
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<SanctionResponse>>

    /** GET /api/v1/blog/moderator/metrics/ - Get community metrics */
    @GET("blog/moderator/metrics/")
    suspend fun getCommunityMetrics(): Response<CommunityMetricsResponse>

    // =========================================================================
    // Blog - Editor Posts
    // Base: /api/v1/blog/editor/posts/
    // =========================================================================

    /** GET /api/v1/blog/editor/posts/ - List all posts (editor view) */
    @GET("blog/editor/posts/")
    suspend fun getEditorPosts(
        @Query("search") search: String? = null,
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<BlogPostDetailResponse>>

    /** GET /api/v1/blog/editor/posts/pending_review/ - Posts pending editor review */
    @GET("blog/editor/posts/pending_review/")
    suspend fun getPendingReviewPosts(
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<BlogPostDetailResponse>>

    /** GET /api/v1/blog/editor/posts/recently_published/ - Posts published in last 7 days */
    @GET("blog/editor/posts/recently_published/")
    suspend fun getRecentlyPublishedPosts(
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<BlogPostDetailResponse>>

    /** POST /api/v1/blog/editor/posts/{id}/publish/ - Publish a post */
    @POST("blog/editor/posts/{id}/publish/")
    suspend fun publishPost(@Path("id") postId: Int): Response<BlogPostDetailResponse>

    /** POST /api/v1/blog/editor/posts/{id}/reject/ - Reject post with editor notes */
    @POST("blog/editor/posts/{id}/reject/")
    suspend fun rejectPost(
        @Path("id") postId: Int,
        @Body rejection: RejectPostRequest
    ): Response<BlogPostDetailResponse>

    /** PATCH /api/v1/blog/editor/posts/{id}/update_notes/ - Update editor notes */
    @PATCH("blog/editor/posts/{id}/update_notes/")
    suspend fun updateEditorNotes(
        @Path("id") postId: Int,
        @Body notes: UpdateNotesRequest
    ): Response<BlogPostDetailResponse>

    // =========================================================================
    // Course Applications
    // Base: /api/v1/applications/
    // =========================================================================

    /** POST /api/v1/applications/ - Apply to a course */
    @POST("applications/")
    suspend fun createApplication(@Body request: CreateApplicationRequest): Response<CourseApplicationResponse>

    /** GET /api/v1/applications/ - List own applications (paginated) */
    @GET("applications/")
    suspend fun getApplications(
        @Query("page") page: Int? = null
    ): Response<PaginatedResponse<CourseApplicationResponse>>

    /** GET /api/v1/applications/{id}/ - Get application detail */
    @GET("applications/{id}/")
    suspend fun getApplicationById(@Path("id") applicationId: Int): Response<CourseApplicationResponse>

    /** POST /api/v1/applications/{id}/cancel/ - Cancel a pending application */
    @POST("applications/{id}/cancel/")
    suspend fun cancelApplication(@Path("id") applicationId: Int): Response<DetailResponse>
}
