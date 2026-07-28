package com.cfbc.android.presentation.moderator

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
import com.cfbc.android.databinding.FragmentModeratorDashboardBinding
import com.cfbc.app.presentation.model.UiEvent
import com.cfbc.app.presentation.viewmodel.ModeratorViewModel
import com.google.android.material.snackbar.Snackbar
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Moderator Dashboard — shows pending reports, active sanctions, and community metrics.
 *
 * Features:
 * - Metrics summary card (reports, sanctions, comments counts)
 * - Pending reports list with approve/reject buttons
 * - Active sanctions list
 *
 * Requirements: 8.1-8.12
 */
@AndroidEntryPoint
class ModeratorDashboardFragment : Fragment() {

    private var _binding: FragmentModeratorDashboardBinding? = null
    private val binding get() = _binding!!

    private val moderatorViewModel: ModeratorViewModel by viewModels()
    private lateinit var reportsAdapter: ReportAdapter
    private lateinit var sanctionsAdapter: SanctionAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentModeratorDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupToolbar()
        setupRecyclerViews()
        observeViewModel()
        moderatorViewModel.loadAll()
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

    private fun setupRecyclerViews() {
        reportsAdapter = ReportAdapter(
            onApprove = { moderatorViewModel.approveReport(it) },
            onReject = { moderatorViewModel.rejectReport(it) }
        )
        binding.reportsRecyclerView.adapter = reportsAdapter

        sanctionsAdapter = SanctionAdapter()
        binding.sanctionsRecyclerView.adapter = sanctionsAdapter
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    moderatorViewModel.uiState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        // Metrics
                        binding.reportsCount.text = state.metrics.totalReportes.toString()
                        binding.sanctionsCount.text = state.metrics.totalSanciones.toString()
                        binding.commentsCount.text = state.metrics.totalComentarios.toString()

                        // Reports
                        reportsAdapter.submitList(state.reports, state.processingReportId)
                        // Sanctions
                        sanctionsAdapter.submitList(state.sanctions)
                    }
                }

                // Observe one-time events
                launch {
                    moderatorViewModel.events.collectLatest { event ->
                        when (event) {
                            is UiEvent.ShowSnackbar -> {
                                Snackbar.make(binding.root, event.message, Snackbar.LENGTH_SHORT).show()
                            }
                            is UiEvent.ShowErrorSnackbar -> {
                                Snackbar.make(binding.root, event.message, Snackbar.LENGTH_LONG).show()
                            }
                            else -> {}
                        }
                    }
                }
            }
        }
    }
}
