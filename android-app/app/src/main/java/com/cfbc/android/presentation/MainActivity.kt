package com.cfbc.android.presentation

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.NavController
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.cfbc.android.R
import com.cfbc.android.databinding.ActivityMainBinding
import com.cfbc.app.infrastructure.security.SecurityManager
import com.google.android.material.snackbar.Snackbar
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

/**
 * Main Activity — single-activity architecture with Navigation Component.
 *
 * Hosts all fragments via NavHostFragment and provides:
 * - Bottom navigation for main sections (Home, Courses, Blog, Profile)
 * - Global snackbar event handling
 * - Background session timeout (re-auth after 5 minutes inactivity)
 * - Hilt injection point for all fragments
 *
 * Requirements: 10.1, 15.7
 */
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    @Inject
    lateinit var securityManager: SecurityManager

    private lateinit var binding: ActivityMainBinding
    private lateinit var navController: NavController

    // =========================================================================
    // Lifecycle
    // =========================================================================

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupNavigation()
        setupBottomNavVisibility()
    }

    /**
     * Background timeout: check session expiry when app resumes.
     * If the user has been inactive for more than 5 minutes,
     * clear auth and redirect to login (Requirement 15.7).
     */
    override fun onResume() {
        super.onResume()
        if (securityManager.isAuthenticated() && securityManager.isSessionExpired()) {
            securityManager.clearAll()
            // Navigate to login if not already there
            val currentDest = navController.currentDestination
            if (currentDest?.id != R.id.loginFragment) {
                // Navigate directly to loginFragment with back stack cleared
                navController.navigate(R.id.loginFragment) {
                    popUpTo(0) { inclusive = true }
                }
            }
        }
        // Record current time as active
        securityManager.updateLastActiveTime()
    }

    /**
     * Update last active time when app goes to background.
     */
    override fun onPause() {
        super.onPause()
        securityManager.updateLastActiveTime()
    }

    // =========================================================================
    // Navigation Setup
    // =========================================================================

    private fun setupNavigation() {
        val navHostFragment = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        navController = navHostFragment.navController

        // Wire bottom navigation with NavController
        binding.bottomNavigation.setupWithNavController(navController)

        // Listen for destination changes to show/hide bottom nav
        navController.addOnDestinationChangedListener { _, destination, _ ->
            val showBottomNav = when (destination.id) {
                R.id.loginFragment -> false
                else -> true
            }
            binding.bottomNavigation.visibility = if (showBottomNav) View.VISIBLE else View.GONE
        }
    }

    private fun setupBottomNavVisibility() {
        // Initial state — check start destination
        val currentDestination = navController.currentDestination
        if (currentDestination?.id == R.id.loginFragment) {
            binding.bottomNavigation.visibility = View.GONE
        }
    }

    // =========================================================================
    // Snackbar Helper
    // =========================================================================

    /**
     * Show a snackbar on the activity's root view.
     * Can be called from fragments via requireActivity().
     */
    fun showSnackbar(message: String, isError: Boolean = false) {
        val snackbar = Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG)
        if (isError) {
            snackbar.setBackgroundTint(getColor(android.R.color.holo_red_dark))
        }
        snackbar.show()
    }
}
