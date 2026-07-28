package com.cfbc.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room entity for caching student profile information.
 * Username is the primary key as it uniquely identifies users.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Entity(tableName = "student_profile")
data class StudentProfileEntity(
    @PrimaryKey val username: String,
    val email: String,
    val firstName: String,
    val lastName: String,
    val nacionalidad: String?,
    val carnet: String?,
    val sexo: String,
    val imageUrl: String?,
    val address: String?,
    val location: String?,
    val provincia: String?,
    val telephone: String?,
    val movil: String?,
    val cachedAt: Long // Unix timestamp when cached
)
