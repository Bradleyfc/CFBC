package com.cfbc.android.presentation.blog

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
import com.cfbc.android.databinding.FragmentBlogListBinding
import com.cfbc.android.presentation.adapter.BlogPostCardAdapter
import com.cfbc.android.presentation.viewmodel.BlogViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Blog list screen — shows published blog posts with category filtering and search.
 *
 * Requirements: 3.1-3.6
 */
@AndroidEntryPoint
class BlogListFragment : Fragment() {

    private var _binding: FragmentBlogListBinding? = null
    private val binding get() = _binding!!

    private val blogViewModel: BlogViewModel by viewModels()

    private lateinit var blogAdapter: BlogPostCardAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentBlogListBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupSearch()
        setupRecyclerView()
        observeViewModel()

        blogViewModel.loadPosts()
        blogViewModel.loadCategories()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupRecyclerView() {
        blogAdapter = BlogPostCardAdapter { slug ->
            val bundle = Bundle().apply { putString("slug", slug) }
            findNavController().navigate(R.id.action_blog_list_to_post, bundle)
        }
        binding.postsRecyclerView.adapter = blogAdapter
    }

    private fun setupSearch() {
        binding.searchView.setOnQueryTextListener(object : androidx.appcompat.widget.SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                blogViewModel.searchPosts(query ?: "")
                return true
            }

            override fun onQueryTextChange(newText: String?): Boolean {
                if (newText.isNullOrEmpty()) {
                    blogViewModel.searchPosts("")
                }
                return false
            }
        })
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    blogViewModel.listState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        binding.emptyText.visibility =
                            if (!state.isLoading && state.posts.isEmpty() && state.error == null)
                                View.VISIBLE else View.GONE

                        // Populate category chips dynamically
                        if (state.categories.isNotEmpty() && binding.categoryChipGroup.childCount <= 1) {
                            for (category in state.categories) {
                                val chip = com.google.android.material.chip.Chip(
                                    requireContext(),
                                    null,
                                    com.google.android.material.R.style.Widget_MaterialComponents_Chip_Filter
                                )
                                chip.id = View.generateViewId()
                                chip.text = category.nombre
                                chip.isChecked = false
                                chip.setOnClickListener {
                                    blogViewModel.filterByCategory(category.id)
                                }
                                binding.categoryChipGroup.addView(chip)
                            }
                        }

                        blogAdapter.submitList(state.posts)
                    }
                }
            }
        }
    }
}
