# Release checklist

Follow `docs/ANDROID_RELEASE_SIGNING.md` for production key creation, release building, certificate verification, and the website-to-phone acceptance test.

## Production-signed release candidate - 2026-09-15

PASS: the first production-key-signed ARES Sync release candidate was built and its signing identity was independently verified with `apksigner`.

Release record:

- versionName: `0.8.0-rc15`
- versionCode: `23`
- source commit: `9b592732ef1bf3c8a6fc8917f41d4d0c1998aebf`
- APK path on the trusted release workstation: `android\ares-sync\release-output\ares-sync.apk`
- APK size: `6300531` bytes
- APK SHA-256: `16e5eef24b56dde1db3fbd0e5be542c5853f329841ae056bc1dd7afb6bf773a8`
- signer DN: `CN=ARES Education, OU=Technology, O=ARES Education, L=Nanyuki, ST=Laikipia, C=KE`
- signing-certificate SHA-256: `F3:FE:05:DF:48:DB:0A:02:F4:50:15:80:B3:B8:B8:BA:93:36:AA:AA:86:C7:5A:F2:F4:32:08:99:71:75:49:47`
- build toolchain: Gradle `8.13`, matching the validated CI baseline

The release build completed successfully after direct `keytool` verification confirmed the existing long-lived `ares-sync` keystore and the correct signing password was used. No signing password, private key, keystore, device credential, enrollment code, or private school data is recorded here.

The exact signed APK was published at the stable setup-portal path on 2026-09-16. Its deployed hash was independently re-verified, and the website-origin clean-phone installation and enrollment test passed. Remaining unchecked items in this checklist still require completion or an explicit release decision before broad rollout.

### Production website-to-phone result - 2026-09-16

- Test device: Google Pixel 9 Pro Fold running Android 17 beta.
- PASS: `https://areseducation.org/phone-setup/` and `setup.html` returned HTTP 200 over valid HTTPS.
- PASS: the live `index.html`, `setup.html`, and `assets/css/site.css` matched the repository copies byte-for-byte.
- PASS: the published APK returned HTTP 200 with the Android package content type and attachment disposition.
- PASS: the downloaded website copy was `6300531` bytes and its SHA-256 matched the approved release hash, `16e5eef24b56dde1db3fbd0e5be542c5853f329841ae056bc1dd7afb6bf773a8`.
- PASS: the obsolete public `ACCEPTANCE_BUILD.txt` was removed and returned HTTP 404.
- PASS: a clean Android phone downloaded `ares-sync.apk` from the public portal. Android's recommended app scan completed successfully, and the app installed and opened.
- PASS: school search returned the canonical St Jude test school, a fresh one-time code enrolled the phone, and the code field inserted the hyphen automatically.
- PASS: automatic setup found ARES2 and ARES, returned to the main screen, and reported Wi-Fi setup complete.
- PASS: the enrolled screen showed St Jude girls, next collection `15 October 2026`, `Everything is ready. No action required.`, and `Usage data: up to date.` This confirms the production schedule rather than the acceptance build's forced-due behavior.
- LIMITATION: the tester moved through the Android permission sequence too quickly to record each prompt again. The end state passed, but this run does not add prompt-by-prompt evidence beyond earlier field tests.
- LIMITATION: this clean installation result applies directly to the tested Android 17 beta device. Other Android versions and manufacturer-specific installer flows remain dependent on the generic recovery guidance and prior tests.

## Android release package

- [x] Production APK is a release-signed build, not a CI debug build.
- [ ] One long-lived ARES production signing key has been created and backed up securely in at least two controlled locations.
- [x] Signing keystore and passwords are stored outside the repository.
- [x] Version name and versionCode are recorded.
- [x] Source commit SHA is recorded.
- [x] APK SHA-256 is recorded.
- [x] Signing-certificate SHA-256 fingerprint is recorded.
- [x] Exact signed APK installs on a clean Android phone.
- [x] First production-signed installation is documented; a debug-signed test APK may require uninstall/re-enrollment because its certificate differs.
- [ ] A later APK signed with the same production key upgrades the production-signed app in place without clearing app data.
- [x] ARES launcher icon uses the ARES logo rather than the generic Android icon.
- [ ] ARES logo and all four appearance modes render correctly.
- [ ] School search and school selector are readable in light and dark system modes.
- [ ] Keyboard does not cover school-search or enrollment-code fields.
- [ ] Notification permission flow works.

## Public setup portal

