# ARES Sync Android MVP

ARES Sync is the replacement for the Automate/legacy-extension phone workflow.

## Validated pilot results

On the real pilot Android API 36 phone and tsavo3 server, manual connection to `ARES2` followed by the current-network test reaches `ares.local`, returns HTTP 200 from the scheduled collection endpoint, downloads the usage CSV, and saves it in app-private pending storage.

The guided teacher-assisted handoff was then validated on the real phone: the teacher selected the ARES Wi-Fi network through Android's system Wi-Fi UI, returned to ARES Sync, and the due usage file downloaded successfully. This validates the production-oriented handoff from system Wi-Fi selection through ARES server download.

Automatic Wi-Fi switching has been exhausted on this pilot device. The API 36 local-only request, API 30 `WifiNetworkSpecifier` compatibility path, API 28 direct `WifiManager` path, forced prior-network disable path, and Automate-owned exclusive-connect path all failed to produce a reliable automatic handoff to `ARES2`.

The central school registry and one-time enrollment service were validated live before the Android enrollment UI was added. The server resolves canonical schools, issues a unique device ID and credential after one-time-code enrollment, and rejects code reuse.

On 2026-09-07, version `0.5.0-school-enrollment` was validated on the real pilot phone against the pilot server formerly named `Tsavo3` and temporarily renamed `Misuni`. First-launch school enrollment completed successfully. The enrolled app then connected through the teacher-assisted `ARES2` handoff and correctly handled HTTP `204` when no collection was due. A temporary `TEST-DUE` collection dated 2026-09-07 was then added to the live server schedule; repeating the same phone flow returned HTTP `200` and identified the due collection as `TEST-DUE`. This validates that adding school enrollment did not break either the no-content or due-collection local-server paths.

A field UI issue was also identified during enrollment: when the teacher enters the enrollment code, the on-screen keyboard can cover the code-entry field. A future UI pass should ensure the form resizes or scrolls the active code field above the keyboard.

The live central endpoint was subsequently validated with per-device authentication. A device-authenticated synthetic upload was accepted and canonicalized to the enrolled school ID, and the exact retry returned `status: duplicate`. Version `0.6.0-central-upload` builds the corresponding automatic Android delivery path.

## First-launch school enrollment

Version `0.5.0-school-enrollment` added first-time device assignment before collection reminders begin.

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

## Current collection and delivery flow

ARES Sync targets API 36 and does not attempt to control Wi-Fi directly. Version `0.6.0-central-upload` uses this flow:

1. A collection date becomes due according to the phone's ARES collection schedule.
2. ARES Sync posts a reminder notification.
3. The teacher taps the reminder and then taps **Connect to ARES or ARES2 wifi network**.
4. ARES Sync opens Android's own Wi-Fi panel.
5. The teacher selects either `ARES2` or `ARES`.
6. When the teacher returns to ARES Sync, the app automatically tests the selected Wi-Fi for `http://ares.local/tracker/prepare_due_usage_upload.php`.
7. If the ARES server is reachable, the due CSV downloads into app-private `pending/` storage.
8. A successful local download marks that collection ID complete on the phone and cancels its collection reminder. Internet delivery is tracked separately so a temporary Internet outage does not make the teacher repeat the local collection.
9. ARES Sync queues one persistent WorkManager job for pending central delivery.
10. The upload job waits for network connectivity and also verifies that Android reports a validated Internet connection before attempting HTTPS delivery.
11. The app uploads each pending CSV to `https://areseducation.org/monitor_upload/` using its enrolled device ID and device credential. It uses the phone's default Internet network, not the special ARES Wi-Fi `Network` object used for the local download.
12. HTTP `201` / `stored` and HTTP `200` / `duplicate` are both treated as server acknowledgements. Only after one of those acknowledgements does the app move the local CSV from `pending/` to app-private `sent/` storage.
13. Transient network or server failures are retried with WorkManager backoff. Permanent HTTP errors leave the file in `pending/` for diagnosis rather than deleting it.
14. Pending upload work is re-enqueued when the app opens/resumes and after reboot.

The collection screen shows the number of files still pending Internet delivery.

The earlier **Collect using current Wi-Fi** button remains removed so the teacher has a single guided action for local collection.

## Central upload authentication

ARES Sync does not contain the global administrative upload key. It sends the unique enrollment identity issued to that phone:

```text
X-ARES-Device-ID: ARES-D-XXXXXXXXXXXX
X-ARES-Device-Credential: <device credential>
```

The central service authenticates those values against protected enrollment state and canonicalizes the uploaded filename to the enrolled `school_id`. This means an old local hostname such as `TSAVO3` cannot become the permanent central school identity.

The central filename contract accepts real quarterly collection IDs and `AUTO`. A temporary local test identifier such as `TEST-DUE` is useful for local collection testing but is intentionally not a production central-upload filename. End-to-end central-upload testing should therefore use `AUTO` or a real scheduled collection ID.

## 2026 collection schedule

The app schedule is maintained in `CollectionSchedule.java` and uses the `Africa/Nairobi` timezone. The pilot schedule may be temporarily adjusted during field testing; the repository version should be checked before production deployment.

Reminders are scheduled for 08:00 Africa/Nairobi on each due date using Android `AlarmManager`. They are date reminders, not exact-to-the-minute alarms. The app also checks for overdue incomplete collections when opened, so a missed alarm does not remove the collection from the workflow. Reminder alarms are rescheduled after reboot, but only for an enrolled phone.

## Permissions

The guided design deliberately removes the experimental Wi-Fi-control permissions. It requires:

- Internet access for HTTPS enrollment, central upload, and the local HTTP collection request;
- network-state access to identify the current Wi-Fi transport and confirm validated Internet for central delivery;
- boot-completed access to restore scheduled reminders and pending upload work after reboot; and
- notification permission on Android 13+ so due-date prompts can be shown.

ARES Sync does not request location permission or nearby-Wi-Fi control permission in this design because Android itself owns the Wi-Fi selection UI.

## Networking

Enrollment uses:

- `GET https://areseducation.org/monitor_upload/schools.php?q=<query>`
- `POST https://areseducation.org/monitor_upload/enroll.php`

Central delivery uses:

- `POST https://areseducation.org/monitor_upload/` as multipart field `usage_file`.

The local collection request continues to use the exact Wi-Fi `Network` selected by the teacher and calls the cleartext local hostname `ares.local`. Central HTTPS upload deliberately does not bind to that local network.

WorkManager `2.11.2` provides persistent constrained background delivery. The worker additionally requires `NET_CAPABILITY_INTERNET` and `NET_CAPABILITY_VALIDATED` on Android's active/default network before opening the central HTTPS connection.

## Build

Open `android/ares-sync` in Android Studio. The app uses JDK 17, `compileSdk = 36`, `targetSdk = 36`, and `minSdk = 29`.

GitHub Actions builds the debug APK with Gradle 8.13 and publishes it as the `ares-sync-debug-apk` workflow artifact.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, enrollment codes, device credentials, or private school registry data belong in this repository.
- `ARES2` and `ARES` selection is performed by the teacher through Android's system Wi-Fi UI; no Wi-Fi credential is embedded in the app.
- Central school lookup, enrollment, and usage upload use HTTPS.
- The global server upload key is not embedded in ARES Sync.
- The device credential is stored only in app-private state on the phone and is never shown in the normal UI.
- Pending CSVs are not removed before server acknowledgement; acknowledged files are retained in app-private `sent/` storage.
- Cleartext HTTP is permitted only for the local hostname `ares.local`.
