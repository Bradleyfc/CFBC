package com.cfbc.android.presentation.login

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.cfbc.android.R
import com.cfbc.android.databinding.FragmentLoginBinding
import com.cfbc.android.presentation.model.UiEvent
import com.cfbc.android.presentation.viewmodel.AuthViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Login screen — authenticates the user via username/password.
 *
 * Observes [AuthViewModel] for auth state and handles:
 * - Form validation (empty fields)
 * - Loading state (shows/hides progress indicator)
 * - Error display
 * - Navigation to home on success
 *
 * Requirements: 5.1-5.5, 10.5
 */
@AndroidEntryPoint
class LoginFragment : Fragment() {

    private var _binding: FragmentLoginBinding? = null
    private val binding get() = _binding!!

    private val authViewModel: AuthViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentLoginBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // If already authenticated, go straight to home
        if (authViewModel.uiState.value.isAuthenticated) {
            findNavController().navigate(R.id.action_login_to_home)
            return
        }

        setupClickListeners()
        observeViewModel()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    // =========================================================================
    // Setup
    // =========================================================================

    private fun setupClickListeners() {
        binding.loginButton.setOnClickListener {
            val username = binding.usernameInput.text?.toString()?.trim() ?: ""
            val password = binding.passwordInput.text?.toString() ?: ""

            if (validateForm(username, password)) {
                authViewModel.login(username, password)
            }
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                // Observe UI state
                launch {
                    authViewModel.uiState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE
                        binding.loginButton.visibility =
                            if (state.isLoading) View.INVISIBLE else View.VISIBLE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }
                    }
                }

                // Observe one-time events
                launch {
                    authViewModel.events.collectLatest { event ->
                        when (event) {
                            is UiEvent.NavigateToHome -> {
                                findNavController().navigate(R.id.action_login_to_home)
                            }
                            is UiEvent.ShowErrorSnackbar -> {
                                showSnackbar(event.message, true)
                            }
                            is UiEvent.ShowSnackbar -> {
                                showSnackbar(event.message)
                            }
                            else -> { /* ignore other events */ }
                        }
                    }
                }
            }
        }
    }

    // =========================================================================
    // Validation
    // =========================================================================

    private fun validateForm(username: String, password: String): Boolean {
        var isValid = true

        if (username.isEmpty()) {
            binding.usernameLayout.error = "El usuario es requerido"
            isValid = false
        } else {
            binding.usernameLayout.error = null
        }

        if (password.isEmpty()) {
            binding.passwordLayout.error = "La contraseña es requerida"
            isValid = false
        } else {
            binding.passwordLayout.error = null
        }

        return isValid
    }

    // =========================================================================
    // Helpers
    // =========================================================================

    private fun showSnackbar(message: String, isError: Boolean = false) {
        val activity = requireActivity() as? com.cfbc.android.presentation.MainActivity
        activity?.showSnackbar(message, isError)
    }
}
