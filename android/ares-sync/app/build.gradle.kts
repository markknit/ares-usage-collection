plugins {
    id("com.android.application")
}

android {
    namespace = "org.areseducation.sync"
    compileSdk = 36

    defaultConfig {
        applicationId = "org.areseducation.sync"
        minSdk = 29
        targetSdk = 36
        versionCode = 4
        versionName = "0.4.0-guided-handoff"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
