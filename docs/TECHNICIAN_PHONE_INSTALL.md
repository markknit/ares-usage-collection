# ARES Sync - Technician Rollout Installation and Teacher Handoff

Use this guide when an ARES technician or ARES Advocate performs a fresh ARES Q4 v1.10 school
installation, then helps a teacher install and enroll ARES Sync. The server package installs without
Internet at the school. Normal Internet or mobile data is still required for central phone
enrollment, and at least one school network named **ARES** or **ARES2** must be in range.

## What ARES Sync does

ARES Sync collects the school's scheduled ARES usage-summary file from the local ARES server. It stores the file privately on the phone until validated Internet is available, then sends it securely to ARES Education. It does not require daily teacher action.

ARES Sync does **not** read the teacher's messages, contacts, photos, documents, or browsing history. On older Android versions, Android may label the Wi-Fi permission as Location; ARES Sync does not use it to determine the phone's physical location.

## Before visiting the teacher

- Obtain the complete, centrally approved `ARES_Q4_Offline_v0.93_amd64_v1.10.zip`. Do not assemble a school package from individual files.
- Confirm you have local administrator access to the Ubuntu 24.04 AMD64 school server.
- Confirm the canonical school name and `ARES-S00XX` ID.
- Confirm the school has an ARES Advocate or other named support contact.
- Bring the official setup address: `https://areseducation.org/phone-setup/`.
- Do not send staff passwords, administrator keys, device credentials, or stored enrollment data to the teacher.

## What you need at the school

- The teacher's Android phone, with sufficient battery and storage.
- Terminal access to the school server and its assigned canonical `ARES-S00XX` ID.
- The complete v1.10 field ZIP and its SHA-256 checksum.
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

## 1. Install and verify the school server

Complete this section before installing ARES Sync on the teacher's phone.

1. Copy the complete v1.10 field ZIP to the server and extract it.
2. Change into the extracted directory.
3. Run `sudo bash preflight.sh ARES-S00XX`, replacing the example with the final or approved provisional school code.
4. Do not continue unless the preflight ends with `READY TO INSTALL: 0 failures`.
5. Run `sudo bash install_offline.sh ARES-S00XX` with the same code.
6. When the installer pauses, open `http://ares.local:3001/login`, create the first Lesson3 Site Administrator, store the credentials securely, then return to the terminal and type `READY`.
7. Enter the Site Administrator credentials when prompted. The installer imports the approved corpus and verifies 95 lesson plans and 806 lessons before continuing.
8. Wait for `ARES Q4 offline installation completed successfully` and record the installation-log path printed by the installer.
9. Sign in to Lesson3 and open sample plans from several subjects. Confirm the plans show Official version `1.0.0`.
10. Confirm `http://ares.local/app_install/` and `http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf` open from the school network.

The installer deploys the Lesson Plan module, Lesson3 v0.93 and its approved JSON corpus, tracking
mappings, ARES Sync usage collection, the approved local APK, `ares.local`, and the school-code
reassignment command. It also installs Tailscale and TigerVNC packages but leaves them stopped,
disabled, and unregistered. It disables the base-image `x11vnc` service. Remote access is activated
later only for an authorized support session with `sudo ares-enable-remote-access`.

The Tsavo Trust module is not included in v1.10; use its separately reviewed installer when it is
ready.

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
