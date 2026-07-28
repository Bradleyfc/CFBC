package com.cfbc.app.data.repository

import com.cfbc.app.data.local.LocalDataSource
import com.cfbc.app.data.local.entity.BlogPostEntity
import com.cfbc.app.data.local.entity.CategoryEntity
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.infrastructure.network.dto.*
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for public blog and author operations.
 *
 * Implements offline-first strategy with LRU cache eviction:
 * - Max 50 blog posts cached locally
 * - Posts older than 30 days are evicted
 * - Last-viewed timestamp tracked for LRU ordering
 *
 * Requirements: 3.1-3.6, 7.1-7.11, 10.11, 10.17, 10.18
 */
@Singleton
class BlogRepository @Inject constructor(
    private val networkDataSource: NetworkDataSource,
    private val localDataSource: LocalDataSource
) {

    // =========================================================================
    // Observable cached data (reactive UI updates)
    // =========================================================================

    /** Observe cached blog posts (reactive). */
    fun observeBlogPosts(): Flow<List<BlogPostEntity>> = localDataSource.observeBlogPosts()

    /** Observe cached categories (reactive). */
    fun observeCategories(): Flow<List<CategoryEntity>> = localDataSource.observeCategories()

    /** Search cached posts (reactive). */
    fun searchPosts(query: String): Flow<List<BlogPostEntity>> =
        localDataSource.searchCachedPosts(query)

    /** Get cached posts by category (reactive). */
    fun observePostsByCategory(categoryId: Int): Flow<List<BlogPostEntity>> =
        localDataSource.observePostsByCategory(categoryId)

    // =========================================================================
    // Public Blog Posts (network-first with cache fallback)
    // =========================================================================

    /**
     * Fetch published blog posts.
     *
     * Offline-first:
     * 1. Fetch from network
     * 2. Cache results and run LRU eviction
     * 3. On failure: return cached data if available
     */
    suspend fun getBlogPosts(
        categoryId: Int? = null,
        featured: Boolean? = null,
        search: String? = null,
        page: Int? = null
    ): Result<List<BlogPostListResponse>> {
        return when (val result = networkDataSource.getBlogPosts(categoryId, featured, search, page)) {
            is Result.Success -> {
                // Cache posts and run eviction
                if (page == null || page <= 1) {
                    val entities = result.data.results.map { it.toEntity() }
                    localDataSource.cacheBlogPosts(entities)
                    localDataSource.evictOldPostsByCount()
                    localDataSource.evictOldPostsByAge()
                }
                Result.Success(result.data.results)
            }
            // On error, just forward it. The UI observes cached data via Flow.
            else -> result
        }
    }

    /**
     * Fetch a single blog post by slug.
     * Updates the lastViewed timestamp for LRU tracking.
     */
    suspend fun getBlogPostBySlug(slug: String): Result<BlogPostDetailResponse> {
        return when (val result = networkDataSource.getBlogPostBySlug(slug)) {
            is Result.Success -> {
                // Cache the post and update LRU
                localDataSource.cacheBlogPost(result.data.toEntity())
                localDataSource.updatePostLastViewed(result.data.id, System.currentTimeMillis())
                result
            }
            is Result.Error -> {
                // Try cache
                val cached = localDataSource.getCachedPostBySlug(slug)
                if (cached != null) {
                    localDataSource.updatePostLastViewed(cached.id, System.currentTimeMillis())
                    Result.Success(cached.toDetailDto())
                } else {
                    result
                }
            }
            is Result.Loading -> result
        }
    }

    // =========================================================================
    // Categories (network-first with cache fallback)
    // =========================================================================

    /**
     * Fetch all blog categories.
     */
    suspend fun getCategories(): Result<List<CategoryResponse>> {
        return when (val result = networkDataSource.getCategories()) {
            is Result.Success -> {
                val entities = result.data.map { it.toEntity() }
                localDataSource.cacheCategories(entities)
                result
            }
            // On error, just forward it. The UI observes cached data via Flow.
            else -> result
        }
    }

    // =========================================================================
    // Author Operations (create/update/delete own posts)
    // These are write operations — always network-first, no cache fallback
    // =========================================================================

    /** Get the author's own posts. */
    suspend fun getAuthorPosts(page: Int? = null): Result<List<BlogPostDetailResponse>> {
        return when (val result = networkDataSource.getAuthorPosts(page)) {
            is Result.Success -> Result.Success(result.data.results)
            else -> result
        }
    }

    /** Get the author's posts filtered by status. */
    suspend fun getAuthorPostsByStatus(
        estado: String
    ): Result<List<BlogPostDetailResponse>> {
        return when (val result = networkDataSource.getAuthorPostsByStatus(estado)) {
            is Result.Success -> Result.Success(result.data.results)
            else -> result
        }
    }

    /** Create a new draft post. */
    suspend fun createPost(request: CreatePostRequest): Result<BlogPostDetailResponse> {
        return networkDataSource.createPost(request)
    }

    /** Update an existing post. */
    suspend fun updatePost(
        postId: Int,
        updates: UpdatePostRequest
    ): Result<BlogPostDetailResponse> {
        return networkDataSource.updatePost(postId, updates)
    }

    /** Delete a draft post. */
    suspend fun deletePost(postId: Int): Result<DetailResponse> {
        return networkDataSource.deletePost(postId)
    }
}

