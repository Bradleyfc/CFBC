package com.cfbc.app.data.local

import android.content.Context
import com.cfbc.app.data.local.dao.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt module for providing Room database and DAOs.
 * 
 * Provides singleton instances of:
 * - CfbcDatabase
 * - All DAOs (BlogDao, CategoryDao, CourseDao, etc.)
 * 
 * Validates Requirements: 12.1, 12.2
 */
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    /**
     * Provides singleton CfbcDatabase instance.
     * 
     * @param context Application context
     * @return CfbcDatabase instance
     */
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): CfbcDatabase {
        return CfbcDatabase.getInstance(context)
    }
    
    /**
     * Provides BlogDao from database.
     * 
     * @param database CfbcDatabase instance
     * @return BlogDao
     */
    @Provides
    @Singleton
    fun provideBlogDao(database: CfbcDatabase): BlogDao {
        return database.blogDao()
    }
    
    /**
     * Provides CategoryDao from database.
     * 
     * @param database CfbcDatabase instance
     * @return CategoryDao
     */
    @Provides
    @Singleton
    fun provideCategoryDao(database: CfbcDatabase): CategoryDao {
        return database.categoryDao()
    }
    
    /**
     * Provides CourseDao from database.
     * 
     * @param database CfbcDatabase instance
     * @return CourseDao
     */
    @Provides
    @Singleton
    fun provideCourseDao(database: CfbcDatabase): CourseDao {
        return database.courseDao()
    }
    
    /**
     * Provides CourseApplicationDao from database.
     * 
     * @param database CfbcDatabase instance
     * @return CourseApplicationDao
     */
    @Provides
    @Singleton
    fun provideCourseApplicationDao(database: CfbcDatabase): CourseApplicationDao {
        return database.courseApplicationDao()
    }
    
    /**
     * Provides StudentDao from database.
     * 
     * @param database CfbcDatabase instance
     * @return StudentDao
     */
    @Provides
    @Singleton
    fun provideStudentDao(database: CfbcDatabase): StudentDao {
        return database.studentDao()
    }
}
