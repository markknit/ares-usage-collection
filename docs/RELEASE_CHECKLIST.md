# Release checklist

Follow `docs/ANDROID_RELEASE_SIGNING.md` for production key creation, release building, certificate verification, and the website-to-phone acceptance test.

## Android release package

- [ ] Production APK is a release-signed build, not a CI debug build.
- [ ] One long-lived ARES production signing key has been created and backed up securely in at least two controlled locations.
- [ ] Signing keystore and passwords are stored outside the repository.
- [ ] Version name and versionCode are recorded.
- [ ] Source commit SHA is recorded.
- [ ] APK SHA-256 is recorded.
- [ ] Signing-certificate SHA-256 fingerprint is recorded.
- [ ] Exact signed APK installs on a clean Android phone.
- [ ] First production-signed installation is documented; a debug-signed test APK may require uninstall/re-enrollment because its certificate differs.
- [ ] A later APK signed with the same production key upgrades the production-signed app in place without clearing app data.
- [ ] ARES logo and all four appearance modes render correctly.
- [ ] School search and school selector are readable in light and dark system modes.
- [ ] Keyboard does not cover school-search or enrollment-code fields.
- [ ] Notification permission flow works.

## Public setup portal

- [ ] Portal validation passes.
- [ ] HTTPS certificate is valid.
- [ ] `public/assets/downloads/ares-sync.apk` exists on the deployed site.
- [ ] Published APK SHA-256 matches the approved release hash.
- [ ] Download button works from an Android phone.
- [ ] Full installation test starts from the deployed website on a clean phone.
- [ ] Sideload instructions match the tested Android install flow.
- [ ] Teacher can recover from the "Allow from this source" prompt.
- [ ] Any Play Protect warning flow is documented accurately without instructing users to disable Play Protect globally.
- [ ] Teacher guide does not require Round Sync, Automate, MacroDroid, rclone, or Google Drive setup.

## Enrollment, Wi-Fi, and phone behavior

- [ ] School search returns the expected canonical school.
- [ ] Fresh one-time enrollment code succeeds.
- [ ] Reused enrollment code is rejected.
- [ ] Fresh mid-year enrollment baselines earlier scheduled periods correctly.
- [ ] Immediately after fresh enrollment, Android asks to save `ARES2` and then `ARES` in two separate one-network confirmation screens.
- [ ] Each one-network confirmation screen presents a usable **Save** control without requiring the Android sheet to be dragged upward.
- [ ] Approving both save requests leaves both networks in Android's normal saved-network list.
- [ ] ARES Sync records successful automatic Wi-Fi setup and no longer shows the setup button.
- [ ] Skipping/rejecting Wi-Fi setup leaves a visible **Set up automatic ARES Wi-Fi** retry path below the status message.
- [ ] Phone reconnects automatically to saved `ARES` or `ARES2` when the school network is available.
- [ ] On the mesh network, Android can roam between mesh access points under the saved `ARES` SSID without ARES Sync managing BSSIDs.
- [ ] Normal enrolled screen shows school, next collection, and no-action-required state after Wi-Fi setup is complete.
- [ ] Due collection first attempts silent local collection.
- [ ] A due collection that cannot reach `ares.local` remains retryable rather than ending permanently.
- [ ] A later retry succeeds after the phone returns to school and Android reconnects to `ARES` or `ARES2`.
- [ ] Manual **Connect to school Wi-Fi** remains available as the fallback when automatic connection does not occur.
- [ ] Pending file survives app/process interruption and phone restart as designed.
- [ ] Upload succeeds after later cellular or Wi-Fi internet access.
- [ ] Pending count returns to zero after central acknowledgement.

## School server

- [ ] Installer runs successfully on a clean/representative school server.
- [ ] Production collection schedule is installed and matches the Android release.
- [ ] Existing report builder completes successfully.
- [ ] State-aware no-due endpoint returns HTTP 204 when appropriate.
- [ ] Due endpoint returns a populated CSV when a collection is due.

## Central service and reporting

- [ ] HTTPS upload service accepts the release app's enrolled-device upload.
- [ ] Duplicate retry is idempotent.
- [ ] Protected incoming/data files are not publicly readable.
- [ ] Local incoming processor validates and archives accepted files once.
- [ ] Invalid files are quarantined.
- [ ] Exact-content duplicates are suppressed.
- [ ] Existing reporting command runs after newly accepted uploads.
- [ ] Known acceptance-test uploads are excluded or removed intentionally before production reporting.

## Operations and rollback

- [ ] Previous approved APK is retained privately for rollback.
- [ ] Previous server/deployment package is retained.
- [ ] Production deployment instructions are current.
- [ ] Teacher installation instructions are current.
- [ ] Technician installation instructions are current.
- [ ] Release/version/hash/certificate record is saved outside the public download directory.
- [ ] Autonomous Android alarm timing limitation is documented until independently field-validated.
