# Deployment Status

Updated 2026-09-13 after rc10 Wi-Fi suggestion field validation.

## Current architecture

ARES usage collection now uses:

1. ARES Sync Android app on the teacher/test phone.
2. School-local collection from `http://ares.local` using the scheduled PHP endpoint.
3. App-private pending-file storage on Android.
4. Deferred direct HTTPS upload to the central ARES service after validated internet returns.
5. Protected central incoming storage.
6. `central-monitoring/process_incoming.py` for local incoming validation, SHA-256 dedupe, quarantine, archive, and optional report execution.

Round Sync, Automate, MacroDroid, phone-side rclone, Google Drive remotes, and Downloads-folder workflows are superseded and are not part of the target production architecture.

## Android status

Current field-test candidate:

- version: `0.8.0-rc10`
- source commit: `95bcfb37174eeb5ede658d7cd7abf7b14a1d4fc5`
- CI run: `#63`
- Wi-Fi onboarding field test: suggestion approval completed successfully.

Validated behavior includes:

- fresh enrollment to a canonical school;
- historical schedule baselining;
- silent local collection path;
- app-private pending storage;
- deferred HTTPS upload after internet returns;
- readable light/dark appearance behavior;
- themed school selection;
- keyboard resize/scroll during enrollment entry;
- ARES logo rendering;
- teacher-facing no-action-required normal state;
- app-level Android approval for ARES Wi-Fi suggestions without the unusable saved-network confirmation sheet;
- automatic association to suggested `ARES`/`ARES2` when competing internet-capable saved Wi-Fi networks are not present.

Important rc10 limitation: when other saved internet-capable Wi-Fi networks are available, Android prefers those networks and does not automatically switch to the offline ARES network. The Wi-Fi Suggestion API therefore solves onboarding and can auto-associate to ARES when it is the preferred available Wi-Fi, but it is not yet proven sufficient as the only scheduled-collection connection mechanism in mixed-network environments.

The CI APK is debug-signed and remains a test artifact. Production distribution still requires the approved release-signing process.

## School-server status

The automated installer and local collection endpoints have passed school-side acceptance testing. The production schedule remains aligned to the approved 2026 term collection dates.

The St Jude server and phone are dedicated test fixtures and may remain in their controlled acceptance state for regression testing.

## Central service status

The enrolled-device HTTPS upload path has passed end-to-end testing. Duplicate upload retry is idempotent, and protected data files are not publicly readable.

The replacement local incoming processor is implemented and locally validated. Live cron/systemd wiring against the production central directories remains a separate deployment step.

Known controlled September acceptance uploads using the real `2026-Q3-MID` collection ID must be explicitly excluded or removed before production reporting ingestion. Do not delete them silently.

## Public setup portal status

The repository portal has been updated for the native ARES Sync workflow:

- stable APK link: `assets/downloads/ares-sync.apk`;
- direct teacher installation flow;
- Android install-from-source warning guidance;
- one-time school enrollment;
- app-level Wi-Fi suggestion approval;
- notification permission;
- mostly automatic collection and upload behavior;
- no Round Sync/Automate/MacroDroid setup requirement.

The portal still needs to be deployed to the final HTTPS path and field-tested by downloading the exact approved release APK from that live page.

## Remaining production milestones

1. Decide and field-validate the final Android connection strategy for due collections when competing internet-capable Wi-Fi networks are present.
2. Build the first production-signed acceptance APK with the protected ARES signing key.
3. Record release version, versionCode, source commit, APK SHA-256, and signing-certificate fingerprint.
4. Publish the exact approved APK to the stable setup-portal path and run the clean-phone website-origin acceptance test.
5. Wire the central incoming processor into the live scheduled service after explicitly handling acceptance-test data.
6. Run the full release checklist and preserve rollback artifacts.
7. Independently validate autonomous AlarmManager timing if required beyond the already validated overdue/silent collection path.
