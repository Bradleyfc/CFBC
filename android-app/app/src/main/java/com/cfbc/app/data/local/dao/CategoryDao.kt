package com.cfbc.app.data.local.dao

import androidx.room.*
import com.cfbc.app.data.local.entity.CategoryEntity
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for blog categories.
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Dao
interface CategoryDao {
    
    /**
     * Get all cached categories ordered by name.
     * 
     * @return Flow emitting list of categories
     */
    @Query("SELECT * FROM categories ORDER BY nombre ASC")
    fun getAllCategories(): Flow<List<CategoryEntity>>
    
    /**
     * Get a category by ID.
     * 
     * @param id Category ID
     * @return CategoryEntity if found, null otherwise
     */
    @Query("SELECT * FROM categories WHERE id = :id")
    suspend fun getCategoryById(id: Int): CategoryEntity?
    
    /**
     * Get a category by slug.
     * 
     * @param slug Category slug
     * @return CategoryEntity if found, null otherwise
     */
    @Query("SELECT * FROM categories WHERE slug = :slug")
    suspend fun getCategoryBySlug(slug: String): CategoryEntity?
    
    /**
     * Insert or update categories.
     * 
     * @param categories List of categories to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategories(categories: List<CategoryEntity>)
    
    /**
     * Insert or update a single category.
     * 
     * @param category Category to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCategory(category: CategoryEntity)
    
    /**
     * Delete all categories from cache.
     */
    @Query("DELETE FROM categories")
    suspend fun deleteAll()
}