// =============================================================================
// Extension functions for Entity ↔ DTO mapping
// =============================================================================

/** Maps a [BlogPostListResponse] to a [BlogPostEntity]. */
fun BlogPostListResponse.toEntity(): BlogPostEntity = BlogPostEntity(
    id = id,
    titulo = titulo,
    slug = slug,
    resumen = resumen,
    contenido = "", // Not included in list serializer
    imagenPrincipalUrl = imagenPrincipalUrl,
    categoriaId = 0, // Not available in list serializer as ID
    categoriaNombre = categoria,
    autorUsername = autorUsername,
    estado = estado,
    fechaPublicacion = parseIsoDate(fechaPublicacion),
    metaDescripcion = metaDescripcion,
    destacada = destacada,
    notasEditor = null,
    cachedAt = System.currentTimeMillis(),
    lastViewed = System.currentTimeMillis()
)

/** Maps a [BlogPostDetailResponse] to a [BlogPostEntity]. */
fun BlogPostDetailResponse.toEntity(): BlogPostEntity = BlogPostEntity(
    id = id,
    titulo = titulo,
    slug = slug,
    resumen = resumen,
    contenido = contenido,
    imagenPrincipalUrl = imagenPrincipalUrl,
    categoriaId = 0, // Not available as ID from StringRelatedField
    categoriaNombre = categoria,
    autorUsername = autorUsername,
    estado = estado,
    fechaPublicacion = parseIsoDate(fechaPublicacion),
    metaDescripcion = metaDescripcion,
    destacada = destacada,
    notasEditor = notasEditor,
    cachedAt = System.currentTimeMillis(),
    lastViewed = System.currentTimeMillis()
)

/** Maps a [BlogPostEntity] to a [BlogPostDetailResponse] (partial data from cache). */
fun BlogPostEntity.toDetailDto(): BlogPostDetailResponse = BlogPostDetailResponse(
    id = id,
    titulo = titulo,
    slug = slug,
    resumen = resumen,
    contenido = contenido,
    imagenPrincipalUrl = imagenPrincipalUrl,
    categoria = categoriaNombre,
    autorUsername = autorUsername,
    estado = estado,
    visibilidad = "publico", // Default from cache
    destacada = destacada,
    permitirComentarios = true, // Default from cache
    fechaCreacion = null, // Not cached
    fechaActualizacion = null, // Not cached
    fechaPublicacion = null, // Not cached as ISO string
    metaDescripcion = metaDescripcion,
    notasEditor = notasEditor
)

/** Maps a [CategoryResponse] to a [CategoryEntity]. */
fun CategoryResponse.toEntity(): CategoryEntity = CategoryEntity(
    id = id,
    nombre = nombre,
    descripcion = descripcion ?: "",
    slug = slug
)

/**
 * Parses an ISO date string to a Unix timestamp in milliseconds.
 * Returns 0 if the string is null or unparseable.
 */
private fun parseIsoDate(isoDate: String?): Long {
    if (isoDate == null) return 0L
    return try {
        java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", java.util.Locale.US).apply {
            timeZone = java.util.TimeZone.getTimeZone("UTC")
        }.parse(isoDate)?.time ?: 0L
    } catch (e: Exception) {
        // Try date-only format
        try {
            java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).parse(isoDate)?.time ?: 0L
        } catch (e2: Exception) {
            0L
        }
    }
}
