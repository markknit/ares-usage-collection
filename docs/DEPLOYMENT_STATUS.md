# Deployment Status

Updated 2026-09-14 after the first rc11 mixed-network field test.

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

The current corrective implementation changes the helper so that action buttons are hidden while setup is active, SSID/fallback progress is explicitly shown, successful server verification records success before returning, and the helper automatically returns to the main screen. That revised flow must be field-tested before rc11/rc12 connection behavior is considered accepted.

Still unverified:

- whether repeating the local-network request on the same access point proceeds without another Android approval prompt;
- whether a different mesh BSSID requires another approval;
- unattended due-collection behavior after setup approval;
- exact autonomous AlarmManager timing.

Validated behavior from earlier candidates still includes fresh canonical-school enrollment, historical schedule baselining, silent local collection when the school network is already available, app-private pending storage, deferred HTTPS upload after internet returns, appearance themes, themed school selection, keyboard-safe enrollment, ARES logo rendering, and the teacher-facing no-action-required normal state.

The CI APKs remain debug-signed test artifacts. Production distribution still requires the approved release-signing process after the mixed-network connection strategy is field-accepted.

## School-server status

The automated installer and local collection endpoints have passed school-side acceptance testing. The installer places `collection_schedule.json` under the tracker web directory, which the Android app uses as a harmless reachability probe during local-network setup. The production schedule remains aligned to the approved 2026 term collection dates.

The St Jude server and phone are dedicated test fixtures and may remain in their controlled acceptance state for regression testing.

## Central service status

The enrolled-device HTTPS upload path has passed end-to-end testing. Duplicate upload retry is idempotent, and protected data files are not publicly readable.

The replacement local incoming processor is implemented and locally validated. Live cron/systemd wiring against the production central directories remains a separate deployment step.

Known controlled September acceptance uploads using the real `2026-Q3-MID` collection ID must be explicitly excluded or removed before production reporting ingestion. Do not delete them silently.

## Public setup portal status

The repository portal has been updated for the native ARES Sync workflow and still needs final HTTPS deployment plus a clean-phone website-origin acceptance test with the exact approved production-signed APK.

Teacher documentation describes Wi-Fi suggestions plus a possible one-time direct local-network approval. Portal wording should be reviewed again after mixed-network field validation before final publication.

## Remaining production milestones

1. Field-test the corrected automatic-return/progress flow with at least one competing internet-capable Wi-Fi network left saved and preferred.
2. Repeat a local-network request on the same AP and then on a second mesh AP/BSSID; document whether Android asks for approval again.
3. Validate a real due-collection retry through the app-specific ARES network while another internet Wi-Fi remains configured.
4. Decide whether the direct local-network mechanism is acceptable for unattended scheduled collections.
5. Build the first production-signed acceptance APK with the protected ARES signing key.
6. Record release version, versionCode, source commit, APK SHA-256, and signing-certificate fingerprint.
7. Publish the exact approved APK to the stable setup-portal path and run the clean-phone website-origin acceptance test.
8. Wire the central incoming processor into the live scheduled service after explicitly handling acceptance-test data.
9. Run the full release checklist and preserve rollback artifacts.
