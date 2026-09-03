# ARES central monitoring web service

This directory contains the HTTPS monitoring upload and device enrollment endpoints intended for deployment at:

`https://areseducation.org/monitor_upload/`

The service has two responsibilities:

1. Accept validated ARES usage CSV files into protected incoming storage.
2. Enroll an ARES Sync phone to one canonical school and issue a unique device credential.

Live credentials, the real school registry, enrollment codes, device records, and uploaded CSV files must never be committed to Git.

## Validated upload deployment

The production upload endpoint at `https://areseducation.org/monitor_upload/` has been deployed and validated over live HTTPS.

The health check returned:

```json
{"service":"ares-monitor-upload","status":"ready","upload_method":"POST multipart/form-data","file_field":"usage_file"}
```

On 2026-09-01, an authenticated synthetic CSV upload was tested against the production endpoint. The first POST returned HTTP `201` with `status: stored`. Repeating the exact same upload returned HTTP `200` with `status: duplicate`, and the protected `incoming` directory contained only one copy of the file. This validates live authentication, multipart upload handling, CSV and filename validation, writable incoming storage, and idempotent retry behavior.

No live upload credential or uploaded CSV is stored in this repository.

## Validated live enrollment deployment

On 2026-09-03, the live school registry and enrollment service at `https://areseducation.org/monitor_upload/` were validated end to end using the pilot Misuuni school record.

The live checks confirmed:

- `GET /monitor_upload/schools.php?q=misuuni` returned the canonical school `ARES-S0016` / `Misuuni Sec`.
- The HTTPS administrator endpoint generated a school-specific one-time enrollment code and returned HTTP `201`.
- `POST /monitor_upload/enroll.php` accepted the selected school plus that code and returned HTTP `201`, a unique `ARES-D-...` device ID, and a 256-bit device credential.
- Reusing the same enrollment code returned HTTP `400` with `enrollment-code-used`.
- `data/enrollment_state.json` stored only an HMAC of the enrollment code and a SHA-256 hash of the device credential; the plaintext enrollment code and raw device credential were absent.
- An independent SHA-256 calculation of the issued device credential matched the stored `credential_hash` exactly.
- Direct HTTPS requests to both `data/schools.json` and `data/enrollment_state.json` returned HTTP `403`, confirming that the protected enrollment data is not web-readable.

No live enrollment code, device credential, enrollment-state file, or live school registry is stored in this repository.

## Files

- `index.php` - public upload health check and authenticated CSV upload endpoint.
- `upload_lib.php` - upload validation and helper functions.
- `schools.php` - school-name search endpoint used during enrollment.
- `enroll.php` - one-time enrollment endpoint that binds a phone to a canonical school.
- `enrollment_lib.php` - school matching, one-time-code, and device credential helpers.
- `enrollment_admin_lib.php` - authenticated web-admin helpers for enrollment-code generation.
- `admin_enrollment_code.php` - HTTPS-only administrator endpoint for generating or rotating one school enrollment code without shell access.
- `generate_enrollment_codes.php` - CLI-only administrator tool for bulk or shell-based enrollment-code generation.
- `school_registry.example.json` - public example of the registry schema only; it contains no live school roster.
- `config.example.php` - configuration template; copy to `config.php` on the server.
- `.htaccess` - prevents direct access to `config.php` and directory listing on Apache/LiteSpeed.
- `incoming/.htaccess` - blocks direct web access to uploaded CSVs.
- `data/.htaccess` - blocks direct web access to the live school registry and enrollment state.

`config.php`, `data/schools.json`, `data/enrollment_state.json`, and uploaded files are excluded by `.gitignore` and must never be committed.

## Deployment

Copy the contents of `central-monitoring/web-upload/` into the web directory that serves `https://areseducation.org/monitor_upload/`.

Copy `config.example.php` to `config.php` on the server if `config.php` does not already exist. If an upload configuration is already live, preserve its existing `upload_key` and add the enrollment settings rather than replacing the file blindly.

Generate three independent 64-character secrets. For example:

```bash
php -r "echo bin2hex(random_bytes(32)), PHP_EOL;"
```

Use separate values as `upload_key`, `enrollment_secret`, and `enrollment_admin_key`. Never place the real values in GitHub, documentation, chat logs, or APK source.

For the pilot, the protected paths can be:

```php
'storage_dir' => __DIR__ . '/incoming',
'school_registry_path' => __DIR__ . '/data/schools.json',
'enrollment_state_path' => __DIR__ . '/data/enrollment_state.json',
```

Keep the included `.htaccess` files in place if the site uses Apache/LiteSpeed. If the host does not honor `.htaccess`, configure the web server to deny direct access to `config.php`, `incoming/`, and `data/`, or preferably move those paths outside the public document root.

### Parent rewrite rules

The `/monitor_upload/` directory is an API/service path and must not be processed by site-wide rules that rewrite `.php` URLs to `.html` or otherwise alter endpoint paths.

On the current Bluehost deployment, the parent `public_html/.htaccess` contained a site-wide `.php` to `.html` redirect. The following exclusion was required immediately after `RewriteEngine On` / `RewriteBase /` and before the extension-redirect rules:

```apache
# Do not rewrite ARES monitoring API endpoints
RewriteRule ^monitor_upload/ - [L]
```

