# ARES Internet Lockdown v1.4.2 - simplified installation

**Installer update only.** The firewall and restore scripts are byte-for-byte identical to v1.4.1. This package reduces setup prompts; it does **not** claim to correct new firewall behavior or replace live acceptance testing.

## Daily commands

| Command | Purpose |
| --- | --- |
| `lockdown-internet --tailscale` | Five-minute rollback test. Verify remote connections and local apps. |
| `lockdown-internet --permanent --tailscale` | Lock down until restored or the next reboot. |
| `restore-internet` | Remove the temporary firewall table. Does not disable reboot lockdown. |
| `lockdown-internet --tailscale --check` | Verify the configuration and nft rules without activating them. |
| `ares-anydesk-diagnose` | Read-only diagnostic if AnyDesk stops connecting. |

The commands request sudo as needed. On a client connected through the standalone LAN router, the ARES firewall governs **ARES server** traffic, not a separate router's own internet connection. DHCP, DNS, mDNS and ARES applications still need a working flat-LAN and access-point configuration.

## Quick install

Copy the ZIP to the Ubuntu server and run:

```bash
unzip ARES_Internet_Lockdown_Package_v1.4.2.zip
cd ares-lockdown-v1.4.2
bash install.sh
```

The installer will:

- Reuse an existing valid LAN interface/subnet configuration.
- Otherwise detect the LAN interface and subnet automatically if only one eligible interface has IPv4. If that interface also carries the default internet route, confirm that student devices actually use it as their LAN (it may otherwise be a modem-only uplink).
- If multiple candidates exist, ask you to select the **student-side** interface(s) by number (do not select a modem-only network).
- Set Mode A (ARES application server) by default, backing up and replacing only the installed script files; existing compatible command wrappers are preserved.
- Validate nftables rules without activating lockdown.
- Ask only whether to enable lockdown at every reboot; **No** is the default. It will require explicit confirmation that real connectivity tests have already passed before enabling that option.

If Tailscale or nftables is not ready, the installer can install files, but it **must not** enable reboot lockdown. It does not install OS packages or bring up Tailscale automatically.

### Test after installation

```bash
lockdown-internet --tailscale --check
lockdown-internet --tailscale
```

Within five minutes, test AnyDesk, Tailscale SSH/VNC, `http://ares.local/` from a wireless client, and browser HTTPS blocking **on the ARES server**. Then restore:

```bash
restore-internet
```

Confirm that AnyDesk reconnects **without rebooting**. Only after passing these tests use `--permanent`.

## Enable lockdown after every reboot

After successfully testing:

```bash
bash install.sh --boot
sudo systemctl is-enabled ares-internet-lockdown.service
```

Answer `YES` when asked whether all remote-access and restoration tests passed. The installer enables the systemd service but does not start it immediately. Perform the first reboot test with local or alternative access available.

To disable **future** reboot lockdown (and restore access now):

```bash
sudo systemctl disable ares-internet-lockdown.service
restore-internet
```

Do not confuse `--permanent` with boot persistence: `--permanent` applies only until the next reboot. Also, a Tailscale/AnyDesk daemon restart may require refreshing the service-scoped firewall exception. Other active firewalls may still have rules of their own.

## Special deployments

Use `bash install.sh --lan 'enp1s0=192.168.50.0/24 wlx001122334455=192.168.60.0/24'` if automatic selection is insufficient. These are **examples**, not parameters for `tsavo3`. Run `ip -br -4 address` to see real device names and addresses.

Use `bash install.sh --mode gateway` only if ARES will actually be configured separately as clients' gateway. This flag does **not** configure Linux routing, DHCP, NAT, or student default gateways. The default is Mode A.

If an existing boot service is enabled, the installer refuses to replace active configuration until you explicitly disable that service. It also refuses to replace files while the ARES lockdown firewall table is active.

## Remaining field checks

- Mesh AP/mDNS behavior (including Tenda MW6), using a wireless client on every node.
- AnyDesk and Tailscale connectivity after lockdown and after restore.
- Reboot-time Tailscale readiness and service exception validity.
- Real nftables behavior on the school Ubuntu build (mock installer tests alone are insufficient).
