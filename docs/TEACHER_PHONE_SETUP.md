# ARES Sync - Teacher Phone Setup and Regular Use

> **Current guide:** This detailed engineering-era setup note is retained for history. Teachers and rollout staff should use [ARES Sync - Teacher Installation and Use Guide](TEACHER_PHONE_GUIDE.md) or its [printable PDF](../output/pdf/ARES_Sync_Teacher_Guide.pdf). The current guide directs teachers to their ARES Advocate or ARES technical-support contact for the required one-time installation key.

This guide is for a teacher or school user setting up ARES Sync on an Android phone.

## First-time setup

1. While the phone has normal internet access, open the official ARES Education phone-setup page.
2. Tap **Download ARES Sync**.
3. Open the downloaded APK.
4. If Android says the browser or Files app is not allowed to install apps:
   - tap **Settings** or **Allow from this source**;
   - allow installation for the app you used to open the ARES APK;
   - go back to the installer and tap **Install**.
5. If Android or Play Protect shows a second warning with a hidden **More details** or similar option, expand it and choose **Install anyway** only if the APK came from the official ARES Education setup page or directly from an ARES technician. Wording varies by phone.
6. Do not disable Play Protect globally. After ARES Sync is installed, you may turn off **Allow from this source** again.
7. Open **ARES Sync**.
8. Search for your school and select the exact school name.
9. Enter the one-time enrollment code supplied by ARES staff.
10. Tap **Enroll this phone**.
11. ARES Sync opens **Enable automatic ARES Wi-Fi**. Android will ask whether ARES Sync may suggest Wi-Fi networks. Choose **Allow**. This is a one-time app-level approval; there is no separate **Save network** sheet for ARES2 or ARES.
12. Android may then ask for **Nearby Wi-Fi devices** access. Choose **Allow**. On Android 12L or older, Android may label the equivalent permission as **Location** even though ARES Sync does not use it to determine the phone's physical location.
13. Android may ask you to approve a direct connection to **ARES2** or **ARES**. Approve the school network shown. This prepares ARES Sync to reach the local school server for a scheduled collection even when another saved Wi-Fi network has internet access.
14. If Android asks for permission to show notifications, choose **Allow**.

The phone is now ready. ARES Sync stores the school assignment and phone credential privately on the device. It registers the open **ARES2** and **ARES** networks with Android as Wi-Fi suggestions and also prepares app-specific local access for scheduled collections. ARES Sync does not store a Wi-Fi password because the school networks are open.

Keep the phone's normal internet Wi-Fi networks saved. ARES Sync's direct school-network request is intended only for its local collection traffic and does not require teachers to forget their normal networks.

If automatic Wi-Fi suggestion approval is declined, Android may require ARES Sync to be re-enabled under **Special app access > Wi-Fi control** before suggestions can be used again.

## Normal use

Most of the time, no action is required. ARES Sync should show:

- the school name;
- the next scheduled collection date;
- **Everything is ready. No action required.**

ARES Sync does not need to remain open.

When a collection is due, ARES Sync first tries any Wi-Fi connection already available to the app. If that cannot reach `ares.local`, ARES Sync can request a temporary local-only connection to **ARES2** or **ARES** and send the collection request specifically over that network. The separate internet connection is left available for normal internet traffic where Android and the phone hardware support concurrent connections.

Android stores approval for a particular access point after the user approves a specific network request. A different mesh access point may still require Android to ask again. This behavior must be field-validated at each deployment pattern before it is treated as fully unattended.

## When a collection is due

ARES Sync first tries to reach the school ARES server silently.

If the phone is already connected to the school ARES network and the server is reachable, the usage collection can complete without teacher action.

If the phone is connected to another internet-capable Wi-Fi network, ARES Sync can request its own local connection to ARES2 or ARES and use that connection only for the school-server request. If Android has already approved the same access point for ARES Sync, the request may complete without another prompt. If Android shows a network approval prompt, approve the school ARES network.

If the first scheduled attempt occurs while the phone is away from school or cannot reach `ares.local`, ARES Sync keeps the collection retryable. When the phone later reaches the school network, a later retry can complete the collection.

If ARES Sync still asks for help:

1. Open ARES Sync.
2. Tap **Connect to school Wi-Fi** or **Set up automatic ARES Wi-Fi**, depending on the message shown.
3. Approve **ARES2** or **ARES** if Android presents a network request.
4. If automatic access still fails, use Android's normal Wi-Fi screen to connect to **ARES2** or **ARES** manually.
5. Return to ARES Sync; the app checks the school server and collects any due usage report.
6. After collection, the report remains safely stored in ARES Sync until normal internet access becomes available.

## Automatic delivery

When normal internet access later becomes available, ARES Sync sends pending usage data automatically in the background. You do not need to keep the app open.

In the app:

- **Usage data: up to date** means nothing is waiting to be sent.
- **waiting to send when Internet is available** means a collection is safely stored on the phone and will upload later.
- **upload needs attention** means the phone should be connected to normal internet and ARES Sync reopened. Contact ARES support if the message remains.

## Important notes

- Do not uninstall ARES Sync after enrollment unless ARES staff instructs you to. Uninstalling removes that phone's enrollment and requires a new one-time enrollment code.
- Do not share enrollment codes between schools.
- Install ARES Sync only from the official ARES Education setup page or from an ARES technician.
- ARES Sync does not require Round Sync, Automate, MacroDroid, rclone, Google Drive setup, or manual file handling.