Without this exclusion, POSTs to endpoints such as `admin_enrollment_code.php` are redirected before PHP runs.

## School registry

The live registry is `data/schools.json` and is intentionally not tracked by Git. Each school has a stable internal ID that should remain unchanged even if its display name is corrected later.

Schema:

```json
{
  "version": 1,
  "schools": [
    {
      "school_id": "ARES-S0001",
      "canonical_name": "Example Secondary School",
      "aliases": ["Example Sec"],
      "active": true
    }
  ]
}
```

The initial pilot registry can be replaced later with the final ARES school list. Existing `school_id` values should be retained when a school is merely renamed or corrected.

## School search endpoint

ARES Sync will call:

```text
GET /monitor_upload/schools.php?q=<partial school name>
```

Queries shorter than two characters are rejected. The endpoint returns at most eight active matches. Search normalization tolerates common school-name variations such as `secondary` versus `sec`, `primary` versus `pry`, `saint` versus `st`, and `airbase` versus `air base`.

The teacher must select a returned canonical school. Free-form teacher text is never stored as the school identity.

## One-time enrollment codes

Enrollment codes are short, teacher-entered codes in the form `XXXX-XXXX`. The alphabet omits easily confused characters such as `I`, `O`, `0`, and `1`.

The server stores only an HMAC of each enrollment code, not its plaintext value. Each code is assigned to one school and can be used only once.

Generate codes from the deployed directory with:

```bash
php generate_enrollment_codes.php --all > private_enrollment_codes.csv
```

The CSV contains plaintext codes and is sensitive. Store it securely and do not commit it.

To generate or replace a code for one school from a shell:

```bash
php generate_enrollment_codes.php --school=ARES-S0001 --rotate
```

`--rotate` revokes any unused previous code for that school before creating the replacement.

## HTTPS enrollment-code administration

Shared hosting may not provide usable shell access. `admin_enrollment_code.php` provides a narrow HTTPS-only alternative for generating one school's enrollment code.

Configure a third independent secret in `config.php`:

```php
'enrollment_admin_key' => '64_CHARACTER_RANDOM_SECRET',
```

The administrator key is never sent to ARES Sync and should be kept only on an administrator's machine and the server. The endpoint accepts it through `X-ARES-Admin-Key` or `Authorization: Bearer ...`.

Example request:

```bash
curl -i \
  -H "X-ARES-Admin-Key: <ADMIN_KEY>" \
  -H "Content-Type: application/json" \
  --data '{"school_id":"ARES-S0001","rotate":true}' \
  https://areseducation.org/monitor_upload/admin_enrollment_code.php
```

A successful response returns HTTP `201` with the canonical school and plaintext one-time enrollment code. The code is returned only in that response; only its HMAC is stored in `data/enrollment_state.json`.

If an unused code already exists and `rotate` is false, the endpoint returns `active-enrollment-code-exists` rather than replacing it silently. When `rotate` is true, any unused prior code for that school is revoked before the new code is generated.

On Windows PowerShell, when using `curl.exe`, writing the JSON payload to a temporary file and sending it with `--data-binary "@file.json"` avoids command-line quoting that can otherwise produce `invalid-json`.

## Enrollment endpoint

ARES Sync submits the teacher-selected canonical school plus the short enrollment code:

```text
POST /monitor_upload/enroll.php
Content-Type: application/json
```

Example body:

```json
{
  "school_id": "ARES-S0001",
  "enrollment_code": "ABCD-EFGH",
  "device_label": "Teacher phone"
}
```

A successful enrollment returns HTTP `201` and includes the canonical school ID/name, a unique device ID, and a random 256-bit device credential returned only once. The server stores only the SHA-256 hash of the device credential. A reused code, a code assigned to another school, or an inactive/unknown school is rejected.

The Android application should store the returned device credential privately and should never show it to the teacher during normal operation.

## Upload health check

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

- `201` with `status: stored` - new file accepted.
- `200` with `status: duplicate` - exact same filename and content already exists; safe retry.
- `400` - invalid filename, file, CSV, or upload request.
- `401` - missing or invalid upload key.
- `409` - same filename already exists with different content.
- `503` - server configuration or storage is not ready.

## Filename contract

The upload endpoint uses the same filename contract as `central-monitoring/process_incoming.py`:

`ARES_USAGE_<SCHOOL>_<COLLECTION>_<YYYY-MM-DD_HH-MM-SS>.csv`

Examples:

- `ARES_USAGE_TSAVO3_2026-Q3-MID_2026-08-27_10-20-30.csv`
- `ARES_USAGE_TSAVO3_AUTO_2026-08-27_10-20-30.csv`

This preserves compatibility with the existing central processing logic.

## Security model

- Production upload and enrollment POSTs require HTTPS.
- Pilot CSV uploads currently use a private upload key; the Android production path will move to per-device credentials.
- Enrollment-code administration requires a third independent administrator key and is HTTPS-only.
- Enrollment codes are school-specific, HMAC-protected at rest, and one-time-use.
- Device credentials are random 256-bit values and are stored server-side only as SHA-256 hashes.
- Free-form school text never becomes the canonical identity; the selected `school_id` does.
- Registry and enrollment state files are denied direct web access and excluded from Git.
- Filenames are strict and cannot contain directory paths.
- Uploaded files must contain plausible CSV content and stay below the configured size limit.
- Exact upload retries are idempotent.
