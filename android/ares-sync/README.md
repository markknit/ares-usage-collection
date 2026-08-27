# ARES Sync Android MVP

ARES Sync is the replacement for the Automate/legacy-extension phone workflow.

## Validated pilot results

On the real pilot Android API 36 phone and tsavo3 server, manual connection to `ARES2` followed by the current-network test reaches `ares.local`, returns HTTP 200 from the scheduled collection endpoint, downloads the usage CSV, and saves it in app-private pending storage.

The guided teacher-assisted handoff was then validated on the real phone: the teacher selected the ARES Wi-Fi network through Android's system Wi-Fi UI, returned to ARES Sync, and the due usage file downloaded successfully. This validates the production-oriented handoff from system Wi-Fi selection through ARES server download.

Automatic Wi-Fi switching has been exhausted on this pilot device. The API 36 local-only request, API 30 `WifiNetworkSpecifier` compatibility path, API 28 direct `WifiManager` path, forced prior-network disable path, and Automate-owned exclusive-connect path all failed to produce a reliable automatic handoff to `ARES2`.

## Current MVP architecture: teacher-assisted Wi-Fi handoff

ARES Sync targets API 36 and does not attempt to control Wi-Fi directly. The production-oriented flow is:

1. A collection date becomes due according to the phone's ARES collection schedule.
2. ARES Sync posts a reminder notification.
3. The teacher taps the reminder and then taps **Connect to ARES or ARES2 wifi network**.
4. ARES Sync opens Android's own Wi-Fi panel.
5. The teacher selects either `ARES2` or `ARES`.
6. When the teacher returns to ARES Sync, the app automatically tests the selected Wi-Fi for `http://ares.local/tracker/prepare_due_usage_upload.php`.
7. If the ARES server is reachable, the due CSV downloads into app-private pending storage.
8. A successful download marks that collection ID complete on the phone and cancels its reminder.
9. The teacher can reconnect the phone to its normal Internet Wi-Fi. Central HTTPS upload remains a later milestone.

The earlier **Collect using current Wi-Fi** button has been removed so the teacher has a single guided action for collection.

## 2026 collection schedule

The app schedule matches the repository's canonical `local-server/collection_schedule.json` and uses the `Africa/Nairobi` timezone:

- `2026-Q3-MID` — 2026-08-14
- `2026-Q3-END` — 2026-09-25
- `2026-Q4-MID` — 2026-11-06
- `2026-Q4-END` — 2026-12-11

The real tsavo3 pilot endpoint previously reported `2026-Q3-MID` with a server due date of 2026-08-03. That deployed-server mismatch must be reconciled separately; the app intentionally follows the repository schedule rather than the stale/mismatched pilot value.

Reminders are scheduled for 08:00 Africa/Nairobi on each due date using Android `AlarmManager`. They are date reminders, not exact-to-the-minute alarms. The app also checks for overdue incomplete collections when opened, so a missed alarm does not remove the collection from the workflow. Reminder alarms are rescheduled after reboot.

## Permissions

The guided design deliberately removes the experimental Wi-Fi-control permissions. It requires:

- Internet access for the local HTTP request;
- network-state access to identify the current Wi-Fi transport;
- boot-completed access to restore scheduled reminders after reboot; and
- notification permission on Android 13+ so due-date prompts can be shown.

ARES Sync does not request location permission or nearby-Wi-Fi control permission in this design because Android itself owns the Wi-Fi selection UI.

## Build

Open `android/ares-sync` in Android Studio. The app uses JDK 17, `compileSdk = 36`, `targetSdk = 36`, and `minSdk = 29`.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, or school-private data belong in this repository.
- `ARES2` and `ARES` selection is performed by the teacher through Android's system Wi-Fi UI; no Wi-Fi credential is embedded in the app.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; future central upload traffic must use HTTPS.
