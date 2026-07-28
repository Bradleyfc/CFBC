package com.cfbc.app.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.repository.CourseRepository
import com.cfbc.app.infrastructure.network.dto.CourseResponse
import com.cfbc.app.infrastructure.network.dto.HomePageResponse
import com.cfbc.app.presentation.model.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * ViewModel for course browsing and home page.
 *
 * Manages:
 * - Available courses list with area/tipo filtering
 * - Course detail view
 * - Home page (available courses + latest news)
 * - Pull-to-refresh support
 * - Offline-first: shows cached data while loading fresh data
 *
 * Requirements: 2.1-2.5, 10.3, 10.4
 */
@HiltViewModel
class CourseViewModel @Inject constructor(
    private val courseRepository: CourseRepository
) : ViewModel() {

    // =========================================================================
    // UI State — Course List
    // =========================================================================

    private val _listState = MutableStateFlow(CourseListUiState())
    val listState: StateFlow<CourseListUiState> = _listState.asStateFlow()

    // =========================================================================
    // UI State — Course Detail
    // =========================================================================

    private val _detailState = MutableStateFlow(CourseDetailUiState())
    val detailState: StateFlow<CourseDetailUiState> = _detailState.asStateFlow()

    // =========================================================================
    // UI State — Home Page
    // =========================================================================

    private val _homeState = MutableStateFlow(HomePageUiState())
    val homeState: StateFlow<HomePageUiState> = _homeState.asStateFlow()

    // =========================================================================
    // Events
    // =========================================================================

    private val _events = Channel<UiEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    // =========================================================================
    // Reactive cache observations (shows cached data immediately)
    // =========================================================================

    /** Observe cached courses reactively (offline-first support). */
    val cachedCourses: Flow<List<com.cfbc.app.data.local.entity.CourseEntity>> =
        courseRepository.observeCourses()

    // =========================================================================
    // Actions — Course List
    // =========================================================================

    /**
     * Load available courses from network.
     * Supports area/tipo filtering.
     */
    fun loadCourses(area: String? = null, tipo: String? = null) {
        viewModelScope.launch {
            _listState.value = _listState.value.copy(
                isLoading = true,
                error = null,
                selectedArea = area,
                selectedTipo = tipo
            )

            when (val result = courseRepository.getCourses(area, tipo)) {
                is Result.Success -> {
                    _listState.value = _listState.value.copy(
                        courses = result.data.map { it.toUiModel() },
                        isLoading = false
                    )
                }
                is Result.Error -> {
                    _listState.value = _listState.value.copy(
                        isLoading = false,
                        error = result.displayMessage
                    )
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /**
     * Pull-to-refresh: silently refresh courses without showing loading indicator.
     */
    fun refreshCourses() {
        viewModelScope.launch {
            _listState.value = _listState.value.copy(isRefreshing = true)

            when (val result = courseRepository.getCourses(
                _listState.value.selectedArea,
                _listState.value.selectedTipo
            )) {
                is Result.Success -> {
                    _listState.value = _listState.value.copy(
                        courses = result.data.map { it.toUiModel() },
                        isRefreshing = false,
                        error = null
                    )
                }
                is Result.Error -> {
                    _listState.value = _listState.value.copy(
                        isRefreshing = false
                    )
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /** Filter courses by area. */
    fun filterByArea(area: String?) {
        loadCourses(area, _listState.value.selectedTipo)
    }

    /** Filter courses by tipo. */
    fun filterByTipo(tipo: String?) {
        loadCourses(_listState.value.selectedArea, tipo)
    }

    // =========================================================================
    // Actions — Course Detail
    // =========================================================================

    /**
     * Load a single course by ID.
     */
    fun loadCourseById(courseId: Int) {
        viewModelScope.launch {
            _detailState.value = CourseDetailUiState(isLoading = true)

            when (val result = courseRepository.getCourseById(courseId)) {
                is Result.Success -> {
                    _detailState.value = CourseDetailUiState(
                        course = result.data.toUiModel()
                    )
                }
                is Result.Error -> {
                    _detailState.value = CourseDetailUiState(error = result.displayMessage)
                    _events.send(UiEvent.ShowErrorSnackbar(result.displayMessage))
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    // =========================================================================
    // Actions — Home Page
    // =========================================================================

    /**
     * Load home page data (available courses + latest news).
     */
    fun loadHomePage() {
        viewModelScope.launch {
            _homeState.value = HomePageUiState(isLoading = true)

            when (val result = courseRepository.getHomePage()) {
                is Result.Success -> {
                    _homeState.value = HomePageUiState(
                        data = result.data.toUiModel()
                    )
                }
                is Result.Error -> {
                    _homeState.value = HomePageUiState(error = result.displayMessage)
                }
                is Result.Loading -> { /* handled */ }
            }
        }
    }

    /** Clear errors. */
    fun clearListError() {
        _listState.value = _listState.value.copy(error = null)
    }

    fun clearDetailError() {
        _detailState.value = _detailState.value.copy(error = null)
    }
}

// =============================================================================
// DTO → UiModel mapping extensions
// =============================================================================

/** Maps a [CourseResponse] to a [CourseUiModel]. */
fun CourseResponse.toUiModel(): CourseUiModel = CourseUiModel(
    id = id,
    name = name,
    description = description,
    area = area,
    areaDisplay = areaDisplay,
    tipo = tipo,
    tipoDisplay = tipoDisplay,
    teacherName = teacherName,
    status = status,
    statusDisplay = statusDisplay,
    dynamicStatus = dynamicStatus,
    dynamicStatusDisplay = dynamicStatusDisplay,
    startDate = startDate,
    enrollmentDeadline = enrollmentDeadline,
    imageUrl = imageUrl,
    cursoAcademicoNombre = cursoAcademicoNombre
)

/** Maps a [HomePageResponse] to a [HomePageUiModel]. */
fun HomePageResponse.toUiModel(): HomePageUiModel = HomePageUiModel(
    availableCourses = availableCourses.map { it.toUiModel() },
    latestNews = latestNews.map { post ->
        BlogPostListItemUiModel(
            id = post.id,
            titulo = post.titulo,
            slug = post.slug,
            resumen = post.resumen,
            imagenPrincipalUrl = post.imagenPrincipalUrl,
            categoria = post.categoria,
            autorUsername = post.autorUsername,
            fechaPublicacion = post.fechaPublicacion,
            destacada = post.destacada
        )
    }
)
