# Live per-device upload validation

Validated against the production endpoint at `https://areseducation.org/monitor_upload/` on 2026-09-07 after deploying the per-device upload authentication changes.

## Result

A previously enrolled pilot device successfully authenticated using its device ID and device credential and uploaded a synthetic ARES usage CSV over HTTPS.

The live endpoint:

- accepted the first upload as a new stored file;
- authenticated the request in `device` mode;
- bound the upload to the enrolled canonical school ID `ARES-S0016`;
- rewrote the submitted legacy school segment to the canonical school ID in the stored filename; and
- returned `status: duplicate` for an immediate exact retry rather than storing a second copy.

The retry response confirmed the canonical stored filename format:

```text
ARES_USAGE_ARES-S0016_AUTO_<timestamp>.csv
```

and returned the enrolled school ID independently of the legacy school segment supplied in the test filename.

This validates the live production behavior required before wiring Android automatic upload: per-device authentication, canonical school identity, HTTPS multipart upload, and idempotent retry acknowledgement.

## Security note

No live device credential, enrollment code, upload key, private enrollment-state contents, or uploaded CSV contents are recorded in this repository.
