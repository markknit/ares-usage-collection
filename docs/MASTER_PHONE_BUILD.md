# Master phone build

## Current Round Sync limitation

The released Round Sync task interface supports **Copy** and **Sync**, but not **Move**. For the ARES workflow, use a **Copy** task and move successfully uploaded files into a local `Download/ARES_Usage_Sent` folder with Automate after upload confirmation. Do not delete the local file until the Google Drive copy has been verified.

## Pilot build sequence

1. Install the approved Round Sync APK.
2. Create these local folders on the phone:
   - `Download/ARES_Usage`
   - `Download/ARES_Usage_Sent`
3. Configure the Google Drive remote named `ARESGoogleDrive`.
4. Create one Round Sync **Copy** task:
   - Source: `Download/ARES_Usage`
   - Destination: `ARESGoogleDrive:ARES Usage Uploads/Incoming`
   - Keep only ARES usage and setup-test files in the source folder so no task filter is required.
5. Chrome currently downloads the CSV into the general `Download` folder. During manual testing, move the CSV into `Download/ARES_Usage`, restart Round Sync if the new file is not visible, and then run the task.
6. Confirm the file appears in Google Drive.
7. Manually move the successfully uploaded pilot file to `Download/ARES_Usage_Sent`.
8. Test failed connectivity and confirm the source file remains available for a later retry.
9. Copy the tested Round Sync task ID from the task's three-dot menu.
10. Export the complete Round Sync configuration as `ARES-RoundSync-Config.zip`.
11. Install Automate by LlamaLab.
12. Create and validate a minimal Automate flow that launches the tested Round Sync task.
13. Add internet detection, download-folder handling, success/failure notification handling, and sent-folder archiving only after the minimal launch flow is stable.
14. Export one Automate flow per school after full validation.

## Validated Automate launch configuration

The working Automate flow uses an **App start** block, not **Service start** and not **App start shortcut**.

Connect:

```text
Flow beginning -> App start
```

Configure the App start block with these values in expression (`fx`) mode:

```text
Package:
"de.felixnuesse.extract"

Activity class:
"ca.pkay.rcloneexplorer.Activities.ShortcutServiceActivity"

Action:
"START_TASK"

Extras:
{
  "task" as Long: TASK_IDn
}
```

Replace `TASK_ID` with the numeric Round Sync task ID. For example, task ID `12` becomes:

```text
{
  "task" as Long: 12n
}
```

The trailing `n` is required so Automate passes the task ID as a Long, matching the Round Sync shortcut activity. The package name must be exactly `de.felixnuesse.extract`; the truncated value `de.felixnuesse.extra` causes `ActivityNotFoundException`.

This flow was validated on the pilot phone: Automate launched the pinned-equivalent Round Sync task and the pending CSV was copied to Google Drive successfully.

## Remaining automation work

Build the remaining flow in small validated stages:

1. Detect restored internet connectivity and launch the validated App start block.
2. Monitor Round Sync success and failure notifications using stable unique text fragments.
3. Move downloaded `ARES_USAGE_*.csv` files from the general `Download` folder into `Download/ARES_Usage`.
4. After confirmed success only, move the uploaded file into `Download/ARES_Usage_Sent`.
5. Test offline failure, delayed retry, duplicate handling, phone restart, and battery restrictions.
6. Export the tested Automate flow and Round Sync configuration for deployment.

The exact Round Sync task ID must be copied from the tested task. Round Sync configuration exports include application settings, tasks, triggers, and remotes; use the app's export feature rather than hand-editing its internal files.

The success-notification text must be confirmed on the actual pilot phone before Automate is configured to archive files. Match notifications from Round Sync specifically, and test both successful and failed uploads before enabling automatic file movement.
