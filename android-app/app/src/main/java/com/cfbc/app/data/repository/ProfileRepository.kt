package com.cfbc.app.data.repository

import com.cfbc.app.data.local.LocalDataSource
import com.cfbc.app.data.local.entity.EnrollmentEntity
import com.cfbc.app.data.local.entity.StudentProfileEntity
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.infrastructure.network.dto.EnrollmentResponse
import com.cfbc.app.infrastructure.network.dto.StudentProfileResponse
import com.cfbc.app.infrastructure.network.dto.StudentProfileUpdateRequest
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for student profile and enrollment operations.
 *
 * Offline-first strategy:
 * 1. Try fetching fresh data from the network
 * 2. On success: cache locally and return fresh data
 * 3. On failure: return cached data if available, or forward error
 *
 * Requirements: 4.1-4.4, 10.6, 10.7
 */
@Singleton
class ProfileRepository @Inject constructor(
    private val networkDataSource: NetworkDataSource,
    private val localDataSource: LocalDataSource,
    private val authRepository: AuthRepository
) {

    // =========================================================================
    // Observable cached data (reactive UI updates)
    // =========================================================================

    /** Observe the cached student profile (reactive). */
    fun observeProfile(): Flow<StudentProfileEntity?> =
        localDataSource.observeProfile(authRepository.currentUsername ?: "")

    /** Observe all cached enrollments (reactive). */
    fun observeEnrollments(): Flow<List<EnrollmentEntity>> =
        localDataSource.observeEnrollments()

    /** Observe active cached enrollments (reactive). */
    fun observeActiveEnrollments(): Flow<List<EnrollmentEntity>> =
        localDataSource.observeActiveEnrollments()

    // =========================================================================
    // Profile (network-first with cache fallback)
    // =========================================================================

    /**
     * Fetch the authenticated user's profile.
     *
     * Offline-first:
     * 1. Fetch from network
     * 2. Cache on success
     * 3. Fall back to cache on error
     */
    suspend fun getProfile(): Result<StudentProfileResponse> {
        return when (val result = networkDataSource.getProfile()) {
            is Result.Success -> {
                // Cache the profile
                localDataSource.cacheProfile(result.data.toEntity())
                result
            }
            is Result.Error -> {
                // Network failed — try cache
                val cached = localDataSource.getAnyCachedProfile()
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
     * Update the authenticated user's profile on the server and cache.
     */
    suspend fun updateProfile(
        nacionalidad: String? = null,
        carnet: String? = null,
        sexo: String? = null,
        address: String? = null,
        location: String? = null,
        provincia: String? = null,
        telephone: String? = null,
        movil: String? = null
    ): Result<StudentProfileResponse> {
        val updates = StudentProfileUpdateRequest(
            nacionalidad = nacionalidad,
            carnet = carnet,
            sexo = sexo,
            address = address,
            location = location,
            provincia = provincia,
            telephone = telephone,
            movil = movil
        )
        return when (val result = networkDataSource.updateProfile(updates)) {
            is Result.Success -> {
                // Update cache with fresh data
                localDataSource.cacheProfile(result.data.toEntity())
                result
            }
            else -> result
        }
    }

    // =========================================================================
    // Enrollments (network-first with cache fallback)
    // =========================================================================

    /**
     * Fetch the authenticated user's enrollments.
     */
    suspend fun getEnrollments(
        activo: String? = null,
        page: Int? = null
    ): Result<List<EnrollmentResponse>> {
        return when (val result = networkDataSource.getEnrollments(activo, page)) {
            is Result.Success -> {
                // Cache enrollments
                if (page == null || page <= 1) {
                    val entities = result.data.results.map { it.toEntity() }
                    localDataSource.cacheEnrollments(entities)
                }
                Result.Success(result.data.results)
            }
            // On error, just forward it. The UI observes cached data via Flow.
            else -> result
        }
    }
}

// =============================================================================
// Extension functions for Entity ↔ DTO mapping
// =============================================================================

/** Maps a [StudentProfileResponse] to a [StudentProfileEntity]. */
fun StudentProfileResponse.toEntity(): StudentProfileEntity = StudentProfileEntity(
    username = username,
    email = email,
    firstName = firstName,
    lastName = lastName,
    nacionalidad = nacionalidad,
    carnet = carnet,
    sexo = sexo,
    imageUrl = imageUrl,
    address = address,
    location = location,
    provincia = provincia,
    telephone = telephone,
    movil = movil,
    cachedAt = System.currentTimeMillis()
)

/** Maps a [StudentProfileEntity] to a [StudentProfileResponse]. */
fun StudentProfileEntity.toDto(): StudentProfileResponse = StudentProfileResponse(
    username = username,
    email = email,
    firstName = firstName,
    lastName = lastName,
    nacionalidad = nacionalidad,
    carnet = carnet,
    sexo = sexo,
    imageUrl = imageUrl,
    address = address,
    location = location,
    provincia = provincia,
    telephone = telephone,
    movil = movil
)

/** Maps an [EnrollmentResponse] to an [EnrollmentEntity]. */
fun EnrollmentResponse.toEntity(): EnrollmentEntity = EnrollmentEntity(
    id = id,
    courseId = courseId,
    courseName = courseName,
    courseArea = courseArea,
    courseTipo = courseTipo,
    courseTeacherName = courseTeacherName,
    estado = estado,
    estadoDisplay = estadoDisplay,
    cursoAcademicoNombre = cursoAcademicoNombre,
    fechaMatricula = fechaMatricula, // ISO date string, stored as-is
    activo = activo,
    cachedAt = System.currentTimeMillis()
)
