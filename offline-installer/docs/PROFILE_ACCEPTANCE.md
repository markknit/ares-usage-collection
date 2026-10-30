# Two-profile acceptance record

Date: 2026-10-29. Baseline: published 5ac6911a24e93381d5f54150e1d897453bf41936.
No live Ubuntu server or client connection is supplied to this checkout yet.
Do not infer field success from mocked service checks or fixture scaffolds.

| Required check | Production | Permanent test | Evidence required |
|---|---|---|---|
| Clean offline install | Pending | Pending | ZIP SHA-256, disconnected Internet, preflight and install logs |
| 95 plans / 806 lessons | Pending | Pending | Installer status and actual database counts |
| Client-side mDNS | Pending | Pending | Resolve selected alias on a separate client; match target LAN address |
| Nginx and Lesson3 URLs | Pending | Pending | Client browser, Host-header HTTP checks, ADMIN_URL and empty SERVER_URL check |
| Tailscale enrollment | Pending | Pending | Device approved, matching machine identity, Tailscale IP; no secrets in evidence |
| Standard OpenSSH over Tailscale | Pending | Pending | Actual SSH login to Tailscale IP and RunSSH=false |
| VNC tunnel and desktop | Pending | Pending | SSH forwarding, VNC authentication, usable Cinnamon 2D desktop |
| Disable/re-enable | Pending | Pending | Service states, closed 5901 after disable, successful reconnection and reboot autostart |
| Activation failure cleanup | Pending | Pending | Inject failure on disposable target, verify remote services stopped and no 5901 listener |
| Core success when declined/failed | Pending | Pending | Real install exit status/logs for default-No and failed activation |

## Software evidence recorded locally

Final local command (24 passing checks):

```powershell
$env:PYTHONPATH='tests'
python -B -m unittest test_profiles test_remote_support test_bundle_profiles test_offline_installer.OfflineInstallerSourceTests -v
```

Python used: bundled Codex runtime Python 3.12; Bash: Git for Windows.
The three existing corpus-status integration tests require Linux/root and are
configured in the Ubuntu CI workflow; they were not counted as local passes.
CI workflows have been updated locally but have not been published or executed.

- Both Android debug profiles build with Gradle 8.13 offline using the installed SDK.
- Both compiled DEX endpoint sets pass profile validation.
- Both compiled Android network-security XML files contain their profile's literal
  hostname and exclude the other profile.
- Test-profile printed guides were regenerated, all five pages rendered and visually
  inspected, and extracted text contains test URLs with no production-alias URL.
- Shell syntax and isolated profile/remote-support/source checks pass.
- Both scaffold profiles package successfully, preserve checksum generation, and
  reject modified package content using actual `sha256sum -c`.
- Fixture tests reject display conflicts, non-loopback VNC listeners, wrong/mixed
  APK endpoints, and public SERVER_URL posture during offline setup.
- Service stubs verify activation cleanup commands and core success after optional
  failure/decline. These do not prove real systemd, Tailscale, SSH or VNC behavior.

Windows scaffold tests substitute only the unavailable rsync copy command; all
remaining builder, URL rendering, shell syntax and checksum logic executes normally.
They contain fixture assets and the NOT_FIELD_READY marker, not a deployable payload.

## Target procedure (repeat for each profile)

Use a clean disposable Ubuntu 24.04 base image and an approved profile-matching APK.
Keep the online demo untouched. Record package identity and checksums before use.
Run preflight, then install with Internet disconnected. Create the first Lesson3
administrator and require actual verified 95/806 counts. Decline optional support
on the first run. Reboot, resolve the alias from a separate device, and open the
teacher install page, Lesson Plans links and Lesson3 login on the selected alias.
Test ARES Sync local discovery/collection on the matching test/production app.

Reconnect Internet and activate from the console. Complete browser enrollment,
then run standard SSH and a real VNC viewer through the printed tunnel. Verify
`tailscale debug prefs` reports RunSSH false (redact other preferences/state).
Confirm every 5901 listener is loopback. Reboot and verify autostart/reconnection.
Disable; verify remote services inactive/disabled and 5901 closed. Re-enable and
repeat the desktop connection. Confirm pre-existing SSH was preserved.

On a disposable fixture, inject an activation failure (e.g. deny browser enrollment
or force VNC startup failure) and verify service/listener cleanup. Exercise the
post-core default-No and failed-activation paths and record core success separately.
Do not deliberately break the online demo or alter real school identities/data.

Keep the v0.94 discussion/content gates in `LESSON3_V094_ACCEPTANCE.md` pending until
their actual UI checks are complete. No claim of complete test-profile/field
acceptance is made before live target and client validation.
