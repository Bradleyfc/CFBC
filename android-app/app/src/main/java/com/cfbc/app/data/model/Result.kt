package com.cfbc.app.data.model

/**
 * Sealed class representing the result of an asynchronous data operation.
 * Used throughout the data layer to communicate loading/success/error states
 * to the presentation layer (ViewModels/UI).
 *
 * @param T The type of data returned on success.
 */
sealed class Result<out T> {

    /** Loading state — operation is in progress, optionally with cached data to show immediately. */
    data class Loading<T>(val data: T? = null) : Result<T>()

    /** Success state — operation completed successfully with data. */
    data class Success<T>(val data: T) : Result<T>()

    /** Error state — operation failed with a throwable and optional message. */
    data class Error(val exception: Throwable, val message: String? = null) : Result<Nothing>() {

        /** Human-readable error message. */
        val displayMessage: String
            get() = message ?: exception.localizedMessage ?: "Ocurrió un error inesperado."

        /** True if the error is related to network connectivity. */
        val isNetworkError: Boolean
            get() = exception is java.io.IOException

        /** True if the error is an authentication failure (401). */
        val isAuthError: Boolean
            get() = message?.contains("401") == true ||
                    message?.contains("no autorizado") == true ||
                    message?.contains("credenciales") == true
    }

    /** Convenience: true if this is a Success. */
    val isSuccess: Boolean get() = this is Success

    /** Convenience: true if this is an Error. */
    val isError: Boolean get() = this is Error

    /** Convenience: true if this is Loading. */
    val isLoading: Boolean get() = this is Loading

    /** Get data if Success, null otherwise. */
    fun getOrNull(): T? = when (this) {
        is Success -> data
        else -> null
    }
}
