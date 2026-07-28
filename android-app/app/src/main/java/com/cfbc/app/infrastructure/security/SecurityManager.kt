package com.cfbc.app.infrastructure.security

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Security Manager - Handles secure storage of authentication tokens and sensitive data.
 * 
 * Uses Android's EncryptedSharedPreferences with AES256 encryption to protect
 * authentication tokens and user credentials stored on the device.
 * 
 * Features:
 * - Token storage using Android Keystore
 * - AES256_SIV key encryption
 * - AES256_GCM value encryption
 * - Automatic key generation and management
 * 
 * Requirements: 15.1, 15.2, 15.8
 */
@Singleton
class SecurityManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    
    companion object {
        // Encrypted SharedPreferences file name
        private const val ENCRYPTED_PREFS_FILE = "cfbc_secure_prefs"
        
        // Storage keys
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_USER_GROUPS = "user_groups"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_USERNAME = "username"
        private const val KEY_LAST_ACTIVE_TIME = "last_active_time"

        /** Session timeout in milliseconds (5 minutes). */
        const val SESSION_TIMEOUT_MS = 5 * 60 * 1000L
    }
    
    /**
     * Lazy initialization of MasterKey for encryption.
     * Uses AES256_GCM scheme for secure key generation.
     */
    private val masterKey: MasterKey by lazy {
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
    }
    
    /**
     * Lazy initialization of EncryptedSharedPreferences.
     * Provides secure storage with AES256 encryption for both keys and values.
     */
    private val encryptedPrefs: SharedPreferences by lazy {
        EncryptedSharedPreferences.create(
            context,
            ENCRYPTED_PREFS_FILE,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
    
    /**
     * Saves authentication token to secure storage.
     * 
     * The token is encrypted using AES256_GCM before storage.
     * 
     * @param token Authentication token from login response
     */
    fun saveAuthToken(token: String) {
        encryptedPrefs.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }
    
    /**
     * Retrieves authentication token from secure storage.
     * 
     * @return Authentication token if exists, null otherwise
     */
    fun getAuthToken(): String? {
        return encryptedPrefs.getString(KEY_AUTH_TOKEN, null)
    }
    
    /**
     * Clears authentication token from secure storage.
     * Called during logout to remove user credentials.
     */
    fun clearAuthToken() {
        encryptedPrefs.edit().remove(KEY_AUTH_TOKEN).apply()
    }
    
    /**
     * Saves user groups (roles) to secure storage.
     * 
     * Groups are stored as a comma-separated string.
     * Example: "Estudiantes,Blog Autor"
     * 
     * @param groups List of user group names
     */
    fun saveUserGroups(groups: List<String>) {
        val groupsString = groups.joinToString(",")
        encryptedPrefs.edit().putString(KEY_USER_GROUPS, groupsString).apply()
    }
    
    /**
     * Retrieves user groups from secure storage.
     * 
     * @return List of user group names, empty list if none stored
     */
    fun getUserGroups(): List<String> {
        val groupsString = encryptedPrefs.getString(KEY_USER_GROUPS, null)
        return groupsString?.split(",")?.filter { it.isNotEmpty() } ?: emptyList()
    }
    
    /**
     * Saves user ID to secure storage.
     * 
     * @param userId User ID from authentication response
     */
    fun saveUserId(userId: Int) {
        encryptedPrefs.edit().putInt(KEY_USER_ID, userId).apply()
    }
    
    /**
     * Retrieves user ID from secure storage.
     * 
     * @return User ID if exists, null otherwise
     */
    fun getUserId(): Int? {
        val userId = encryptedPrefs.getInt(KEY_USER_ID, -1)
        return if (userId != -1) userId else null
    }
    
    /**
     * Saves username to secure storage.
     * 
     * @param username Username from authentication response
     */
    fun saveUsername(username: String) {
        encryptedPrefs.edit().putString(KEY_USERNAME, username).apply()
    }
    
    /**
     * Retrieves username from secure storage.
     * 
     * @return Username if exists, null otherwise
     */
    fun getUsername(): String? {
        return encryptedPrefs.getString(KEY_USERNAME, null)
    }
    
    /**
     * Checks if user is currently authenticated.
     * 
     * @return true if authentication token exists, false otherwise
     */
    fun isAuthenticated(): Boolean {
        return getAuthToken() != null
    }
    
    /**
     * Clears all stored authentication data.
     * Called during logout to remove all user credentials and session data.
     */
    fun clearAll() {
        encryptedPrefs.edit().clear().apply()
    }
    
    /**
     * Checks if user has a specific group membership.
     * 
     * @param groupName Group name to check (e.g., "Estudiantes", "Blog Autor")
     * @return true if user is member of the group, false otherwise
     */
    fun hasGroup(groupName: String): Boolean {
        return getUserGroups().contains(groupName)
    }
    
    /**
     * Checks if user is a student.
     * 
     * @return true if user has "Estudiantes" group membership
     */
    fun isStudent(): Boolean {
        return hasGroup("Estudiantes")
    }
    
    /**
     * Checks if user is a blog author.
     * 
     * @return true if user has "Blog Autor" group membership
     */
    fun isBlogAuthor(): Boolean {
        return hasGroup("Blog Autor")
    }
    
    /**
     * Checks if user is a blog moderator.
     * 
     * @return true if user has "Blog Moderador" group membership
     */
    fun isBlogModerator(): Boolean {
        return hasGroup("Blog Moderador")
    }
    
    /**
     * Checks if user is an editor.
     * 
     * @return true if user has "Editor" group membership
     */
    fun isEditor(): Boolean {
        return hasGroup("Editor")
    }

    /**
     * Records current time as last user activity.
     * Called whenever the user performs an action.
     */
    fun updateLastActiveTime() {
        encryptedPrefs.edit().putLong(KEY_LAST_ACTIVE_TIME, System.currentTimeMillis()).apply()
    }

    /**
     * Checks if the user's session has expired due to inactivity.
     *
     * @return true if session has timed out (no activity for SESSION_TIMEOUT_MS)
     */
    fun isSessionExpired(): Boolean {
        val lastActive = encryptedPrefs.getLong(KEY_LAST_ACTIVE_TIME, 0L)
        if (lastActive == 0L) return false // First launch, no timeout yet
        return (System.currentTimeMillis() - lastActive) > SESSION_TIMEOUT_MS
    }

    /**
     * Clears session timeout data while preserving auth token.
     * This allows the session to be refreshed without requiring re-login.
     */
    fun clearSessionTimeout() {
        encryptedPrefs.edit().remove(KEY_LAST_ACTIVE_TIME).apply()
    }
}
