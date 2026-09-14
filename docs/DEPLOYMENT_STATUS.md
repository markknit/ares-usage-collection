# Deployment Status

Updated 2026-09-14 for the rc11 mixed-network local-request candidate.

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

Last field-validated candidate:

- version: `0.8.0-rc10`
- source commit: `95bcfb37174eeb5ede658d7cd7abf7b14a1d4fc5`
- CI run: `#63`
- Wi-Fi suggestion approval: passed.
- automatic association to `ARES`/`ARES2`: passed when no competing internet-capable saved Wi-Fi was preferred.

The launcher-icon milestone was then completed in commit `dd7277614b38da43d3250612003d2a6ea1ba915e`; CI run `#64` passed and the manifest now uses the ARES logo for the launcher icon.

Current implementation candidate for field testing:

- planned version: `0.8.0-rc11`
- planned versionCode: `19`
- purpose: preserve rc10 Wi-Fi suggestions for onboarding, while adding an app-specific `WifiNetworkSpecifier` local-only request for `ARES2`/`ARES` when another Wi-Fi network is preferred.

The rc11 design first tries the currently available Wi-Fi. If it cannot reach the school server, ARES Sync requests a local-only ARES network and sends the school-server request over the returned Android `Network` rather than binding the entire app process. Setup requires the appropriate Android Wi-Fi runtime permission and verifies the direct path by reaching `http://ares.local/tracker/collection_schedule.json`.

This rc11 mechanism is not field-accepted yet. It must be tested while an internet-capable Wi-Fi network remains saved and preferred. Android approval persistence is associated with the particular access point selected by the user, so repeated access on the same AP and behavior on a second mesh BSSID must both be verified. Hardware support for simultaneous internet Wi-Fi plus a local-only Wi-Fi connection can also vary by phone; field behavior is authoritative.

Validated behavior from earlier candidates still includes:

- fresh enrollment to a canonical school;
- historical schedule baselining;
- silent local collection path when the school network is already available;
- app-private pending storage;
- deferred HTTPS upload after internet returns;
- readable light/dark appearance behavior;
- themed school selection;
- keyboard resize/scroll during enrollment entry;
- ARES logo rendering;
- teacher-facing no-action-required normal state;
- app-level Android approval for ARES Wi-Fi suggestions without the unusable saved-network confirmation sheet.

The CI APKs remain debug-signed test artifacts. Production distribution still requires the approved release-signing process after the rc11 connection strategy is field-accepted.

## School-server status

The automated installer and local collection endpoints have passed school-side acceptance testing. The installer places `collection_schedule.json` under the tracker web directory, which rc11 uses as a harmless reachability probe during local-network setup. The production schedule remains aligned to the approved 2026 term collection dates.

The St Jude server and phone are dedicated test fixtures and may remain in their controlled acceptance state for regression testing.

## Central service status

The enrolled-device HTTPS upload path has passed end-to-end testing. Duplicate upload retry is idempotent, and protected data files are not publicly readable.

The replacement local incoming processor is implemented and locally validated. Live cron/systemd wiring against the production central directories remains a separate deployment step.

Known controlled September acceptance uploads using the real `2026-Q3-MID` collection ID must be explicitly excluded or removed before production reporting ingestion. Do not delete them silently.

## Public setup portal status

The repository portal has been updated for the native ARES Sync workflow and still needs final HTTPS deployment plus a clean-phone website-origin acceptance test with the exact approved production-signed APK.

Teacher documentation for rc11 now describes Wi-Fi suggestions plus a possible one-time direct local-network approval. Portal wording should be reviewed again after rc11 field validation before final publication.

## Remaining production milestones

1. Build and field-test rc11 with at least one competing internet-capable Wi-Fi network left saved and preferred.
2. Verify same-AP repeat behavior and a second mesh AP/BSSID; document any user approval still required.
3. Decide whether the rc11 direct local-network mechanism is acceptable for unattended due collections. Do not assume background approval behavior until tested.
4. Build the first production-signed acceptance APK with the protected ARES signing key.
5. Record release version, versionCode, source commit, APK SHA-256, and signing-certificate fingerprint.
6. Publish the exact approved APK to the stable setup-portal path and run the clean-phone website-origin acceptance test.
7. Wire the central incoming processor into the live scheduled service after explicitly handling acceptance-test data.
8. Run the full release checklist and preserve rollback artifacts.
9. Independently validate autonomous AlarmManager timing if required beyond the already validated overdue/silent collection path.
