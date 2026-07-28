package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.BlogRepository
import com.cfbc.app.infrastructure.network.dto.*
import com.cfbc.app.presentation.model.CategoryUiModel
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
 * ViewModel for the blog post editor (create/edit mode).
 *
 * Manages:
 * - Loading categories for the dropdown
 * - Loading existing post data for editing
 * - Creating new draft posts
 * - Updating existing posts
 * - Form validation
 *
 * Requirements: 7.7, 7.9, 7.11, 10.17, 10.18
 */
data class BlogEditorUiState(
    val categories: List<CategoryUiModel> = emptyList(),
    val isLoading: Boolean = false,
    val isSaving: Boolean = false,
    val isCategoriesLoading: Boolean = false,
    val saveSuccess: Boolean = false,
    val error: String? = null,
    val createdPostId: Int? = null
)

@HiltViewModel
class BlogEditorViewModel @Inject constructor(
    private val blogRepository: BlogRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(BlogEditorUiState())
    val uiState: StateFlow<BlogEditorUiState> = _uiState.asStateFlow()

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    /** Load all categories for the category dropdown. */
    fun loadCategories() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isCategoriesLoading = true)

            when (val result = blogRepository.getCategories()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        categories = result.data.map { it.toUiModel() },
                        isCategoriesLoading = false
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isCategoriesLoading = false,
                        error = result.displayMessage
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    /** Create a new draft post. */
    fun createPost(
        titulo: String,
        resumen: String,
        contenido: String,
        categoriaId: Int?,
        metaDescripcion: String?,
        destacada: Boolean,
        visibilidad: String
    ) {
        viewModelScope.launch {
            // Validate
            val validationError = validateForm(titulo, resumen, contenido)
            if (validationError != null) {
                _uiState.value = _uiState.value.copy(error = validationError)
                return@launch
            }

            _uiState.value = _uiState.value.copy(isSaving = true, error = null)

            val request = CreatePostRequest(
                titulo = titulo,
                resumen = resumen,
                contenido = contenido,
                categoria = categoriaId,
                metaDescripcion = metaDescripcion?.takeIf { it.isNotBlank() },
                destacada = destacada,
                visibilidad = visibilidad
            )

            when (val result = blogRepository.createPost(request)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        saveSuccess = true,
                        createdPostId = result.data.id
                    )
                    _events.send(UiEvent.ShowSnackbar("Post creado como borrador"))
                    _events.send(UiEvent.NavigateBack)
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        error = result.displayMessage
                    )
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
        }
    }

    /** Update an existing post. */
    fun updatePost(
        postId: Int,
        titulo: String,
        resumen: String,
        contenido: String,
        categoriaId: Int?,
        metaDescripcion: String?,
        destacada: Boolean,
        visibilidad: String
    ) {
        viewModelScope.launch {
            val validationError = validateForm(titulo, resumen, contenido)
            if (validationError != null) {
                _uiState.value = _uiState.value.copy(error = validationError)
                return@launch
            }

            _uiState.value = _uiState.value.copy(isSaving = true, error = null)

            val updates = UpdatePostRequest(
                titulo = titulo,
                resumen = resumen,
                contenido = contenido,
                categoria = categoriaId,
                metaDescripcion = metaDescripcion?.takeIf { it.isNotBlank() },
                destacada = destacada,
                visibilidad = visibilidad
            )

            when (val result = blogRepository.updatePost(postId, updates)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        saveSuccess = true
                    )
                    _events.send(UiEvent.ShowSnackbar("Post actualizado"))
                    _events.send(UiEvent.NavigateBack)
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        error = result.displayMessage
                    )
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    private fun validateForm(titulo: String, resumen: String, contenido: String): String? {
        if (titulo.isBlank()) return "El título es obligatorio."
        if (resumen.isBlank()) return "El resumen es obligatorio."
        if (contenido.isBlank()) return "El contenido es obligatorio."
        return null
    }

    private fun CategoryResponse.toUiModel() = CategoryUiModel(
        id = id,
        nombre = nombre,
        descripcion = descripcion,
        slug = slug
    )
}
