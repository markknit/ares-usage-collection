# ARES Sync Rollout Runbook

Use this runbook to prepare and execute a controlled school rollout of ARES Sync. It links the approved release artifacts, school-server update, phone installation, evidence to record, and rollback decisions.

## Current rollout classification

The production portal, production-signed APK installation, enrollment, automatic ARES/ARES2 setup, controlled due collection, deferred HTTPS upload, and school-server components have passed their recorded acceptance tests.

This is suitable for a **controlled rollout with named ARES support**, not yet an unsupported mass rollout. Before relying on the system for unattended production reporting, complete or explicitly accept the open gates in [Deployment Status](DEPLOYMENT_STATUS.md):

1. schedule the central incoming processor against the live protected directories;
2. prove or explicitly accept the autonomous Android alarm-timing limitation;
3. test repeat local-network requests on the same AP and a second mesh BSSID;
4. test a later same-key APK as an in-place upgrade; and
5. preserve the current APK and server release package for rollback.

## Approved phone release

| Item | Approved value |
|---|---|
| Version | `0.8.0-rc15` |
| versionCode | `23` |
| APK filename | `ares-sync.apk` |
| APK size | `6300531` bytes |
| APK SHA-256 | `16e5eef24b56dde1db3fbd0e5be542c5853f329841ae056bc1dd7afb6bf773a8` |
| Public setup page | `https://areseducation.org/phone-setup/` |

Do not replace the APK during an active rollout without treating it as a new release and repeating the release checklist.

## Roles

- **Release owner:** approves the exact APK, server release folder, production schedule, and rollback copies.
- **Central operator:** confirms protected upload storage and the scheduled incoming processor are healthy.
- **ARES technician / Advocate:** updates the school server, installs and enrolls the teacher phone, records non-secret evidence, and provides first-line support.
- **Teacher:** keeps ARES Sync installed, leaves notifications allowed, and contacts the ARES Advocate when the app says it needs attention.

## Gate 1 - central service

Before enrolling rollout phones, the central operator must confirm:

- enrolled-device HTTPS upload is available;
- incoming and archive directories are protected and have sufficient free space;
- controlled acceptance files remain outside the live processor input;
- the incoming processor runs on an approved schedule and reports failures to a named operator;
- a current backup exists for enrollment state and other irreplaceable central configuration; and
- the reporting command is either enabled and verified or deliberately deferred with an owner and date.

Do not put central paths, credentials, enrollment state, or school registry data in this public repository or in rollout notes.

## Gate 2 - school server

Use the centrally approved release folder. At the school, confirm the normal ARES usage report already works, then run:

```bash
sudo bash local-server/update_school_server.sh --school-code ARES-S00XX
```

Follow [Technician Server Installation](TECHNICIAN_SERVER_INSTALL.md) for prerequisites, nonstandard PHP users, verification, and recovery.

Record only:

- canonical school name and `ARES-S00XX` ID;
- release commit or release-folder identifier;
- update date and technician;
- pass/fail result;
- backup-directory path printed by the installer;
- measured CSV byte count printed by the smoke test; and
- any non-secret follow-up note.

Stop the rollout at that school if the update fails, the measured CSV is zero, or it exceeds `2097152` bytes.

## Gate 3 - teacher phone

Use [Technician Installation and Teacher Handoff](TECHNICIAN_PHONE_INSTALL.md). Give the teacher [ARES Sync - Teacher Installation and Use Guide](TEACHER_PHONE_GUIDE.md), printed or electronically.

The technician must:

1. generate the one-time key from the protected staff portal;
2. install only from the official phone-setup page;
3. select the exact canonical school;
4. approve the Android prompts for automatic school-network access;
5. wait for the app to return to the main screen; and
6. verify the school, next collection date, ready state, up-to-date state, and completed Wi-Fi setup before leaving.

Never record an installation key, staff password, device credential, or teacher-private phone data in the rollout log.

## Data allowance and exact measurement

ARES Sync uploads the school CSV, not the 6.3 MB installer, at each scheduled collection. The central service rejects an individual CSV above 2 MiB.

Until measurements from representative schools are available, budget **5 MB per scheduled collection**. This covers the maximum accepted file, secure-transfer overhead, and one complete retry. With six scheduled collections, budget **30 MB per teacher phone per year**, excluding initial installation and future APK updates.

Measure a school's current CSV without sending it:

```bash
stat -c '%s bytes' /mnt/sda3/var/www/tracker/reports/combined_usage.csv
```

Record the byte count for each school. After the first production collection, compare the source size, central received size, and retry count before reducing the allowance.

## First-wave monitoring

For the first controlled wave, use a small set of schools with named technicians. On each collection date, confirm:

- the phone advances to the next approved collection;
- the app returns to `Usage data: up to date.` after normal Internet becomes available;
- the central processor accepts the file once and no unexpected file remains in incoming;
- the filename identifies the correct school and collection; and
- the reporting output includes the school exactly once.

Do not ask a teacher to send screenshots containing installation keys or private credentials. A screenshot of the non-secret main status screen is acceptable when needed for support.

## Stop and escalate

Stop enrollment or collection at the affected school and contact the named ARES support owner when:

- the server updater fails or the CSV exceeds 2 MiB;
- the app shows the wrong school or collection date;
- Android offers no safe path to install the official APK;
- automatic school-network setup does not complete and the documented manual fallback fails;
- a pending file remains after validated Internet is available; or
- the central service rejects, duplicates, misidentifies, or cannot process a file.

Preserve non-secret logs and exact error text. Do not repeatedly generate enrollment keys or delete pending/central files as an improvised fix.

## Rollback

- **Phone:** do not install an older APK over a newer one unless it is an approved, same-key rollback and Android permits the version transition. If uninstalling is required, enrollment is erased and a new one-time key will be needed.
- **School server:** stop phone rollout, preserve terminal output, and use the timestamped backup under `/var/backups/ares-usage-collection/` only under ARES technical direction.
- **Central service:** stop scheduled processing before restoring state or moving files. Preserve rejected and incoming files until the incident owner decides their disposition.
- **Public portal:** restore only a privately retained, approved APK and verify its hash after publishing.

## Closeout

After each rollout wave, the release owner reviews school measurements, failures, Android variants, central processing, and support requests. Expand the next wave only after open incidents have owners and no issue can cause silent loss, duplication, or attribution of school usage data.
