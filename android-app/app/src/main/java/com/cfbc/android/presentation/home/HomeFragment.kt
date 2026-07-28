package com.cfbc.android.presentation.home

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
import com.cfbc.android.databinding.FragmentHomeBinding
import com.cfbc.android.presentation.adapter.BlogPostCardAdapter
import com.cfbc.android.presentation.adapter.CourseCardAdapter
import com.cfbc.android.presentation.model.UiEvent
import com.cfbc.android.presentation.viewmodel.AuthViewModel
import com.cfbc.android.presentation.viewmodel.CourseViewModel
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Home screen — dashboard showing available courses and latest blog news.
 *
 * Requirements: 10.4
 */
@AndroidEntryPoint
class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!

    private val courseViewModel: CourseViewModel by viewModels()
    private val authViewModel: AuthViewModel by viewModels()

    private lateinit var coursesAdapter: CourseCardAdapter
    private lateinit var newsAdapter: BlogPostCardAdapter

    /** Whether the current user is authenticated. */
    private var isAuthenticated: Boolean = false

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupClickListeners()
        setupRecyclerViews()
        observeViewModel()

        // Load data
        courseViewModel.loadHomePage()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupClickListeners() {
        binding.logoutButton.setOnClickListener {
            authViewModel.logout()
        }

        binding.viewAllCoursesButton.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_courses_list)
        }

        binding.viewAllBlogButton.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_blog_list)
        }

        binding.applicationsCard.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_applications)
        }

        // Role-based dashboard cards
        binding.authorDashboardCard.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_author_dashboard)
        }
        binding.moderatorDashboardCard.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_moderator_dashboard)
        }
        binding.editorDashboardCard.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_editor_dashboard)
        }
    }

    private fun setupRecyclerViews() {
        coursesAdapter = CourseCardAdapter { courseId ->
            val bundle = Bundle().apply { putInt("courseId", courseId) }
            findNavController().navigate(R.id.action_home_to_course_detail, bundle)
        }
        binding.coursesRecyclerView.adapter = coursesAdapter

        newsAdapter = BlogPostCardAdapter { slug ->
            val bundle = Bundle().apply { putString("slug", slug) }
            findNavController().navigate(R.id.action_home_to_blog_post, bundle)
        }
        binding.newsRecyclerView.adapter = newsAdapter
    }

    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                // Observe home state
                launch {
                    courseViewModel.homeState.collectLatest { state ->
                        binding.loadingIndicator.visibility =
                            if (state.isLoading) View.VISIBLE else View.GONE

                        if (state.error != null) {
                            binding.errorText.text = state.error
                            binding.errorText.visibility = View.VISIBLE
                        } else {
                            binding.errorText.visibility = View.GONE
                        }

                        state.data?.let { homeData ->
                            coursesAdapter.submitList(homeData.availableCourses)
                            newsAdapter.submitList(homeData.latestNews)
                        }
                    }
                }

                // Observe auth state for role-based navigation visibility
                launch {
                    authViewModel.uiState.collectLatest { authState ->
                        isAuthenticated = authState.isAuthenticated

                        // Show/hide applications card only for authenticated students
                        binding.applicationsCard.visibility =
                            if (authState.isAuthenticated && authState.groups.any { it == "Estudiantes" })
                                View.VISIBLE else View.GONE

                        // Show/hide role-based dashboard cards
                        val hasBlogRole = authState.isAuthenticated && (
                            authState.groups.any { it == "Blog Autor" } ||
                            authState.groups.any { it == "Blog Moderador" } ||
                            authState.groups.any { it == "Editor" }
                        )
                        binding.dashboardSectionTitle.visibility =
                            if (hasBlogRole) View.VISIBLE else View.GONE

                        binding.authorDashboardCard.visibility =
                            if (authState.isAuthenticated && authState.groups.any { it == "Blog Autor" })
                                View.VISIBLE else View.GONE

                        binding.moderatorDashboardCard.visibility =
                            if (authState.isAuthenticated && authState.groups.any { it == "Blog Moderador" })
                                View.VISIBLE else View.GONE

                        binding.editorDashboardCard.visibility =
                            if (authState.isAuthenticated && authState.groups.any { it == "Editor" })
                                View.VISIBLE else View.GONE
                    }
                }

                // Observe auth events for logout navigation
                launch {
                    authViewModel.events.collectLatest { event ->
                        when (event) {
                            is UiEvent.NavigateToLogin -> {
                                findNavController().navigate(R.id.action_home_to_login)
                            }
                            else -> { /* handle other events */ }
                        }
                    }
                }
            }
        }
    }
}
