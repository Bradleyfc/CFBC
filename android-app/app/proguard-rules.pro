# =============================================================================
# CFBC Android App - ProGuard Rules for Release Builds
# Requirements: 15.5, 15.8
# =============================================================================

# ---- Hilt / Dagger ----
-keep class dagger.hilt.** { *; }
-keep class javax.inject.** { *; }
-keep class * extends dagger.hilt.android.internal.managers.ViewComponentManager$FragmentContextWrapper { *; }

# ---- Retrofit ----
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keepattributes AnnotationDefault
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}
-dontwarn org.codehaus.mojo.animal_sniffer.IgnoreJRERequirement
-dontwarn javax.annotation.**
-dontwarn kotlin.Unit
-dontwarn retrofit2.KotlinExtensions
-dontwarn retrofit2.KotlinExtensions$*

# ---- Gson ----
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class com.google.gson.** { *; }
-keep class * extends com.google.gson.TypeAdapter
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer

# ---- API DTOs (serialization/deserialization) ----
-keep class com.cfbc.app.infrastructure.network.dto.** { *; }
-keepclassmembers class com.cfbc.app.infrastructure.network.dto.** {
    @com.google.gson.annotations.SerializedName <fields>;
}

# ---- Room ----
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-dontwarn androidx.room.paging.**

# ---- Coil ----
-dontwarn coil.**

# ---- OkHttp ----
-dontwarn okhttp3.**
-dontwarn okio.**

# ---- EncryptedSharedPreferences ----
-keep class androidx.security.crypto.** { *; }
-dontwarn androidx.security.crypto.**

# ---- Navigation Component ----
-keep class androidx.navigation.** { *; }
-keep class * extends androidx.navigation.NavArgs

# ---- Kotlin Coroutines ----
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-keepclassmembers class kotlinx.coroutines.** {
    volatile <fields>;
}

# ---- Keep ViewBinding classes ----
-keep class * implements androidx.viewbinding.ViewBinding { *; }

# ---- Keep model classes ----
-keep class com.cfbc.app.presentation.model.** { *; }

# ---- Remove debug logging in release ----
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int d(...);
}
