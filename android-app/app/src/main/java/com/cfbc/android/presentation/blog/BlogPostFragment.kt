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
import coil.load
import com.cfbc.android.R
import com.cfbc.android.databinding.FragmentBlogPostBinding
import com.cfbc.android.presentation.viewmodel.BlogViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Blog post detail screen — shows full article content.
 *
 * Receives slug via Safe Args from navigation graph.
 *
 * Requirements: 3.1, 3.2
 */
@AndroidEntryPoint
class BlogPostFragment : Fragment() {

    private var _binding: FragmentBlogPostBinding? = null
    private val binding get() = _binding!!

    private val blogViewModel: BlogViewModel by viewModels()

    private var slug: String = ""

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentBlogPostBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Get slug from Safe Args
        slug = arguments?.getString("slug", "") ?: ""

        setupToolbar()
        observeViewModel()

        if (slug.isNotEmpty()) {
            blogViewModel.loadPostBySlug(slug)
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
        binding.shareButton.setOnClickListener {
            val shareIntent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(android.content.Intent.EXTRA_TEXT, "Mira este artículo: $slug")
            }
            startActivity(android.content.Intent.createChooser(shareIntent, "Compartir"))
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    blogViewModel.detailState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        state.post?.let { post ->
                            binding.postImage.visibility = View.VISIBLE
                            binding.categoryBadge.visibility = View.VISIBLE
                            binding.postTitle.visibility = View.VISIBLE
                            binding.authorLayout.visibility = View.VISIBLE
                            binding.divider.visibility = View.VISIBLE
                            binding.postContent.visibility = View.VISIBLE

                            binding.postTitle.text = post.titulo
                            binding.categoryBadge.text = post.categoria
                            binding.authorName.text = post.autorUsername
                            binding.publishDate.text = post.fechaPublicacion ?: ""
                            binding.postContent.text = post.contenido

                            post.imagenPrincipalUrl?.let { url ->
                                binding.postImage.load(url) {
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
}
