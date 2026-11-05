# Optional remote support: Tailscale SSH and a saved VNC connection

## Normal technician use

Complete activation once on each school server. On the support computer, sign
into the approved Tailscale account and keep its app connected. Save the school's
Tailscale address in the VNC viewer with port **5901**. Open that saved connection
and enter the VNC password; no PowerShell tunnel is needed. RealVNC and TigerVNC
single address fields accept `<TAILSCALE-IP>::5901`. The browser SSH button in the Tailscale
admin console is also available when the tailnet's SSH policy permits access.
Connecting in that browser console does not connect Windows applications to the
tailnet. Sign into the Windows Tailscale app separately. The owner confirmed
direct RealVNC access after doing so on November 4; updated activation and
reboot/disable/re-enable checks remain separate acceptance steps.

This simpler workflow is a source follow-up to the November 4 ZIP, whose
activation still prints tunnel instructions and disables Tailscale SSH. Use the
updated complete package when published; rerunning that older activation helper
would undo the manually enabled browser SSH setting.

After core installation and verification succeed, the installer attempts to
prepare the pinned offline Tailscale/TigerVNC payloads. Preparation preserves
existing active services, enablement, Tailscale identity and x11vnc console access.
It does not stop/disable support services merely to offer optional activation.
Missing remote-support prerequisites or preparation failure give a warning and
do not fail the completed core installation. Optional activation is offered only
after successful preparation and defaults to No. Deferral, failure or partial
activation does not undo core success.
Existing Tailscale identity is never logged out, reset or deleted by these commands.

If preparation was deferred, ARES support can diagnose its log and retry from the
extracted package with `sudo bash remote-access/prepare_remote_access.sh`. This
requires Ubuntu 24.04, OpenSSH, Cinnamon 2D and an available port 5901 unless
the existing active TigerVNC already owns that port. These are
remote-support requirements, not prerequisites for core offline installation.

The v1.13 source uses the canonical activation/disable scripts and the shared
`remote_support_common.sh` helper installed under `/usr/local/lib/ares`.
Lesson3 remains v0.94. No final v1.13 field ZIP or live acceptance is established
by this source change. Preserve the v1.12 artifact and dated evidence unchanged.

## Enrollment and command-line access

Run at an interactive console:

```bash
sudo ares-enable-remote-access
```

Press Enter at the school-name prompt to keep the current hostname, then
confirm it (default Yes). To rename deliberately, enter a school name and approve
the normalized name (default No). Invalid names reprompt; EOF defers without a
Python traceback or service changes. This never
changes the selected mDNS profile alias. The ARES server needs outbound Internet
for enrollment and connectivity. The technician may open the authentication URL
on a phone using cellular data; the phone need not be on the ARES network. The
phone's connection does not provide Internet to an otherwise offline server.

Already enrolled **and connected** nodes reuse their identity without another
enrollment request. Otherwise the command asks whether to begin/resume and clearly
displays Tailscale's authentication output on `/dev/tty`. That output bypasses
both activation logging and any parent installer's logging. Never copy an
authentication URL into an evidence record or support log.

