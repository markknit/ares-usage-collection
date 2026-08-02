# Deployment Status

## tsavo3 pilot school server

Validated on 2026-07-27.

### Role

`tsavo3` is the pilot school-side ARES server and usage-data source. It is not yet the production central processor or public setup portal host.

### Installed components

- `/usr/local/sbin/ares_prepare_usage_upload.sh`
- `/etc/ares/usage-upload.conf`
- `/mnt/sda3/var/www/tracker/prepare_usage_upload.php`
- `/mnt/sda3/var/www/tracker/collection_schedule.json`
- `/mnt/sda3/var/www/tracker/uploads/`
- `/etc/sudoers.d/ares-usage-export`

The runtime configuration and sudoers file are server-local and are not stored in this repository.

### Current pilot identifier

- Host: `tsavo3`
- School/export code: `TSAVO3`
- Report source: `/mnt/sda3/var/www/tracker/reports/combined_usage.csv`
- Local export endpoint: `http://ares.local/tracker/prepare_usage_upload.php?collection=AUTO`
- Collection schedule: `http://ares.local/tracker/collection_schedule.json`
- Cloud incoming folder: `ARES Usage Uploads/Incoming`
- Phone pending folder: `Download/ARES_Usage`
- Phone sent folder: `Download/ARES_Usage_Sent`
- Phone automation and upload app: Automate by LlamaLab
- Current upload architecture: Automate native Google Drive upload block

### Validation completed

- Repository portal validation passed for two configured schools.
- Static portal tests passed.
- Export shell script passed `bash -n` syntax validation.
- PHP endpoint passed `php -l` syntax validation.
- Existing report builder completed successfully.
- Timestamped CSV export was generated in the tracker uploads directory.
- Exported CSV contained the expected header and usage records.
- SHA-256 metadata was generated.
- Nginx/PHP request returned HTTP 200.
- Response content type was CSV.
- Response supplied a timestamped `ARES_USAGE_TSAVO3_AUTO_*.csv` filename.
- Downloaded CSV size matched the generated report.
- Android phone successfully downloaded the expected timestamped CSV from `ares.local` while connected to the ARES network.
- MacroDroid was rejected for the pilot because unattended free use requires recurring advertisement-based renewal or a paid upgrade.
- Automate by LlamaLab was installed successfully and opened without requiring an upgrade or recurring advertisement renewal.
- The Automate network block was tested with internet unavailable. The flow waited at the network check and, without a second manual start, resumed automatically when internet connectivity was restored.
- Automate's native Google Drive upload block successfully uploaded a pilot CSV from `Download/ARES_Usage` to the central Google Drive incoming folder.
- The direct Automate upload test confirmed that Round Sync is not required for the target phone architecture.
- The complete direct upload path was validated using these Automate blocks in sequence:
  1. `Flow beginning`
  2. `Data network default` with `Proceed: Immediately`
  3. `Data network default` with `Proceed: When changed`
  4. `File exists`
  5. `Google Drive upload`
  6. `File move`
  7. `Toast show`
- With internet already available, the immediate `Data network default` path proceeded without waiting for a connectivity transition.
- With internet initially unavailable, the second `Data network default` block waited and then resumed automatically after connectivity returned.
- `File exists` prevented an upload attempt when the configured pending CSV was absent.
- `Google Drive upload` completed successfully to `ARES Usage Uploads/Incoming`.
- `File move` ran only from the successful output of `Google Drive upload` and moved the uploaded CSV from `Download/ARES_Usage` to `Download/ARES_Usage_Sent`.
- The success `Toast show` block executed after the file move completed.

### Superseded pilot path

Round Sync was installed and validated during the initial pilot. The following tests remain useful historical evidence but are no longer part of the target deployment architecture:

- Round Sync connected directly to Google Drive through the `ARESGoogleDrive` remote.
- A pinned Round Sync home-screen shortcut successfully launched the upload task.
- Automate successfully launched a Round Sync task through an App start block.
- The Automate-triggered Round Sync task copied a pending CSV to Google Drive.
- Notification-based Round Sync success and failure detection was explored but is no longer required.

Do not continue building new deployment logic around Round Sync unless the native Automate Google Drive implementation fails later acceptance testing.

### Next milestone

Add and validate the scheduled collection-download workflow:

1. Detect the configured ARES Wi-Fi network both when already connected and when connected later.
2. Check whether a collection is due inside the approved date window.
3. Request the usage CSV from `ares.local` and save it directly into `Download/ARES_Usage`.
4. Pass the exact downloaded file path into the validated direct upload flow.
5. Prevent duplicate collection downloads and repeated uploads.
6. Test offline failure, delayed retry, phone restart, duplicate handling, and battery restrictions.
7. Update the setup portal and deployment documentation to remove Round Sync requirements.
8. Export and validate the school-specific Automate flow.
