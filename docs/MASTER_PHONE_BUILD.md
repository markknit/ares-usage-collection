# ARES Sync Phone Build

The production phone architecture is the native ARES Sync Android app. Round Sync, Automate, MacroDroid, phone-side rclone, Google Drive remotes, and public Downloads-folder workflows are superseded and are not required for deployment.

## Current validated candidate

The current field-validated candidate is ARES Sync `0.8.0-rc6` from commit `02eca4133e2df560fce1f2c10ae382c0fb9a7544`.

This candidate validated the teacher-facing UI, enrollment flow, silent local collection path, app-private pending storage, deferred HTTPS upload, and the final WebP logo rendering on the dedicated test phone.

The CI-produced APK is debug-signed and is for testing only. Production distribution must use a release-signed APK built from the approved release commit.

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

When a collection is due, ARES Sync first attempts local collection silently. If the phone cannot reach the school server, the app asks the teacher to connect to ARES2 or ARES. After local collection, pending usage data is stored in the app-private pending directory and is sent automatically when normal validated internet access later becomes available.

## Installation behavior

Direct APK distribution can trigger Android's unknown-source/install-from-source warning and, on some devices, a Play Protect warning. The public setup page and teacher guide explain the expected steps.

Do not instruct teachers to disable Play Protect globally. A teacher should proceed only with an APK obtained from the official ARES Education setup page or an ARES technician.

## Upgrade and rollback

Keep versionCode monotonically increasing so an approved release can upgrade an existing installation normally.

Retain the previous approved APK privately. If a release fails field validation, stop deployment and restore the previous approved APK and corresponding documentation/package rather than silently changing the live file.
