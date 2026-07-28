package com.cfbc.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room entity for caching blog categories.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Entity(tableName = "categories")
data class CategoryEntity(
    @PrimaryKey val id: Int,
    val nombre: String,
    val descripcion: String,
    val slug: String
)
