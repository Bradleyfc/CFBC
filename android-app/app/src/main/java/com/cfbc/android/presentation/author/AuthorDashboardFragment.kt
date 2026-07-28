package com.cfbc.android.presentation.author

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
import com.cfbc.android.databinding.FragmentAuthorDashboardBinding
import com.cfbc.android.presentation.adapter.BlogPostCardAdapter
import com.cfbc.app.presentation.model.toListItem
import com.cfbc.app.presentation.viewmodel.AuthorViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Author Dashboard — shows the author's posts grouped by status with counts.
 *
 * Features:
 * - Status filter chips (Todos, Borrador, Pendiente, Publicado, Archivado)
 * - Summary card with counts per status
 * - Posts list filtered by selected status
 *
 * Requirements: 7.1-7.11
 */
@AndroidEntryPoint
class AuthorDashboardFragment : Fragment() {

    private var _binding: FragmentAuthorDashboardBinding? = null
    private val binding get() = _binding!!

    private val authorViewModel: AuthorViewModel by viewModels()
    private lateinit var postsAdapter: BlogPostCardAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentAuthorDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupToolbar()
        setupFilterChips()
        setupRecyclerView()
        observeViewModel()
        authorViewModel.loadPosts()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupToolbar() {
        binding.toolbar.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        // Create Post FAB
        binding.createFab.setOnClickListener {
            findNavController().navigate(R.id.action_author_to_editor)
        }
    }

    private fun setupFilterChips() {
        binding.chipAll.setOnClickListener { authorViewModel.filterByStatus(null) }
        binding.chipBorrador.setOnClickListener { authorViewModel.filterByStatus("borrador") }
        binding.chipPending.setOnClickListener { authorViewModel.filterByStatus("pendiente_revision") }
        binding.chipPublished.setOnClickListener { authorViewModel.filterByStatus("publicado") }
        binding.chipArchived.setOnClickListener { authorViewModel.filterByStatus("archivado") }
    }

    private fun setupRecyclerView() {
        postsAdapter = BlogPostCardAdapter { slug ->
            val bundle = Bundle().apply { putString("slug", slug) }
            // Navigate using the generic blog post detail destination
            findNavController().navigate(R.id.action_author_to_blog_post, bundle)
        }
        binding.postsRecyclerView.adapter = postsAdapter
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    authorViewModel.uiState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        // Update summary counts
                        binding.borradorCount.text = state.borradorCount.toString()
                        binding.pendingCount.text = state.pendienteRevisionCount.toString()
                        binding.publishedCount.text = state.publicadoCount.toString()
                        binding.archivedCount.text = state.archivadoCount.toString()

                        // Filter posts by selected status
                        val filteredPosts = if (state.selectedStatus == null) {
                            state.posts
                        } else {
                            state.posts.filter { it.estado == state.selectedStatus }
                        }
                        postsAdapter.submitList(
                            filteredPosts.map { it.toListItem() }
                        )

                        binding.emptyText.visibility =
                            if (!state.isLoading && filteredPosts.isEmpty() && state.error == null)
                                View.VISIBLE else View.GONE
                    }
                }
            }
        }
    }
}

