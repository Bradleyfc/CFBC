package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.BlogRepository
import com.cfbc.app.infrastructure.network.dto.BlogPostDetailResponse
import com.cfbc.app.presentation.model.AuthorDashboardUiState
import com.cfbc.app.presentation.model.BlogPostDetailUiModel
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
 * ViewModel for the Blog Author dashboard.
 *
 * Manages:
 * - Listing the author's posts grouped by status
 * - Filtering by status
 * - Post counts per status
 *
 * Requirements: 7.1-7.11, 10.11, 10.17, 10.18
 */
@HiltViewModel
class AuthorViewModel @Inject constructor(
    private val blogRepository: BlogRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthorDashboardUiState())
    val uiState: StateFlow<AuthorDashboardUiState> = _uiState.asStateFlow()

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    /** Load all author posts and compute counts per status. */
    fun loadPosts() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = blogRepository.getAuthorPosts()) {
                is Result.Success -> {
                    val posts = result.data.map { it.toAuthorUiModel() }
                    _uiState.value = _uiState.value.copy(
                        posts = posts,
                        borradorCount = posts.count { it.estado == "borrador" },
                        pendienteRevisionCount = posts.count { it.estado == "pendiente_revision" },
                        publicadoCount = posts.count { it.estado == "publicado" },
                        archivadoCount = posts.count { it.estado == "archivado" },
                        isLoading = false
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.displayMessage
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    /** Refresh posts (pull-to-refresh). */
    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true)
            loadPosts()
            _uiState.value = _uiState.value.copy(isRefreshing = false)
        }
    }

    /** Filter posts by status. Pass null to show all. */
    fun filterByStatus(status: String?) {
        _uiState.value = _uiState.value.copy(selectedStatus = status)
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}

/** Maps a [BlogPostDetailResponse] to a [BlogPostDetailUiModel] for the author dashboard. */
private fun BlogPostDetailResponse.toAuthorUiModel(): BlogPostDetailUiModel = BlogPostDetailUiModel(
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
