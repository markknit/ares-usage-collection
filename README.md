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
- `local-server/` - one-command school-server updater, safe school-code reassignment command, installer, local export wrapper, due-collection endpoint, and schedule.
- `central-monitoring/web-upload/` - HTTPS upload, school search, enrollment, and device-authentication service.
- `central-monitoring/process_incoming.py` - local incoming-file processor for the central server.
- `public/` - teacher-facing setup portal assets.
- `docs/` - technician, acceptance, deployment, and workflow documentation.
- `tests/` - portal, upload/enrollment, and central processor tests.
- `offline-installer/internet-lockdown/` - complete owner-supplied Internet Lockdown v1.4.2 project and original handoff; [installer integration](offline-installer/docs/INTERNET_LOCKDOWN.md).

## Phone rollout guides

For the local ARES school-server download workflow, use the refreshed offline
copies (revision 2026-11-01):

- [Teacher installation and user manual](output/pdf/offline/ARES_Sync_Teacher_Guide.pdf) - 2 pages.
- [Technician installation and handoff manual](output/pdf/offline/ARES_Sync_Technician_Guide.pdf) - 3 pages.

These use the explicit local page `http://ares.local/app_install/index.html`.
Their sources are `offline-installer/docs/TEACHER_PHONE_GUIDE.md` and
`offline-installer/docs/TECHNICIAN_PHONE_INSTALL.md`. Regenerate with:

```bash
python3 offline-installer/tools/render_rollout_guides.py --source-dir offline-installer/docs --output-dir output/pdf/offline
```

To publish them on an existing server, transfer both PDFs into the `ares` user's
Downloads folder, then run on the Ubuntu server:

```bash
sudo install -m 0644 -o ares -g www-data \
  /mnt/sda3/home/ares/Downloads/ARES_Sync_Teacher_Guide.pdf \
  /mnt/sda3/home/ares/Downloads/ARES_Sync_Technician_Guide.pdf \
  /mnt/sda3/var/www/downloads/
```

The direct server links are `/downloads/ARES_Sync_Teacher_Guide.pdf` and
`/downloads/ARES_Sync_Technician_Guide.pdf`. The teacher PDF covers both phone
installation and ordinary use and is the appropriate teacher-section manual link.
This copy procedure does not run the server installer or edit the admin module.

The owner subsequently supplied a final admin page, Admin_tools entry and manual
for grouped deployment by the normal installer. That approved manual is served
at `/admin/ARES_Sync_User_Guide.pdf` inside the existing password-protected admin
folder. See [approved admin content](offline-installer/admin-content/README.md).

General Internet-download guidance remains available separately:

- [Technician server update, phone installation, and teacher handoff](docs/TECHNICIAN_PHONE_INSTALL.md) ([printable PDF](output/pdf/ARES_Sync_Technician_Guide.pdf))
- [Teacher installation and use guide](docs/TEACHER_PHONE_GUIDE.md) ([printable PDF](output/pdf/ARES_Sync_Teacher_Guide.pdf))
- [Technician school-server installation and update guide](docs/TECHNICIAN_SERVER_INSTALL.md)
- [Controlled rollout runbook](docs/ROLLOUT_RUNBOOK.md)

Rebuild both PDFs after editing either Markdown source:

```bash
python3 tools/build_rollout_guides.py
```

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
python3 -m unittest -v tests/test_server_installer.py
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
