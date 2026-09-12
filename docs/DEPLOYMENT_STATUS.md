# Deployment Status

Updated 2026-09-11 after Android UI field acceptance and installation-portal productization.

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

Field-validated candidate:

- version: `0.8.0-rc6`
- source commit: `02eca4133e2df560fce1f2c10ae382c0fb9a7544`
- CI run: `#58`
- UI/accessibility field acceptance: passed on the dedicated test phone.

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
- teacher-facing no-action-required normal state.

The CI APK is debug-signed and remains a test artifact. Production distribution still requires an approved release-signing process.

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
- notification permission;
- mostly automatic collection and upload behavior;
- no Round Sync/Automate/MacroDroid setup requirement.

The portal still needs to be deployed to the final HTTPS path and field-tested by downloading the exact approved release APK from that live page.

## Remaining production milestones

1. Define and protect the production Android signing key and build a release-signed APK.
2. Record release version, versionCode, source commit, and SHA-256.
3. Publish the exact approved APK to the stable setup-portal path.
4. Deploy and field-test the public phone-setup portal on Android.
5. Wire the central incoming processor into the live scheduled service after explicitly handling acceptance-test data.
6. Run the full release checklist and preserve rollback artifacts.
7. Independently validate autonomous AlarmManager timing if required beyond the already validated overdue/silent collection path.
