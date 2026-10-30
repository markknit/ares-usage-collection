plugins {
    id("com.android.application")
}

fun releaseSecret(name: String): String? =
    providers.gradleProperty(name).orNull ?: providers.environmentVariable(name).orNull

val releaseStoreFile = releaseSecret("ARES_RELEASE_STORE_FILE")
val releaseStorePassword = releaseSecret("ARES_RELEASE_STORE_PASSWORD")
val releaseKeyAlias = releaseSecret("ARES_RELEASE_KEY_ALIAS")
val releaseKeyPassword = releaseSecret("ARES_RELEASE_KEY_PASSWORD")
val releaseSigningConfigured = listOf(
    releaseStoreFile,
    releaseStorePassword,
    releaseKeyAlias,
    releaseKeyPassword
).all { !it.isNullOrBlank() }

val aresProfile = providers.gradleProperty("aresProfile").orElse("production").get()
require(aresProfile in listOf("production", "test")) { "aresProfile must be production or test" }
val localServerHost = if (aresProfile == "test") "ares-test.local" else "ares.local"

android {
    namespace = "org.areseducation.sync"
    compileSdk = 36

    defaultConfig {
        applicationId = "org.areseducation.sync"
        minSdk = 29
        targetSdk = 36
        versionCode = 23
        versionName = "0.8.0-rc15"
        buildConfigField("boolean", "ACCEPTANCE_TEST_MODE", "false")
        buildConfigField("String", "LOCAL_SERVER_URL", "\"http://$localServerHost\"")
        resValue("string", "ares_server_host", localServerHost)
        if (aresProfile == "test") {
            applicationId = "org.areseducation.sync.test"
            versionNameSuffix = "-test-profile"
        }
    }

    buildFeatures {
        buildConfig = true
    }

    signingConfigs {
        create("release") {
            if (releaseSigningConfigured) {
                storeFile = file(releaseStoreFile!!)
                storePassword = releaseStorePassword!!
                keyAlias = releaseKeyAlias!!
                keyPassword = releaseKeyPassword!!
            }
        }
    }

    buildTypes {
        create("acceptance") {
            initWith(getByName("debug"))
            matchingFallbacks += listOf("debug")
            versionNameSuffix = "-acceptance"
            buildConfigField("boolean", "ACCEPTANCE_TEST_MODE", "true")
        }
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
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

tasks.configureEach {
    if (name == "validateSigningRelease") {
        doFirst {
            if (!releaseSigningConfigured) {
                throw GradleException(
                    "ARES release signing is not configured. Set ARES_RELEASE_STORE_FILE, " +
                        "ARES_RELEASE_STORE_PASSWORD, ARES_RELEASE_KEY_ALIAS, and " +
                        "ARES_RELEASE_KEY_PASSWORD as Gradle properties or environment variables."
                )
            }
        }
    }
}

dependencies {
    implementation("androidx.work:work-runtime:2.11.2")
}
