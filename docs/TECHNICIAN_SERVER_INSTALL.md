# ARES Usage Collection - Technician Server Installation

Use this procedure on an **existing ARES school server that already has the normal usage-tracking/reporting system working**. It does not install or repair the base ARES usage tracker.

## What the installer adds

The installer adds the school-side components needed by ARES Sync:

- `/usr/local/sbin/ares_prepare_usage_upload.sh`
- `/etc/ares/usage-upload.conf`
- `/mnt/sda3/var/www/tracker/prepare_usage_upload.php`
- `/mnt/sda3/var/www/tracker/prepare_due_usage_upload.php`
- `/mnt/sda3/var/www/tracker/collection_schedule.json` when one is not already present
- `/mnt/sda3/var/www/tracker/uploads/`
- `/etc/sudoers.d/ares-usage-export`

It validates the shell/PHP files, strictly validates the production collection schedule, verifies the existing report builder and CSV before making changes, backs up files it replaces, validates the sudoers entry, and by default runs an `AUTO` export smoke test. The smoke test reports the exact current CSV size and rejects a file above the central service's 2 MiB limit.

## Before installation

Confirm all of the following:

1. The existing usage report builder works:
   ```bash
   sudo /usr/local/sbin/ares_build_reports.sh
   ```
2. The source report exists and is not empty:
   ```bash
   ls -lh /mnt/sda3/var/www/tracker/reports/combined_usage.csv
   ```
3. The server already serves `http://ares.local/` to phones connected to `ARES` or `ARES2`.
4. You know the school's stable ARES school ID. Prefer the canonical central ID such as `ARES-S0016` rather than an old hostname.
5. `local-server/collection_schedule.json` has been reviewed and is the approved schedule for this installation. The installer preserves an existing server schedule unless `--replace-schedule` is explicitly supplied.

## Recommended rollout update

Copy the centrally approved, vetted release folder to the school server. Do not assemble an update from individual files. Change into the release-folder root and run:

```bash
sudo bash local-server/update_school_server.sh --school-code ARES-S00XX
```

Replace `ARES-S00XX` with the school's assigned ID.

The update command intentionally replaces the server's collection schedule with the approved schedule in the release folder. It backs up the existing schedule and every other replaced component first. Stop if the folder's schedule has not been approved for production.

For a server whose PHP-FPM worker does not run as `www-data`, specify the correct account:

```bash
sudo bash local-server/update_school_server.sh \
  --school-code ARES-S00XX \
  --web-user PHP_USER
```

Use `--help` to see the update behavior. The underlying `install_usage_collection.sh --help` lists path overrides for nonstandard school servers.

For a first installation where an already-reviewed local schedule must be preserved, use the base installer instead:

```bash
sudo bash local-server/install_usage_collection.sh --school-code ARES-S00XX
```

## Expected result

A successful install ends with:

```text
ARES usage-collection server installation complete.
```

and an `AUTO export smoke test passed` message unless the smoke test was deliberately skipped.

The result also includes, for example:

```text
Measured usage CSV: 184320
```

Record this byte count in the rollout log. This is the approximate payload before small multipart/HTTPS overhead. A retry can send the whole file again.

The script also reports the backup directory it created under:

```text
/var/backups/ares-usage-collection/
```

## Post-install checks

### 1. Confirm installed files

```bash
ls -l /usr/local/sbin/ares_prepare_usage_upload.sh
cat /etc/ares/usage-upload.conf
ls -l /mnt/sda3/var/www/tracker/prepare_due_usage_upload.php
ls -l /mnt/sda3/var/www/tracker/collection_schedule.json
ls -ld /mnt/sda3/var/www/tracker/uploads
```

The configuration file must not contain passwords, OAuth tokens, central upload credentials, or phone enrollment credentials.

### 2. Measure the current payload exactly

The installer reports this automatically. To measure it again later without generating or uploading anything:

```bash
stat -c '%s bytes' /mnt/sda3/var/www/tracker/reports/combined_usage.csv
```

The result must be greater than zero and no more than `2097152` bytes (2 MiB). Until representative measurements are collected, use 5 MB per scheduled collection as the teacher's conservative mobile-data allowance; that covers the maximum accepted file, secure-transfer overhead, and one full retry.

### 3. Confirm normal state-aware no-due behavior

A bare request to `prepare_due_usage_upload.php` does not contain the phone's completion state. If earlier scheduled collections are already past, the bare request may legitimately return the earliest due collection rather than HTTP `204`.

To reproduce the app's normal request, pass the latest collection already completed on the phone. For a freshly enrolled phone in September 2026, for example:

```bash
curl -sS -D - -o /dev/null \
  "http://ares.local/tracker/prepare_due_usage_upload.php?last_completed=2026-Q2-END"
```

Before the approved Term 3 mid-term due date, the expected response is HTTP `204` with:

```text
X-ARES-Reason: no-due-collection
```

### 4. Controlled collection test

For acceptance testing only, back up `collection_schedule.json`, make one valid production collection ID (for example `2026-Q3-MID`) due on the test date, then use ARES Sync to collect it. Do not use `TEST-DUE`, because the central production filename contract intentionally rejects that identifier.

After the test, restore the approved schedule. A phone used in a controlled test that marked a future production collection complete must also be uninstalled/data-cleared and freshly enrolled before real deployment.

## Re-running the installer

The installer is designed to be safely re-run:

- replaced component files and configuration are backed up first;
- an existing `collection_schedule.json` is preserved by default;
- use `--replace-schedule` only when intentionally deploying a new approved schedule.

The recommended `update_school_server.sh` command always supplies `--replace-schedule`, because a rollout update must put the vetted schedule and server components on the same release.

## If the update fails

1. Do not start phone enrollment on that server.
2. Save the complete terminal output and the backup-directory path printed by the installer.
3. Correct the reported prerequisite or contact ARES technical support.
4. Re-run the same update command only after the cause is understood.

The installer performs all prerequisite checks before it begins backups or replacements. If a later installation step fails, the prior files remain in the timestamped backup directory under `/var/backups/ares-usage-collection/`; restoration should be directed by ARES technical support so the component set and schedule stay consistent.

## Scope

A successful server installation proves only the school-side collection endpoint and CSV export path. Phone enrollment and central HTTPS delivery are validated separately through the teacher acceptance test.
