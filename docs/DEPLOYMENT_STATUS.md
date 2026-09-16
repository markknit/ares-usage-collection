# Deployment Status

Updated 2026-09-16 after production portal deployment and the clean-phone website-origin installation test.

## Current architecture

ARES usage collection uses:

1. ARES Sync Android app on the teacher/test phone.
2. School-local collection from `http://ares.local` using the scheduled PHP endpoint.
3. App-private pending-file storage on Android.
4. Deferred direct HTTPS upload to the central ARES service after validated internet returns.
5. Protected central incoming storage.
6. `central-monitoring/process_incoming.py` for local incoming validation, SHA-256 dedupe, quarantine, archive, and optional report execution.

Round Sync, Automate, MacroDroid, phone-side rclone, Google Drive remotes, and Downloads-folder workflows are superseded and are not part of the target production architecture.

## Android status

Last cleanly accepted onboarding baseline:

- version: `0.8.0-rc10`
- source commit: `95bcfb37174eeb5ede658d7cd7abf7b14a1d4fc5`
- CI run: `#63`
- Wi-Fi suggestion approval: passed.
- automatic association to `ARES`/`ARES2`: passed when no competing internet-capable saved Wi-Fi was preferred.

The launcher-icon milestone was completed in commit `dd7277614b38da43d3250612003d2a6ea1ba915e`; CI run `#64` passed and the manifest uses the ARES logo for the launcher icon. The icon also passed field inspection on rc11.

The rc11 mixed-network candidate added an app-specific `WifiNetworkSpecifier` local-only request for `ARES2`/`ARES` while preserving rc10 Wi-Fi suggestions. It first tries the currently available Wi-Fi; if the school server is not reachable there, the due path can request a local-only ARES network and send school-server traffic over the returned Android `Network` rather than binding the whole app process.

### rc11 field result - 2026-09-14

The phone began the test already connected to an internet-capable Wi-Fi network. During post-enrollment setup, Android successfully connected through the ARES local-network flow and subsequently showed a successful ARES2 connection as the sequence continued. This is strong evidence that Android can authorize/use the school-local networks even with a competing internet Wi-Fi configured.

However, the helper flow itself failed acceptance: after the successful connection sequence it remained on the setup screen with automatic/manual choices instead of returning to the ARES Sync main screen. Pressing Android Back returned to the main screen but produced a false Wi-Fi setup failure state. The several-second transition between network steps also lacked a clear "setup is continuing" message.

ARES and ARES2 are not expected to appear as ordinary Android saved networks in this architecture. Wi-Fi suggestions and `WifiNetworkSpecifier` requests are app-managed network mechanisms, not entries in the normal saved-network list.

The corrected helper flow has now passed field testing in the production-signed rc15 build. During clean-phone enrollment it found ARES2 and ARES, completed automatic Wi-Fi setup, and returned to the main screen with a successful setup state. The tester did not pause to record each intermediate permission/progress screen, so the final outcome is validated but this run does not add prompt-by-prompt evidence.

Still unverified:

- whether repeating the local-network request on the same access point proceeds without another Android approval prompt;
- whether a different mesh BSSID requires another approval;
- unattended due-collection behavior after setup approval;
- exact autonomous AlarmManager timing.

Validated behavior from earlier candidates still includes fresh canonical-school enrollment, historical schedule baselining, silent local collection when the school network is already available, app-private pending storage, deferred HTTPS upload after internet returns, appearance themes, themed school selection, keyboard-safe enrollment, ARES logo rendering, and the teacher-facing no-action-required normal state.

The first production-key-signed build is version `0.8.0-rc15` (`versionCode 23`). Its release record, APK SHA-256, and signing-certificate fingerprint are recorded in `docs/RELEASE_CHECKLIST.md`. The production website-to-phone installation and fresh enrollment test passed on 2026-09-16. A later same-key in-place upgrade test remains outstanding.

## School-server status

The automated installer and local collection endpoints have passed school-side acceptance testing. The installer places `collection_schedule.json` under the tracker web directory, which the Android app uses as a harmless reachability probe during local-network setup. The production schedule remains aligned to the approved 2026 term collection dates.

The St Jude server and phone are dedicated test fixtures and may remain in their controlled acceptance state for regression testing.

## Central service status

The enrolled-device HTTPS upload path has passed end-to-end testing. Duplicate upload retry is idempotent, and protected data files are not publicly readable.

The replacement local incoming processor is implemented and locally validated. Live cron/systemd wiring against the production central directories remains a separate deployment step.

Known controlled September acceptance uploads using the real `2026-Q3-MID` collection ID must be explicitly excluded or removed before production reporting ingestion. Do not delete them silently.

## Public setup portal status

The repository portal is deployed at `https://areseducation.org/phone-setup/`. The live HTML and stylesheet matched the repository copies, and the obsolete `ACCEPTANCE_BUILD.txt` marker was removed. The published APK was independently downloaded and matched the approved production SHA-256 exactly.

The public download button, Android install flow, app scan, clean installation, fresh St Jude enrollment, automatic ARES/ARES2 setup, and return to the normal enrolled screen all passed from the public website on a Google Pixel 9 Pro Fold running Android 17 beta. The production screen showed the next collection on 15 October 2026 and no forced-due acceptance behavior. Manufacturer-specific and other Android-version installer flows are not established by this single clean-device test.

## Remaining production milestones

1. Repeat a local-network request on the same AP and then on a second mesh AP/BSSID; document whether Android asks for approval again.
2. Validate a real due-collection retry through the app-specific ARES network while another internet Wi-Fi remains configured.
3. Decide whether the direct local-network mechanism is acceptable for unattended scheduled collections.
4. Validate a later APK signed with the production key upgrades the installed production-signed app in place without clearing enrollment.
5. Wire the central incoming processor into the live scheduled service after explicitly handling acceptance-test data.
6. Complete or explicitly disposition the remaining release-checklist items and preserve rollback artifacts.
