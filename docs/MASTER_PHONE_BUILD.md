# ARES Sync Phone Build

The production phone architecture is the native ARES Sync Android app. Round Sync, Automate, MacroDroid, phone-side rclone, Google Drive remotes, and public Downloads-folder workflows are superseded and are not required for deployment.

## Current approved production package

The approved package is ARES Sync `0.8.0-rc15` (`versionCode 23`) built from source commit `9b592732ef1bf3c8a6fc8917f41d4d0c1998aebf` and signed with the ARES production key.

The exact production APK was published at the official setup portal, downloaded to a clean Google Pixel 9 Pro Fold running Android 17 beta, scanned, installed, freshly enrolled, and returned successfully from automatic ARES/ARES2 setup to the normal production-schedule screen. The approved APK size, SHA-256, and signing-certificate fingerprint are recorded in `RELEASE_CHECKLIST.md`.

CI-produced APKs remain debug/acceptance artifacts and must not replace the published production-signed package.

## Production build requirements

1. Build from the approved production release commit.
2. Use the ARES production signing key.
3. Keep keystore files, passwords, credentials, and signing secrets outside this repository.
4. Record:
   - versionName;
   - versionCode;
   - source commit SHA;
   - APK SHA-256;
   - build date.
5. Test the exact signed APK on a clean Android phone.
6. Verify enrollment, appearance, school search, keyboard behavior, notification permission, collection status, and background upload.
7. Publish the approved APK as `public/assets/downloads/ares-sync.apk` only after it passes the release checklist.

## Teacher phone behavior

After enrollment, the normal screen should show the school, next collection date, and a no-action-required state.

When a collection is due, ARES Sync first attempts local collection silently. If the current network cannot reach the school server, the app can request app-specific access to ARES or ARES2; the documented manual connection remains the fallback. After local collection, pending usage data is stored in the app-private pending directory and is sent automatically when normal validated internet access later becomes available.

## Installation behavior

Direct APK distribution can trigger Android's unknown-source/install-from-source warning and, on some devices, a Play Protect warning. The public setup page and teacher guide explain the expected steps.

Do not instruct teachers to disable Play Protect globally. A teacher should proceed only with an APK obtained from the official ARES Education setup page or an ARES technician.

## Upgrade and rollback

Keep versionCode monotonically increasing so an approved release can upgrade an existing installation normally.

Retain the previous approved APK privately. If a release fails field validation, stop deployment and restore the previous approved APK and corresponding documentation/package rather than silently changing the live file.
