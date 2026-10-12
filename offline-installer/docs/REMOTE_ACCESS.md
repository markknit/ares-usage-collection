# Optional Remote Access: Tailscale and TigerVNC

ARES Q4 Offline Installer v1.11 installs the remote-access prerequisites but leaves them inactive.
The field installation does not register the server with Tailscale, create a VNC password, start a
VNC desktop, or expose a VNC port.

## State immediately after field installation

- Tailscale and TigerVNC are installed from the checksummed offline payload.
- `tailscaled.service` and `tigervncserver@:1.service` are stopped and disabled.
- Tailscale is not registered with a tailnet.
- No TigerVNC listener exists on port 5901.
- The base-image `x11vnc` service is stopped and disabled.
- The future TigerVNC session is configured for Cinnamon 2D and localhost-only listening.

This state requires no remote-access credentials and does not open a remote-control service.

## Activate during an authorized support session

The server must have working Internet access. At the server console, run:

```bash
sudo ares-enable-remote-access
```

The command:

1. requests a new, unique VNC password without printing or storing it in the installation log;
2. starts a separate headless Cinnamon 2D desktop on display `:1`;
3. binds TigerVNC only to localhost on TCP 5901;
4. starts Tailscale and asks the technician to complete its normal browser authorization;
5. enables Tailscale SSH; and
6. prints the SSH-tunnel command needed before connecting a VNC viewer.

Do not expose TCP 5901 through the router, Nginx, or a public firewall rule. The intended connection
is a VNC viewer through an authenticated Tailscale SSH tunnel.

If activation fails, the command stops both services so a partial activation does not leave remote
access running.

## Disable after support

Run:

```bash
sudo ares-disable-remote-access
```

This stops and disables TigerVNC and Tailscale while retaining their packages and local
configuration for a later authorized session. If the server must also be removed from the
organization's Tailscale device list, an authorized Tailscale administrator must perform that
separate account-side action.

## Verification

After installation, but before activation:

```bash
sudo systemctl is-active tailscaled.service || true
sudo systemctl is-active 'tigervncserver@:1.service' || true
sudo ss -ltnp | grep ':5901 ' || echo 'PASS: port 5901 is closed'
sudo pgrep -x x11vnc || echo 'PASS: x11vnc is not running'
```

The expected service result is `inactive`, port 5901 is closed, and `x11vnc` is not running.

## Desktop fallback

Cinnamon 2D is the tested default for Ubuntu 24.04 ARES servers. Openbox remains installed as a
manual recovery fallback, but v1.11 does not automatically switch desktop sessions. XFCE, Xpra,
and the Tsavo Trust module are not included in this remote-access package.
