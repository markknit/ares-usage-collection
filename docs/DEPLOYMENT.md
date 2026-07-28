# Deployment

## 1. Host requirements

A normal HTTPS web host with PHP 8+ is sufficient. The portal is mostly static. PHP is used only for asset checks, test-file generation, and lightweight event logging.

Deploy the contents of `public/` as the web root. Give the sibling `data/` directory write permission to the web-server account, but do not expose it as a public URL.

Protect `admin.html` and the event APIs with HTTP authentication or your normal administrative access control.

## 2. Required master-phone artifacts

Place these in `public/assets/downloads/`:

- `roundsync-approved.apk`: exact pilot-tested APK.
- `ARES-RoundSync-Config.zip`: exported from the tested Round Sync master phone.
- `ARES-<SCHOOL_CODE>-Automation.macro`: exported MacroDroid automation for each school.

Record SHA-256 hashes before publishing. Do not replace an APK or configuration silently; update the deployment register and rerun acceptance tests.

## 3. Add schools

Run:

```bash
python3 tools/build_school_assets.py --code KISASI --name "Kisasi Secondary School" --ssid ARES2
```

Then create and place `public/assets/downloads/ARES-KISASI-Automation.macro`.

## 4. Production URL and QR codes

Use school-specific URLs:

`https://setup.example.org/setup.html?school=MISUUNI`

Generate and print one QR code per school. The school code is carried in the URL; browser cookies are not required.

## 5. Local ARES server

Deploy:

- `local-server/ares_prepare_usage_upload.sh` to `/usr/local/sbin/`.
- `local-server/usage-upload.conf.example` to `/etc/ares/usage-upload.conf`, edited for that school.
- `local-server/prepare_usage_upload.php` to the tracker web directory.
- `local-server/collection_schedule.json` to `/tracker/collection_schedule.json`.

Add a narrowly scoped sudoers entry allowing the web-server account to run only the report wrapper.

## 6. Cloud upload target

The validated pilot target is Google Drive through the Round Sync remote `ARESGoogleDrive`.

Use this destination folder:

`ARESGoogleDrive:ARES Usage Uploads/Incoming`

Round Sync performs a **Copy** from `Download/ARES-Usage`. Successfully confirmed files are moved locally to `Download/ARES-Usage-Sent` by the later MacroDroid workflow.

## 7. Central processing

Run `central-monitoring/process_incoming.py` on a schedule against the Google Drive Incoming folder through rclone. The processor is provider-neutral: pass the configured rclone remote path with `--remote` and the archive destination with `--archive`.

It validates names and CSV structure, suppresses exact duplicates by SHA-256, archives accepted files, removes accepted incoming files, and optionally runs the existing reporting command.
