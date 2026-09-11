# ARES Usage Collection - Clean Acceptance Test Preparation

Use this checklist before beginning a clean second-school acceptance test.

## 1. Choose the test school/server

Select a different existing ARES school server that already has the normal usage-tracking/reporting system installed and working.

Record, outside the public repository:

- canonical school name;
- canonical central school ID (`ARES-S00XX`);
- server hostname for technician access;
- whether the school uses `ARES2`, `ARES`, or both.

Confirm the school exists in the protected central school registry before generating an enrollment code. Do not commit the protected registry or private school data.

## 2. Approve the collection schedule for the test

The school-server installer can install `local-server/collection_schedule.json`, but the dates must be reviewed first.

The current 2026 production schedule uses mid-term and end-term collections for Terms 1, 2, and 3. The Android app and school-server schedule must remain aligned until a single authoritative schedule source is implemented.

For controlled acceptance testing, use a valid production-style collection ID such as `2026-Q3-MID`. Do not use `TEST-DUE` for an end-to-end central upload test.

## 3. Prepare the server installation package

The package must include:

- `local-server/install_usage_collection.sh`;
- `local-server/ares_prepare_usage_upload.sh`;
- `local-server/prepare_usage_upload.php`;
- `local-server/prepare_due_usage_upload.php`;
- the reviewed `local-server/collection_schedule.json`.

The technician will run the installer from the repository/release root.

Windows checkouts must preserve Unix LF line endings for shell scripts. The repository `.gitattributes` file enforces LF for `*.sh` and `*.bash` files.

## 4. Publish the ARES Sync test APK on the ARES website

The updated setup portal expects this relative file:

```text
assets/downloads/ares-sync.apk
```

Before the teacher test:

1. Take the exact APK built from the validated production candidate branch.
2. Record its SHA-256 hash.
3. Rename/copy the approved APK to `ares-sync.apk` in the website's `assets/downloads/` directory.
4. Deploy the updated `public/index.html`, `public/setup.html`, existing stylesheet assets, and the APK under a stable ARES Education website path.
5. Open the page on an Android phone and confirm that **Download ARES Sync** actually downloads the APK.

The APK is not currently stored in the public GitHub repository and must not be assumed to exist merely because the HTML link is present.

## 5. Choose the live website URL

The public ARES Education home page is live, but the new phone-setup portal has not yet been deployed there.

Use a dedicated path that does not disturb the main website, for example:

```text
https://areseducation.org/phone-setup/
```

Whatever path is chosen should remain stable enough to print/share with teachers later.

## 6. Prepare enrollment for the test phone

After selecting the school:

1. Verify the school search endpoint returns the expected canonical school.
2. Use the existing central `enrollment_admin_key` to generate a new one-time code for that school.
3. Keep the administrator key private. Only the short one-time enrollment code is given to the teacher/tester.
4. Use a fresh Android installation (a different phone, or uninstall/reinstall ARES Sync) so the first-run enrollment flow is genuinely tested.
5. On first enrollment, ARES Sync marks schedule entries strictly before the enrollment date as historical/completed. It then sends the latest completed collection as `last_completed` when it asks the school server for a due collection.

## 7. Confirm the test server prerequisites

Before running the installer, verify on the second server:

```bash
sudo /usr/local/sbin/ares_build_reports.sh
ls -lh /mnt/sda3/var/www/tracker/reports/combined_usage.csv
```

Also confirm a phone on `ARES`/`ARES2` can resolve and reach:

```text
http://ares.local/
```

If PHP-FPM does not run as `www-data`, identify the actual PHP/web worker account so it can be supplied to the installer with `--web-user`.

## 8. State-aware no-due check

A bare request to `prepare_due_usage_upload.php` has no phone completion state. If earlier scheduled collections are already past, a bare request is expected to return the earliest due collection.

To reproduce the app's normal no-due request, pass the phone's latest completed collection. For example, after a fresh September 2026 enrollment where Term 1 and Term 2 are historical:

