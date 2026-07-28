package com.cfbc.android.presentation.editor

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
import com.cfbc.android.databinding.FragmentEditorDashboardBinding
import com.cfbc.android.presentation.adapter.BlogPostCardAdapter
import com.cfbc.app.presentation.model.UiEvent
import com.cfbc.app.presentation.model.toListItem
import com.cfbc.app.presentation.viewmodel.EditorViewModel
import com.google.android.material.snackbar.Snackbar
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Editor Dashboard — manages the editorial workflow.
 *
 * Features:
 * - Search posts by author username
 * - Pending review posts list
 * - Recently published posts list
 *
 * Requirements: 9.1-9.12
 */
@AndroidEntryPoint
class EditorDashboardFragment : Fragment() {

    private var _binding: FragmentEditorDashboardBinding? = null
    private val binding get() = _binding!!

    private val editorViewModel: EditorViewModel by viewModels()
    private lateinit var pendingAdapter: BlogPostCardAdapter
    private lateinit var recentAdapter: BlogPostCardAdapter
    private lateinit var searchResultsAdapter: BlogPostCardAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentEditorDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupToolbar()
        setupSearch()
        setupRecyclerViews()
        observeViewModel()
        editorViewModel.loadAll()
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

    private fun setupSearch() {
        binding.searchView.setOnQueryTextListener(object : androidx.appcompat.widget.SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                editorViewModel.searchPosts(query ?: "")
                return true
            }

            override fun onQueryTextChange(newText: String?): Boolean {
                if (newText.isNullOrEmpty()) {
                    editorViewModel.searchPosts("")
                }
                return false
            }
        })
    }

    private fun setupRecyclerViews() {
        val postClickListener: (String) -> Unit = { slug ->
            val bundle = Bundle().apply { putString("slug", slug) }
            findNavController().navigate(R.id.action_editor_to_blog_post, bundle)
        }

        pendingAdapter = BlogPostCardAdapter(postClickListener)
        binding.pendingRecyclerView.adapter = pendingAdapter

        recentAdapter = BlogPostCardAdapter(postClickListener)
        binding.recentRecyclerView.adapter = recentAdapter

        searchResultsAdapter = BlogPostCardAdapter(postClickListener)
        binding.searchResultsRecyclerView.adapter = searchResultsAdapter
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    editorViewModel.uiState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        // Pending review
                        binding.pendingCountBadge.text = state.pendingReviewCount.toString()
                        pendingAdapter.submitList(
                            state.pendingReviewPosts.map { it.toListItem() }
                        )

                        // Recently published
                        binding.recentCountBadge.text = state.recentlyPublishedCount.toString()
                        recentAdapter.submitList(
                            state.recentlyPublishedPosts.map { it.toListItem() }
                        )

                        // Search results
                        val hasSearchResults = state.searchResults.isNotEmpty()
                        binding.searchResultsTitle.visibility =
                            if (hasSearchResults) View.VISIBLE else View.GONE
                        binding.searchResultsRecyclerView.visibility =
                            if (hasSearchResults) View.VISIBLE else View.GONE
                        searchResultsAdapter.submitList(
                            state.searchResults.map { it.toListItem() }
                        )
                    }
                }

                // Observe one-time events
                launch {
                    editorViewModel.events.collectLatest { event ->
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

