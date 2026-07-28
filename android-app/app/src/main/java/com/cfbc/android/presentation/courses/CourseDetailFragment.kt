package com.cfbc.android.presentation.courses

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import coil.load
import com.cfbc.android.R
import com.cfbc.android.databinding.FragmentCourseDetailBinding
import com.cfbc.android.presentation.model.UiEvent
import com.cfbc.android.presentation.viewmodel.CourseApplicationViewModel
import com.cfbc.android.presentation.viewmodel.CourseViewModel
import com.google.android.material.snackbar.Snackbar
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Course detail screen — shows full course information with apply button.
 *
 * Receives courseId via Safe Args from navigation graph.
 *
 * Requirements: 2.1, 2.5
 */
@AndroidEntryPoint
class CourseDetailFragment : Fragment() {

    private var _binding: FragmentCourseDetailBinding? = null
    private val binding get() = _binding!!

    private val courseViewModel: CourseViewModel by viewModels()
    private val applicationViewModel: CourseApplicationViewModel by viewModels()

    private var courseId: Int = 0

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentCourseDetailBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Get courseId from Safe Args
        courseId = arguments?.getInt("courseId", 0) ?: 0

        setupToolbar()
        setupClickListeners()
        observeViewModel()
        observeApplicationEvents()

        if (courseId > 0) {
            courseViewModel.loadCourseById(courseId)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupToolbar() {
        binding.toolbar.setNavigationOnClickListener {
            findNavController().navigateUp()
        }
    }

    private fun setupClickListeners() {
        binding.applyButton.setOnClickListener {
            applicationViewModel.applyToCourse(courseId)
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    courseViewModel.detailState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        state.course?.let { course ->
                            // Show all views
                            binding.courseImage.visibility = View.VISIBLE
                            binding.courseName.visibility = View.VISIBLE
                            binding.infoCard.visibility = View.VISIBLE
                            binding.descriptionCard.visibility = View.VISIBLE
                            binding.applyButton.visibility = View.VISIBLE

                            // Populate data
                            binding.courseName.text = course.name
                            binding.teacherValue.text = course.teacherName
                            binding.typeValue.text = course.tipoDisplay
                            binding.statusValue.text = course.dynamicStatusDisplay
                            binding.datesValue.text = buildString {
                                course.startDate?.let { append("Inicio: $it") }
                                course.enrollmentDeadline?.let {
                                    if (isNotEmpty()) append("\n")
                                    append("Cierre: $it")
                                }
                            }
                            binding.descriptionValue.text = course.description ?: "Sin descripción"

                            // Set area badge
                            binding.applyButton.text = "Aplicar a ${course.name}"

                            // Load image with Coil
                            course.imageUrl?.let { url ->
                                binding.courseImage.load(url) {
                                    placeholder(android.R.drawable.ic_menu_gallery)
                                    error(android.R.drawable.ic_menu_gallery)
                                    crossfade(true)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private fun observeApplicationEvents() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                // Observe submission state to toggle button
                launch {
                    applicationViewModel.uiState.collectLatest { state ->
                        binding.applyButton.isEnabled = !state.isSubmitting
                        binding.applyButton.text = if (state.isSubmitting) {
                            "Enviando solicitud..."
                        } else {
                            "Aplicar a este curso"
                        }
                    }
                }

                // Observe one-time events (success/error snackbars + navigation)
                launch {
                    applicationViewModel.events.collectLatest { event ->
                        when (event) {
                            is UiEvent.ShowSnackbar -> {
                                Snackbar.make(binding.root, event.message, Snackbar.LENGTH_SHORT).show()
                            }
                            is UiEvent.ShowErrorSnackbar -> {
                                Snackbar.make(binding.root, event.message, Snackbar.LENGTH_LONG)
                                    .setBackgroundTint(
                                        ContextCompat.getColor(requireContext(), android.R.color.holo_red_dark)
                                    )
                                    .show()
                            }
                            is UiEvent.NavigateToApplications -> {
                                findNavController().navigate(R.id.action_course_detail_to_applications)
                            }
                            else -> { /* handle other events */ }
                        }
                    }
                }
            }
        }
    }
}