```bash
curl -sS -D - -o /dev/null \
  "http://ares.local/tracker/prepare_due_usage_upload.php?last_completed=2026-Q2-END"
```

Before the Term 3 mid-term due date, the expected response is HTTP `204` with:

```text
X-ARES-Reason: no-due-collection
```

## 9. Acceptance-test stopping points

Do not change the ARES Sync UI during a clean functional test. Record problems as they occur.

The test should stop and be diagnosed if any of these checkpoints fail:

1. technician installer completes and `AUTO` smoke export is generated;
2. phone downloads and installs ARES Sync from the ARES website;
3. fresh school enrollment succeeds;
4. state-aware no-due request returns HTTP `204` when no later collection is due;
5. due collection returns HTTP `200` and one pending central file appears;
6. app is left in the background and normal internet is restored;
7. central upload completes without reopening ARES Sync to trigger it;
8. central server acknowledges the upload and pending count returns to zero.

## Validated school-side acceptance checkpoint

A clean second-server installation was validated on 2026-09-10 without recording school-private data in the repository. The following passed:

- existing usage report builder produced populated `combined_usage.csv`;
- `ares.local` was reachable on the school network;
- automated installer completed and generated an `AUTO` smoke export;
- PHP/nginx `prepare_usage_upload.php?collection=AUTO` returned HTTP `200` and a populated CSV;
- state-aware `prepare_due_usage_upload.php?last_completed=2026-Q2-END` returned HTTP `204` and `X-ARES-Reason: no-due-collection` before the next scheduled collection.

The initial transferred shell script had Windows CRLF line endings; `.gitattributes` was added afterward to enforce LF endings for future checkouts.

## Validated phone-side silent collection checkpoint

On 2026-09-10, a freshly enrolled acceptance-test phone was connected to the school ARES network with a controlled `2026-Q3-MID` collection due. After the overdue scheduler path ran, the app showed exactly one file pending central upload and advanced the next scheduled collection to `2026-11-25`.

That state validates the silent local collection path through the background worker: successful local download, completion marking for `2026-Q3-MID`, queuing of one pending central upload, and advancement to the next collection. The background worker does not update the foreground status text with a manual-download-style "downloaded" message, so the pending-upload count and advanced next date are the expected success indicators.

The exact delivery timing of the inexact Android alarm was not independently validated by this checkpoint; `setAndAllowWhileIdle()` may be deferred by Android. The functional overdue/silent collection path is validated.

## Validated end-to-end phone upload checkpoint

On 2026-09-10, after the successful silent local collection above, the phone was returned from the ARES school network to normal Internet access. The pending usage file was then uploaded successfully to the central HTTPS service.

This completes the functional end-to-end acceptance path for the current design:

- fresh phone enrollment to a canonical school;
- historical-period baselining through `last_completed`;
- silent local collection over the ARES network;
- app-private pending-file storage;
- completion/next-date advancement after a successful local download;
- deferred central delivery after validated Internet access becomes available.

The visible `/Downloads/ares_usage/prepare_due_usage_upload.php` file observed during testing is legacy residue from the older browser/Downloads workflow. The current Android collection client stores the live pending CSV under the app-private `files/pending/` directory and does not use `/Downloads/ares_usage` for the central-upload path.

## Production reset after controlled acceptance testing

The controlled September 10 due-date override exists only on the frozen acceptance snapshot and must not be deployed to production. The production schedule remains:

- `2026-Q3-MID`: 2026-10-15
- `2026-Q3-END`: 2026-11-25

Any school server used for the controlled test must have its approved production schedule restored before real use. Any phone used for the controlled test must be uninstalled/data-cleared and freshly enrolled with the production APK before it is used for the real October collection, because the acceptance test marked `2026-Q3-MID` complete in that phone's local state.

## Known follow-up items not to hide during productization

- The collection schedule currently exists in both the Android app and school server. A single source of truth still needs to be designed.
- The new HTTPS incoming directory is validated, but final central reporting/processing still needs to be reconciled with the older rclone-based processor.
- The ARES Sync user interface needs simplification after the functional acceptance test.
