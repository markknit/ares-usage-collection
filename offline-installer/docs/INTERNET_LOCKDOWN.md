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

The integration installs `lockdown-internet`, `restore-internet`,
`ares-configure-lockdown` and `ares-anydesk-diagnose` even when no network
adapter has an address or no interactive terminal is attached. The original
v1.4.2 source and firewall engine remain unchanged. No LAN address or interface
name is guessed or embedded at build time.

Installation does not apply firewall rules, enable boot persistence, start
Tailscale or download packages. It needs the existing OS tools (`nft`, `ip`,
Python and systemd). Missing prerequisites defer optional setup without failing
the successful core installation.

If lockdown is already active or enabled at boot, its runtime scripts, commands,
configuration and services are preserved. Optional remote/AnyDesk preparation
also defers, avoiding service restarts that could invalidate cgroup allowances.

## First use after connecting a network

Run from a local console or a separately arranged support connection:

```bash
lockdown-internet
```

If no current LAN mapping exists, this command asks which numbered interface and
subnet student devices actually use. It never silently trusts a modem-only
uplink, including when that is the only interface. If there is no eligible
student IPv4 LAN yet, selection remains pending; connect/configure the LAN and
run the same command again. Installing offline does not activate a firewall.
LAN selection requires a terminal; subsequent use reuses a current mapping.
The supplied engine then applies its normal five-minute rollback test.

Restore does not require any LAN selection or active adapter:

```bash
restore-internet
```

Reselect a LAN after a subnet/interface change with `ares-configure-lockdown`.
For Tailscale exceptions, bring it online first and use
`lockdown-internet --tailscale`. Other original options pass through unchanged.
The wrapper sends `--confirm` directly to the rule engine so an in-progress test
can be confirmed without an unrelated LAN configuration prompt.

The original `install.sh --boot` procedure remains a separate advanced opt-in,
after the documented live connectivity/recovery tests. It is not run by the ARES
master installer. The original versioned manual explains the firewall engine;
this guide describes the added deferred LAN-selection commands. The operating PDF is:



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

The integration's disconnected installation and service/firewall cases are
exercised with fake commands, while LAN selection is checked independently. Those tests do not establish live AnyDesk, Tailscale,
Docker, IPv6, mesh mDNS, restoration or reboot behavior. The handoff reports only
initial user-observed v1.4.2 success; its remaining field limitations are retained.
The v1.4.2 installer deliberately contains v1.4.1 firewall code/banners.
