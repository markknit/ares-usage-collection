# ARES Sync - Technician Rollout Installation and Teacher Handoff

Use this guide when an ARES technician or ARES Advocate prepares a school server, then helps a teacher install and enroll ARES Sync. Complete both parts at the school, with normal Internet available and at least one school network named **ARES** or **ARES2** in range.

## What ARES Sync does

ARES Sync collects the school's scheduled ARES usage-summary file from the local ARES server. It stores the file privately on the phone until validated Internet is available, then sends it securely to ARES Education. It does not require daily teacher action.

ARES Sync does **not** read the teacher's messages, contacts, photos, documents, or browsing history. On older Android versions, Android may label the Wi-Fi permission as Location; ARES Sync does not use it to determine the phone's physical location.

## Before visiting the teacher

- Obtain the centrally approved ARES usage-collection release folder. Do not assemble an update from individual files.
- Confirm the school server's existing usage report works and that you have administrator access.
- Confirm the canonical school name and `ARES-S00XX` ID.
- Confirm the school has an ARES Advocate or other named support contact.
- Bring the official setup address: `https://areseducation.org/phone-setup/`.
- Do not send staff passwords, administrator keys, device credentials, or stored enrollment data to the teacher.

## What you need at the school

- The teacher's Android phone, with sufficient battery and storage.
- Terminal access to the school server and its assigned canonical `ARES-S00XX` ID.
- Normal Internet through mobile data or Internet-capable Wi-Fi.
- ARES or ARES2 within range.
- Access to the protected ARES staff enrollment portal.
- The teacher's permission to install the app and approve the required Android prompts.

## If the final school ID is not assigned yet

- Install the server package with a unique provisional code such as `PENDING-SRV001`; use the server's asset identifier so it remains traceable.
- Record which physical server received that provisional code.
- Do **not** enroll a teacher's phone while the server still has a provisional code.
- After ARES assigns the canonical ID, run `sudo ares-set-school-code ARES-S00XX` on the server.
- Continue only after the command reports reassignment complete and its verified `AUTO` filename contains the final ID.

<!-- pagebreak -->

## 1. Update and verify the school server

Complete this section before installing ARES Sync on the teacher's phone.

1. Copy the complete, centrally approved `ares-usage-collection` release folder to the school server.
2. Open a terminal, change into the root of that release folder, and confirm that `local-server/update_school_server.sh` is present.
3. Confirm the existing report source is present and nonempty at `/mnt/sda3/var/www/tracker/reports/combined_usage.csv`.
4. Run `sudo bash local-server/update_school_server.sh --school-code ARES-S00XX`, replacing `ARES-S00XX` with the school's assigned canonical ID.
5. If the server's PHP worker does not use `www-data`, add `--web-user PHP_USER` with the correct account.
6. Wait for `ARES usage-collection server installation complete.` and `AUTO export smoke test passed`.
7. Record the backup-directory path and measured CSV byte count printed by the updater.
8. Confirm that the measured file is greater than zero and no more than `2097152` bytes.
9. Follow the post-install checks in `docs/TECHNICIAN_SERVER_INSTALL.md`, including the state-aware due-endpoint check.

The updater validates the approved production schedule and existing report path before changing installed files. It backs up replaced components, installs the export wrapper, PHP endpoints, production schedule, configuration, upload directory, and scoped sudoers entry, then generates a test export.

If any check fails, stop. Do not enroll a teacher's phone until the server problem is understood and the update passes. Keep the terminal output and backup path for ARES technical support; do not improvise by deleting server or phone data.

## 2. Generate the one-time installation key

1. On your own trusted device, open the protected ARES staff enrollment portal.
2. Sign in with the shared staff password.
3. Search for the school and confirm both its canonical name and `ARES-S00XX` ID.
4. Select **Generate one-time code**.
5. Keep the displayed `XXXX-XXXX` code private and use it immediately on the teacher's phone.
6. Sign out of the staff portal when finished.

The teacher guide calls this an **installation key**. The app and staff portal may call it an **enrollment code**. They are the same one-time value. It works for only one phone enrollment. Never record it in GitHub, a shared document, or an unsecured message.

If the portal reports that an unused code already exists, do not replace it automatically. Replace it only when the earlier code is lost or must be revoked.

<!-- pagebreak -->

## 3. Download and install ARES Sync

1. Keep the phone connected to normal Internet.
2. In Chrome, open `https://areseducation.org/phone-setup/`.
3. Select **Start phone setup**, then **Download ARES Sync**.
4. Open `ares-sync.apk` from the browser's Downloads list or notification.
5. If Android asks which installer to use, select **Android installer**.
6. If Android blocks installation from the browser or Files app, open **Settings**, enable **Allow from this source** for that app, return to the installer, and continue.
7. If Android recommends an app scan, allow the scan. Continue only after it passes.
8. If Play Protect presents a different warning, use **More details** or the equivalent and install only after confirming the APK came from the official ARES page.
9. Never disable Play Protect globally.
10. Select **Install**, then **Open**.

