package com.cfbc.android.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.CourseApplicationRepository
import com.cfbc.app.infrastructure.network.dto.CourseApplicationResponse
import com.cfbc.app.presentation.model.ApplicationListUiState
import com.cfbc.app.presentation.model.CourseApplicationUiModel
import com.cfbc.app.presentation.model.UiEvent
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for course application operations.
 *
 * Manages:
 * - Applying to a course
 * - Listing the user's applications
 * - Cancelling a pending application
 *
 * Requirements: 10.8
 */
@HiltViewModel
class CourseApplicationViewModel @Inject constructor(
    private val applicationRepository: CourseApplicationRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ApplicationListUiState())
    val uiState: StateFlow<ApplicationListUiState> = _uiState.asStateFlow()

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    /** Observe cached applications reactively. */
    val cachedApplications: Flow<List<com.cfbc.app.data.local.entity.CourseApplicationEntity>> =
        applicationRepository.observeApplications()

    /** Load user's applications from network. */
    fun loadApplications() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = applicationRepository.getApplications()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        applications = result.data.map { it.toUiModel() },
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

    /** Apply to a course. */
    fun applyToCourse(courseId: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSubmitting = true, submitError = null)

            when (val result = applicationRepository.createApplication(courseId)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(isSubmitting = false)
                    _events.send(UiEvent.ShowSnackbar("Solicitud enviada exitosamente"))
                    _events.send(UiEvent.NavigateToApplications)
                    loadApplications()
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isSubmitting = false,
                        submitError = result.displayMessage
                    )
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
        }
    }

    /** Cancel a pending application. */
    fun cancelApplication(applicationId: Int) {
        viewModelScope.launch {
            when (val result = applicationRepository.cancelApplication(applicationId)) {
                is Result.Success -> {
                    _events.send(UiEvent.ShowSnackbar("Solicitud cancelada"))
                    loadApplications()
                }
                is Result.Error -> {
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> {}
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null, submitError = null)
    }

    fun clearSubmitSuccess() {
        _uiState.value = _uiState.value.copy(submitSuccess = false)
    }
}

/** Maps a [CourseApplicationResponse] to a [CourseApplicationUiModel]. */
fun CourseApplicationResponse.toUiModel(): CourseApplicationUiModel = CourseApplicationUiModel(
    id = id,
    courseName = courseName,
    courseArea = courseArea,
    courseAreaDisplay = courseAreaDisplay,
    courseTeacherName = courseTeacherName,
    status = status,
    statusDisplay = statusDisplay,
    submissionDate = submissionDate,
    notes = notes
)
