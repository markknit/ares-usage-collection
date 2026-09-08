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

It validates the shell/PHP files, validates the collection schedule JSON, backs up files it replaces, validates the sudoers entry, and by default runs an `AUTO` export smoke test.

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

## Install

Transfer a current copy of the `ares-usage-collection` repository/release folder to the server, change into its root directory, then run:

```bash
sudo bash local-server/install_usage_collection.sh --school-code ARES-S00XX
```

Replace `ARES-S00XX` with the school's assigned ID.

For a server whose PHP-FPM worker does not run as `www-data`, specify the correct account:

```bash
sudo bash local-server/install_usage_collection.sh \
  --school-code ARES-S00XX \
  --web-user PHP_USER
```

Use `--help` to see path overrides and test options.

## Expected result

A successful install ends with:

```text
ARES usage-collection server installation complete.
```

and an `AUTO export smoke test passed` message unless the smoke test was deliberately skipped.

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

### 2. Confirm normal no-due behavior

While the schedule has no collection due today, a phone/browser connected to the school ARES network should receive HTTP `204` from:

```text
http://ares.local/tracker/prepare_due_usage_upload.php
```

### 3. Controlled collection test

For acceptance testing only, back up `collection_schedule.json`, make one valid production collection ID (for example `2026-Q3-MID`) due on the test date, then use ARES Sync to collect it. Do not use `TEST-DUE`, because the central production filename contract intentionally rejects that identifier.

After the test, restore the approved schedule.

## Re-running the installer

The installer is designed to be safely re-run:

- replaced component files and configuration are backed up first;
- an existing `collection_schedule.json` is preserved by default;
- use `--replace-schedule` only when intentionally deploying a new approved schedule.

## Scope

A successful server installation proves only the school-side collection endpoint and CSV export path. Phone enrollment and central HTTPS delivery are validated separately through the teacher acceptance test.
