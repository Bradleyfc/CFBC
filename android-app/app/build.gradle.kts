plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.kapt)
    alias(libs.plugins.hilt.android)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.cfbc.android"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {
        applicationId = "com.cfbc.android"
        minSdk = libs.versions.minSdk.get().toInt()
        targetSdk = libs.versions.targetSdk.get().toInt()
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        
        vectorDrawables {
            useSupportLibrary = true
        }
    }

    flavorDimensions += "environment"
    
    productFlavors {
        create("emulator") {
            dimension = "environment"
            // For Android Emulator - 10.0.2.2 maps to host's 127.0.0.1
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000/\"")
            buildConfigField("String", "WEB_BASE_URL", "\"http://10.0.2.2:8000/\"")
            resValue("string", "env_name", "Emulador")
        }
        
        create("wifi") {
            dimension = "environment"
            // For Physical Device on WiFi - Your computer's actual IP
            buildConfigField("String", "API_BASE_URL", "\"http://192.168.1.101:8000/\"")
            buildConfigField("String", "WEB_BASE_URL", "\"http://192.168.1.101:8000/\"")
            resValue("string", "env_name", "WiFi Local")
        }
        
        create("production") {
            dimension = "environment"
            // For Production server on internet
            buildConfigField("String", "API_BASE_URL", "\"https://cfbc.example.com/\"")
            buildConfigField("String", "WEB_BASE_URL", "\"https://cfbc.example.com/\"")
            resValue("string", "env_name", "Producción")
        }
    }

    signingConfigs {
        create("release") {
            // Para pruebas, puedes usar valores de prueba
            // En producción, usa variables de entorno o archivos seguros
            storeFile = file("../cfbc-release-key.jks")
            storePassword = System.getenv("KEYSTORE_PASSWORD") ?: "changeme"
            keyAlias = "cfbc-key"
            keyPassword = System.getenv("KEY_PASSWORD") ?: "changeme"
        }
    }

    buildTypes {
        debug {
            // Development build - connects to local server
            isDebuggable = true
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            
            buildConfigField("Boolean", "ENABLE_CERTIFICATE_PINNING", "false")
            buildConfigField("Boolean", "ENABLE_LOGGING", "true")
            
            // Debug resource values
            resValue("string", "app_name", "CFBC Debug")
        }
        
        release {
            // Production build - connects to internet hosting
            isMinifyEnabled = true
            isShrinkResources = true
            signingConfig = signingConfigs.getByName("release")
            
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            
            buildConfigField("Boolean", "ENABLE_CERTIFICATE_PINNING", "true")
            buildConfigField("Boolean", "ENABLE_LOGGING", "false")
            
            // Production resource values
            resValue("string", "app_name", "CFBC")
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf(
            "-opt-in=kotlin.RequiresOptIn",
            "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
            "-opt-in=kotlinx.coroutines.FlowPreview"
        )
    }
    
    buildFeatures {
        buildConfig = true
        viewBinding = true
    }
    
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
            excludes += "META-INF/DEPENDENCIES"
            excludes += "META-INF/LICENSE"
            excludes += "META-INF/LICENSE.txt"
            excludes += "META-INF/license.txt"
            excludes += "META-INF/NOTICE"
            excludes += "META-INF/NOTICE.txt"
            excludes += "META-INF/notice.txt"
            excludes += "META-INF/ASL2.0"
            excludes += "META-INF/*.kotlin_module"
        }
    }
}

dependencies {
    // AndroidX Core
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.activity.ktx)
    implementation(libs.androidx.fragment.ktx)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.recyclerview)
    implementation(libs.androidx.cardview)
    implementation(libs.androidx.swiperefreshlayout)
    
    // Lifecycle
    implementation(libs.androidx.lifecycle.viewmodel.ktx)
    implementation(libs.androidx.lifecycle.livedata.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.savedstate)
    
    // Navigation
    implementation(libs.androidx.navigation.fragment.ktx)
    implementation(libs.androidx.navigation.ui.ktx)
    
    // Material Design
    implementation(libs.material)
    
    // Dependency Injection - Hilt
    implementation(libs.hilt.android)
    kapt(libs.hilt.compiler)
    
    // Networking - Retrofit
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)
    implementation(libs.retrofit.converter.kotlinx.serialization)
    
    // Networking - OkHttp
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging.interceptor)
    
    // Kotlinx Serialization
    implementation(libs.kotlinx.serialization.json)
    
    // Database - Room
    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    kapt(libs.room.compiler)
    
    // Image Loading - Coil
    implementation(libs.coil)
    implementation(libs.coil.gif)
    
    // Security
    implementation(libs.androidx.security.crypto)
    
    // Coroutines
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.coroutines.android)
    
    // Testing - Unit Tests
    testImplementation(libs.junit)
    testImplementation(libs.kotest.runner.junit5)
    testImplementation(libs.kotest.assertions.core)
    testImplementation(libs.kotest.property)
    testImplementation(libs.kotest.framework.datatest)
    testImplementation(libs.mockk)
    testImplementation(libs.turbine)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.room.testing)
    
    // Testing - Android Instrumented Tests
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.kotest.extensions.robolectric)
    androidTestImplementation(libs.mockk.android)
    androidTestImplementation(libs.hilt.android.testing)
    kaptAndroidTest(libs.hilt.compiler)
}

// Allow references to generated code
kapt {
    correctErrorTypes = true
}
