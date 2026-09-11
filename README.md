# ARES Usage Collection

This repository contains the Android, school-server, central HTTPS upload, and reporting components for ARES Education usage-data collection.

## Current production architecture

The validated workflow is:

1. ARES Sync is enrolled to one canonical school using a one-time school enrollment code.
2. On a scheduled collection date, ARES Sync attempts a silent download from the local school server over `ARES` / `ARES2` using `http://ares.local/`.
3. The downloaded CSV is stored in the app-private pending directory on the phone.
4. When validated Internet access becomes available later, ARES Sync uploads the pending CSV to the central HTTPS service at `https://areseducation.org/monitor_upload/` using its per-device credential.
5. The central service stores the file in protected local incoming storage.
6. `central-monitoring/process_incoming.py` validates and archives accepted files locally, deduplicates by SHA-256, quarantines invalid/conflicting files, and can trigger the reporting command after new files are accepted.

Round Sync and phone-side rclone are no longer part of the production data path. Older Round Sync/Downloads references are legacy documentation and should not be used for new deployments.

## Main components

- `android/ares-sync/` - ARES Sync Android application.
- `local-server/` - school-server installer, local export wrapper, due-collection endpoint, and schedule.
- `central-monitoring/web-upload/` - HTTPS upload, school search, enrollment, and device-authentication service.
- `central-monitoring/process_incoming.py` - local incoming-file processor for the central server.
- `public/` - teacher-facing setup portal assets.
- `docs/` - technician, acceptance, deployment, and workflow documentation.
- `tests/` - portal, upload/enrollment, and central processor tests.

## Central incoming processor

The HTTPS upload service writes accepted CSVs to a protected local `incoming` directory. Process them with:

```bash
python3 central-monitoring/process_incoming.py \
  --incoming /path/to/monitor_upload/incoming \
  --archive /path/to/ares-archive \
  --state /path/to/processed.json \
  --report-command '/path/to/report-command'
```

Accepted files are archived as:

```text
<archive>/<collection>/<school>/<filename>
```

Behavior:

- filename must match the ARES usage filename contract;
- content must be a plausible CSV;
- SHA-256 is used for content deduplication;
- exact-content duplicates are removed from incoming safely;
- invalid files and filename conflicts are moved to a quarantine directory instead of deleted;
- state is written atomically after each accepted file;
- the optional report command runs once after one or more new files are accepted.

The default quarantine path is a sibling `rejected/` directory next to `incoming/`. Use `--rejected` to override it.

No rclone configuration or cloud credentials are required by the processor.

## Validate

Run the focused local tests with:

```bash
python3 -m unittest -v tests/test_process_incoming.py
python3 tools/validate_portal.py
python3 tests/test_portal.py
php tests/test_web_upload.php
php tests/test_enrollment.php
```

The Android build is validated by the `ARES Sync Android` GitHub Actions workflow.

## Production schedule

The approved 2026 production schedule currently includes:

- `2026-Q1-MID` - 2026-02-16
- `2026-Q1-END` - 2026-03-25
- `2026-Q2-MID` - 2026-06-15
- `2026-Q2-END` - 2026-07-24
- `2026-Q3-MID` - 2026-10-15
- `2026-Q3-END` - 2026-11-25

The Android and school-server copies of this schedule must remain aligned until a single authoritative schedule source is implemented.

## Security

Never commit passwords, OAuth tokens, live `rclone.conf` files, Round Sync exports containing active credentials, device credentials, enrollment administrator secrets, enrollment state, live school registries, or private school data.
