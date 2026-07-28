package com.cfbc.app.data.repository

import com.cfbc.app.data.local.LocalDataSource
import com.cfbc.app.data.model.Result
import com.cfbc.app.data.remote.NetworkDataSource
import com.cfbc.app.infrastructure.security.SecurityManager
import com.cfbc.app.infrastructure.network.dto.LoginResponse
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for authentication operations.
 *
 * Handles:
 * - Login: authenticate via API, store token securely, cache profile locally
 * - Logout: clear token, clear all local cache
 * - Session check: verify if user is authenticated
 *
 * Requirements: 5.1-5.5, 10.5, 15.1, 15.2
 */
@Singleton
class AuthRepository @Inject constructor(
    private val networkDataSource: NetworkDataSource,
    private val localDataSource: LocalDataSource,
    private val securityManager: SecurityManager
) {

    /** True if the user has a stored auth token. */
    val isAuthenticated: Boolean
        get() = securityManager.isAuthenticated()

    /** The stored username, or null. */
    val currentUsername: String?
        get() = securityManager.getUsername()

    /** The stored user groups (roles). */
    val currentGroups: List<String>
        get() = securityManager.getUserGroups()

    /**
     * Authenticate the user with the server.
     *
     * On success:
     * 1. Stores token, username, groups, and userId in EncryptedSharedPreferences
     * 2. Returns the [LoginResponse] with token and user info
     *
     * On failure: returns [Result.Error] with a descriptive message.
     */
    suspend fun login(username: String, password: String): Result<LoginResponse> {
        return when (val result = networkDataSource.login(username, password)) {
            is Result.Success -> {
                val response = result.data
                // Persist authentication data securely
                securityManager.saveAuthToken(response.token)
                securityManager.saveUsername(response.username)
                securityManager.saveUserGroups(response.groups)
                // Return success
                Result.Success(response)
            }
            is Result.Error -> result
            is Result.Loading -> result // Not expected from networkDataSource
        }
    }

    /**
     * Log out the current user.
     *
     * 1. Tries to invalidate the token on the server (ignores failure)
     * 2. Clears all locally stored auth data
     * 3. Clears all cached data from the local database
     */
    suspend fun logout() {
        // Attempt server-side logout (best effort — ignore failures)
        networkDataSource.logout()

        // Clear all local state
        securityManager.clearAll()
        localDataSource.clearAll()
    }

    /** Check if the user has a specific group membership. */
    fun hasGroup(groupName: String): Boolean = securityManager.hasGroup(groupName)

    /** Check if the user is a student. */
    fun isStudent(): Boolean = securityManager.isStudent()

    /** Check if the user is a blog author. */
    fun isBlogAuthor(): Boolean = securityManager.isBlogAuthor()

    /** Check if the user is a blog moderator. */
    fun isBlogModerator(): Boolean = securityManager.isBlogModerator()

    /** Check if the user is an editor. */
    fun isEditor(): Boolean = securityManager.isEditor()
}
