package com.cfbc.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room entity for caching student course applications.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Entity(tableName = "course_applications")
data class CourseApplicationEntity(
    @PrimaryKey val id: Int,
    val courseId: Int,
    val courseName: String,
    val studentUsername: String,
    val status: String, // "pending", "approved", "rejected"
    val statusDisplay: String,
    val submissionDate: Long, // Unix timestamp in milliseconds
    val processedDate: Long?, // Unix timestamp in milliseconds, nullable
    val notes: String?,
    val cachedAt: Long // Unix timestamp when cached
)
