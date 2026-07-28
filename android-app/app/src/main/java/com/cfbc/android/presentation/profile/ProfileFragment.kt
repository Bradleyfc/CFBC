package com.cfbc.android.presentation.profile

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
import coil.load
import com.cfbc.android.R
import com.cfbc.android.databinding.FragmentProfileBinding
import com.cfbc.android.presentation.adapter.EnrollmentAdapter
import com.cfbc.android.presentation.viewmodel.ProfileViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Profile screen — view and edit student profile, see enrollments.
 *
 * Features:
 * - View mode: displays profile info and enrollments
 * - Edit mode: editable text fields with save button
 * - Pull-to-refresh support
 *
 * Requirements: 4.1-4.4, 10.6, 10.7
 */
@AndroidEntryPoint
class ProfileFragment : Fragment() {

    private var _binding: FragmentProfileBinding? = null
    private val binding get() = _binding!!

    private val profileViewModel: ProfileViewModel by viewModels()

    /** Tracks whether we're in edit mode. */
    private var isEditing = false

    private lateinit var enrollmentAdapter: EnrollmentAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentProfileBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupClickListeners()
        setupRecyclerView()
        observeViewModel()

        profileViewModel.loadAll()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupClickListeners() {
        binding.editToggleButton.setOnClickListener {
            toggleEditMode()
        }

        binding.saveButton.setOnClickListener {
            saveProfile()
        }

        binding.gradesSection.setOnClickListener {
            navigateToStudentSection("calificaciones/")
        }
        binding.attendanceSection.setOnClickListener {
            navigateToStudentSection("asistencias/")
        }
        binding.evaluationsSection.setOnClickListener {
            navigateToStudentSection("evaluaciones/")
        }
        binding.historySection.setOnClickListener {
            navigateToStudentSection("historial/")
        }
    }

    private fun navigateToStudentSection(path: String) {
        val bundle = Bundle().apply {
            putString("sectionPath", path)
            putString("webBaseUrl", "https://cfbc.example.com") // Configure per environment
        }
        findNavController().navigate(R.id.action_profile_to_student_sections, bundle)
    }

    private fun setupRecyclerView() {
        enrollmentAdapter = EnrollmentAdapter()
        binding.enrollmentsRecyclerView.adapter = enrollmentAdapter
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    profileViewModel.uiState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        // Show/hide profile sections
                        val hasProfile = state.profile != null
                        binding.profileHeaderCard.visibility = if (hasProfile) View.VISIBLE else View.GONE
                        binding.profileInfoCard.visibility = if (hasProfile) View.VISIBLE else View.GONE

                        // Update enrollment list
                        enrollmentAdapter.submitList(state.enrollments)

                        state.profile?.let { profile ->
                            binding.fullName.text = profile.fullName
                            binding.emailText.text = profile.email
                            profile.imageUrl?.let { url ->
                                binding.avatarImage.load(url) {
                            placeholder(android.R.drawable.ic_menu_gallery)
                            error(android.R.drawable.ic_menu_gallery)
                                    crossfade(true)
                                }
                            }

                            // Populate text fields (view mode)
                            binding.nacionalidadText.text = profile.nacionalidad ?: "No especificada"
                            binding.telephoneText.text = profile.telephone ?: "No especificado"
                            binding.movilText.text = profile.movil ?: "No especificado"
                            binding.addressText.text = profile.address ?: "No especificada"
                            binding.locationText.text = profile.location ?: "No especificado"
                            binding.provinciaText.text = profile.provincia ?: "No especificada"

                            // Populate input fields (edit mode)
                            binding.nacionalidadInput.setText(profile.nacionalidad ?: "")
                            binding.telephoneInput.setText(profile.telephone ?: "")
                            binding.movilInput.setText(profile.movil ?: "")
                            binding.addressInput.setText(profile.address ?: "")
                            binding.locationInput.setText(profile.location ?: "")
                            binding.provinciaInput.setText(profile.provincia ?: "")
                        }

                        // Save state
                        if (state.saveSuccess) {
                            isEditing = false
                            updateViewMode()
                            val activity = requireActivity() as? com.cfbc.android.presentation.MainActivity
                            activity?.showSnackbar("Perfil actualizado exitosamente")
                            profileViewModel.clearSaveSuccess()
                        }
                    }
                }
            }
        }
    }

    private fun toggleEditMode() {
        isEditing = !isEditing
        if (isEditing) {
            updateEditMode()
        } else {
            updateViewMode()
        }
    }

    private fun updateEditMode() {
        // Show edit fields, hide text views
        binding.nacionalidadLayout.visibility = View.VISIBLE
        binding.nacionalidadText.visibility = View.GONE
        binding.telephoneLayout.visibility = View.VISIBLE
        binding.telephoneText.visibility = View.GONE
        binding.movilLayout.visibility = View.VISIBLE
        binding.movilText.visibility = View.GONE
        binding.addressLayout.visibility = View.VISIBLE
        binding.addressText.visibility = View.GONE
        binding.locationLayout.visibility = View.VISIBLE
        binding.locationText.visibility = View.GONE
        binding.provinciaLayout.visibility = View.VISIBLE
        binding.provinciaText.visibility = View.GONE

        binding.saveButton.visibility = View.VISIBLE
        binding.editToggleButton.text = "Cancelar"
    }

    private fun updateViewMode() {
        // Show text views, hide edit fields
        binding.nacionalidadLayout.visibility = View.GONE
        binding.nacionalidadText.visibility = View.VISIBLE
        binding.telephoneLayout.visibility = View.GONE
        binding.telephoneText.visibility = View.VISIBLE
        binding.movilLayout.visibility = View.GONE
        binding.movilText.visibility = View.VISIBLE
        binding.addressLayout.visibility = View.GONE
        binding.addressText.visibility = View.VISIBLE
        binding.locationLayout.visibility = View.GONE
        binding.locationText.visibility = View.VISIBLE
        binding.provinciaLayout.visibility = View.GONE
        binding.provinciaText.visibility = View.VISIBLE

        binding.saveButton.visibility = View.GONE
        binding.editToggleButton.text = "Editar"
    }

    private fun saveProfile() {
        profileViewModel.updateProfile(
            nacionalidad = binding.nacionalidadInput.text?.toString()?.trim(),
            telephone = binding.telephoneInput.text?.toString()?.trim(),
            movil = binding.movilInput.text?.toString()?.trim(),
            address = binding.addressInput.text?.toString()?.trim(),
            location = binding.locationInput.text?.toString()?.trim(),
            provincia = binding.provinciaInput.text?.toString()?.trim()
        )
    }
}