- [x] Portal validation passes.
- [x] HTTPS certificate is valid.
- [x] `public/assets/downloads/ares-sync.apk` exists on the deployed site.
- [x] Published APK SHA-256 matches the approved release hash.
- [x] Download button works from an Android phone.
- [x] Full installation test starts from the deployed website on a clean phone.
- [x] Sideload instructions match the tested Android install flow.
- [ ] Teacher can recover from the "Allow from this source" prompt.
- [x] Any Play Protect warning flow is documented accurately without instructing users to disable Play Protect globally.
- [x] Teacher guide does not require Round Sync, Automate, MacroDroid, rclone, or Google Drive setup.

## Enrollment, Wi-Fi, and phone behavior

- [x] School search returns the expected canonical school.
- [x] Fresh one-time enrollment code succeeds.
- [ ] Reused enrollment code is rejected.
- [ ] Fresh mid-year enrollment baselines earlier scheduled periods correctly.
- [x] Immediately after fresh enrollment, ARES Sync requests Android's one-time app-level approval to suggest Wi-Fi networks; it does not open the `ACTION_WIFI_ADD_NETWORKS` saved-network sheet.
- [x] Android's Wi-Fi suggestion approval prompt is usable on the first attempt and does not overlap the system gesture/navigation area.
- [x] Approving the prompt registers both open networks, `ARES2` and `ARES`, as ARES Sync suggestions.
- [ ] On Android 12+, ARES Sync receives the suggestion-approval callback and records setup complete.
- [ ] Declining suggestion approval leaves manual **Connect to school Wi-Fi** available and documents the **Special app access > Wi-Fi control** recovery path.
- [x] Android 13+ setup requests **Nearby Wi-Fi devices** once, with `neverForLocation`; Android 12L and earlier use the legacy fine-location Wi-Fi permission only through API 32.
- [x] rc11 successfully obtained direct ARES local-network connections while a normal internet-capable Wi-Fi network remained saved.
- [x] The setup helper automatically returns to the main ARES Sync screen after a verified local-network connection and displays success rather than a false failure state.
- [ ] While setup is moving between ARES/ARES2 or falling back from one SSID to the other, the helper displays a clear continuing/setup-in-progress message and does not expose action buttons until intervention is actually required.
- [ ] After suggestion approval, setup makes a specific `WifiNetworkSpecifier` request for `ARES2` or `ARES` and verifies `http://ares.local/tracker/collection_schedule.json` over the returned `Network`.
- [ ] ARES Sync does not bind the whole process to the ARES network; only the local collection request is sent over the returned ARES `Network`.
- [ ] Repeating a specific request to the same approved access point can reconnect without another user approval prompt.
- [ ] A different mesh access point is tested to determine whether Android requires another approval for the new BSSID.
- [ ] After approval, Android auto-connects to `ARES` or `ARES2` when available even though the school network normally has no internet access.
- [ ] On the mesh network, Android can roam between access points under the suggested `ARES` SSID without ARES Sync managing BSSIDs.
- [x] Normal enrolled screen shows school, next collection, and no-action-required state after Wi-Fi setup is complete.
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

### rc11 mixed-network local request field result - 2026-09-14

- PASS: testing began while the phone was already connected to an internet-capable Wi-Fi network.
- PASS: Android successfully connected through the ARES local-network authorization flow and then also showed a successful ARES2 connection during the sequence.
- PASS: the ARES launcher icon rendered correctly.
- EXPECTED: ARES/ARES2 do not appear as ordinary Android saved networks because this path uses Wi-Fi suggestions and app-specific `WifiNetworkSpecifier` requests rather than saved-network entries.
- FAIL/UX: after the apparent successful network connections, the helper remained on its setup screen with automatic/manual action choices instead of automatically returning to the main screen.
- FAIL/UX: returning with Android Back caused the main screen to report Wi-Fi setup failure even though successful ARES network connections had already occurred.
- FAIL/UX: there was no clear continuing message during the several-second transition between the ARES and ARES2 portions of the setup flow.
- NEXT: field-test the revised helper flow that hides action buttons while work is in progress, reports SSID fallback/progress, records success before returning, and automatically returns to the main screen after verification.
- STILL UNVERIFIED: whether a repeat local-network request on the same AP proceeds without another approval prompt, and whether a different mesh BSSID requires another approval.

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
- [x] Known acceptance-test uploads are excluded or removed intentionally before production reporting.

## Operations and rollback

- [ ] Previous approved APK is retained privately for rollback.
- [ ] Previous server/deployment package is retained.
- [ ] Production deployment instructions are current.
- [ ] Teacher installation instructions are current.
- [ ] Technician installation instructions are current.
- [ ] Release/version/hash/certificate record is saved outside the public download directory.
- [ ] Autonomous Android alarm timing limitation is documented until independently field-validated.