Android wording varies by phone. Stop and contact ARES technical support if Android offers no safe path to install the official APK.

## 4. Enroll the phone

1. In ARES Sync, type at least two letters of the school name and select **Find school**.
2. Select the exact canonical school. Verify the school with the teacher before continuing.
3. Enter the eight-character installation key. The app inserts the hyphen automatically.
4. Select **Enroll this phone**.

If enrollment fails, do not generate multiple keys blindly. Recheck the selected school, Internet connection, and code. A used code cannot be reused.

## 5. Approve automatic school-network access

After enrollment, ARES Sync starts one-time Wi-Fi setup. Approve each prompt that appears:

1. Allow ARES Sync to suggest Wi-Fi networks.
2. Allow **Nearby Wi-Fi devices**. On older Android versions, allow the equivalent Location permission.
3. Approve a connection to ARES or ARES2 when Android asks.
4. Allow notifications when requested.

ARES Sync may try both ARES2 and ARES. Wait for it to finish. A successful setup returns automatically to the main screen.

## 6. Verify the completed installation

Do not leave until the main screen shows all of the following:

- the correct school name;
- the next approved collection date;
- **Everything is ready. No action required.**
- **Usage data: up to date.**
- a status stating that automatic school Wi-Fi setup is complete.

If the next collection date is already past or the app reports a pending collection during a new rollout, stop and verify the production schedule before proceeding.

<!-- pagebreak -->

## 7. Explain the system to the teacher

Use this short explanation:

> ARES Sync normally works in the background. On scheduled dates it collects a small usage-summary file from the school ARES server. It may briefly use ARES or ARES2 for that local collection. When the phone later has normal Internet, it sends the file securely to ARES Education. You do not need to open the app every day.

Tell the teacher:

- Keep the app installed and keep notifications allowed.
- Keep the phone's normal Internet Wi-Fi networks saved.
- Approve ARES or ARES2 if Android asks again at a different school access point.
- **Usage data: up to date** means there is nothing waiting to send.
- **Waiting to send when Internet is available** is normal; connect to normal Internet and allow the app time to send.
- Contact the school's ARES Advocate if the app says **needs attention**, repeatedly asks for help, shows the wrong school, or does not return to the ready state.
- A new phone or a reinstallation requires a new one-time installation key.

## Mobile-data guidance

The uploaded item is the school's CSV usage-summary file, not the 6 MB installer. The server currently rejects any usage file larger than 2 MiB. Actual files are expected to be much smaller, but representative production files must be measured during rollout.

Until measurements are recorded, budget **5 MB per scheduled collection**. This covers the 2 MiB technical ceiling, HTTPS overhead, and one full retry. With six scheduled collections, a conservative annual allowance is **30 MB per teacher phone**, excluding initial app download and future app updates.

Whenever possible, let pending files upload over ordinary Internet Wi-Fi. ARES Sync may also use mobile data when that is the phone's validated Internet connection.

## Installation record

Record only non-secret rollout information:

- School name and ID: ______________________________
- Server update passed: Yes / No
- Server backup path: ______________________________
- Measured CSV size in bytes: ______________________
- Teacher or assigned phone: _______________________
- Phone model and Android version: _________________
- Installation date: _______________________________
- Technician / ARES Advocate: ______________________
- Next collection date shown: ______________________
- Final ready state confirmed: Yes / No
- Notes or follow-up: ______________________________

Do not record the one-time installation key, staff password, device credential, or other secret.

<!-- pagebreak -->

## Quick troubleshooting

### School-server update fails

- Stop before enrolling the teacher's phone.
- Preserve the complete terminal output and any backup-directory path shown.
- Confirm that the approved release folder is complete, the school ID is correct, and the existing report builder and source CSV are available.
- Do not restore, delete, or replace server files manually; contact ARES technical support with the non-secret error text.

### Download will not start

- Confirm normal Internet is working.
- Reload the official setup page.
- Check browser download permissions and free storage.

### Android will not install the APK

- Confirm the APK came from the official ARES page.
- Allow installation from the browser or Files app being used.
- Complete the recommended scan.
- Do not disable Play Protect globally.

### School is not found or enrollment fails

- Confirm normal Internet is available.
- Search using only part of the school name.
- Verify the canonical school and ID in the staff portal.
- Generate a new key only if the earlier key was used, lost, or intentionally revoked.

### Automatic Wi-Fi setup does not finish

- Confirm ARES or ARES2 is in range.
- Allow Nearby Wi-Fi devices and network suggestions.
- Approve the Android request for ARES or ARES2.
- Use **Connect to school Wi-Fi** as the manual fallback, then return to ARES Sync.

### A pending file does not send

- Connect the phone to validated normal Internet.
- Open ARES Sync once and wait several minutes.
- If **needs attention** remains, record the non-secret status message and contact ARES technical support.
