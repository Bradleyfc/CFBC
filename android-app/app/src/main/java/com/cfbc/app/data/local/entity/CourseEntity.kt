package com.cfbc.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room entity for caching course information.
 * Includes denormalized statusAvailable field for efficient filtering.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Entity(tableName = "courses")
data class CourseEntity(
    @PrimaryKey val id: Int,
    val name: String,
    val description: String?,
    val area: String,
    val tipo: String,
    val teacherName: String,
    val classQuantity: Int,
    val status: String,
    val statusDisplay: String,
    val cursoAcademicoNombre: String?,
    val startDate: Long?, // Unix timestamp in milliseconds
    val statusAvailable: Boolean, // Denormalized for filtering available courses
    val cachedAt: Long // Unix timestamp when cached
)
