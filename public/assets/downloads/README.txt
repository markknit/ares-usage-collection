ARES SYNC PHONE SETUP DOWNLOAD AREA

The public setup page links to this exact filename:

1. ares-sync.apk
   - Must be the exact approved production release APK.
   - Production APK must be release-signed; do not publish a CI debug build as the permanent teacher package.
   - Record versionName, versionCode, source commit SHA, and SHA-256 before deployment.
   - Verify the deployed file hash matches the approved release hash.
   - Test the exact deployed APK on an Android phone through the public setup page.

Current field-validation reference:
- ARES Sync 0.8.0-rc6
- source commit: 02eca4133e2df560fce1f2c10ae382c0fb9a7544
- this reference build is CI debug-signed and is not the final production distribution package.

Do not place passwords, signing keys, enrollment codes, device credentials, OAuth tokens,
live rclone configuration, or private school data in this public directory.

Round Sync, Automate, MacroDroid, phone-side rclone, Google Drive configuration exports,
and school-specific phone automation files are not part of the production ARES Sync architecture.
