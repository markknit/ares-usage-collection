# Deployment

## 1. Host requirements

A normal HTTPS web host with PHP 8+ is sufficient. The portal is mostly static. PHP is used only for asset checks, test-file generation, and lightweight event logging.

Deploy the contents of `public/` as the web root. Give the sibling `data/` directory write permission to the web-server account, but do not expose it as a public URL.

Protect `admin.html` and the event APIs with HTTP authentication or your normal administrative access control.

## 2. Approved ARES Sync APK

The production APK approval record is `config/approved_apk.json`. It identifies the production download URL and exact SHA-256 used by the ARES Q4 Offline Builder.

Do not substitute GitHub debug or acceptance APK artifacts for the production APK. Do not silently replace the approved APK; update the approval manifest only after the replacement production APK has been tested and its SHA-256 recorded.

## 3. Add schools

Run:

```bash
python3 tools/build_school_assets.py --code KISASI --name "Kisasi Secondary School" --ssid ARES2
```

Use the canonical permanent school ID assigned by ARES.

## 4. Production online setup

The hosted setup portal remains available for installations where normal Internet is convenient. The offline school package described below is the preferred fallback where Internet is unavailable or unreliable.

## 5. Local ARES server

Deploy the usage-collection server components using the approved rollout package. The Q4 Offline Installer additionally deploys:

- the approved production ARES Sync APK to `/mnt/sda3/var/www/downloads/ares-sync.apk`;
- its checksum to `/mnt/sda3/var/www/downloads/ares-sync.apk.sha256`; and
- the teacher installation page to `/mnt/sda3/var/www/app_install/index.html`.

The teacher-facing local URL is:

`http://ares.local/app_install/`

The direct APK URL is:

`http://ares.local/downloads/ares-sync.apk`

The `app_install` path is intentionally more specific than a generic `install` path to reduce accidental discovery by users who do not need the app.

The school-side installer must verify the bundled APK checksum before publishing it. Installing the APK from the local server does not require Internet. Enrollment may still require normal Internet/mobile data when the one-time installation key is submitted to the central enrollment service.

## 6. Offline field bundle

Build the field package on an Internet-connected ARES/Linux machine with the approved Offline Builder:

```bash
sudo bash build_offline_bundle.sh \
  --source "/home/ares/Downloads/ARES_Q4_Update" \
  --output "/home/ares/Downloads/ARES_Q4_Update_offline"
```

The builder reads `config/approved_apk.json`, downloads the approved production APK, verifies the exact SHA-256, bundles the APK and Lesson3 container images, generates package checksums, and refuses Internet-dependent field scripts.

At the school:

```bash
sudo bash preflight.sh ARES-S00XX
sudo bash install_offline.sh ARES-S00XX
```

Do not proceed when preflight reports `NOT READY`.

## 7. Teacher installation at an offline school

1. Connect the Android phone to ARES or ARES2.
2. Open `http://ares.local/app_install/`.
3. Download and install ARES Sync.
4. Use the one-time installation/enrollment code supplied by ARES staff.
5. If enrollment requires central verification, enable normal Internet or mobile data for that step.

See `docs/TECHNICIAN_PHONE_INSTALL.md` and `docs/TEACHER_PHONE_GUIDE.md` for the detailed procedure.
