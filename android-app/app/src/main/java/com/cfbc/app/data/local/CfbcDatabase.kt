package com.cfbc.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.cfbc.app.data.local.dao.*
import com.cfbc.app.data.local.entity.*

/**
 * Room Database for CFBC Android application.
 * 
 * Provides local caching for:
 * - Blog posts with LRU eviction (max 50 posts or 30 days)
 * - Categories
 * - Courses
 * - Course applications
 * - Student profile
 * - Enrollments
 * 
 * Features:
 * - Automatic migrations (fallbackToDestructiveMigration for development)
 * - Singleton pattern for app-wide database access
 * - Support for offline-first architecture
 * 
 * Validates Requirements: 12.1, 12.2, 12.6, 12.7
 */
@Database(
    entities = [
        BlogPostEntity::class,
        CategoryEntity::class,
        CourseEntity::class,
        CourseApplicationEntity::class,
        StudentProfileEntity::class,
        EnrollmentEntity::class
    ],
    version = 1,
    exportSchema = true
)
abstract class CfbcDatabase : RoomDatabase() {
    
    /**
     * Provides access to blog posts DAO.
     */
    abstract fun blogDao(): BlogDao
    
    /**
     * Provides access to categories DAO.
     */
    abstract fun categoryDao(): CategoryDao
    
    /**
     * Provides access to courses DAO.
     */
    abstract fun courseDao(): CourseDao
    
    /**
     * Provides access to course applications DAO.
     */
    abstract fun courseApplicationDao(): CourseApplicationDao
    
    /**
     * Provides access to student data DAO.
     */
    abstract fun studentDao(): StudentDao
    
    companion object {
        private const val DATABASE_NAME = "cfbc_database.db"
        
        @Volatile
        private var INSTANCE: CfbcDatabase? = null
        
        /**
         * Get singleton database instance.
         * Uses double-checked locking for thread safety.
         * 
         * @param context Application context
         * @return CfbcDatabase singleton instance
         */
        fun getInstance(context: Context): CfbcDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: buildDatabase(context).also { INSTANCE = it }
            }
        }
        
        /**
         * Build the database instance.
         * 
         * In production: Use proper migration strategy
         * In development: Use fallbackToDestructiveMigration for simplicity
         * 
         * @param context Application context
         * @return CfbcDatabase instance
         */
        private fun buildDatabase(context: Context): CfbcDatabase {
            return Room.databaseBuilder(
                context.applicationContext,
                CfbcDatabase::class.java,
                DATABASE_NAME
            )
                // For development: destroy and rebuild database on schema changes
                // TODO: Replace with proper migrations for production
                .fallbackToDestructiveMigration()
                .build()
        }
        
        /**
         * Clear database instance (for testing).
         */
        @androidx.annotation.VisibleForTesting
        fun clearInstance() {
            INSTANCE = null
        }
    }
}
