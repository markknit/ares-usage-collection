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
- [ ] ARES launcher icon uses the ARES logo rather than the generic Android icon.
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
- [x] Immediately after fresh enrollment, ARES Sync requests Android's one-time app-level approval to suggest Wi-Fi networks; it does not open the `ACTION_WIFI_ADD_NETWORKS` saved-network sheet.
- [x] Android's Wi-Fi suggestion approval prompt is usable on the first attempt and does not overlap the system gesture/navigation area.
- [x] Approving the prompt registers both open networks, `ARES2` and `ARES`, as ARES Sync suggestions.
- [ ] On Android 12+, ARES Sync receives the suggestion-approval callback and records setup complete.
- [ ] Declining suggestion approval leaves manual **Connect to school Wi-Fi** available and documents the **Special app access > Wi-Fi control** recovery path.
- [ ] Android 13+ setup requests **Nearby Wi-Fi devices** once, with `neverForLocation`; Android 12L and earlier use the legacy fine-location Wi-Fi permission only through API 32.
- [ ] After suggestion approval, setup makes a specific `WifiNetworkSpecifier` request for `ARES2` or `ARES` and verifies `http://ares.local/tracker/collection_schedule.json` over the returned `Network`.
- [ ] The local-network setup succeeds while one or more normal internet-capable Wi-Fi networks remain saved.
- [ ] ARES Sync does not bind the whole process to the ARES network; only the local collection request is sent over the returned ARES `Network`.
- [ ] Repeating a specific request to the same approved access point can reconnect without another user approval prompt.
- [ ] A different mesh access point is tested to determine whether Android requires another approval for the new BSSID.
- [ ] After approval, Android auto-connects to `ARES` or `ARES2` when available even though the school network normally has no internet access.
- [ ] On the mesh network, Android can roam between access points under the suggested `ARES` SSID without ARES Sync managing BSSIDs.
- [ ] Normal enrolled screen shows school, next collection, and no-action-required state after Wi-Fi setup is complete.
- [ ] Due collection first attempts the currently available Wi-Fi network.
- [ ] If the current Wi-Fi cannot reach `ares.local`, the due worker requests an app-specific local `ARES2`/`ARES` network and retries the download over that returned `Network`.
- [ ] A due collection that cannot reach `ares.local` remains retryable rather than ending permanently.
- [ ] A later retry succeeds after the phone returns to school and ARES local access becomes available.
- [ ] Manual **Connect to school Wi-Fi** remains available as the fallback when automatic connection does not occur.
- [ ] Pending file survives app/process interruption and phone restart as designed.
- [ ] Upload succeeds after later cellular or Wi-Fi internet access.
- [ ] Pending count returns to zero after central acknowledgement.

### rc10 Wi-Fi suggestion field result - 2026-09-13

- PASS: the app-level Wi-Fi suggestion approval completed successfully without the unusable saved-network bottom sheet.
- PASS: with competing internet-capable saved Wi-Fi networks removed, Android immediately selected the ARES suggestions and connected to `ARES`/`ARES2` even though they do not provide internet access.
- LIMITATION: while other saved internet-capable Wi-Fi networks were available, Android preferred those networks and did not switch to `ARES`/`ARES2`.
- RELEASE IMPACT: the Suggestion API is validated for onboarding and automatic association when ARES is the preferred available Wi-Fi, but it is not sufficient by itself as the sole scheduled-collection connection mechanism in mixed-network environments.

### rc11 mixed-network local request test - pending

- [ ] Restore at least one saved internet-capable Wi-Fi network and leave it connected/preferred.
- [ ] Upgrade rc10 to rc11 without clearing enrollment data.
- [ ] Confirm the launcher icon is the ARES logo.
- [ ] ARES Sync shows the automatic Wi-Fi setup button again because direct local-network authorization is new in rc11.
- [ ] Tap setup and grant **Nearby Wi-Fi devices** if Android asks.
- [ ] Approve the specific ARES2/ARES local-network request if Android asks.
- [ ] Setup completes only after ARES Sync reaches `ares.local` over the requested local `Network`.
- [ ] Confirm the phone's normal internet-capable Wi-Fi remains saved; do not forget it for this test.
- [ ] Repeat the local request on the same AP and record whether Android skips the approval dialog.
- [ ] Test from a second mesh AP/BSSID and record whether Android asks again.

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
