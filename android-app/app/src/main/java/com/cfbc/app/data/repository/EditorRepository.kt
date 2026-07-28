package com.cfbc.app.data.repository

import com.cfbc.app.data.model.Result
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.infrastructure.network.dto.BlogPostDetailResponse
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for blog editor operations.
 *
 * Handles:
 * - Reviewing posts pending publication
 * - Publishing or rejecting posts with editor notes
 * - Updating editor notes on posts
 *
 * Editor data is not cached locally since it's an administrative workflow
 * that requires real-time data from the server.
 *
 * Requirements: 9.1-9.12, 10.13, 10.19, 10.20
 */
@Singleton
class EditorRepository @Inject constructor(
    private val networkDataSource: NetworkDataSource
) {

    /**
     * Get all posts (editor view — includes all statuses).
     */
    suspend fun getPosts(
        search: String? = null,
        page: Int? = null
    ): Result<List<BlogPostDetailResponse>> {
        return when (val result = networkDataSource.getEditorPosts(search, page)) {
            is Result.Success -> Result.Success(result.data.results)
            else -> result
        }
    }

    /**
     * Get posts pending editor review (estado = pendiente_revision).
     */
    suspend fun getPendingReview(page: Int? = null): Result<List<BlogPostDetailResponse>> {
        return when (val result = networkDataSource.getPendingReviewPosts(page)) {
            is Result.Success -> Result.Success(result.data.results)
            else -> result
        }
    }

    /**
     * Get recently published posts (last 7 days).
     */
    suspend fun getRecentlyPublished(page: Int? = null): Result<List<BlogPostDetailResponse>> {
        return when (val result = networkDataSource.getRecentlyPublishedPosts(page)) {
            is Result.Success -> Result.Success(result.data.results)
            else -> result
        }
    }

    /**
     * Publish a post — changes estado to 'publicado'.
     */
    suspend fun publishPost(postId: Int): Result<BlogPostDetailResponse> {
        return networkDataSource.publishPost(postId)
    }

    /**
     * Reject a post — sends it back to the author with editor notes.
     */
    suspend fun rejectPost(postId: Int, notasEditor: String): Result<BlogPostDetailResponse> {
        return networkDataSource.rejectPost(postId, notasEditor)
    }

    /**
     * Update editor notes on a post without changing its status.
     */
    suspend fun updateNotes(postId: Int, notasEditor: String): Result<BlogPostDetailResponse> {
        return networkDataSource.updateEditorNotes(postId, notasEditor)
    }
}
