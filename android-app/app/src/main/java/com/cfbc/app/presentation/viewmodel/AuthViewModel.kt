package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.AuthRepository
import com.cfbc.app.presentation.model.AuthUiState
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
 * ViewModel for authentication operations.
 *
 * Manages:
 * - Login state (authenticated/anonymous)
 * - User session (username, groups)
 * - Login and logout actions
 *
 * Requirements: 5.1-5.5, 10.5
 */
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    // =========================================================================
    // UI State
    // =========================================================================

    private val _uiState = MutableStateFlow(
        AuthUiState(
            isAuthenticated = authRepository.isAuthenticated,
            username = authRepository.currentUsername,
            groups = authRepository.currentGroups
        )
    )
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    /** One-time events (navigation, snackbar). */
    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    // =========================================================================
    // Actions
    // =========================================================================

    /**
     * Attempt login with username and password.
     * On success: updates auth state and emits NavigateToHome event.
     * On failure: updates error in UI state.
     */
    fun login(username: String, password: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            when (val result = authRepository.login(username, password)) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isAuthenticated = true,
                        username = result.data.username,
                        groups = result.data.groups,
                        isLoading = false,
                        error = null
                    )
                    _events.send(UiEvent.ShowSnackbar("Inicio de sesión exitoso"))
                    _events.send(UiEvent.NavigateToHome)
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = result.displayMessage
                    )
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled by isLoading flag */ }
            }
        }
    }

    /**
     * Log out the current user.
     * On completion: resets auth state and emits NavigateToLogin event.
     */
    fun logout() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            authRepository.logout()
            _uiState.value = AuthUiState()
            _events.send(UiEvent.ShowSnackbar("Sesión cerrada"))
            _events.send(UiEvent.NavigateToLogin)
        }
    }

    /**
     * Clear any error from the UI state.
     */
    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    /**
     * Check if current user has a specific role/group.
     */
    fun hasGroup(groupName: String): Boolean = authRepository.hasGroup(groupName)

    /** Check if user is a student. */
    fun isStudent(): Boolean = authRepository.isStudent()

    /** Check if user is a blog author. */
    fun isBlogAuthor(): Boolean = authRepository.isBlogAuthor()

    /** Check if user is a blog moderator. */
    fun isBlogModerator(): Boolean = authRepository.isBlogModerator()

    /** Check if user is an editor. */
    fun isEditor(): Boolean = authRepository.isEditor()
}
