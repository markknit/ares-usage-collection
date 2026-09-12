# ARES Sync Android release signing

ARES Sync production APKs must use one long-lived ARES signing identity. Android requires future updates for the same application ID to be signed with the same key.

## Security rules

Never commit any of the following:

- release keystore files (`.jks`, `.keystore`);
- keystore passwords;
- key passwords;
- signing environment-variable files;
- copies of production-signed APKs intended only for deployment;
- enrollment/device credentials or private school data.

The repository `.gitignore` excludes the normal signing-key and release-output paths, but the operator must still review `git status` before every commit.

## 1. Create the ARES release key once

Run this on the trusted Windows release workstation, outside the Git repository. Example PowerShell command:

```powershell
New-Item -ItemType Directory -Force C:\ARES-Secrets | Out-Null

keytool -genkeypair `
  -keystore C:\ARES-Secrets\ares-sync-release.jks `
  -alias ares-sync `
  -keyalg RSA `
  -keysize 4096 `
  -validity 10000
```

`keytool` will ask for the keystore/key password and certificate identity information.

Use an organization-controlled password and store it in the organization's password manager. Do not paste the password into chat, documentation, source files, or GitHub.

## 2. Back up the signing key

The release key is operationally critical. Losing it can prevent future APKs from upgrading the installed production app.

Maintain at least two encrypted backups under ARES administrative control, in separate secure locations. Record the key alias (`ares-sync`) and recovery procedure without recording passwords in this repository.

## 3. Configure one PowerShell session

Set the four required values only in the local release shell:

```powershell
$env:ARES_RELEASE_STORE_FILE = "C:\ARES-Secrets\ares-sync-release.jks"
$env:ARES_RELEASE_STORE_PASSWORD = Read-Host "Keystore password" -AsSecureString | ConvertFrom-SecureString -AsPlainText
$env:ARES_RELEASE_KEY_ALIAS = "ares-sync"
$env:ARES_RELEASE_KEY_PASSWORD = Read-Host "Key password" -AsSecureString | ConvertFrom-SecureString -AsPlainText
```

These environment variables exist only for the current process/session unless the operator deliberately persists them. Do not use `setx` for the passwords.

If the key password is the same as the keystore password, it still must be supplied in both variables.

## 4. Build the signed release APK

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_android_release.ps1
```

The script:

1. refuses to run if any signing variable is missing;
2. runs Gradle `:app:assembleRelease`;
3. verifies the APK exists;
4. copies it to `android\ares-sync\release-output\ares-sync.apk`;
5. prints its SHA-256 hash.

The release-output directory is ignored by Git.

## 5. Verify the signing certificate

Before deployment, inspect the built APK:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\36.0.0\apksigner.bat" verify --print-certs .\android\ares-sync\release-output\ares-sync.apk
```

If that exact Build Tools path is not installed, use the installed `apksigner` from the Android SDK Build Tools directory.

Record the signing certificate SHA-256 fingerprint in the private release register. Future production releases must use the same certificate.

## 6. Record the release

For each release, record outside the public download directory:

- versionName;
- versionCode;
- source commit SHA;
- APK SHA-256;
- signing-certificate SHA-256 fingerprint;
- build date;
- tester/device used for clean installation;
- public deployment date and URL.

Do not treat a CI debug APK as the production package.

## 7. Website-to-phone acceptance test

After the signed APK is built and its hash recorded:

1. deploy the portal under the intended HTTPS path (for example `/phone-setup/`);
2. place the exact approved signed APK at `assets/downloads/ares-sync.apk` on the web host;
3. verify the web-host copy has the same SHA-256 as the approved APK;
4. use a clean Android phone and start from the public/staging website;
5. tap **Download ARES Sync**;
6. follow the tested Android sideload warning flow;
7. install and open the app;
8. search/select the test school;
9. enter a fresh one-time enrollment code;
10. allow notifications;
11. confirm the normal enrolled screen shows the school, next collection, and no-action-required state;
12. verify the logo, appearance selection, dark-mode school selector, and keyboard scrolling.

This website-originated clean-phone test must pass before the portal/APK combination is considered rollout-ready.

## 8. Upgrade test

Also install the release-signed APK over a phone already running a previous APK signed with the same production key. Android should accept the update without uninstalling or clearing app data.

The first production-signed installation establishes the production signing lineage. Existing debug-signed test APKs may require uninstall/re-enrollment because their signing certificate differs from the production key.
