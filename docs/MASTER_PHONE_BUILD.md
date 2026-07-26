# Master phone build

1. Install the approved Round Sync APK.
2. Configure the common OneDrive remote.
3. Create one task using **Move**, source `Download/ARES-Usage`, destination `ARES-OneDrive:ARES Usage Uploads/Incoming`, with an include filter for `ARES_USAGE_*.csv` and `ARES_SETUP_TEST_*.txt`.
4. Schedule the task every two hours and permit any connected network.
5. Run successful and failed-connectivity tests.
6. Export the complete Round Sync configuration as `ARES-RoundSync-Config.zip`.
7. In MacroDroid, build no more than five macros so the free edition remains usable:
   - Schedule refresh and reminder calculation.
   - Due/overdue reminder.
   - ARES Wi-Fi connected: retrieve schedule, select due collection, download CSV.
   - Internet connected: launch Round Sync task intent.
   - Pending-file check and completion notification.
8. Store school variables: school code, SSID, local URL, schedule URL, Round Sync task ID, local folder.
9. Export one `.macro` file per school.

The exact Round Sync task ID must be copied from the tested task and inserted into the MacroDroid intent action. Round Sync configuration exports include application settings, tasks, triggers, and remotes; use the app's export feature rather than hand-editing its internal files.
