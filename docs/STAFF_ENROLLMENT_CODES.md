# ARES Staff Enrollment Code Portal

ARES staff should generate teacher enrollment codes through the protected staff page instead of constructing JSON or curl commands during routine setup.

## Staff URL

After deployment, open:

```text
https://areseducation.org/monitor_upload/staff_enrollment.php
```

The page uses the existing enrollment backend and canonical school registry. It does not replace the API endpoint `admin_enrollment_code.php`; that endpoint remains available for automation and diagnostics.

## Staff workflow

1. Open the staff enrollment page over HTTPS.
2. Enter the ARES enrollment administration key. Keep this key in the approved ARES password manager; do not put it in email, notes, chat, or teacher documentation.
3. Search for the school by name.
4. Confirm the canonical school name and school ID shown in the result.
5. Click **Generate one-time code**.
6. Copy the returned `XXXX-XXXX` code and give only that short code to the teacher.
7. The teacher enters the code in ARES Sync during enrollment.
8. Sign out when finished.

Each code is assigned to one school and can be used only once. The plaintext code is shown only in the generation response. Server enrollment state stores only its HMAC.

## Existing unused code

If an unused code already exists for the selected school, the portal does not silently replace it. Because plaintext codes are not stored, ARES cannot display the earlier code again.

The page will offer **Replace unused code and generate new code**. Use that only when the earlier code is lost or should be revoked. The previous unused code is revoked before the replacement is generated.

## Security behavior

The staff page:

- requires the existing `enrollment_admin_key` configured in the protected server `config.php`;
- requires HTTPS when the monitoring service is configured to require HTTPS;
- never writes the administration key to the repository or enrollment-state file;
- stores only an authenticated flag and CSRF token in the PHP session after successful sign-in;
- uses a Secure, HttpOnly, SameSite=Strict session cookie scoped to the monitoring path;
- expires staff authorization after 15 minutes of inactivity;
- regenerates the session ID after sign-in;
- requires a CSRF token for code generation, rotation, and sign-out;
- sends `Cache-Control: no-store` and browser hardening headers;
- escapes school names and other rendered values before displaying them;
- does not change the one-use enrollment-code or device-credential security model.

## Deployment

Upload this file from the repository:

```text
central-monitoring/web-upload/staff_enrollment.php
```

to the existing live monitoring directory beside `admin_enrollment_code.php`, `enrollment_lib.php`, `enrollment_admin_lib.php`, and `config.php`.

No new production secret is required. The page uses the already configured `enrollment_admin_key` and `enrollment_secret`.

The existing site-wide rewrite exclusion for `/monitor_upload/` must remain in place so PHP endpoint paths are not redirected to `.html`.

## Live validation checklist

After upload:

1. Open the staff URL and confirm the login page loads over HTTPS.
2. Confirm an incorrect administration key is rejected.
3. Sign in with the real administration key without sharing it in chat or logs.
4. Search for a known test school and confirm the expected canonical result.
5. Generate a fresh one-time code and record only the short teacher code privately.
6. Confirm an immediate second generation attempt reports that an unused code already exists.
7. If testing rotation, explicitly replace the unused test code and confirm the old code no longer works.
8. Enroll the dedicated test phone with the new code and confirm reuse is rejected.
9. Sign out and confirm the staff page returns to the login screen.

Do not use a production teacher or production school for destructive rotation testing unless there is an operational reason to invalidate an existing unused code.

## Rollback

If the staff page has a deployment problem, remove only `staff_enrollment.php` from the live monitoring directory. The existing HTTPS administrator API and enrollment service remain unchanged and can continue to generate codes through the previously validated process.
