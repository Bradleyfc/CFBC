package com.cfbc.android.presentation.applications

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.cfbc.android.R
import com.cfbc.android.databinding.FragmentApplicationsListBinding
import com.cfbc.android.presentation.adapter.CourseApplicationAdapter
import com.cfbc.android.presentation.model.UiEvent
import com.cfbc.android.presentation.viewmodel.CourseApplicationViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Application list screen — shows the user's course applications with status and cancel action.
 *
 * Requirements: 10.8
 */
@AndroidEntryPoint
class ApplicationListFragment : Fragment() {

    private var _binding: FragmentApplicationsListBinding? = null
    private val binding get() = _binding!!

    private val applicationViewModel: CourseApplicationViewModel by viewModels()

    private lateinit var applicationAdapter: CourseApplicationAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentApplicationsListBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupRecyclerView()
        observeViewModel()
        applicationViewModel.loadApplications()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupRecyclerView() {
        applicationAdapter = CourseApplicationAdapter { applicationId ->
            applicationViewModel.cancelApplication(applicationId)
        }
        binding.applicationsRecyclerView.adapter = applicationAdapter
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    applicationViewModel.uiState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        binding.emptyText.visibility =
                            if (!state.isLoading && state.applications.isEmpty() && state.error == null)
                                View.VISIBLE else View.GONE

                        applicationAdapter.submitList(state.applications)
                    }
                }

                launch {
                    applicationViewModel.events.collectLatest { event ->
                        when (event) {
                            is UiEvent.ShowSnackbar -> {
                                val activity = requireActivity() as? com.cfbc.android.presentation.MainActivity
                                activity?.showSnackbar(event.message)
                            }
                            is UiEvent.ShowErrorSnackbar -> {
                                val activity = requireActivity() as? com.cfbc.android.presentation.MainActivity
                                activity?.showSnackbar(event.message, true)
                            }
                            else -> {}
                        }
                    }
                }
            }
        }
    }
}
