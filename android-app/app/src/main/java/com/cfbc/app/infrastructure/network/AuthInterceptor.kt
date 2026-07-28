package com.cfbc.app.infrastructure.network

import android.content.Context
import com.cfbc.app.infrastructure.security.SecurityManager
import dagger.hilt.android.qualifiers.ApplicationContext
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Authentication Interceptor - Automatically injects authentication tokens into API requests.
 * 
 * This interceptor retrieves the stored authentication token from secure storage
 * and adds it to outgoing requests as an Authorization header.
 * 
 * Header format: "Authorization: Token <auth_token>"
 * 
 * Requirements: 15.1, 15.2
 */
@Singleton
class AuthInterceptor @Inject constructor(
    @ApplicationContext private val context: Context,
    private val securityManager: SecurityManager
) : Interceptor {
    
    companion object {
        private const val HEADER_AUTHORIZATION = "Authorization"
        private const val TOKEN_PREFIX = "Token"
    }
    
    /**
     * Intercepts outgoing requests and adds authentication header if token exists.
     * 
     * @param chain Interceptor chain
     * @return Response from the server
     */
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        
        // Get authentication token from secure storage
        val token = securityManager.getAuthToken()
        
        // If token exists, add it to the request
        val request = if (token != null) {
            originalRequest.newBuilder()
                .addHeader(HEADER_AUTHORIZATION, "$TOKEN_PREFIX $token")
                .build()
        } else {
            originalRequest
        }
        
        return chain.proceed(request)
    }
}
