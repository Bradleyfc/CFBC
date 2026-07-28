package com.cfbc.android

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * Main Application class for CFBC Android app.
 * Annotated with @HiltAndroidApp to trigger Hilt's code generation.
 */
@HiltAndroidApp
class CfbcApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // Initialize app-wide configurations
        if (BuildConfig.DEBUG) {
            // Enable debug logging
            enableDebugLogging()
        }
    }
    
    private fun enableDebugLogging() {
        // Debug logging is configured through OkHttp interceptor in NetworkModule
        android.util.Log.d("CfbcApplication", "Debug mode enabled")
    }
}
