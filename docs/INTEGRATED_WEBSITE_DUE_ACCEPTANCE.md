# Integrated website-to-due-date acceptance test

This test validates the complete teacher-facing path in one controlled run:

1. download ARES Sync from the ARES website;
2. install it on a clean Android phone;
3. enroll the phone with a fresh one-time code;
4. complete the current ARES/ARES2 Wi-Fi authorization flow while a normal internet-capable Wi-Fi remains saved;
5. make `2026-Q3-MID` immediately due on the controlled test server;
6. collect the school usage CSV through the app-specific ARES local-network path;
7. retain the file privately on the phone;
8. upload it automatically to the central HTTPS service after normal internet is available.

## Safety boundaries

The original acceptance plan designated St Jude as the dedicated fixture. The completed 2026-09-15 integrated run instead used Misuuni (`ARES-S0016`) under a temporary controlled acceptance schedule. Do not deploy the acceptance APK or acceptance schedule to normal production use.

The controlled APK uses the real production-style collection ID `2026-Q3-MID`, not `TEST-DUE`, so the complete central path is exercised. Any resulting central acceptance upload must be explicitly excluded or removed before production reporting ingestion.

Never place an enrollment admin key, enrollment secret, device credential, one-time enrollment code, signing keystore, password, or private school data in this repository or in the public website directory.

## Controlled Android build

The Android project contains a separate `acceptance` build type. It is debug-signed and must never become the permanent production APK.

The acceptance build:

- uses version `0.8.0-rc15-acceptance` / versionCode `23`;
- keeps the production release schedule unchanged in normal debug/release builds;
- makes `2026-Q3-MID` due on the current Nairobi date inside the acceptance build;
- queues the acceptance collection immediately after fresh enrollment rather than waiting for the normal 08:00 scheduled alarm;
- uses the same rc14 Wi-Fi suggestion and app-specific local-network code intended for production.

GitHub Actions builds both the normal debug APK and the controlled acceptance APK. The integrated website artifact copies the acceptance APK to the exact portal filename:

```text
assets/downloads/ares-sync.apk
```

The artifact also contains `ACCEPTANCE_BUILD.txt` with the source commit and APK SHA-256.

## Controlled school-server schedule

The repository file:

```text
local-server/collection_schedule.acceptance.json
```

is for controlled acceptance use only. It moves only `2026-Q3-MID` to `2026-09-15`; the production schedule file remains unchanged.

Before the integrated test, preserve the test server's current schedule and install the acceptance schedule:

```bash
sudo cp /mnt/sda3/var/www/tracker/collection_schedule.json \
  /mnt/sda3/var/www/tracker/collection_schedule.before-integrated-acceptance.json
sudo cp local-server/collection_schedule.acceptance.json \
  /mnt/sda3/var/www/tracker/collection_schedule.json
sudo chown root:root /mnt/sda3/var/www/tracker/collection_schedule.json
sudo chmod 0644 /mnt/sda3/var/www/tracker/collection_schedule.json
```

Confirm the test endpoint sees `2026-Q3-MID` as due after `2026-Q2-END`:

```bash
curl -sS -D - -o /dev/null \
  "http://ares.local/tracker/prepare_due_usage_upload.php?last_completed=2026-Q2-END"
```

Expected result: HTTP `200` with `X-ARES-Collection: 2026-Q3-MID`.

After the test, restore the authoritative production schedule before any production use. Do not blindly restore an old backup if its dates differ from the repository production schedule.

## Website deployment

Deploy the contents of the GitHub Actions artifact `ares-phone-setup-acceptance` to the controlled phone-setup website path. The deployed directory must contain:

```text
index.html
setup.html
assets/css/site.css
assets/downloads/ares-sync.apk
ACCEPTANCE_BUILD.txt
```

Do not deploy the repository's empty/nonexistent APK path by itself. The CI artifact is authoritative for this controlled test because it contains the APK built from the same source commit as the portal package.

Before testing on the phone:

1. open the HTTPS setup URL in a browser;
2. verify the page loads without certificate warnings;
3. verify **Download ARES Sync** downloads an APK;
4. independently calculate the deployed APK SHA-256 and compare it with `ACCEPTANCE_BUILD.txt`.

## Clean-phone test sequence

