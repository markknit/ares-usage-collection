# Optional remote support: OpenSSH over Tailscale, localhost TigerVNC

Core installation prepares Tailscale and TigerVNC, stops/disables both, and disables
legacy x11vnc. It offers activation only after core verification succeeds; the
default answer is No. A declined or failed activation leaves core success intact.
Preparation does not erase an existing Tailscale registration or VNC password.

OpenSSH and Cinnamon 2D must already exist in the Ubuntu 24.04 base image. Neither
preflight nor core installation enrolls the server in a tailnet. No router port
forward, public VNC listener, or Tailscale SSH server is created.

## Activate

At the console, with Internet access, run `sudo ares-enable-remote-access`.
Enter the full school name, confirm its normalized Linux/Tailscale hostname,
complete Tailscale browser approval if needed, and create a unique VNC password
if none exists. The account is `ares`, session Cinnamon 2D, display `:1`, port
5901. The mDNS profile alias is independent and is never changed by activation.

The canonical source is `templates/ares_enable_remote_access.sh`; the builder
packages that file and preparation installs it under `/usr/local/sbin`.
Its Python configuration helper is installed under `/usr/local/lib/ares`.
There is no second activation implementation or post-preparation overwrite.

Activation explicitly runs `tailscale set --ssh=false` and uses standard OpenSSH.
The official [Tailscale instructions](https://tailscale.com/docs/features/tailscale-ssh)
document that command for disabling previously enabled Tailscale SSH.
Tailnet policy must permit standard TCP 22, and the support user needs ordinary
OpenSSH credentials/authorized keys. No credentials are embedded in this package.

The bundled Ubuntu Noble `tigervnc-standalone-server` version
`1.13.1+dfsg-2build2` reads Perl syntax from `~/.vnc/tigervnc.conf` and its password
from `~/.vnc/passwd`, per the exact-version
[Ubuntu manual](https://manpages.ubuntu.com/manpages/noble/man8/tigervncsession.8.html).
The command writes these under the `ares` home with restricted permissions.
It rejects an existing `:1` assignment to another user, preserves other displays,
and rejects an unrelated listener occupying 5901. Every detected 5901 listener
must be IPv4/IPv6 loopback. A failing check stops/disables TigerVNC and Tailscale.

Successful activation enables both services for reboot autostart. It also enables
OpenSSH, records its prior active/enabled state, and preserves that baseline on
subsequent activation. A failure restores the prior SSH state and rolls back a
hostname change. Error logs are root-only under `/var/lib/ares/remote-support`.
Configuration and tailnet enrollment may remain for a retry after failure.

From the authorized support computer, use the Tailscale IP printed by activation:

```powershell
ssh -N -L 5901:127.0.0.1:5901 ares@100.x.y.z
```

Keep that terminal open and connect the VNC viewer to `127.0.0.1:5901`. A service
health check is not evidence of a working client tunnel or usable desktop.

## Disable and re-enable

Run `sudo ares-disable-remote-access`. It stops/disables TigerVNC and Tailscale,
checks that 5901 is closed, and restores the pre-activation OpenSSH service state.
Existing SSH used for another purpose remains available. It retains the tailnet
registration, VNC password and hostname. Account-side removal from the tailnet is
a separate administrative action. Re-enable with the same activation command;
an existing VNC password is reused, and the machine hostname is confirmed again.

Verify on the server: `systemctl is-active tailscaled.service`,
`systemctl is-active 'tigervncserver@:1.service'`, and `ss -ltnp`.
Complete the live checks in `PROFILE_ACCEPTANCE.md` for both profiles before
field acceptance. v1.13 TsavoTrust integration is documented in
[TSAVO_TRUST.md](TSAVO_TRUST.md); remote-support behavior is unchanged by that step.
