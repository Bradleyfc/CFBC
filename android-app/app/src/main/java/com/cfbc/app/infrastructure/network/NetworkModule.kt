package com.cfbc.app.infrastructure.network

import android.content.Context
import com.cfbc.app.BuildConfig
import com.cfbc.app.infrastructure.security.SecurityManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.CertificatePinner
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

/**
 * Network Module - Provides networking infrastructure for the CFBC Android application.
 * 
 * Features:
 * - Environment-based URL switching (debug/release)
 * - OkHttp client with authentication interceptor
 * - Certificate pinning (production only)
 * - Logging interceptor (verbose in debug, disabled in release)
 * - Connection timeouts (30s connect, 30s read)
 * 
 * Requirements: 15.1, 15.2, 15.5, 15.8
 */
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    /**
     * Build configuration for environment switching.
     * - Debug: http://192.168.1.100:8000/ (local WiFi development)
     * - Release: https://cfbc.example.com/ (production internet hosting)
     */
    object Config {
        /**
         * Base URL for API requests - controlled by build variant.
         * Set in build.gradle.kts buildTypes.
         */
        val BASE_URL: String = BuildConfig.API_BASE_URL
        
        /**
         * Base URL for WebView content - controlled by build variant.
         * Set in build.gradle.kts buildTypes.
         */
        val WEB_BASE_URL: String = BuildConfig.WEB_BASE_URL
        
        /**
         * Certificate pinning enabled flag - controlled by build variant.
         * Only enabled in production builds for security.
         */
        val ENABLE_CERTIFICATE_PINNING: Boolean = BuildConfig.ENABLE_CERTIFICATE_PINNING
    }
    
    /**
     * Provides the configured OkHttpClient instance.
     * 
     * Features:
     * - AuthInterceptor for token injection
     * - HttpLoggingInterceptor (verbose in debug, disabled in release)
     * - Certificate pinning (production only)
     * - Connection timeouts: 30s connect, 30s read
     * 
     * @param context Application context
     * @param authInterceptor Authentication interceptor for token injection
     * @return Configured OkHttpClient instance
     */
    @Provides
    @Singleton
    fun provideOkHttpClient(
        @ApplicationContext context: Context,
        authInterceptor: AuthInterceptor
    ): OkHttpClient {
        return OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(provideLoggingInterceptor())
            .apply {
                // Only use certificate pinning in production
                if (Config.ENABLE_CERTIFICATE_PINNING) {
                    certificatePinner(provideCertificatePinner())
                }
            }
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    
    /**
     * Provides HTTP logging interceptor.
     * - Debug builds: BODY level (verbose logging)
     * - Release builds: NONE (no logging)
     * 
     * @return HttpLoggingInterceptor configured for current build type
     */
    @Provides
    @Singleton
    fun provideLoggingInterceptor(): HttpLoggingInterceptor {
        return HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }
    }
    
    /**
     * Provides certificate pinner for production builds.
     * 
     * Certificate pinning prevents man-in-the-middle attacks by validating
     * the server's SSL certificate against known public key hashes.
     * 
     * NOTE: Replace the placeholder hash with your actual server's certificate hash.
     * To get the certificate hash:
     * 1. Run: openssl s_client -connect cfbc.example.com:443 | openssl x509 -pubkey -noout | openssl pkey -pubin -outform der | openssl dgst -sha256 -binary | openssl enc -base64
     * 2. Add the output to the certificatePinner below
     * 
     * @return CertificatePinner configured for production domain
     */
    @Provides
    @Singleton
    fun provideCertificatePinner(): CertificatePinner {
        return CertificatePinner.Builder()
            // TODO: Replace with actual certificate hash for production domain
            // Format: sha256/[base64-encoded-public-key-hash]
            .add("cfbc.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
            // You can add backup pins for redundancy
            // .add("cfbc.example.com", "sha256/BACKUP_HASH_HERE")
            .build()
    }
    
    /**
     * Provides Retrofit instance configured with base URL and OkHttp client.
     * 
     * @param okHttpClient Configured OkHttpClient instance
     * @return Retrofit instance for API service creation
     */
    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl(Config.BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    /**
     * Provides the CFBC API service interface.
     * 
     * @param retrofit Configured Retrofit instance
     * @return CfbcApiService for making API calls
     */
    @Provides
    @Singleton
    fun provideCfbcApiService(retrofit: Retrofit): CfbcApiService {
        return retrofit.create(CfbcApiService::class.java)
    }
}
