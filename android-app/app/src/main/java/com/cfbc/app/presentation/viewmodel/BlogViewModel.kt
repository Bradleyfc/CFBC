package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.BlogRepository
import com.cfbc.app.infrastructure.network.dto.*
import com.cfbc.app.presentation.model.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for blog browsing, search, and author operations.
 *
 * Manages:
 * - Published blog posts list with category/search filtering
 * - Blog post detail view
 * - Categories list
 * - Author post management (create, edit, delete)
 *
 * Requirements: 3.1-3.6, 7.1-7.11, 10.11, 10.17, 10.18
 */
@HiltViewModel
class BlogViewModel @Inject constructor(
    private val blogRepository: BlogRepository
) : ViewModel() {

    // =========================================================================
    // UI State — Blog List
    // =========================================================================

    private val _listState = MutableStateFlow(BlogListUiState())
    val listState: StateFlow<BlogListUiState> = _listState.asStateFlow()

    // =========================================================================
    // UI State — Post Detail
    // =========================================================================

    private val _detailState = MutableStateFlow(BlogPostDetailUiState())
    val detailState: StateFlow<BlogPostDetailUiState> = _detailState.asStateFlow()

    // =========================================================================
    // Events
    // =========================================================================

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    // =========================================================================
    // Reactive cache observations
    // =========================================================================

    /** Observe cached blog posts reactively (offline-first). */
    val cachedPosts: Flow<List<com.cfbc.app.data.local.entity.BlogPostEntity>> =
        blogRepository.observeBlogPosts()

    /** Observe cached categories reactively. */
    val cachedCategories: Flow<List<com.cfbc.app.data.local.entity.CategoryEntity>> =
        blogRepository.observeCategories()

    // =========================================================================
    // Actions — Blog List
    // =========================================================================

    /**
     * Load published blog posts with optional filtering.
     */
    fun loadPosts(categoryId: Int? = null, search: String? = null) {
        viewModelScope.launch {
            _listState.value = _listState.value.copy(
                isLoading = true,
                error = null,
                selectedCategoryId = categoryId,
                searchQuery = search ?: ""
            )

            when (val result = blogRepository.getBlogPosts(categoryId, search = search)) {
                is Result.Success -> {
                    _listState.value = _listState.value.copy(
                        posts = result.data.map { it.toUiModel() },
                        isLoading = false
                    )
                }
                is Result.Error -> {
                    _listState.value = _listState.value.copy(
                        isLoading = false,
                        error = result.displayMessage
                    )
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /**
     * Pull-to-refresh: silently refresh posts.
     */
    fun refreshPosts() {
        viewModelScope.launch {
            _listState.value = _listState.value.copy(isRefreshing = true)

            when (val result = blogRepository.getBlogPosts(
                _listState.value.selectedCategoryId,
                search = _listState.value.searchQuery.ifEmpty { null }
            )) {
                is Result.Success -> {
                    _listState.value = _listState.value.copy(
                        posts = result.data.map { it.toUiModel() },
                        isRefreshing = false,
                        error = null
                    )
                }
                is Result.Error -> {
                    _listState.value = _listState.value.copy(isRefreshing = false)
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /** Filter posts by category. */
    fun filterByCategory(categoryId: Int?) {
        loadPosts(categoryId, _listState.value.searchQuery.ifEmpty { null })
    }

    /** Search posts by query string. */
    fun searchPosts(query: String) {
        loadPosts(_listState.value.selectedCategoryId, query.ifEmpty { null })
    }

    // =========================================================================
    // Actions — Categories
    // =========================================================================

    /**
     * Load all blog categories.
     */
    fun loadCategories() {
        viewModelScope.launch {
            when (val result = blogRepository.getCategories()) {
                is Result.Success -> {
                    _listState.value = _listState.value.copy(
                        categories = result.data.map { it.toUiModel() }
                    )
                }
                is Result.Error -> {
                    // Categories are non-critical — just log, don't show error
                    _listState.value = _listState.value.copy(
                        categories = emptyList()
                    )
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    // =========================================================================
    // Actions — Post Detail
    // =========================================================================

    /**
     * Load a single blog post by slug.
     */
    fun loadPostBySlug(slug: String) {
        viewModelScope.launch {
            _detailState.value = BlogPostDetailUiState(isLoading = true)

            when (val result = blogRepository.getBlogPostBySlug(slug)) {
                is Result.Success -> {
                    _detailState.value = BlogPostDetailUiState(
                        post = result.data.toUiModel()
                    )
                }
                is Result.Error -> {
                    _detailState.value = BlogPostDetailUiState(error = result.displayMessage)
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    // =========================================================================
    // Actions — Author Operations
    // =========================================================================

    /**
     * Create a new draft post.
     * Returns the created post's ID on success, null on failure.
     */
    fun createPost(
        titulo: String,
        resumen: String,
        contenido: String,
        categoriaId: Int? = null,
        metaDescripcion: String? = null
    ) {
        viewModelScope.launch {
            val request = CreatePostRequest(
                titulo = titulo,
                resumen = resumen,
                contenido = contenido,
                categoria = categoriaId,
                metaDescripcion = metaDescripcion
            )

            when (val result = blogRepository.createPost(request)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Artículo creado como borrador"))
                    _events.send(UiEvent.NavigateBack)
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /**
     * Update an existing post.
     */
    fun updatePost(
        postId: Int,
        titulo: String? = null,
        resumen: String? = null,
        contenido: String? = null,
        categoriaId: Int? = null
    ) {
        viewModelScope.launch {
            val updates = UpdatePostRequest(
                titulo = titulo,
                resumen = resumen,
                contenido = contenido,
                categoria = categoriaId
            )

            when (val result = blogRepository.updatePost(postId, updates)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Artículo actualizado"))
                    _events.send(UiEvent.NavigateBack)
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /**
     * Delete a draft post.
     */
    fun deletePost(postId: Int) {
        viewModelScope.launch {
            when (val result = blogRepository.deletePost(postId)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Artículo eliminado"))
                    _events.send(UiEvent.NavigateBack)
                    // Refresh the list
                    loadPosts()
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    // =========================================================================
    // Utility
    // =========================================================================

    fun clearListError() {
        _listState.value = _listState.value.copy(error = null)
    }

    fun clearDetailError() {
        _detailState.value = _detailState.value.copy(error = null)
    }
}

// =============================================================================
// DTO → UiModel mapping extensions
// =============================================================================

/** Maps a [BlogPostListResponse] to a [BlogPostListItemUiModel]. */
fun BlogPostListResponse.toUiModel(): BlogPostListItemUiModel = BlogPostListItemUiModel(
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

/** Maps a [BlogPostDetailResponse] to a [BlogPostDetailUiModel]. */
fun BlogPostDetailResponse.toUiModel(): BlogPostDetailUiModel = BlogPostDetailUiModel(
    id = id,
    titulo = titulo,
    slug = slug,
    resumen = resumen,
    contenido = contenido,
    imagenPrincipalUrl = imagenPrincipalUrl,
    categoria = categoria,
    autorUsername = autorUsername,
    estado = estado,
    fechaPublicacion = fechaPublicacion,
    fechaCreacion = fechaCreacion,
    fechaActualizacion = fechaActualizacion,
    destacada = destacada,
    metaDescripcion = metaDescripcion,
    notasEditor = notasEditor
)

/** Maps a [CategoryResponse] to a [CategoryUiModel]. */
fun CategoryResponse.toUiModel(): CategoryUiModel = CategoryUiModel(
    id = id,
    nombre = nombre,
    descripcion = descripcion,
    slug = slug
)
