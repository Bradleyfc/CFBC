package com.cfbc.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Room entity for caching blog posts locally.
 * Supports LRU eviction based on lastViewed timestamp.
 * 
 * Validates Requirements: 12.1, 12.2, 12.6, 12.7
 */
@Entity(tableName = "blog_posts")
data class BlogPostEntity(
    @PrimaryKey val id: Int,
    val titulo: String,
    val slug: String,
    val resumen: String,
    val contenido: String,
    val imagenPrincipalUrl: String?,
    val categoriaId: Int,
    val categoriaNombre: String,
    val autorUsername: String,
    val estado: String,
    val fechaPublicacion: Long, // Unix timestamp in milliseconds
    val metaDescripcion: String?,
    val destacada: Boolean,
    val notasEditor: String?,
    val cachedAt: Long, // Unix timestamp when cached
    val lastViewed: Long // Unix timestamp when last viewed (for LRU eviction)
)
