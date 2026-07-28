package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.ProfileRepository
import com.cfbc.app.infrastructure.network.dto.EnrollmentResponse
import com.cfbc.app.infrastructure.network.dto.StudentProfileResponse
import com.cfbc.app.presentation.model.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for student profile and enrollment management.
 *
 * Manages:
 * - Student profile viewing and editing
 * - Enrollment list (current and historical)
 * - Offline-first: shows cached data while loading fresh data
 *
 * Requirements: 4.1-4.4, 10.6, 10.7
 */
@HiltViewModel
class ProfileViewModel @Inject constructor(
    private val profileRepository: ProfileRepository
) : ViewModel() {

    // =========================================================================
    // UI State
    // =========================================================================

    private val _uiState = MutableStateFlow(ProfileUiState())
    val uiState: StateFlow<ProfileUiState> = _uiState.asStateFlow()

    // =========================================================================
    // Events
    // =========================================================================

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    // =========================================================================
    // Reactive cache observations
    // =========================================================================

    /** Observe cached profile reactively. */
    val cachedProfile: Flow<com.cfbc.app.data.local.entity.StudentProfileEntity?> =
        profileRepository.observeProfile()

    /** Observe cached enrollments reactively. */
    val cachedEnrollments: Flow<List<com.cfbc.app.data.local.entity.EnrollmentEntity>> =
        profileRepository.observeEnrollments()

    /** Observe active cached enrollments only. */
    val cachedActiveEnrollments: Flow<List<com.cfbc.app.data.local.entity.EnrollmentEntity>> =
        profileRepository.observeActiveEnrollments()

    // =========================================================================
    // Actions — Profile
    // =========================================================================

    /**
     * Load the authenticated user's profile from network.
     * Falls back to cache on error.
     */
    fun loadProfile() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = profileRepository.getProfile()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        profile = result.data.toUiModel(),
                        isLoading = false
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.displayMessage
                    )
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /**
     * Pull-to-refresh: silently refresh profile without loading indicator.
     */
    fun refreshProfile() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true)

            when (val result = profileRepository.getProfile()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        profile = result.data.toUiModel(),
                        isRefreshing = false,
                        error = null
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(isRefreshing = false)
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /**
     * Update the authenticated user's profile.
     */
    fun updateProfile(
        nacionalidad: String? = null,
        carnet: String? = null,
        sexo: String? = null,
        address: String? = null,
        location: String? = null,
        provincia: String? = null,
        telephone: String? = null,
        movil: String? = null
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, saveError = null, saveSuccess = false)

            when (val result = profileRepository.updateProfile(
                nacionalidad = nacionalidad,
                carnet = carnet,
                sexo = sexo,
                address = address,
                location = location,
                provincia = provincia,
                telephone = telephone,
                movil = movil
            )) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        profile = result.data.toUiModel(),
                        isSaving = false,
                        saveSuccess = true
                    )
                    _events.send(UiEvent.ShowSnackbar("Perfil actualizado exitosamente"))
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        saveError = result.displayMessage
                    )
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    // =========================================================================
    // Actions — Enrollments
    // =========================================================================

    /**
     * Load the authenticated user's enrollments.
     */
    fun loadEnrollments(activo: String? = null) {
        viewModelScope.launch {
            when (val result = profileRepository.getEnrollments(activo)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        enrollments = result.data.map { it.toUiModel() }
                    )
                }
                is Result.Error -> {
                    // Enrollments are secondary — don't block UI, just log
                    _events.send(UiEvent.ShowErrorSnackbar(
                        "No se pudieron cargar las matrículas: ${result.displayMessage}"
                    ))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /**
     * Load both profile and enrollments in parallel.
     */
    fun loadAll() {
        loadProfile()
        loadEnrollments()
    }

    // =========================================================================
    // Utility
    // =========================================================================

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun clearSaveSuccess() {
        _uiState.value = _uiState.value.copy(saveSuccess = false)
    }
}

// =============================================================================
// DTO → UiModel mapping extensions
// =============================================================================

/** Maps a [StudentProfileResponse] to a [StudentProfileUiModel]. */
fun StudentProfileResponse.toUiModel(): StudentProfileUiModel = StudentProfileUiModel(
    username = username,
    email = email,
    firstName = firstName,
    lastName = lastName,
    fullName = "$firstName $lastName".trim(),
    nacionalidad = nacionalidad,
    carnet = carnet,
    sexo = sexo,
    imageUrl = imageUrl,
    address = address,
    location = location,
    provincia = provincia,
    telephone = telephone,
    movil = movil
)

/** Maps an [EnrollmentResponse] to an [EnrollmentUiModel]. */
fun EnrollmentResponse.toUiModel(): EnrollmentUiModel = EnrollmentUiModel(
    id = id,
    courseName = courseName,
    courseArea = courseArea,
    courseAreaDisplay = courseAreaDisplay,
    courseTipo = courseTipo,
    courseTipoDisplay = courseTipoDisplay,
    courseTeacherName = courseTeacherName,
    estado = estado,
    estadoDisplay = estadoDisplay,
    cursoAcademicoNombre = cursoAcademicoNombre,
    fechaMatricula = fechaMatricula,
    activo = activo
)
