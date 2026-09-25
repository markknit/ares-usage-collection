# Release checklist

## APK and offline installer

- [ ] `config/approved_apk.json` identifies package `org.areseducation.sync` on the production channel.
- [ ] Approved production APK SHA-256 is recorded and independently checked.
- [ ] Offline builder refuses an APK whose SHA-256 differs from the approval manifest.
- [ ] Debug/acceptance APK artifacts are not used as production fallbacks.
- [ ] Field ZIP passes `unzip -t` and package `SHA256SUMS` verification.
- [ ] Offline preflight reports `READY TO INSTALL` on the target ARES server.
- [ ] Full field installation completes with WAN/Internet disconnected.
- [ ] `http://ares.local/app_install/` opens from a phone connected to ARES/ARES2.
- [ ] `http://ares.local/downloads/ares-sync.apk` downloads successfully while Internet is unavailable.
- [ ] Downloaded APK installs successfully on a clean test phone.
- [ ] One-time installation/enrollment key works on the intended phone.
- [ ] Teacher guide and technician guide use `http://ares.local/app_install/` and match the current enrollment process.

## Usage collection

- [ ] Existing tracking/reporting job still runs after the server update.
- [ ] Scheduled usage collection works from the local ARES server.
- [ ] Pending file survives phone restart.
- [ ] Upload succeeds after later cellular or Internet-capable Wi-Fi access.
- [ ] Teacher receives expected collection/completion status.
- [ ] Central processor accepts the upload once and suppresses duplicates.

## Security and operations

- [ ] Staff enrollment/admin interface remains access-controlled.
- [ ] One-time installation keys are not stored in rollout documents or logs.
- [ ] APK is served only as the approved production file; the school installer does not rebuild it.
- [ ] Tailscale/TigerVNC remain optional and are not required for offline school installation.
