# Two-profile acceptance record

Updated: 2026-10-30. Baseline: published 5ac6911a24e93381d5f54150e1d897453bf41936.
Implementation commits: `785825f`, `3dccba4`, and `608cb7e` (Lesson3 v0.94 / bundle v1.12).
Current source targets bundle v1.13 with Lesson3 v0.94; v1.12 artifact evidence
is retained unchanged. See [Tsavo Trust](TSAVO_TRUST.md) for external-source
requirements, mapping reconciliation, backup/restore behavior and pending tests.
Live acceptance status: **Pending for every check in both profiles**, including
the target procedure and referenced Lesson3 UI/content checks below.
No live Ubuntu server or client connection is supplied to this checkout yet.
Do not infer field success from mocked service checks or fixture scaffolds.

## Field evidence recorded separately

[2026-10-30 v1.12 remote-access field evidence](evidence/2026-10-30-v1.12-remote-access-field-test.md)
records a successful user-reported manual TigerVNC component test. Packaged
remote-support acceptance remains **Pending**. The manual result does not satisfy
packaged display `:1`, Tailscale-path SSH/VNC, reboot/autostart, disable/re-enable
or activation failure cleanup. Every live acceptance row below remains Pending
for both profiles.

| Required check | Production | Permanent test | Evidence required |
|---|---|---|---|
| Clean offline install | Pending | Pending | ZIP SHA-256, disconnected Internet, preflight and install logs |
| 95 plans / 806 lessons | Pending | Pending | Installer status and actual database counts |
| Client-side mDNS | Pending | Pending | Resolve selected alias on a separate client; match target LAN address |
| Nginx and Lesson3 URLs | Pending | Pending | Client browser, Host-header HTTP checks, ADMIN_URL and empty SERVER_URL check |
| ARES Sync discovery/collection | Pending | Pending | Actual phone using the matching approved profile APK against the selected server alias |
| Tailscale enrollment | Pending | Pending | Device approved, matching machine identity, Tailscale IP; no secrets in evidence |
| Standard OpenSSH over Tailscale | Pending | Pending | Actual SSH login to Tailscale IP and RunSSH=false |
| VNC tunnel and desktop | Pending | Pending | SSH forwarding, VNC authentication, usable Cinnamon 2D desktop |
| Disable/re-enable | Pending | Pending | Service states, closed 5901 after disable, successful reconnection and reboot autostart |
| Activation partial failure and retry | Pending | Pending | Fail TigerVNC after Tailscale/SSH succeed; capture diagnostics before VNC stop, working command-line path, preserved identity and enrollment-free VNC retry |
| SSH service/socket baseline restoration | Pending | Pending | Ubuntu 24.04 active/enabled ssh.socket and inactive/disabled ssh.service; saved pair restored by disable without unnecessary service enablement |
| Enrollment timeout and secret-free logs | Pending | Pending | Offline/deferred/timeout retry command, connected identity reuse, console-only authentication URL and absence from activation/installer logs |
| Core success when declined/failed | Pending | Pending | Real install exit status/logs for default-No and failed activation |
| TsavoTrust offline install and repeat | Pending | Pending | Installed eight-file hashes, unchanged prior mapping rows, exactly one new Tsavo key and correct portal link |
| TsavoTrust portal, videos and tracking | Pending | Pending | Actual rendered card/logo, all six videos with seeking/ranges, correct report attribution and preserved Ol Pejeta history |
| TsavoTrust failure restoration | Pending | Pending | Disposable-target copy/publication/HTTP failure, restored prior module/link/map and reviewed recovery evidence |

## Historical v1.12 software evidence recorded locally

The latest v1.13 remote-support source tests are recorded in
[STATUS.md](../../STATUS.md). They exercise service stubs and do not change any
Pending live result above. The approved v1.13 partial-failure policy is defined in
[REMOTE_ACCESS.md](REMOTE_ACCESS.md); preserve working Tailscale/SSH when VNC fails.

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

On a disposable fixture, separately defer/deny enrollment and force VNC failure
after Tailscale/SSH succeed. The latter must return partial failure, print VNC
diagnostics before stopping only TigerVNC, and preserve working Tailscale/SSH and
identity. Retry must repair VNC without re-enrollment. Verify both SSH unit baseline
states on disable, including Ubuntu socket activation. Verify timeout/retry and
authentication-URL omission from both logs without storing the URL in evidence.
Exercise post-core default-No, partial and failed paths; record core success separately.
Do not deliberately break the online demo or alter real school identities/data.

Keep the v0.94 discussion/content gates in `LESSON3_V094_ACCEPTANCE.md` pending until
their actual UI checks are complete. No claim of complete test-profile/field
acceptance is made before live target and client validation.
