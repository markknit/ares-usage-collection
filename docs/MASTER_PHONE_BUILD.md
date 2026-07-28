# Master phone build

## Current Round Sync limitation

The released Round Sync task interface supports **Copy** and **Sync**, but not **Move**. For the ARES workflow, use a **Copy** task and move successfully uploaded files into a local `Download/ARES-Usage-Sent` folder with MacroDroid after upload confirmation. Do not delete the local file until the Google Drive copy has been verified.

## Pilot build sequence

1. Install the approved Round Sync APK.
2. Create these local folders on the phone:
   - `Download/ARES-Usage`
   - `Download/ARES-Usage-Sent`
3. Configure the Google Drive remote named `ARESGoogleDrive`.
4. Create one Round Sync **Copy** task:
   - Source: `Download/ARES-Usage`
   - Destination: `ARESGoogleDrive:ARES Usage Uploads/Incoming`
   - Keep only ARES usage and setup-test files in the source folder so no task filter is required.
5. Run the task manually and confirm the file appears in Google Drive.
6. Manually move the successfully uploaded pilot file to `Download/ARES-Usage-Sent`.
7. Test failed connectivity and confirm the source file remains available for a later retry.
8. Copy the tested Round Sync task ID from the task's three-dot menu.
9. Export the complete Round Sync configuration as `ARES-RoundSync-Config.zip`.
10. In MacroDroid, build no more than five macros so the free edition remains usable:
    - Schedule refresh and reminder calculation.
    - Due/overdue reminder.
    - ARES Wi-Fi connected: retrieve the schedule, select the due collection, and save the CSV to `Download/ARES-Usage`.
    - Internet connected: launch the Round Sync task intent.
    - Round Sync success notification: move uploaded files to `Download/ARES-Usage-Sent`, then show completion status.
11. Store school variables: school code, SSID, local URL, schedule URL, Round Sync task ID, pending folder, and sent folder.
12. Export one `.macro` file per school.

The exact Round Sync task ID must be copied from the tested task and inserted into the MacroDroid intent action. Round Sync configuration exports include application settings, tasks, triggers, and remotes; use the app's export feature rather than hand-editing its internal files.

The success-notification text must be confirmed on the actual pilot phone before MacroDroid is configured to archive files. Match notifications from Round Sync specifically, and test both successful and failed uploads before enabling automatic file movement.
