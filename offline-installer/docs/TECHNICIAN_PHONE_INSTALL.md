# ARES Sync - Technician Rollout Installation and Teacher Handoff

Use this guide when an ARES technician or ARES Advocate prepares a school server, then helps a teacher install and enroll ARES Sync.

## What changed for offline school installations

The approved production ARES Sync APK is now bundled into the ARES Q4 Offline package and copied to the school server. A teacher connected to the school ARES network can install the app without Internet access by opening:

`http://ares.local/app_install/index.html`

The direct APK is also available at:

`http://ares.local/downloads/ares-sync.apk`

The local install page is intentionally named `app_install` rather than a generic `install` path to reduce accidental discovery by users who do not need to install the app.

Keep `index.html` in the link. Some ARES servers route directory addresses through
the file manager; the explicit filename opens the installation page directly.
The administrator can use `/app_install/index.html` for an entry at the end of
the teacher section. Adding that menu entry is a separate server-content edit.

The one-time installation key is still supplied by ARES staff. Installing the APK itself does not require Internet. If the current ARES Sync enrollment process needs to contact the central ARES enrollment service, normal Internet or mobile data is required when the teacher enrolls the phone.

## Before visiting the teacher

- Use the centrally approved ARES Q4 Offline field ZIP. Do not assemble a school package from individual files.
- Confirm the school server's existing usage report works and that you have administrator access.
- Confirm the canonical school name and `ARES-S00XX` ID.
- Obtain or be able to generate the teacher's one-time installation key from the protected ARES staff enrollment system.
- Use the normal master command below; it checks the package and prerequisites automatically.

## 1. Install and verify the school server

1. Copy the complete offline field ZIP to the server and extract it into a new folder.
2. Open a terminal in the extracted `ARES_Q4_Offline_...` directory and run:

   ```bash
   sudo bash install_offline.sh ARES-S00XX
   ```

   Replace `ARES-S00XX` with the school's final or approved provisional code.
   The installer checks the package and server automatically. No separate
   preflight or manual checksum command is needed.
3. When prompted, open `http://ares.local:3001/login`, create the first Lesson3
   Site Administrator, and store the credentials. Return to the terminal, type
   `READY`, then enter the administrator email and password when asked.
4. Wait for `ARES Q4 offline installation completed successfully`. The installer
   imports and verifies 95 lesson plans and 806 lessons and installs Tsavo Trust.
5. If asked to activate remote support, press Enter for No during an offline
   installation. A warning about unavailable remote support does not invalidate
   a successful core installation. Save the installation log path printed on screen.
6. From another device on the school network, open `http://ares.local`, check
   Lesson Plans and the Lesson3 login, and open Tsavo Trust and play a video.
   Confirm `http://ares.local/app_install/index.html` opens before setting up teacher phones.

If the package check fails, copy the complete ZIP again and extract it into a new
folder. For any other installation failure, stop and send ARES support the printed
installation log. Do not run individual component installers to work around it.

Remote-support preparation is attempted after the core installation succeeds.
It may require additional server prerequisites; its failure leaves the completed
offline installation usable. ARES support can arrange preparation and activation
later. Activation needs outbound Internet on the server. See `docs/REMOTE_ACCESS.md`.

The bundled Internet Lockdown v1.4.2 project is prepared afterward, with activation
and reboot persistence left as separate choices. Confirm/select the actual
student-side LAN if prompted. Existing active or boot-enabled lockdown is
preserved and its upgrade is deferred; optional remote preparation is also
deferred in that case. If setup needs prerequisites or later attention, core
ARES installation remains successful. See `docs/INTERNET_LOCKDOWN.md` and the
supplied operating PDF under `/opt/ares/internet-lockdown/ares-lockdown-v1.4.2/`.

Initial release acceptance is handled by ARES build/support staff using
`docs/PROFILE_ACCEPTANCE.md` and `docs/LESSON3_V094_ACCEPTANCE.md`. Technicians do
not repeat the build qualification procedure at each school. A warning alone is
not evidence of failure; an installation error or failed browser check needs support.

## 2. Generate the one-time installation key

1. On a trusted ARES staff device with Internet access, open the protected enrollment portal.
2. Confirm the teacher's school and canonical `ARES-S00XX` ID.
3. Generate the one-time installation/enrollment code.
4. Keep it private and use it only for the intended phone.

The teacher guide calls this an **installation key**. The app or staff portal may call it an **enrollment code**. They are the same one-time value.

## 3. Install ARES Sync from the school server

1. Connect the teacher's Android phone to the local ARES or ARES2 school network.
2. In Chrome, open `http://ares.local/app_install/index.html`.
3. Tap **Download ARES Sync for Android**.
4. Open `ares-sync.apk` from the download notification or browser Downloads list.
5. If Android blocks installation from Chrome or Files, open the offered Settings page and enable **Allow from this source** only for the app being used to open the APK.
6. Allow a Play Protect/app scan if offered. Do not disable Play Protect globally.
7. Tap **Install**, then **Open**.

The APK download and installation can be completed while the school has no Internet connection.

## 4. Enroll the phone

1. If enrollment requires central verification, connect the phone to normal Internet or enable mobile data before this step.
2. In ARES Sync, find and select the exact school.
3. Enter the one-time installation key from ARES staff.
4. Select **Enroll this phone**.
5. If enrollment fails, verify the selected school, Internet availability, and code. Do not generate multiple replacement keys blindly.

## 5. Approve school-network access

After enrollment, approve the Android prompts required by ARES Sync:

- network suggestions;
- Nearby Wi-Fi devices (or the older Android Location-equivalent permission);
- ARES or ARES2 connection approval if requested; and
- notifications.

Wait for setup to return to the main screen.

## 6. Verify the completed installation

Before leaving, confirm that the app shows the correct school and a normal ready/up-to-date state. Also verify that the server's usage-collection endpoint and report generation remain operational.

## Teacher explanation

Explain that ARES Sync normally works in the background. On scheduled collection dates it obtains the school's usage-summary file from the local ARES server. When normal Internet later becomes available, it sends any pending file securely to ARES Education.

Tell the teacher:

- Keep ARES Sync installed and notifications enabled.
- A new phone or reinstallation requires a new one-time installation key.
- Contact the ARES Advocate if the app shows the wrong school, repeatedly needs attention, or fails to return to the ready state.
- The local page `http://ares.local/app_install/index.html` is for installing/reinstalling ARES Sync while connected to the school ARES network.

## Quick troubleshooting

### `ares.local/app_install/index.html` does not open

- Confirm the phone is connected to ARES or ARES2.
- On the server, test `curl -I -H 'Host: ares.local' http://127.0.0.1/app_install/index.html`.
- Confirm `/mnt/sda3/var/www/app_install/index.html` exists.

### APK will not download

- Confirm `/mnt/sda3/var/www/downloads/ares-sync.apk` exists and is nonempty.
- Test `curl -I -H 'Host: ares.local' http://127.0.0.1/downloads/ares-sync.apk`.

### Android will not install the APK

- Confirm it came from the local ARES server.
- Allow installation from the specific browser/Files source when Android asks.
- Complete the recommended app scan.
- Do not disable Play Protect globally.

### Enrollment fails

- The offline APK installation may be complete even when enrollment cannot yet reach the central ARES service.
- Restore normal Internet/mobile data, verify the exact school, and retry the same valid code before issuing another one.
