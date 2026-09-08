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

Before the clean test, decide which collection schedule is authoritative. The pilot Misuuni server and repository schedule have previously differed, so do not treat either copy as automatically correct.

For the acceptance test, use a valid production-style collection ID such as `2026-Q3-MID`. Do not use `TEST-DUE` for an end-to-end central upload test.

## 3. Prepare the server installation package

Use the `android-central-upload-field-validation` branch until the clean acceptance test is complete.

The package must include:

- `local-server/install_usage_collection.sh`;
- `local-server/ares_prepare_usage_upload.sh`;
- `local-server/prepare_usage_upload.php`;
- `local-server/prepare_due_usage_upload.php`;
- the reviewed `local-server/collection_schedule.json`.

The technician will run the installer from the repository/release root.

## 4. Publish the ARES Sync test APK on the ARES website

The updated setup portal expects this relative file:

```text
assets/downloads/ares-sync.apk
```

Before the teacher test:

1. Take the exact APK built from the validated `android-central-upload-field-validation` branch.
2. Record its SHA-256 hash.
3. Rename/copy the approved test APK to `ares-sync.apk` in the website's `assets/downloads/` directory.
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

## 8. Acceptance-test stopping points

Do not change the ARES Sync UI during this clean test. Record problems as they occur.

The test should stop and be diagnosed if any of these checkpoints fail:

1. technician installer completes and `AUTO` smoke export is generated;
2. phone downloads and installs ARES Sync from the ARES website;
3. fresh school enrollment succeeds;
4. no-due collection returns HTTP `204` when expected;
5. due collection returns HTTP `200` and one pending central file appears;
6. app is left in the background and normal internet is restored;
7. central upload completes without reopening ARES Sync to trigger it;
8. central server acknowledges the upload and pending count returns to zero.

## Known follow-up items not to hide during the test

- The collection schedule currently exists in both the Android app and school server. A single source of truth still needs to be designed.
- Android does not yet pass `last_completed` to the school endpoint even though the endpoint supports it.
- The new HTTPS incoming directory is validated, but final central reporting/processing still needs to be reconciled with the older rclone-based processor.
- The ARES Sync user interface needs simplification after the functional acceptance test.
