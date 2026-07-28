package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.EditorRepository
import com.cfbc.app.infrastructure.network.dto.BlogPostDetailResponse
import com.cfbc.app.presentation.model.BlogPostDetailUiModel
import com.cfbc.app.presentation.model.EditorDashboardUiState
import com.cfbc.app.presentation.model.UiEvent
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for the Editor dashboard.
 *
 * Manages:
 * - Posts pending review (pendiente_revision)
 * - Recently published posts (last 7 days)
 * - Searching posts by author
 * - Publishing and rejecting posts
 * - Updating editor notes
 *
 * Requirements: 9.1-9.12, 10.13, 10.19, 10.20
 */
@HiltViewModel
class EditorViewModel @Inject constructor(
    private val editorRepository: EditorRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(EditorDashboardUiState())
    val uiState: StateFlow<EditorDashboardUiState> = _uiState.asStateFlow()

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    /** Load pending review and recently published posts. */
    fun loadAll() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            loadPendingReview()
            loadRecentlyPublished()
            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    /** Refresh all data (pull-to-refresh). */
    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true)
            loadPendingReview()
            loadRecentlyPublished()
            _uiState.value = _uiState.value.copy(isRefreshing = false)
        }
    }

    private suspend fun loadPendingReview() {
        when (val result = editorRepository.getPendingReview()) {
            is Result.Success -> {
                val posts = result.data.map { it.toEditorUiModel() }
                _uiState.value = _uiState.value.copy(
                    pendingReviewPosts = posts,
                    pendingReviewCount = posts.size
                )
            }
            is Result.Error -> {
                _uiState.value = _uiState.value.copy(error = result.displayMessage)
            }
            is Result.Loading -> {}
        }
    }

    private suspend fun loadRecentlyPublished() {
        when (val result = editorRepository.getRecentlyPublished()) {
            is Result.Success -> {
                val posts = result.data.map { it.toEditorUiModel() }
                _uiState.value = _uiState.value.copy(
                    recentlyPublishedPosts = posts,
                    recentlyPublishedCount = posts.size
                )
            }
            is Result.Error -> {
                _uiState.value = _uiState.value.copy(error = result.displayMessage)
            }
            is Result.Loading -> {}
        }
    }

    /** Search posts by author username. */
    fun searchPosts(query: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(searchQuery = query, isSearching = true)
            if (query.isBlank()) {
                _uiState.value = _uiState.value.copy(searchResults = emptyList(), isSearching = false)
                return@launch
            }
            when (val result = editorRepository.getPosts(search = query)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        searchResults = result.data.map { it.toEditorUiModel() },
                        isSearching = false
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(isSearching = false)
                }
                is Result.Loading -> {}
            }
        }
    }

    /** Publish a post. */
    fun publishPost(postId: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(publishingPostId = postId)
            when (val result = editorRepository.publishPost(postId)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Post publicado exitosamente"))
                    loadAll()
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
            _uiState.value = _uiState.value.copy(publishingPostId = null)
        }
    }

    /** Reject a post with editor notes (sends back to author as borrador). */
    fun rejectPost(postId: Int, notasEditor: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(rejectingPostId = postId)
            when (val result = editorRepository.rejectPost(postId, notasEditor)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Post devuelto al autor con notas"))
                    loadAll()
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
            _uiState.value = _uiState.value.copy(rejectingPostId = null)
        }
    }

    /** Update editor notes on a post. */
    fun updateNotes(postId: Int, notasEditor: String) {
        viewModelScope.launch {
            when (val result = editorRepository.updateNotes(postId, notasEditor)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Notas del editor actualizadas"))
                    loadAll()
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}

/** Maps a [BlogPostDetailResponse] to a [BlogPostDetailUiModel] for the editor dashboard. */
private fun BlogPostDetailResponse.toEditorUiModel(): BlogPostDetailUiModel = BlogPostDetailUiModel(
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