Enrollment uses `tailscale up --timeout=120s`, with an outer 125-second deadline
and a further five-second forced-termination grace. It cannot wait indefinitely.
See [Tailscale's timeout reference](https://tailscale.com/docs/reference/tailscale-cli/up).
Offline, deferred or incomplete approval returns status 3 and prints:

```bash
sudo ares-enable-remote-access
```

Retry after providing outbound Internet/approval. Failure handling preserves
Tailscale identity and does not shut down its daemon. It never uses logout,
forced reauthentication or a state-file reset.

Activation applies `tailscale set --ssh=true --operator=ares` automatically.
`--ssh=true` enables Tailscale SSH, including the browser console; `--operator`
allows ares to manage the local Tailscale client without sudo. It does not replace
tailnet access policy or authorize a new account. Ubuntu OpenSSH remains
available on the LAN and its service/socket baseline is retained. No credentials
are bundled. Windows PowerShell access also requires the Windows Tailscale app
to be connected; the browser console establishes its own separate connection.

### Restored-image or deleted-device registration

`Running` with `Self.Online=false` is not an accepted coordination connection.
The November 4 target reached relays but repeatedly received `404: node not
found`. That indicates an unrecognized stored registration; it is not evidence
of a missing network adapter. Activation now prints the actual health message.
From an independent LAN SSH, AnyDesk or local console connection, an operator
can request a fresh sign-in:

```bash
sudo tailscale up --force-reauth --hostname=YOUR-SCHOOL-NAME --ssh=true --operator=ares --timeout=120s
```

Use the actual school hostname, open the displayed URL privately and approve
the device. Then retry `sudo ares-enable-remote-access`. Reauthentication can
interrupt Tailscale sessions; ordinary installer retries never force it.

## SSH baseline and socket activation

Before changing SSH, the command records presence, active state and enabled state
of **both** `ssh.service` and `ssh.socket` in root-only
`/var/lib/ares/remote-support/ssh-before.conf`. The baseline is non-secret, validated
as data rather than sourced as shell code, and preserved across activation retries.
An active `ssh.socket` already provides SSH; activation does not enable
`ssh.service` unnecessarily. If neither unit is active, the available unmasked
socket is preferred, with the service used when the socket is absent.

The Ubuntu 24.04 field baseline (active/enabled socket, inactive/disabled service)
has fixture coverage. Actual Tailscale-path SSH and disable/re-enable remain Pending.
Socket activation can naturally start the service when a new SSH connection arrives.

For a legacy service-only baseline, the original file is retained as
`ssh-before.conf.v1`, its recorded service booleans are kept, and the current socket
state is captured. The legacy format did not record exact enabled-state kinds;
its yes/no service value maps to enabled/disabled. Review that limitation when
accepting an upgraded target; no missing historical socket evidence is invented.

## TigerVNC desktop and password

The standalone desktop uses user `ares`, display `:1`, port 5901, and loopback-only
binding. Tailscale Serve forwards its private port 5901 to that local listener,
so viewers connect to the school's Tailscale address directly. It neither
terminates nor reconfigures the physical GNOME/AnyDesk session.
It never kills desktop processes or another service owning a conflicting port.

For a new password, the script explicitly prompts:

```text
Enter TigerVNC password
Re-enter TigerVNC password to confirm
```

Input is hidden, must match, and must contain 6-8 characters. TigerVNC uses only
the first eight characters. There are at most three attempts. A single line is
passed through stdin to `tigervncpasswd -f`; exactly one eight-byte normal-access
record is installed with mode 0600. No view-only password is requested or created.
Passwords are neither command-line arguments nor printed/logged. An existing
eight-byte normal-access record is reused; a missing or other-sized record requires
the explicit prompts. See the [pinned Ubuntu password manual](https://manpages.ubuntu.com/manpages/noble/man1/tigervncpasswd.1.html).

`~/.vnc/tigervnc.conf` uses supported `$AlwaysShared` spelling, `$localhost = "yes"`
and an explicit `$vncStartup` pointing to `~/.vnc/Xtigervnc-session`. That executable
startup file clears inherited session-bus variables and runs:

```bash
exec dbus-run-session -- cinnamon-session-cinnamon2d
```

This is a separate session bus for the VNC desktop. The per-user startup mechanism
is documented in [Ubuntu's exact-version configuration manual](https://manpages.ubuntu.com/manpages/noble/man5/tigervnc.conf.5x.html).
The display map preserves other displays and rejects `:1` ownership conflicts.
Activation requires three consecutive samples of an active unit and exclusively
IPv4/IPv6-loopback port 5901 listeners within a 20-sample startup window.

It then saves and verifies this private forwarding rule:

```bash
sudo tailscale serve --bg --tcp=5901 tcp://127.0.0.1:5901
```

The background rule resumes after reboot. Activation reuses an exact existing
rule, preserves routes on other ports, and refuses a conflicting/foreground or
public Funnel configuration on port 5901. It never resets the whole Serve
configuration. The local VNC listener remains loopback-only; the new path is
private to the tailnet and subject to its access rules. See
[Tailscale TCP forwarding](https://tailscale.com/docs/reference/tailscale-cli/serve)
and [browser SSH](https://tailscale.com/docs/features/tailscale-ssh/tailscale-ssh-console).

## Partial failure and retry

If Tailscale is connected and SSH is available but TigerVNC fails, activation
returns **2 (partial failure)**. It prints unit status, recent VNC journal entries
and existing current-display VNC logs **before** stopping/disabling only
`tigervncserver@:1.service`. Logs are read as `ares`, not through root-followed
symlinks. Working Tailscale and SSH remain operational; SSH/hostname rollback is
not performed on this path. Retry instructions are always printed. If display
ownership conflicts with another user, activation fails without stopping that
user's existing unit.

The retry reuses connected Tailscale enrollment and the original SSH baseline,
then repairs/restarts TigerVNC. Status 0 means host-side activation checks passed;
status 1 is another failure. These checks do not establish a working client login,
saved viewer connection or usable desktop. If forwarding setup fails after
TigerVNC is healthy, the helper retains both SSH and TigerVNC and reports partial
failure. Complete the live acceptance matrix separately.

Activation logs are root-only under `/var/lib/ares/remote-support`. In addition to
the terminal-only enrollment output, the logging pipeline omits HTTP(S) URLs from
diagnostics as defense in depth. Do not capture passwords, authentication URLs or
unredacted Tailscale addresses in field evidence.

The command prints the SSH address and the VNC host/port directly on the console.
After full activation, save this address in a Windows VNC viewer:

```text
Host: <TAILSCALE-IP>
Port: 5901
TigerVNC address: <TAILSCALE-IP>::5901
```

Keep the Windows Tailscale app connected. The already-tested LAN SSH tunnel
remains a support fallback for the loopback listener, not a routine login step.

## Disable and remaining acceptance

`sudo ares-disable-remote-access` deliberately stops/disables Tailscale and
TigerVNC, verifies port 5901 is closed and restores the original SSH service/socket
active/enabled configuration. Identity, password, configuration and baseline are
retained for re-enable, including the private Serve rule. Stopping Tailscale
stops that route; re-enabling restores it. Errors are reported if restoration or
shutdown fails.

Packaged display `:1`, actual Tailscale-path SSH/VNC, reboot/autostart, full
disable/re-enable, partial-failure recovery and physical-session coexistence remain
**Pending** for both profiles in [PROFILE_ACCEPTANCE.md](PROFILE_ACCEPTANCE.md).
TsavoTrust is documented separately in [TSAVO_TRUST.md](TSAVO_TRUST.md).

## November 4 SSH rerun evidence

The operator's `20261104_102223` transcript confirms a healthy existing Lesson3
and installed corpus were preserved and core checks passed. Optional preparation
then disabled legacy x11vnc and left new services inactive; activation failed on
an empty/unusable school name before enabling Tailscale. The November 4 source
corrects that prompt and preserves existing support during preparation. These
source checks do not establish a new live Tailscale/VNC activation.
