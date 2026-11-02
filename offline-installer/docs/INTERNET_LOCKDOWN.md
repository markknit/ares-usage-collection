# ARES Internet Lockdown v1.4.2 in the offline installer

The owner supplied `ARES_Internet_Lockdown_v1.4.2_GitHub_Handoff.zip` for import
and GitHub synchronization on 2026-11-02. Its complete project is preserved under
`offline-installer/internet-lockdown/`: the original handoff `STATUS.md`, release
scripts, README, release notes, operating PDF and unchanged checksum manifest.
The upstream status describes the earlier standalone handoff; this integration
document and the repository-root STATUS record the subsequent repository work.

## Normal installation

After core ARES installation and optional remote support, the master prepares
the lockdown project. The versioned source and documentation are retained at:

```text
/opt/ares/internet-lockdown/STATUS.md
/opt/ares/internet-lockdown/ares-lockdown-v1.4.2/
```

With an interactive terminal and the required existing OS tools, the integration
calls the supplied installer with `--no-boot`. That installer discovers or reuses
the actual student-facing LAN mapping and may ask the technician to confirm a
shared LAN/uplink or select numbered LAN interfaces. No school-specific interface
or IP address is embedded in this integration. Upstream default mode is `server`;
an existing gateway-mode selection is retained by the supplied installer.

Installation does not activate firewall rules, restore an existing firewall,
enable boot persistence, start Tailscale or install OS packages. Its firewall
readiness invocation uses only `--tailscale --check`. A readiness warning does
not mean real connectivity was tested or that activation is ready.

If lockdown is already active or enabled at boot, existing rules, runtime scripts,
configuration and services are retained, and setup is deferred. Optional remote
preparation is also deferred so it does not restart/replace service-cgroup-based
Tailscale exceptions. Missing tools or noninteractive input similarly leave the
project available for later setup; optional setup failure does not invalidate a
successful core installation. The existing `nft`, `ip`, Python, systemd and core
utilities are prerequisites; no dependency download occurs at the school.

## Later setup and use

From an interactive Ubuntu terminal, when the operator has arranged safe access
and the upstream prerequisites are satisfied:

```bash
sudo bash /opt/ares/internet-lockdown/ares-lockdown-v1.4.2/install.sh --no-boot
```

The upstream installer refuses an in-place upgrade while lockdown is active or
boot lockdown is enabled. The ARES installer does not remove those protections
automatically. Use the supplied operating guide to arrange a later upgrade and
to choose temporary, permanent-for-this-boot or reboot-persistent operation.

The project provides `lockdown-internet`, `restore-internet` and
`ares-anydesk-diagnose`. A later reboot opt-in uses the supplied `install.sh
--boot` procedure and its live-test confirmation. No boot setting is selected by
the ARES master installer. The operating PDF is:

```text
/opt/ares/internet-lockdown/ares-lockdown-v1.4.2/ARES_Internet_Lockdown_README_v1.4.2.pdf
```

## Preservation and verification

The field bundle stores the entire project under
`remote-access/internet-lockdown/`, an existing generated component. Imported
files are excluded from profile text substitution and Git newline conversion.
The versioned release, including its original SHA256SUMS, stays byte-for-byte
identical in both ARES profiles. `ares.local` in the standalone operating examples
is retained as part of the supplied documentation, not rendered for a profile.

Independent ZIP verification compares every imported file against the reviewed
source and checks the upstream manifest. The shared offline audit recognizes
only the exact upstream error message recommending installation of missing
nftables; it does not allow execution of package installation or downloads.

The helper's service/firewall cases are exercised with fake commands and a fake
upstream system installer. Those tests do not establish live AnyDesk, Tailscale,
Docker, IPv6, mesh mDNS, restoration or reboot behavior. The handoff reports only
initial user-observed v1.4.2 success; its remaining field limitations are retained.
The v1.4.2 installer deliberately contains v1.4.1 firewall code/banners.
