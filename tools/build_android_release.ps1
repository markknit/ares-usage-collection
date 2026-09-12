param(
    [string]$GradleCommand = "gradle"
)

$ErrorActionPreference = "Stop"

$required = @(
    "ARES_RELEASE_STORE_FILE",
    "ARES_RELEASE_STORE_PASSWORD",
    "ARES_RELEASE_KEY_ALIAS",
    "ARES_RELEASE_KEY_PASSWORD"
)

$missing = @()
foreach ($name in $required) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        $missing += $name
    }
}

if ($missing.Count -gt 0) {
    throw "Missing release signing variables: $($missing -join ', ')"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$androidRoot = Join-Path $repoRoot "android\ares-sync"
$outputDir = Join-Path $androidRoot "release-output"
$sourceApk = Join-Path $androidRoot "app\build\outputs\apk\release\app-release.apk"
$targetApk = Join-Path $outputDir "ares-sync.apk"

$storeFile = [Environment]::GetEnvironmentVariable("ARES_RELEASE_STORE_FILE")
if (-not (Test-Path -LiteralPath $storeFile)) {
    throw "Release keystore was not found at ARES_RELEASE_STORE_FILE."
}

Write-Host "Building signed ARES Sync release APK..."
& $GradleCommand -p $androidRoot :app:clean :app:assembleRelease
if ($LASTEXITCODE -ne 0) {
    throw "Gradle release build failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path -LiteralPath $sourceApk)) {
    throw "Release APK was not produced at $sourceApk"
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
Copy-Item -LiteralPath $sourceApk -Destination $targetApk -Force

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $targetApk).Hash.ToLowerInvariant()
$size = (Get-Item -LiteralPath $targetApk).Length

Write-Host ""
Write-Host "Release APK: $targetApk"
Write-Host "Size: $size bytes"
Write-Host "SHA-256: $hash"
Write-Host ""
Write-Host "Next: verify the APK signing certificate, record the release metadata, then deploy this exact file to the setup portal for the website-to-phone acceptance test."
