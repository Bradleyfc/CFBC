package com.cfbc.app.data.local.dao

import androidx.room.*
import com.cfbc.app.data.local.entity.BlogPostEntity
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for blog posts with LRU cache eviction support.
 * 
 * Features:
 * - Query cached posts with pagination
 * - Insert/update posts with conflict resolution
 * - LRU eviction based on lastViewed timestamp
 * - Age-based eviction (30 days max)
 * - Count-based eviction (50 posts max)
 * 
 * Validates Requirements: 12.1, 12.2, 12.6, 12.7
 */
@Dao
interface BlogDao {
    
    /**
     * Get all cached blog posts ordered by publication date (newest first).
     * Returns a Flow for reactive updates.
     * 
     * @return Flow emitting list of cached blog posts
     */
    @Query("SELECT * FROM blog_posts ORDER BY fechaPublicacion DESC")
    fun getAllPosts(): Flow<List<BlogPostEntity>>
    
    /**
     * Get cached blog posts with pagination.
     * 
     * @param limit Maximum number of posts to return (default 50)
     * @return Flow emitting list of cached blog posts
     */
    @Query("SELECT * FROM blog_posts ORDER BY fechaPublicacion DESC LIMIT :limit")
    fun getCachedPosts(limit: Int = 50): Flow<List<BlogPostEntity>>
    
    /**
     * Get a single blog post by slug.
     * 
     * @param slug Post slug
     * @return BlogPostEntity if found, null otherwise
     */
    @Query("SELECT * FROM blog_posts WHERE slug = :slug")
    suspend fun getPostBySlug(slug: String): BlogPostEntity?
    
    /**
     * Get a single blog post by ID.
     * 
     * @param id Post ID
     * @return BlogPostEntity if found, null otherwise
     */
    @Query("SELECT * FROM blog_posts WHERE id = :id")
    suspend fun getPostById(id: Int): BlogPostEntity?
    
    /**
     * Insert or update blog posts.
     * Uses REPLACE strategy to overwrite existing posts.
     * 
     * @param posts List of posts to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPosts(posts: List<BlogPostEntity>)
    
    /**
     * Insert or update a single blog post.
     * 
     * @param post Post to insert/update
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPost(post: BlogPostEntity)
    
    /**
     * Update the lastViewed timestamp for a post (for LRU eviction).
     * Called when user views a post to mark it as recently accessed.
     * 
     * @param postId Post ID
     * @param lastViewed New lastViewed timestamp (Unix milliseconds)
     */
    @Query("UPDATE blog_posts SET lastViewed = :lastViewed WHERE id = :postId")
    suspend fun updateLastViewed(postId: Int, lastViewed: Long)
    
    /**
     * Get the count of cached posts.
     * 
     * @return Number of posts in cache
     */
    @Query("SELECT COUNT(*) FROM blog_posts")
    suspend fun getPostCount(): Int
    
    /**
     * Delete posts that exceed the count limit using LRU eviction.
     * Keeps the most recently viewed posts up to the specified limit.
     * 
     * Example: If limit is 50 and there are 60 posts, deletes the 10
     * least recently viewed posts.
     * 
     * @param limit Maximum number of posts to keep (default 50)
     */
    @Query("""
        DELETE FROM blog_posts 
        WHERE id NOT IN (
            SELECT id FROM blog_posts 
            ORDER BY lastViewed DESC 
            LIMIT :limit
        )
    """)
    suspend fun evictOldPostsByCount(limit: Int = 50)
    
    /**
     * Delete posts older than the specified age.
     * Default is 30 days (2592000000 milliseconds).
     * 
     * @param maxAgeMillis Maximum age in milliseconds (default 30 days)
     * @param currentTime Current time in Unix milliseconds
     */
    @Query("""
        DELETE FROM blog_posts 
        WHERE cachedAt < :currentTime - :maxAgeMillis
    """)
    suspend fun evictOldPostsByAge(
        maxAgeMillis: Long = 2592000000, // 30 days
        currentTime: Long = System.currentTimeMillis()
    )
    
    /**
     * Delete all blog posts from cache.
     * Used during logout or cache clear operations.
     */
    @Query("DELETE FROM blog_posts")
    suspend fun deleteAll()
    
    /**
     * Delete a specific blog post by ID.
     * 
     * @param postId Post ID to delete
     */
    @Query("DELETE FROM blog_posts WHERE id = :postId")
    suspend fun deletePostById(postId: Int)
    
    /**
     * Search posts by title or content.
     * Uses SQLite FTS (Full-Text Search) LIKE operator.
     * 
     * @param query Search query
     * @return Flow emitting list of matching posts
     */
    @Query("""
        SELECT * FROM blog_posts 
        WHERE titulo LIKE '%' || :query || '%' 
           OR contenido LIKE '%' || :query || '%'
        ORDER BY fechaPublicacion DESC
    """)
    fun searchPosts(query: String): Flow<List<BlogPostEntity>>
    
    /**
     * Get posts by category ID.
     * 
     * @param categoryId Category ID
     * @return Flow emitting list of posts in the category
     */
    @Query("SELECT * FROM blog_posts WHERE categoriaId = :categoryId ORDER BY fechaPublicacion DESC")
    fun getPostsByCategory(categoryId: Int): Flow<List<BlogPostEntity>>
}
