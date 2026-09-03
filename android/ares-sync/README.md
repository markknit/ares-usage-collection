# ARES Sync Android MVP

ARES Sync is the replacement for the Automate/legacy-extension phone workflow.

## Validated pilot results

On the real pilot Android API 36 phone and tsavo3 server, manual connection to `ARES2` followed by the current-network test reaches `ares.local`, returns HTTP 200 from the scheduled collection endpoint, downloads the usage CSV, and saves it in app-private pending storage.

The guided teacher-assisted handoff was then validated on the real phone: the teacher selected the ARES Wi-Fi network through Android's system Wi-Fi UI, returned to ARES Sync, and the due usage file downloaded successfully. This validates the production-oriented handoff from system Wi-Fi selection through ARES server download.

Automatic Wi-Fi switching has been exhausted on this pilot device. The API 36 local-only request, API 30 `WifiNetworkSpecifier` compatibility path, API 28 direct `WifiManager` path, forced prior-network disable path, and Automate-owned exclusive-connect path all failed to produce a reliable automatic handoff to `ARES2`.

The central school registry and one-time enrollment service were validated live before the Android enrollment UI was added. The server resolves canonical schools, issues a unique device ID and credential after one-time-code enrollment, and rejects code reuse.

## First-launch school enrollment

Version `0.5.0-school-enrollment` adds first-time device assignment before collection reminders begin.

The setup flow is:

1. The teacher opens ARES Sync while the phone has normal Internet access.
2. The teacher types part of the school name and taps **Find school**.
3. ARES Sync calls the live HTTPS school-search endpoint and displays canonical matches.
4. The teacher selects the exact school and enters the school's one-time enrollment code.
5. ARES Sync posts the canonical `school_id`, code, and phone model label to the HTTPS enrollment endpoint.
6. A successful enrollment stores the returned canonical school name, stable school ID, unique device ID, and device credential in app-private `SharedPreferences`.
7. The enrollment screen disappears and the normal collection screen becomes active.
8. Collection alarms and notifications are not scheduled until enrollment is complete.

The app never stores the teacher's free-form search text as school identity. Only a canonical server-returned `school_id` can be enrolled.

The current beta stores the device credential in private app storage using `Context.MODE_PRIVATE`. Android application backup is disabled in the manifest. Production credential hardening can be revisited independently without changing the enrollment protocol.

## Current MVP architecture: teacher-assisted Wi-Fi handoff

ARES Sync targets API 36 and does not attempt to control Wi-Fi directly. After enrollment, the collection flow is:

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

The app schedule is maintained in `CollectionSchedule.java` and uses the `Africa/Nairobi` timezone. The pilot schedule may be temporarily adjusted during field testing; the repository version should be checked before production deployment.

Reminders are scheduled for 08:00 Africa/Nairobi on each due date using Android `AlarmManager`. They are date reminders, not exact-to-the-minute alarms. The app also checks for overdue incomplete collections when opened, so a missed alarm does not remove the collection from the workflow. Reminder alarms are rescheduled after reboot, but only for an enrolled phone.

## Permissions

The guided design deliberately removes the experimental Wi-Fi-control permissions. It requires:

- Internet access for HTTPS enrollment and the local HTTP collection request;
- network-state access to identify the current Wi-Fi transport;
- boot-completed access to restore scheduled reminders after reboot; and
- notification permission on Android 13+ so due-date prompts can be shown.

ARES Sync does not request location permission or nearby-Wi-Fi control permission in this design because Android itself owns the Wi-Fi selection UI.

## Networking

Enrollment uses:

- `GET https://areseducation.org/monitor_upload/schools.php?q=<query>`
- `POST https://areseducation.org/monitor_upload/enroll.php`

These requests run on a worker executor rather than the Android UI thread. Redirects are deliberately not followed so a server rewrite/configuration error is surfaced instead of silently changing an API request.

The existing local collection request continues to use the exact Wi-Fi `Network` selected by the teacher and calls the cleartext local hostname `ares.local`.

## Build

Open `android/ares-sync` in Android Studio. The app uses JDK 17, `compileSdk = 36`, `targetSdk = 36`, and `minSdk = 29`.

GitHub Actions builds the debug APK with Gradle 8.13 and publishes it as the `ares-sync-debug-apk` workflow artifact.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, enrollment codes, device credentials, or private school registry data belong in this repository.
- `ARES2` and `ARES` selection is performed by the teacher through Android's system Wi-Fi UI; no Wi-Fi credential is embedded in the app.
- Central school lookup and enrollment use HTTPS.
- The device credential is stored only in app-private state on the phone and is never shown in the normal UI.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; central traffic must use HTTPS.
