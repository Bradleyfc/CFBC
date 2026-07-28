package com.cfbc.app.data.repository

import com.cfbc.app.data.local.LocalDataSource
import com.cfbc.app.data.local.entity.CourseApplicationEntity
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.infrastructure.network.dto.CourseApplicationResponse
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for course application operations.
 *
 * Students apply to courses before being enrolled.
 * Supports offline-first: caches applications locally and shows cached data on error.
 *
 * Requirements: 10.8
 */
@Singleton
class CourseApplicationRepository @Inject constructor(
    private val networkDataSource: NetworkDataSource,
    private val localDataSource: LocalDataSource
) {

    // =========================================================================
    // Observable cached data (reactive UI updates)
    // =========================================================================

    /** Observe cached applications (reactive). */
    fun observeApplications(): Flow<List<CourseApplicationEntity>> =
        localDataSource.observeApplications()

    /** Observe pending cached applications (reactive). */
    fun observePendingApplications(): Flow<List<CourseApplicationEntity>> =
        localDataSource.observePendingApplications()

    // =========================================================================
    // Network-first operations
    // =========================================================================

    /**
     * Apply to a course. Network-only (no cache fallback for writes).
     */
    suspend fun createApplication(courseId: Int): Result<CourseApplicationResponse> {
        return when (val result = networkDataSource.createApplication(courseId)) {
            is Result.Success -> {
                localDataSource.cacheApplication(result.data.toEntity())
                result
            }
            else -> result
        }
    }

    /**
     * List the authenticated user's applications.
     * Offline-first: cache on success, fall back to cache on error.
     */
    suspend fun getApplications(page: Int? = null): Result<List<CourseApplicationResponse>> {
        return when (val result = networkDataSource.getApplications(page)) {
            is Result.Success -> {
                if (page == null || page <= 1) {
                    val entities = result.data.results.map { it.toEntity() }
                    localDataSource.cacheApplications(entities)
                }
                Result.Success(result.data.results)
            }
            else -> result
        }
    }

    /**
     * Cancel a pending application. Network-only.
     */
    suspend fun cancelApplication(applicationId: Int): Result<Unit> {
        return when (val result = networkDataSource.cancelApplication(applicationId)) {
            is Result.Success -> {
                localDataSource.deleteCachedApplication(applicationId)
                Result.Success(Unit)
            }
            else -> result
        }
    }
}

// =============================================================================
// Extension functions for Entity ↔ DTO mapping
// =============================================================================

/** Maps a [CourseApplicationResponse] to a [CourseApplicationEntity]. */
fun CourseApplicationResponse.toEntity(): CourseApplicationEntity = CourseApplicationEntity(
    id = id,
    courseId = course,
    courseName = courseName,
    studentUsername = studentUsername,
    status = status,
    statusDisplay = statusDisplay,
    submissionDate = 0L, // Parse from ISO string if needed
    processedDate = null,
    notes = notes,
    cachedAt = System.currentTimeMillis()
)
