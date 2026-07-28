package com.cfbc.app.data.repository

import com.cfbc.app.data.local.LocalDataSource
import com.cfbc.app.data.local.entity.CourseEntity
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.infrastructure.network.dto.CourseResponse
import com.cfbc.app.infrastructure.network.dto.HomePageResponse
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for course-related operations.
 *
 * Implements offline-first strategy:
 * 1. Try fetching fresh data from the network
 * 2. On success: cache the data locally and return it
 * 3. On failure: return cached data if available, or forward the error
 *
 * Requirements: 2.1-2.5, 10.3, 10.4
 */
@Singleton
class CourseRepository @Inject constructor(
    private val networkDataSource: NetworkDataSource,
    private val localDataSource: LocalDataSource
) {

    // =========================================================================
    // Observable cached data (for UI that updates reactively)
    // =========================================================================

    /** Observe cached courses (reactive). */
    fun observeCourses(): Flow<List<CourseEntity>> = localDataSource.observeCourses()

    /** Observe cached available courses (reactive). */
    fun observeAvailableCourses(limit: Int = 50): Flow<List<CourseEntity>> =
        localDataSource.observeAvailableCourses(limit)

    /** Observe cached courses by area (reactive). */
    fun observeCoursesByArea(area: String): Flow<List<CourseEntity>> =
        localDataSource.observeCoursesByArea(area)

    /** Observe cached courses by tipo (reactive). */
    fun observeCoursesByTipo(tipo: String): Flow<List<CourseEntity>> =
        localDataSource.observeCoursesByTipo(tipo)

    // =========================================================================
    // Network-first operations (with cache fallback)
    // =========================================================================

    /**
     * Fetch available courses from the network.
     *
     * Offline-first strategy:
     * 1. Try the network call
     * 2. On success: cache results and return them
     * 3. On failure: return cached data if available, otherwise forward error
     */
    suspend fun getCourses(
        area: String? = null,
        tipo: String? = null,
        page: Int? = null
    ): Result<List<CourseResponse>> {
        return when (val result = networkDataSource.getCourses(area, tipo, page)) {
            is Result.Success -> {
                // Cache the course list locally (if page 1, replace cache)
                if (page == null || page <= 1) {
                    val entities = result.data.results.map { it.toEntity() }
                    localDataSource.cacheCourses(entities)
                }
                Result.Success(result.data.results)
            }
            // On error, just forward it. The UI observes cached data via Flow.
            else -> result
        }
    }

    /**
     * Fetch a single course by ID.
     * Network-first with cache fallback.
     */
    suspend fun getCourseById(courseId: Int): Result<CourseResponse> {
        return when (val result = networkDataSource.getCourseById(courseId)) {
            is Result.Success -> {
                // Cache the single course
                localDataSource.cacheCourse(result.data.toEntity())
                result
            }
            is Result.Error -> {
                // Try cache
                val cached = localDataSource.getCachedCourseById(courseId)
                if (cached != null) {
                    Result.Success(cached.toDto())
                } else {
                    result
                }
            }
            is Result.Loading -> result
        }
    }

    /**
     * Fetch home page data (available courses + latest news).
     * Does NOT cache home page data as it's a combined view.
     */
    suspend fun getHomePage(): Result<HomePageResponse> {
        return when (val result = networkDataSource.getHomePage()) {
            is Result.Success -> {
                // Cache the courses from home page
                val courseEntities = result.data.availableCourses.map { it.toEntity() }
                localDataSource.cacheCourses(courseEntities)
                result
            }
            else -> result
        }
    }
}

// =============================================================================
// Extension functions for Entity ↔ DTO mapping
// =============================================================================

/**
 * Maps a [CourseResponse] (network DTO) to a [CourseEntity] (Room entity).
 */
fun CourseResponse.toEntity(): CourseEntity = CourseEntity(
    id = id,
    name = name,
    description = description,
    area = area,
    tipo = tipo,
    teacherName = teacherName,
    classQuantity = classQuantity,
    status = status,
    statusDisplay = statusDisplay,
    cursoAcademicoNombre = cursoAcademicoNombre,
    startDate = startDate, // ISO date string, stored as-is
    statusAvailable = status == "I", // "I" = En etapa de inscripción
    cachedAt = System.currentTimeMillis()
)

/**
 * Maps a [CourseEntity] (Room entity) back to a [CourseResponse] (network DTO).
 */
fun CourseEntity.toDto(): CourseResponse = CourseResponse(
    id = id,
    name = name,
    description = description,
    area = area,
    tipo = tipo,
    teacher = 0, // Not cached
    teacherName = teacherName,
    teacherUsername = "", // Not cached
    classQuantity = classQuantity,
    status = status,
    statusDisplay = statusDisplay,
    dynamicStatus = "", // Not cached
    dynamicStatusDisplay = "", // Not cached
    cursoAcademico = null, // Not cached
    cursoAcademicoNombre = cursoAcademicoNombre,
    enrollmentDeadline = null, // Not cached
    startDate = startDate,
    imageUrl = null, // Not cached
    fechaCreacion = null, // Not cached
    fechaActualizacion = null // Not cached
)