1. Keep at least one normal internet-capable Wi-Fi network saved and connected.
2. Uninstall any existing debug ARES Sync installation so enrollment is genuinely fresh.
3. Remove old downloaded ARES APK files if they could be confused with the new test package.
4. Open the ARES phone-setup website on the phone.
5. Download and install ARES Sync from the website.
6. Confirm the launcher uses the ARES logo.
7. Search for the controlled test school and select the canonical school name.
8. Enter a fresh one-time enrollment code without manually typing the hyphen; confirm the app formats it as `XXXX-XXXX`.
9. Enroll the phone.
10. Approve Wi-Fi suggestion access if Android asks.
11. Approve Nearby Wi-Fi devices access if Android asks.
12. Approve the ARES or ARES2 direct local-network request if Android asks.
13. Confirm setup returns automatically to the main screen and reports success.
14. Leave the normal internet-capable Wi-Fi saved. Do not forget it.
15. Allow the immediate controlled due worker to run. Do not manually connect to ARES unless the app explicitly falls back to manual recovery.
16. Confirm `2026-Q3-MID` completes and the next scheduled collection advances to `2026-11-25`.
17. Confirm the app reports one pending collection if central upload has not yet occurred.
18. Leave ARES Sync in the background and make normal validated internet available.
19. Confirm the pending collection uploads without reopening the app to trigger it.
20. Confirm the central service acknowledges the upload and the phone returns to zero pending collections.

## Pass criteria

The integrated test passes only if all of these are true:

- website download works from the intended HTTPS path;
- the downloaded APK hash matches the CI acceptance package;
- clean install and first-run enrollment work;
- Wi-Fi setup completes with a normal internet Wi-Fi still saved;
- at least one ARES/ARES2 local network reaches `ares.local`;
- the due collection completes through the background worker;
- the file is held privately pending upload when necessary;
- upload occurs automatically after validated internet returns;
- central acknowledgement clears the pending item;
- no teacher action beyond the documented one-time setup approvals is needed.

Record any Android system prompt text that differs from the guide, but do not change the app or website during the clean test unless the test is stopped and restarted from the beginning.

## Field result - 2026-09-15

PASS: the controlled integrated website-to-central acceptance test completed successfully on Misuuni (`ARES-S0016`).

Validated in the field:

- the phone-setup website loaded correctly over HTTPS;
- the initial APK download failure was traced to a parent Apache rewrite that redirected `.apk` to `.html`; adding the dedicated `public/.htaccess` exception made the APK return HTTP `200` as `application/vnd.android.package-archive` with the expected byte count;
- the acceptance APK downloaded from the live website and installed successfully;
- fresh school enrollment succeeded using a valid one-time enrollment code;
- ARES Sync validated both `ARES` and `ARES2` during setup;
- the controlled due worker located the school server, collected the due `2026-Q3-MID` usage data, and uploaded it to the protected central `/monitor_upload/incoming` path;
- after completion, the app advanced the next collection to `25 November 2026`.

The user reported a few minor installation-flow simplifications to review later, but none blocked the end-to-end acceptance path.

This result validates the complete controlled path from website download through install, enrollment, school-network validation, due collection, central upload, and schedule advancement. It does not by itself validate exact autonomous AlarmManager timing, same-AP reapproval persistence, or different mesh-BSSID behavior.

## Cleanup result - 2026-09-15

PASS: controlled acceptance state was removed from active production paths before proceeding to the production-signed APK stage.

- Misuuni's live `collection_schedule.json` was restored to the repository-authoritative production dates: `2026-Q3-MID` = `2026-10-15` and `2026-Q3-END` = `2026-11-25`.
- The saved pre-test backup was not restored because inspection showed it also contained acceptance/obsolete dates.
- The September controlled upload records were moved out of top-level `/monitor_upload/incoming/` into `/monitor_upload/incoming/acceptance-test/`, preserving test evidence while keeping the processor's active input clean.
- The moved files included the Misuuni `2026-Q3-MID` acceptance record, the earlier Misuuni `AUTO` upload validation record, and two St Jude `2026-Q3-MID` controlled test records.

## After the test

1. Restore the controlled server to the authoritative production schedule. **Completed 2026-09-15.**
2. Explicitly identify and exclude/remove controlled acceptance uploads before production reporting. **Completed 2026-09-15 by moving them to `incoming/acceptance-test/`.**
3. Record the field result in project documentation. **Completed.**
4. Proceed to the first production-key-signed APK using the real production schedule.
5. Publish and test the final production-signed APK from the website; the debug-signed controlled package is not the production release.
