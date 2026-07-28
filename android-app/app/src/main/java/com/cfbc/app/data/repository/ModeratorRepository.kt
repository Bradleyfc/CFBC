package com.cfbc.app.data.repository

import com.cfbc.app.data.model.Result
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.infrastructure.network.dto.CommentReportResponse
import com.cfbc.app.infrastructure.network.dto.CommunityMetricsResponse
import com.cfbc.app.infrastructure.network.dto.SanctionResponse
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for blog moderator operations.
 *
 * Moderator data is not cached locally since it's administrative and
 * should always show the latest state from the server.
 *
 * Requirements: 8.1-8.12, 10.12, 10.21, 10.22
 */
@Singleton
class ModeratorRepository @Inject constructor(
    private val networkDataSource: NetworkDataSource
) {

    /**
     * Get pending comment reports.
     */
    suspend fun getReports(page: Int? = null): Result<List<CommentReportResponse>> {
        return when (val result = networkDataSource.getModeratorReports(page)) {
            is Result.Success -> Result.Success(result.data.results)
            else -> result
        }
    }

    /**
     * Approve a report — hides the associated comment.
     */
    suspend fun approveReport(reportId: Int): Result<CommentReportResponse> {
        return networkDataSource.approveReport(reportId)
    }

    /**
     * Reject a report — keeps the comment visible.
     */
    suspend fun rejectReport(reportId: Int): Result<CommentReportResponse> {
        return networkDataSource.rejectReport(reportId)
    }

    /**
     * Get active user sanctions.
     */
    suspend fun getSanctions(page: Int? = null): Result<List<SanctionResponse>> {
        return when (val result = networkDataSource.getModeratorSanctions(page)) {
            is Result.Success -> Result.Success(result.data.results)
            else -> result
        }
    }

    /**
     * Get community metrics for the current month.
     */
    suspend fun getCommunityMetrics(): Result<CommunityMetricsResponse> {
        return networkDataSource.getCommunityMetrics()
    }
}
