package com.cfbc.android.presentation.editor

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.cfbc.android.R
import com.cfbc.android.databinding.FragmentBlogEditorBinding
import com.cfbc.app.presentation.model.UiEvent
import com.cfbc.app.presentation.viewmodel.BlogEditorViewModel
import com.google.android.material.snackbar.Snackbar
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Blog post editor — create new posts or edit existing ones.
 *
 * Features:
 * - Title, summary, content text fields with validation
 * - Category dropdown (loaded from API)
 * - Meta description with character counter
 * - Featured toggle switch
 * - Visibility radio buttons (Publico, Indexable, Privado)
 * - Save as draft button in toolbar
 *
 * Modes:
 * - Create mode: No postId argument → creates new draft
 * - Edit mode: postId argument → loads existing post (future enhancement)
 *
 * Requirements: 7.7, 7.9, 7.11
 */
@AndroidEntryPoint
class BlogPostEditorFragment : Fragment() {

    private var _binding: FragmentBlogEditorBinding? = null
    private val binding get() = _binding!!

    private val editorViewModel: BlogEditorViewModel by viewModels()

    /** postId > 0 means edit mode. */
    private var postId: Int = 0

    /** List of category IDs indexed by dropdown position. */
    private var categoryIds: List<Int> = emptyList()

    /** Currently selected category ID from the dropdown. */
    private var selectedCategoryId: Int? = null

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentBlogEditorBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        postId = arguments?.getInt("postId", 0) ?: 0

        setupToolbar()
        setupCategoryDropdown()
        observeViewModel()

        // Load categories for dropdown
        editorViewModel.loadCategories()

        // Set title based on mode
        binding.toolbar.title = if (postId > 0) "Editar Post" else "Nuevo Post"
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupToolbar() {
        binding.toolbar.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        binding.submitButton.setOnClickListener {
            submitPost()
        }
    }

    private fun setupCategoryDropdown() {
        binding.categoryDropdown.setOnItemClickListener { _, _, position, _ ->
            selectedCategoryId = categoryIds.getOrNull(position)
        }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    editorViewModel.uiState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isCategoriesLoading) View.VISIBLE else View.GONE

                        // Show/hide error
                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        // Disable submit while saving
                        binding.submitButton.isEnabled = !state.isSaving
                        binding.submitButton.text =
                            if (state.isSaving) "Guardando..." else "Guardar"

                        // Populate category dropdown
                        if (state.categories.isNotEmpty()) {
                            categoryIds = state.categories.map { it.id }
                            val categoryNames = state.categories.map { it.nombre }
                            val adapter = ArrayAdapter(
                                requireContext(),
                                android.R.layout.simple_dropdown_item_1line,
                                categoryNames
                            )
                            binding.categoryDropdown.setAdapter(adapter)
                        }
                    }
                }

                launch {
                    editorViewModel.events.collectLatest { event ->
                        when (event) {
                            is UiEvent.ShowSnackbar -> {
                                Snackbar.make(binding.root, event.message, Snackbar.LENGTH_SHORT).show()
                            }
                            is UiEvent.ShowErrorSnackbar -> {
                                Snackbar.make(binding.root, event.message, Snackbar.LENGTH_LONG).show()
                            }
                            is UiEvent.NavigateBack -> {
                                findNavController().navigateUp()
                            }
                            else -> {}
                        }
                    }
                }
            }
        }
    }

    private fun submitPost() {
        val titulo = binding.titleInput.text?.toString()?.trim() ?: ""
        val resumen = binding.summaryInput.text?.toString()?.trim() ?: ""
        val contenido = binding.contentInput.text?.toString()?.trim() ?: ""
        val metaDescripcion = binding.metaInput.text?.toString()?.trim()
        val categoriaId = selectedCategoryId
        val destacada = binding.featuredSwitch.isChecked
        val visibilidad = when (binding.visibilityGroup.checkedRadioButtonId) {
            R.id.visibilityIndexable -> "indexable"
            R.id.visibilityPrivate -> "privado"
            else -> "publico"
        }

        if (postId > 0) {
            editorViewModel.updatePost(
                postId = postId,
                titulo = titulo,
                resumen = resumen,
                contenido = contenido,
                categoriaId = categoriaId,
                metaDescripcion = metaDescripcion,
                destacada = destacada,
                visibilidad = visibilidad
            )
        } else {
            editorViewModel.createPost(
                titulo = titulo,
                resumen = resumen,
                contenido = contenido,
                categoriaId = categoriaId,
                metaDescripcion = metaDescripcion,
                destacada = destacada,
                visibilidad = visibilidad
            )
        }
    }
}
