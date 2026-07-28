package com.cfbc.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room entity for caching student course enrollments.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Entity(tableName = "enrollments")
data class EnrollmentEntity(
    @PrimaryKey val id: Int,
    val courseId: Int,
    val courseName: String,
    val courseArea: String,
    val courseTipo: String,
    val courseTeacherName: String,
    val estado: String, // "P" (Activo), "A" (Aprobado), "BA", "BL", "BI"
    val estadoDisplay: String, // Human-readable status
    val cursoAcademicoNombre: String?,
    val fechaMatricula: Long, // Unix timestamp in milliseconds
    val activo: Boolean,
    val cachedAt: Long // Unix timestamp when cached
)
