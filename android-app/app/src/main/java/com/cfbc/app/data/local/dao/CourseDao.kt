package com.cfbc.app.data.local.dao

import androidx.room.*
import com.cfbc.app.data.local.entity.CourseEntity
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for courses.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Dao
interface CourseDao {
    
    /**
     * Get all cached courses ordered by start date (newest first).
     * 
     * @return Flow emitting list of courses
     */
    @Query("SELECT * FROM courses ORDER BY startDate DESC")
    fun getAllCourses(): Flow<List<CourseEntity>>
    
    /**
     * Get available courses only (statusAvailable = true).
     * 
     * @param limit Maximum number of courses to return (default 50)
     * @return Flow emitting list of available courses
     */
    @Query("SELECT * FROM courses WHERE statusAvailable = 1 ORDER BY startDate DESC LIMIT :limit")
    fun getAvailableCourses(limit: Int = 50): Flow<List<CourseEntity>>
    
    /**
     * Get a course by ID.
     * 
     * @param courseId Course ID
     * @return CourseEntity if found, null otherwise
     */
    @Query("SELECT * FROM courses WHERE id = :courseId")
    suspend fun getCourseById(courseId: Int): CourseEntity?
    
    /**
     * Get courses filtered by area.
     * 
     * @param area Course area filter
     * @return Flow emitting list of courses in the area
     */
    @Query("SELECT * FROM courses WHERE area = :area ORDER BY startDate DESC")
    fun getCoursesByArea(area: String): Flow<List<CourseEntity>>
    
    /**
     * Get courses filtered by tipo.
     * 
     * @param tipo Course tipo filter
     * @return Flow emitting list of courses of that tipo
     */
    @Query("SELECT * FROM courses WHERE tipo = :tipo ORDER BY startDate DESC")
    fun getCoursesByTipo(tipo: String): Flow<List<CourseEntity>>
    
    /**
     * Get courses filtered by both area and tipo.
     * 
     * @param area Course area filter
     * @param tipo Course tipo filter
     * @return Flow emitting list of matching courses
     */
    @Query("SELECT * FROM courses WHERE area = :area AND tipo = :tipo ORDER BY startDate DESC")
    fun getCoursesByAreaAndTipo(area: String, tipo: String): Flow<List<CourseEntity>>
    
    /**
     * Insert or update courses.
     * 
     * @param courses List of courses to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCourses(courses: List<CourseEntity>)
    
    /**
     * Insert or update a single course.
     * 
     * @param course Course to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCourse(course: CourseEntity)
    
    /**
     * Delete all courses from cache.
     */
    @Query("DELETE FROM courses")
    suspend fun deleteAll()
    
    /**
     * Delete a specific course by ID.
     * 
     * @param courseId Course ID to delete
     */
    @Query("DELETE FROM courses WHERE id = :courseId")
    suspend fun deleteCourseById(courseId: Int)
}
