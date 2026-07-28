package com.cfbc.app.data.local.dao

import androidx.room.*
import com.cfbc.app.data.local.entity.EnrollmentEntity
import com.cfbc.app.data.local.entity.StudentProfileEntity
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for student profile and enrollments.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Dao
interface StudentDao {
    
    // ========== Student Profile ==========
    
    /**
     * Get the cached student profile.
     * Only one profile is stored at a time (for the logged-in user).
     * 
     * @param username Student username
     * @return Flow emitting student profile or null
     */
    @Query("SELECT * FROM student_profile WHERE username = :username LIMIT 1")
    fun getProfile(username: String): Flow<StudentProfileEntity?>
    
    /**
     * Get any cached student profile (for single-user app).
     * 
     * @return StudentProfileEntity if exists, null otherwise
     */
    @Query("SELECT * FROM student_profile LIMIT 1")
    suspend fun getAnyProfile(): StudentProfileEntity?
    
    /**
     * Insert or update student profile.
     * Only one profile is stored at a time.
     * 
     * @param profile Student profile to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertProfile(profile: StudentProfileEntity)
    
    /**
     * Delete student profile.
     * Called during logout.
     */
    @Query("DELETE FROM student_profile")
    suspend fun deleteProfile()
    
    // ========== Enrollments ==========
    
    /**
     * Get all cached enrollments ordered by matricula date (newest first).
     * 
     * @return Flow emitting list of enrollments
     */
    @Query("SELECT * FROM enrollments ORDER BY fechaMatricula DESC")
    fun getAllEnrollments(): Flow<List<EnrollmentEntity>>
    
    /**
     * Get active enrollments only.
     * 
     * @return Flow emitting list of active enrollments
     */
    @Query("SELECT * FROM enrollments WHERE activo = 1 ORDER BY fechaMatricula DESC")
    fun getActiveEnrollments(): Flow<List<EnrollmentEntity>>
    
    /**
     * Get an enrollment by ID.
     * 
     * @param id Enrollment ID
     * @return EnrollmentEntity if found, null otherwise
     */
    @Query("SELECT * FROM enrollments WHERE id = :id")
    suspend fun getEnrollmentById(id: Int): EnrollmentEntity?
    
    /**
     * Get enrollments for a specific course.
     * 
     * @param courseId Course ID
     * @return Flow emitting list of enrollments for the course
     */
    @Query("SELECT * FROM enrollments WHERE courseId = :courseId")
    fun getEnrollmentsByCourse(courseId: Int): Flow<List<EnrollmentEntity>>
    
    /**
     * Insert or update enrollments.
     * 
     * @param enrollments List of enrollments to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEnrollments(enrollments: List<EnrollmentEntity>)
    
    /**
     * Insert or update a single enrollment.
     * 
     * @param enrollment Enrollment to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEnrollment(enrollment: EnrollmentEntity)
    
    /**
     * Delete all enrollments from cache.
     * Called during logout.
     */
    @Query("DELETE FROM enrollments")
    suspend fun deleteAllEnrollments()
    
    /**
     * Delete a specific enrollment by ID.
     * 
     * @param enrollmentId Enrollment ID to delete
     */
    @Query("DELETE FROM enrollments WHERE id = :enrollmentId")
    suspend fun deleteEnrollmentById(enrollmentId: Int)
}
