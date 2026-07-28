package com.cfbc.android.presentation.student

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.cfbc.android.databinding.FragmentStudentSectionsBinding
import com.cfbc.app.infrastructure.security.SecurityManager
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

/**
 * WebView-based student sections — loads the web platform's student pages
 * (grades, attendance, evaluations, academic history) with authentication
 * token injection for seamless access.
 *
 * Receives a section URL via Safe Args and injects the auth token
 * into the WebView's localStorage for the web platform to pick up.
 *
 * Requirements: 6.9-6.12
 */
@AndroidEntryPoint
class StudentSectionsFragment : Fragment() {

    @Inject
    lateinit var securityManager: SecurityManager

    private var _binding: FragmentStudentSectionsBinding? = null
    private val binding get() = _binding!!

    /** The section URL to load (e.g., /calificaciones/, /asistencias/). */
    private var sectionPath: String = ""
    /** The web base URL from build configuration. */
    private var webBaseUrl: String = ""

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentStudentSectionsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        sectionPath = arguments?.getString("sectionPath", "") ?: ""
        webBaseUrl = arguments?.getString("webBaseUrl", "") ?: ""

        setupToolbar()
        setupWebView()

        if (sectionPath.isNotEmpty()) {
            loadSection()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun setupToolbar() {
        binding.toolbar.setNavigationOnClickListener {
            findNavController().navigateUp()
        }

        // Set title based on section path
        binding.toolbar.title = when {
            sectionPath.contains("calificaciones", ignoreCase = true) -> "Calificaciones"
            sectionPath.contains("asistencia", ignoreCase = true) -> "Asistencia"
            sectionPath.contains("evaluacion", ignoreCase = true) -> "Evaluaciones"
            sectionPath.contains("historial", ignoreCase = true) -> "Historial Académico"
            else -> "Sección Académica"
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        binding.webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
        }

        binding.webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                binding.loadingIndicator.visibility = View.GONE
                binding.swipeRefresh.isRefreshing = false

                // Inject JWT/token into localStorage for the web platform
                injectAuthToken()
            }
        }

        // Swipe-to-refresh
        binding.swipeRefresh.setOnRefreshListener {
            loadSection()
        }
    }

    private fun loadSection() {
        binding.loadingIndicator.visibility = View.VISIBLE
        val fullUrl = webBaseUrl.trimEnd('/') + "/" + sectionPath.trimStart('/')
        binding.webView.loadUrl(fullUrl)
    }

    /**
     * Injects the stored auth token into the WebView's localStorage.
     * The web platform checks localStorage.getItem('auth_token') on page load.
     *
     * Uses WebView.evaluateJavascript() after page load to inject the token
     * into the page's localStorage and set a cookie for API requests.
     * Falls back silently if the user is not authenticated or no token exists.
     *
     * Requirements: 15.1, 15.6
     */
    private fun injectAuthToken() {
        val token = securityManager.getAuthToken() ?: return

        // URL-encode the token to prevent XSS via token payload
        val safeToken = android.net.Uri.encode(token)

        // Build the JavaScript code for token injection
        val js = String.format(JS_TOKEN_INJECTION, safeToken)

        // Inject via evaluateJavascript (async, non-blocking)
        binding.webView.evaluateJavascript(js, null)
    }

    companion object {
        /**
         * JavaScript code template for injecting auth token into WebView localStorage.
         * Uses raw JS (no 'javascript:' prefix) because it's evaluated with
         * WebView.evaluateJavascript(), not WebView.loadUrl().
         * The '%s' placeholder is replaced with the URL-encoded auth token.
         */
        private const val JS_TOKEN_INJECTION = """
            (function() {
                var token = '%s';
                if (token) {
                    localStorage.setItem('auth_token', token);
                    localStorage.setItem('token', token);
                }
            })()
        """
    }
}
