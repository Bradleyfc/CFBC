package com.cfbc.android.presentation.courses

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
import com.cfbc.android.databinding.FragmentCoursesListBinding
import com.cfbc.android.presentation.adapter.CourseCardAdapter
import com.cfbc.android.presentation.viewmodel.CourseViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Courses list screen — shows available courses with area/tipo filtering.
 *
 * Requirements: 2.1-2.5, 10.3
 */
@AndroidEntryPoint
class CoursesListFragment : Fragment() {

    private var _binding: FragmentCoursesListBinding? = null
    private val binding get() = _binding!!

    private val courseViewModel: CourseViewModel by viewModels()

    private lateinit var courseAdapter: CourseCardAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentCoursesListBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        setupToolbar()
        setupFilterChips()
        setupRecyclerView()
        observeViewModel()

        courseViewModel.loadCourses()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupRecyclerView() {
        courseAdapter = CourseCardAdapter { courseId ->
            val bundle = Bundle().apply { putInt("courseId", courseId) }
            findNavController().navigate(R.id.action_courses_list_to_detail, bundle)
        }
        binding.coursesRecyclerView.adapter = courseAdapter
    }

    private fun setupToolbar() {
        binding.toolbar.setNavigationOnClickListener {
            findNavController().navigateUp()
        }
        binding.searchView.setOnQueryTextListener(object : androidx.appcompat.widget.SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean = false
            override fun onQueryTextChange(newText: String?): Boolean {
                // TODO: Filter courses list by name
                return false
            }
        })
    }

    private fun setupFilterChips() {
        binding.areaAll.setOnClickListener { courseViewModel.filterByArea(null) }
        binding.areaIdiomas.setOnClickListener { courseViewModel.filterByArea("idiomas") }
        binding.areaComputacion.setOnClickListener { courseViewModel.filterByArea("computacion") }
        binding.areaHumanidades.setOnClickListener { courseViewModel.filterByArea("humanidades") }
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    courseViewModel.listState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        binding.emptyText.visibility =
                            if (!state.isLoading && state.courses.isEmpty() && state.error == null)
                                View.VISIBLE else View.GONE

                        courseAdapter.submitList(state.courses)
                    }
                }
            }
        }
    }
}
