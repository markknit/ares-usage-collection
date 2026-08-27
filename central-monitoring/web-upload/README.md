# ARES central monitoring web upload

This directory contains the HTTPS upload endpoint intended for deployment at:

`https://areseducation.org/monitor_upload/`

It accepts one ARES usage CSV at a time using `POST multipart/form-data`, validates the existing ARES filename contract, requires a private upload key, and stores the file in a protected `incoming` directory.

## Files

- `index.php` — public health-check and upload endpoint.
- `upload_lib.php` — validation and helper functions.
- `config.example.php` — configuration template; copy to `config.php` on the server.
- `.htaccess` — prevents direct access to `config.php` and directory listing on Apache/LiteSpeed.
- `incoming/.htaccess` — blocks direct web access to uploaded CSVs.

`config.php` and uploaded files are excluded by the repository `.gitignore` and must never be committed.

## Deployment

1. Copy the contents of `central-monitoring/web-upload/` into the web directory that serves `https://areseducation.org/monitor_upload/`.
2. Copy `config.example.php` to `config.php` on the server.
3. Generate a private upload key, for example:

   ```bash
   php -r "echo bin2hex(random_bytes(32)), PHP_EOL;"
   ```

4. Put that value in `config.php` as `upload_key`. Do not put the real key in GitHub, documentation, chat logs, or an APK source file.
5. Make sure PHP can write to the configured `storage_dir`.
6. Keep the included `.htaccess` files in place if the site uses Apache/LiteSpeed. If the host does not honor `.htaccess`, configure the web server to deny access to `config.php` and `incoming/`, or preferably set `storage_dir` to an absolute directory outside the public web root.

The pilot configuration can use:

```php
'storage_dir' => __DIR__ . '/incoming',
```

because the included `incoming/.htaccess` denies web access. Storage outside the document root is preferred when the hosting account permits it.

## Health check

A browser or GET request to:

`https://areseducation.org/monitor_upload/`

should return JSON similar to:

```json
{"service":"ares-monitor-upload","status":"ready","upload_method":"POST multipart/form-data","file_field":"usage_file"}
```

The health check does not reveal the upload key or stored filenames.

## Pilot upload test

Use a valid ARES usage filename and the private key stored only on the server/test machine:

```bash
curl -i \
  -H "X-ARES-Upload-Key: <UPLOAD_KEY>" \
  -F "usage_file=@ARES_USAGE_TSAVO3_2026-Q3-MID_2026-08-27_10-20-30.csv" \
  https://areseducation.org/monitor_upload/
```

Expected responses:

- `201` with `status: stored` — new file accepted.
- `200` with `status: duplicate` — exact same filename and content already exists; safe retry.
- `400` — invalid filename, file, CSV, or upload request.
- `401` — missing or invalid upload key.
- `409` — same filename already exists with different content.
- `503` — server configuration or storage is not ready.

## Filename contract

The endpoint uses the same filename contract as `central-monitoring/process_incoming.py`:

`ARES_USAGE_<SCHOOL>_<COLLECTION>_<YYYY-MM-DD_HH-MM-SS>.csv`

Examples:

- `ARES_USAGE_TSAVO3_2026-Q3-MID_2026-08-27_10-20-30.csv`
- `ARES_USAGE_TSAVO3_AUTO_2026-08-27_10-20-30.csv`

This preserves compatibility with the existing central processing logic.

## Security model

- Production POSTs require HTTPS.
- Uploads require a private key supplied through `X-ARES-Upload-Key` or `Authorization: Bearer ...`.
- Filenames are strict and cannot contain directory paths.
- Files over the configured size limit are rejected.
- Files must contain plausible CSV content.
- Writes use a temporary file followed by an atomic rename.
- Exact retries are idempotent.
- `config.php` and live uploaded CSVs are excluded from Git.

The pilot uses one server-side upload key. A later enrollment milestone should replace this with per-device credentials so no shared long-lived secret has to be embedded in the production application.
