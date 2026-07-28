package com.cfbc.app.data.local.dao

import androidx.room.*
import com.cfbc.app.data.local.entity.CourseApplicationEntity
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for course applications.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Dao
interface CourseApplicationDao {
    
    /**
     * Get all cached course applications ordered by submission date (newest first).
     * 
     * @return Flow emitting list of course applications
     */
    @Query("SELECT * FROM course_applications ORDER BY submissionDate DESC")
    fun getAllApplications(): Flow<List<CourseApplicationEntity>>
    
    /**
     * Get pending course applications only.
     * 
     * @return Flow emitting list of pending applications
     */
    @Query("SELECT * FROM course_applications WHERE status = 'pending' ORDER BY submissionDate DESC")
    fun getPendingApplications(): Flow<List<CourseApplicationEntity>>
    
    /**
     * Get an application by ID.
     * 
     * @param id Application ID
     * @return CourseApplicationEntity if found, null otherwise
     */
    @Query("SELECT * FROM course_applications WHERE id = :id")
    suspend fun getApplicationById(id: Int): CourseApplicationEntity?
    
    /**
     * Get applications for a specific course.
     * 
     * @param courseId Course ID
     * @return Flow emitting list of applications for the course
     */
    @Query("SELECT * FROM course_applications WHERE courseId = :courseId ORDER BY submissionDate DESC")
    fun getApplicationsByCourse(courseId: Int): Flow<List<CourseApplicationEntity>>
    
    /**
     * Insert or update course applications.
     * 
     * @param applications List of applications to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertApplications(applications: List<CourseApplicationEntity>)
    
    /**
     * Insert or update a single application.
     * 
     * @param application Application to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertApplication(application: CourseApplicationEntity)
    
    /**
     * Delete a specific application by ID.
     * Used when canceling an application.
     * 
     * @param applicationId Application ID to delete
     */
    @Query("DELETE FROM course_applications WHERE id = :applicationId")
    suspend fun deleteApplicationById(applicationId: Int)
    
    /**
     * Delete all applications from cache.
     */
    @Query("DELETE FROM course_applications")
    suspend fun deleteAll()
}
