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
- Local export endpoint: `http://ares.edu/tracker/prepare_usage_upload.php?collection=AUTO`
- Collection schedule: `http://ares.edu/tracker/collection_schedule.json`

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

### Next milestone

Validate Android collection from the `tsavo3` ARES Wi-Fi network:

1. Connect the pilot Android phone to the school network.
2. Download a generated CSV from the local endpoint.
3. Preserve the file while the phone has no internet connection.
4. Upload it to the central OneDrive Incoming folder after internet access returns.
5. Confirm successful receipt before implementing the remaining phone automation.
