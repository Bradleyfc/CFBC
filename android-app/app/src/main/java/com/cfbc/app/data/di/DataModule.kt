package com.cfbc.app.data.di

import com.cfbc.app.data.local.LocalDataSource
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.data.repository.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * Hilt module providing data layer dependencies.
 *
 * Provides singleton instances of:
 * - NetworkDataSource (wraps API calls with error handling)
 * - LocalDataSource (wraps Room DAOs with caching logic)
 * - All repositories (offline-first data access)
 *
 * Requirements: 12.1, 12.2, 15.1, 15.2
 */
@Module
@InstallIn(SingletonComponent::class)
object DataModule {

    // =========================================================================
    // Data Sources
    // =========================================================================

    @Provides
    @Singleton
    fun provideNetworkDataSource(
        networkDataSource: NetworkDataSource
    ): NetworkDataSource = networkDataSource

    @Provides
    @Singleton
    fun provideLocalDataSource(
        localDataSource: LocalDataSource
    ): LocalDataSource = localDataSource

    // =========================================================================
    // Repositories
    // =========================================================================

    @Provides
    @Singleton
    fun provideAuthRepository(
        authRepository: AuthRepository
    ): AuthRepository = authRepository

    @Provides
    @Singleton
    fun provideCourseRepository(
        courseRepository: CourseRepository
    ): CourseRepository = courseRepository

    @Provides
    @Singleton
    fun provideProfileRepository(
        profileRepository: ProfileRepository
    ): ProfileRepository = profileRepository

    @Provides
    @Singleton
    fun provideBlogRepository(
        blogRepository: BlogRepository
    ): BlogRepository = blogRepository

    @Provides
    @Singleton
    fun provideModeratorRepository(
        moderatorRepository: ModeratorRepository
    ): ModeratorRepository = moderatorRepository

    @Provides
    @Singleton
    fun provideEditorRepository(
        editorRepository: EditorRepository
    ): EditorRepository = editorRepository
}
