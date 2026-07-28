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
- Cloud remote: `ARESGoogleDrive`
- Cloud incoming folder: `ARES Usage Uploads/Incoming`

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
- Round Sync connected directly to Google Drive through the `ARESGoogleDrive` remote.
- A manual Round Sync copy task uploaded the downloaded ARES CSV to Google Drive successfully.

### Next milestone

Automate the tested phone workflow with MacroDroid:

1. Confirm the Round Sync task ID and success/failure notification text.
2. Test failed connectivity and confirm the pending CSV remains on the phone.
3. Create the internet-connected MacroDroid trigger that launches the Round Sync task.
4. Move successfully confirmed files to `Download/ARES-Usage-Sent`.
5. Export and validate the school-specific MacroDroid configuration.
