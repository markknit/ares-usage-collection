# ARES Internet Lockdown — STATUS.md

**Release:** v1.4.2 (2026-11-02)  
**Handoff prepared:** 2026-11-02  
**Project:** ARES Education — Ubuntu/Nginx server internet restrictions  
**Purpose:** Standalone, evidence-based project handoff for importing the complete v1.4.2 distribution into an *existing* GitHub repository, maintaining it, diagnosing faults, and deploying subsequent versions safely.  
**Repository status:** Destination repository was not supplied; **nothing has been committed or pushed** by this handoff.  
**Deployment status:** User reports v1.4.2 “appears to be working ok” on `tsavo3`; this is an initial field observation, **not a completed acceptance test or production certification**.

> **Authoritative source of implementation truth:** the scripts in `ares-lockdown-v1.4.2/` inside `ARES_Internet_Lockdown_Package_v1.4.2.zip`. This STATUS file describes and reviews them; it does not replace reading the scripts. Do not confuse the separate GitHub handoff ZIP with the original installable distribution.

## 1. Executive status and decisions

The project temporarily prevents ordinary internet traffic to/from an ARES server while preserving essential remote support and same-subnet educational applications. It operates using an *additional, removable* `nftables` table, not by flushing pre-existing firewall configuration. v1.4.2 changes the **installer and documentation only**; its firewall and restoration scripts are byte-for-byte the v1.4.1 versions. This was verified from the package contents and supported by its release notes.

**Agreed deployment model:**

- **Mode A (`server`) — default and expected at most schools.** ARES hosts educational services and remains reachable from student devices over a **single flat IP subnet / layer-2 domain**. Student internet access through a separate router is a local school decision; ARES cannot filter packets that do not traverse it.
- **Mode B (`gateway`) — rare and advanced.** An administrator may configure clients to use ARES as the off-subnet gateway. The script labels the mode and blocks public forwarding, but **does not** configure DHCP, IP forwarding, NAT, upstream routing, or client gateway settings. Both modes currently block public forwarding.
- Mesh units (for example, Tenda Nova MW6) act as **access points/bridges**, not independently internet-connected routers. ARES may provide DHCP/DNS or a separate standalone router may do so. The USB Wi-Fi hotspot is a separate optional student-facing interface.
- `ares.local` discovery depends on mDNS being carried between wired and wireless devices on the flat LAN. Same-subnet addressing by itself does not prove multicast forwarding works; Tenda MW6 must still be field-tested.
- Optional internet uplink may be through USB modem, USB Ethernet, or another adapter. Some deployments share a physical NIC between local clients and the default internet route, which is why trusted traffic is defined by **both interface and IPv4 subnet**, not simply by RFC1918 address.

### Active threads / acceptance status

| Thread | State at handoff | Evidence / next action |
|---|---|---|
| v1.4.2 package integrity | **Verified locally** | Original ZIP extraction, `sha256sum -c SHA256SUMS` for all eight manifested files, ZIP integrity, and Bash syntax passed during handoff preparation. |
| Simplified installer | **Written; mock-tested in prior release; user reports initial success** | `install.sh` auto-discovers LAN and preserves wrappers. Release notes document mocked installation cases; no repeat production installer execution was performed during preparation of this STATUS file. |
| v1.4.2 firewall behavior | **Initial field success; not fully accepted** | User stated “appears to be working ok.” Recheck AnyDesk during lockdown *and after restore*, Tailscale SSH/VNC, local educational apps, and blocked ordinary HTTPS. |
| LAN/subnet validation | **Implemented; live coverage limited** | v1.4.1 code rejects missing NICs, out-of-subnet mappings, and overly broad subnet. Previously `wlp1s0` was configured but nonexistent on `tsavo3`. |
| AnyDesk exception/recovery | **Known unresolved reliability risk** | v1.4 originally disrupted AnyDesk and `restore-internet` alone did not revive it; a reboot was required. No conclusive per-process/socket root cause yet. Diagnostic helper included. |
| Tailscale exceptions | **Implemented; live re-test required after reboot** | Tailscale uses service-cgroup matching for TCP 443, `tailscale0` restrictions for SSH/VNC, and UDP transport allowances. Daemon restarts may invalidate the cgroup match. |
| Boot persistence | **Available, status on `tsavo3` unknown at this handoff** | `install.sh --boot` can install and enable a systemd one-shot service after a test confirmation; check `systemctl is-enabled`. Earlier `tsavo3` output showed `not-found`, before any subsequent installer decisions. |
| USB hotspot / multiple LANs | **Implemented; real topology test pending** | Installer can select multiple interface/subnet pairs; test with adapters present at boot and after removal/reinsertion. |
| Tenda MW6 mDNS | **Not yet verified** | User will test from client on each mesh node, including wireless backhaul and offline startup. |
| GitHub integration | **Not started** | Choose destination repository/branch, copy release subtree without overwriting existing files, review, commit, and push according to repo policy. |

## 2. Exact release contents and provenance

The **original** `ARES_Internet_Lockdown_Package_v1.4.2.zip` expands to:

```text
ares-lockdown-v1.4.2/
  install.sh                          # primary interactive installer
  install_lockdown_commands.sh        # compatibility entry point -> install.sh
  lockdown_internet.sh                # firewall rules, runtime options, test rollback
  restore_internet.sh                 # removes only ARES lockdown table
  ares_anydesk_diagnose.sh            # read-only AnyDesk process/socket snapshot
  README.md                           # concise installation/usage notes
  ARES_Internet_Lockdown_README_v1.4.2.pdf
  RELEASE_NOTES.txt                   # date and v1.4.2 changes
  SHA256SUMS                           # checksum manifest for other eight files
```

Validated source hashes from the original package (SHA-256):

```text
5e39717038dae558277a5af0604dda91c8fe576571fc589aace361ea9ebabd3b  install.sh
2a2249eb9497327d51c7cca6728db59cd8c7f8c1a8b4ad8555a3526d6cae9b1b  install_lockdown_commands.sh
a7890ef0b00625952eca20b5715e0524b0aa4d223745e8b99c766f6dfec38541  lockdown_internet.sh
7dcd25311b783c5bf4ca71b7db6d782d1c065cf2bf61613a0d75250db44a532c  restore_internet.sh
96c7a881d851770ee232ad313541f8729ad89463952864d11f66ec1fdd228eb1  ares_anydesk_diagnose.sh
```

Check the full manifest after extracting:

```bash
cd ares-lockdown-v1.4.2
sha256sum -c SHA256SUMS
bash -n install.sh install_lockdown_commands.sh lockdown_internet.sh \
  restore_internet.sh ares_anydesk_diagnose.sh
```

**Do not regenerate hashes or silently edit the versioned scripts while importing them.** Any later behavior changes warrant a new release/version, tests, updated notes, and renewed checksums. The original v1.4.2 installer/lockdown script prints `v1.4.1` in some firewall messages because the firewall code was deliberately unchanged.

### Version history and why decisions changed

| Version | Important change / lesson |
|---|---|
| Initial | Explicit SSH 22, VNC 5901/5909, AnyDesk port exceptions, manual restore and temporary rollback. |
| v1.2 | Added Tailscale. Allowing unrestricted outbound TCP 443 kept Tailscale working but also allowed general HTTPS browsing; unacceptable as full server lockdown. |
| v1.3 | Restricted TCP 443 to connections attributed to `tailscaled.service` using nftables cgroup v2 socket matching. Added optional systemd persistence. |
| v1.4 | Replaced unrestricted RFC1918 trust with explicit student-facing interfaces; a stale/wrong interface (`wlp1s0`) and AnyDesk disruptions caused failed field acceptance. |
| v1.4.1 | Required `interface=exact IPv4 subnet` mappings, validated that interface/address actually exist; added read-only AnyDesk diagnostics. |
| **v1.4.2** | **Installer simplification only:** automatic discovery/reuse, fewer prompts, backups, wrapper preservation, conservative boot opt-in. No change to filter or restore scripts. |

## 3. Network architecture and operating assumptions

### Typical flat-network (Mode A) deployment

```text
                 optional Internet uplink
                (modem / Ethernet / Wi-Fi)
                           |
                 [ ARES Ubuntu server ]
                 applications + firewall
                 DHCP/DNS at some schools
                           |
                      flat school LAN
                           |
                 [ bridge-mode mesh APs ]
                           |
               students' phones / laptops
```

Alternatively, a **standalone** LAN router provides DHCP/DNS on the *same subnet*. It may also be the clients' internet gateway. In that case the ARES firewall limits traffic **to/from the server**, but cannot stop independent client-to-router internet traffic. ARES-as-gateway is optional, and should never be inferred merely because a standalone router exists.

For `tsavo3`, previously observed **diagnostic examples only**, not reusable school defaults:

```text
LAN + default-route interface: wlxe84e0698ec2b
LAN IPv4:                     192.168.12.113/24
LAN IPv4 network:             192.168.12.0/24
Default route:                via 192.168.12.1
Tailscale interface:          tailscale0
Tailscale IPv4 (variable):    100.x.y.z (do not hardcode in repository)
Docker bridges observed:      docker0, br-2707aa628daa
Bad prior configured NIC:     wlp1s0   (not present)
```

**Never copy these interface names/IP addresses into another school's configuration.** The Tailscale hostname and Tailscale IPv4 address are not hardcoded in the rules.

### mDNS and the bridge requirement

`ares.local` uses mDNS (UDP 5353, IPv4 224.0.0.251 / IPv6 ff02::fb), not standard upstream DNS routing. ARES and ordinary users should share the flat layer-2 multicast domain. Bridge-mode wireless APs must not enable guest isolation or client-to-wired blocking; mesh/backhaul behavior remains vendor- and firmware-dependent. Test per node, including reboot without internet. With a standalone DNS router, do not assume its DNS cache substitutes for mDNS.

## 4. Firewall architecture (as implemented)

### Rule ownership, ordering and lifecycle

- Creates an independent `inet` nftables table named **`ares_internet_lockdown`**.
- Chains `input_lockdown`, `output_lockdown`, and `forward_lockdown` attach to the `input`, `output`, and `forward` hooks at priority **`-150`**. Each chain's policy is `accept`, but the last explicit rule is `counter drop`, so traffic not matching an earlier exception is denied.
- `nft -c -f` validates generated rules before application. `--check` stops after checking and never installs the table.
- The firewall script refuses to apply a second lockdown while that table exists. Restoration deletes **only** that table. It does **not** flush UFW, Docker or unrelated nftables rules, reverse NAT changes, reset applications, or disable a boot service.
- **An `accept` in this additional base chain cannot override a later `drop` by another firewall chain.** Docker/UFW/other rules may still affect connectivity; inspect the whole `nft list ruleset` if diagnosing interaction.
- Temporary mode schedules a `systemd-run` timer to call `/usr/local/sbin/restore_internet.sh` after **5 minutes**. `--confirm` cancels an existing rollback timer; it is **not** a command to initiate lockdown. `--permanent` applies without that timer, but is **not** persistent across reboot.

### Network allowances and restrictions

| Packet class | Intended disposition in v1.4.2 |
|---|---|
| Loopback `lo` | Permitted. |
| Trusted **student-facing interface AND matching IPv4 subnet** | Incoming traffic from that subnet and outgoing traffic to it permitted, preserving local ARES browser apps. Local broadcast/multicast, DHCP and link-local/ULA IPv6 exceptions also exist. |
| Other private-address networks on an untrusted uplink | **Not automatically trusted** just for being RFC1918. |
| SSH TCP 22 / VNC TCP 5901 and 5909 | Permitted inbound and outbound on non-Tailscale interfaces as port exceptions; over `tailscale0`, only these TCP service ports and supporting traffic are allowed. |
| AnyDesk TCP 6568 | Permitted outbound generally and inbound established replies; this is a **port exception**, not proof that only AnyDesk uses it. |
| AnyDesk fallback `--anydesk-fallback` | Experimental outbound TCP 80/443 only if socket matches `anydesk.service` cgroup. May miss separately launched user-session processes. Do not assume successful without testing. |
| Tailscale transport with `--tailscale` | Direct UDP uses default local port 41641 (override via `ARES_TAILSCALE_UDP_PORT`), outbound UDP/3478 for NAT traversal, and outbound TCP/443 only from `tailscaled.service` cgroup. Return traffic is allowed per explicit rules. |
| `tailscale0` overlay | SSH/VNC and supporting DNS (`100.100.100.100`) and ICMP permitted; other overlay traffic dropped. Without `--tailscale`, the overlay interface is dropped. |
| DNS | Outbound TCP/UDP 53 permitted generally; incoming established DNS replies permitted. This supports resolver operation but is **not** a tightly scoped DNS-only-for-Tailscale rule. |
| DHCP / IPv6 network control / ICMP | Explicit allowance for service/network operation. |
| Docker bridge networks | Local private Docker addresses and some bridge-to-LAN forwarding permitted; public forwarding dropped. External Docker/NAT rules still require integration testing. |
| Public forwarded traffic | **Dropped in Mode A and Mode B** unless covered by a specific earlier allowance; this is not a full gateway setup tool. |
| General server HTTPS browsing | Intended to be blocked unless an application happens to use an allowed exception (e.g. service-scoped 443 or allowed private destination); verify from the server. |

**Scope limitations:** this is primarily an operational-access firewall, not malware containment or a cryptographically enforced application allowlist. Open TCP ports can be used by other software; DNS/ICMP and some multicast exceptions remain. The untrusted side's TCP 22/5901/5909 exceptions are broad, not limited to designated support IPs. Privileged users/processes can alter the firewall. No guarantee of internet isolation on traffic bypassing ARES (separate gateway, cellular device, a secondary route, or bridged path). IPv6 requires an explicit test on every deployment.

### Service cgroup matching and restart caveat

The TCP 443 Tailscale exception uses `socket cgroupv2` for the active `tailscaled.service` (systemd cgroup v2). The experimental AnyDesk fallback uses the cgroup for `anydesk.service`. **Changing service cgroups or restarting daemons while lockdown is active can invalidate these matches**. A service marked `active` does not prove every socket uses that cgroup, especially AnyDesk's desktop session process. Confirm with the included diagnostic utility; if necessary restore safely, restart the affected daemon, then repeat a temporary lockdown test. Avoid indiscriminately opening TCP 443 to all applications; that was the v1.2 regression.

## 5. Installer behavior and installed paths

### Normal installation

```bash
unzip ARES_Internet_Lockdown_Package_v1.4.2.zip
cd ares-lockdown-v1.4.2
bash install.sh
```

The installer requires working `ip`, `python3`, `nft`, `systemctl`, `install`, `cmp` and `date`, and root authorization through `sudo`; it does **not** install Ubuntu packages or start Tailscale for you. It refuses to upgrade while the ARES lockdown table is active or the boot lockdown service is already enabled. Restore/disable first from a safe console. On a single eligible LAN interface, it auto-detects `interface=IPv4 network/CIDR`, asking for confirmation if that interface also has the system's default route. On multiple interfaces, it asks for numbered selections. It reuses an existing **valid** subnet mapping; still review whether the mapping is intended for students. Avoid selecting a modem-only interface.

**Installed system files:**

```text
/etc/ares/internet-lockdown.conf             root:root 0600
/usr/local/sbin/lockdown_internet.sh         0700
/usr/local/sbin/restore_internet.sh          0700
/usr/local/sbin/ares_anydesk_diagnose.sh     0700
/usr/local/bin/lockdown-internet             auto-sudo wrapper, when not already present
/usr/local/bin/restore-internet              auto-sudo wrapper
/usr/local/bin/ares-anydesk-diagnose         auto-sudo wrapper
/usr/local/bin/lockdown_internet             compatibility symlink
/usr/local/bin/restore_internet              compatibility symlink
/etc/systemd/system/ares-internet-lockdown.service   created only if boot opt-in
```

The installer backs up changed script/config files using timestamped `.bak.YYYYMMDD-HHMMSS` names; identical scripts are not rewritten. Existing compatible wrappers are preserved. A name conflict causes an error **but installation is not fully transactional**: review any files already installed before retrying.

Configuration file values follow this pattern (illustrative; do not copy blindly):

```bash
ARES_LAN_NETWORKS='wlxe84e0698ec2b=192.168.12.0/24'
ARES_MODE=server
```

The actual generated file uses shell-escaped assignments and is sourced by the privileged lockdown script. It **must** be owned by root and mode `0600`. `--mode gateway` is an advanced label only; it does not enable routing. For an interface unavailable at install or activation (e.g., detached USB AP), install or reconfigure only after that interface is present and has the intended address, or lockdown validation will fail.

### Installer options

```text
bash install.sh                     normal auto-detected install; boot question defaults No
bash install.sh --boot              opt into reboot service after explicit live-test YES
bash install.sh --no-boot           skip boot opt-in
bash install.sh --lan 'IFACE=NET/CIDR [IFACE=NET/CIDR ...]'
bash install.sh --mode gateway      advanced mode; NOT routing/NAT configuration
bash install_lockdown_commands.sh   legacy entry point; forwards to install.sh
```

Installer preflight invokes the installed firewall script with `--tailscale --check`; if it cannot check Tailscale/cgroup/nftables readiness, it warns and **must not** enable the boot service. Installation itself does not activate lockdown.

## 6. Operator command reference

| Operator command | Meaning |
|---|---|
| `lockdown-internet --tailscale --check` | Validate current config, service identity and nft syntax; does **not** activate firewall. Run while table is absent. |
| `lockdown-internet --tailscale` | Temporary 5-minute rollback test. |
| `lockdown-internet --confirm` | Cancel the *currently pending* 5-minute rollback; leaves lockdown active until restore/reboot. |
| `lockdown-internet --permanent --tailscale` | Apply lockdown with no automatic restore timer; applies to **current boot only**. |
| `lockdown-internet --tailscale --anydesk-fallback` | Experimental AnyDesk HTTP/HTTPS service-cgroup exception in temporary test. |
| `restore-internet` | Delete ARES nft table and cancel pending test timer; does **not** restart AnyDesk or disable boot service. |
| `ares-anydesk-diagnose` | Read-only service/cgroup/socket snapshot; output can contain remote IP addresses. |
| `bash install.sh --boot` | Enable systemd boot application *after* preflight and explicit test confirmation. |

Hyphenated commands are wrappers that invoke `sudo` if required. Underscore commands are symlinks to root-requiring scripts. If a wrapper is missing, call its explicit path with `sudo`, e.g. `sudo /usr/local/sbin/restore_internet.sh`.

**Order matters:** if you previously applied temporary mode, restore or confirm it before attempting another activation. Do not apply `--permanent` on top of an active table; the script refuses it. To change mode or fallback options, restore first, then activate with the new flags.

## 7. Safe field acceptance protocol (required for each server/profile)

1. **Recoverable baseline:** have local console or known-working LAN/Tailscale SSH access; make sure `restore-internet` works and AnyDesk is connected before beginning. Record IPs/interfaces: `ip -br -4 address`, `ip route`, `tailscale status`. Confirm no legacy `@reboot` lockdown cron entry and no unexpected active boot service.
2. **Validate the real topology:** `sudo cat /etc/ares/internet-lockdown.conf`, `ip -br -4 address`, `ip -4 route show default`. Check each configured `interface=IPv4/CIDR` pair; do not trust an upstream-only modem LAN.
3. **Preflight:** `lockdown-internet --tailscale --check`. A passing preflight checks syntactic and dependency readiness; it does **not** prove live data flows.
4. **Start temporary lockdown:** `lockdown-internet --tailscale`; do not use `--permanent` initially. The automatic restoration window is five minutes.
5. **Exercise remote support from a *second* device:** live AnyDesk login, Tailscale SSH TCP 22, VNC TCP 5901 and 5909 as applicable. Do not equate `tailscale status` with tested SSH or VNC data paths.
6. **Exercise student access:** a student phone/laptop connected via each AP or USB hotspot opens `http://ares.local/` and the relevant Nginx/Kiwix/Kolibri/lesson-editor resources. Check DHCP/DNS as relevant, and try both an mDNS name and direct ARES IP to isolate discovery failures.
7. **Exercise blocking:** ordinary internet browsing on the **ARES server** must fail over IPv4 and IPv6. In Mode B only, explicitly test off-subnet forwarding from a student device. In Mode A, a separate router's student internet policy is *outside the ARES firewall's control*.
8. **Restore and recheck:** `restore-internet`; confirm the nft table is absent, ordinary server connectivity returns, and **AnyDesk reconnects without reboot**. If not, capture diagnostics *before* restarting services; `sudo systemctl restart anydesk` is a recovery option after gathering evidence.
9. **Only after all relevant tests pass:** choose `lockdown-internet --permanent --tailscale` and, separately, `bash install.sh --boot` if the school requires reboot persistence. Perform a supervised reboot test with an alternative path available; inspect service status, table existence and connectivity after reboot.

**Minimum acceptance evidence to save per school:** date, hostname, OS, physical/AP/hotspot interfaces and subnets, selected profile, DNS/DHCP provider, command flags, expected/observed result for each test, logs or screenshots for failures, whether reboot persistence is enabled, and the technician approving the result. Avoid storing AnyDesk credentials or private keys in Git.

## 8. Diagnose and repair — decision tree

### A. Commands unavailable / installation or version mismatch

```bash
command -v lockdown-internet restore-internet ares-anydesk-diagnose
type -a lockdown-internet
ls -l /usr/local/sbin/lockdown_internet.sh /usr/local/bin/lockdown-internet
grep -nE 'v1\.4\.1|ARES_LAN_NETWORKS|--tailscale' /usr/local/sbin/lockdown_internet.sh | head
```

The code is expected to identify the firewall rules as **v1.4.1** inside a **v1.4.2 installer release**. If the command rejects `--tailscale`, it may point to an older wrapper/script. Inspect the actual file path, then install from the verified release with lockdown disabled. Do not replace scripts while the table is active or boot service enabled.

### B. Invalid LAN interface, missing config, or wrong subnet

```bash
ip -br -4 address
ip -4 route show default
sudo ls -l /etc/ares/internet-lockdown.conf
sudo cat /etc/ares/internet-lockdown.conf
lockdown-internet --tailscale --check
```

Prior incident: `wlp1s0` did not exist; the live adapter was `wlxe84e0698ec2b`. Never blindly copy a network interface or subnet from another school. With restored connectivity and disabled boot service, rerun `bash install.sh` to auto-discover, or use `--lan` for exceptional multi-interface layouts. A LAN interface that also carries the default route is acceptable only when its **specific local subnet** serves real ARES clients.

### C. Lockdown active / restore appears ineffective

```bash
sudo nft list table inet ares_internet_lockdown
sudo nft list ruleset
sudo systemctl is-enabled ares-internet-lockdown.service
sudo systemctl status ares-internet-lockdown.service --no-pager
restore-internet
sudo nft list table inet ares_internet_lockdown
```

Expected after successful restore: `nft` reports **No such file or directory** for that ARES table. If table is gone but network access is still broken, investigate the application or other firewall rules; `restore-internet` does not reset AnyDesk, routing, DNS, Docker, UFW, or Tailscale. A boot service (if enabled) will reapply lockdown **on next reboot**, even after a manual restore.

### D. AnyDesk blocked, or fails to recover after restore

```bash
sudo ares-anydesk-diagnose
systemctl is-active anydesk
systemctl show -P ControlGroup anydesk.service
ps -C anydesk -o pid,uid,comm
sudo ss -tunap | grep -i anydesk
```

Collect the snapshot **before lockdown**, **during temporary lockdown**, and **after restore** if possible. Compare whether AnyDesk sockets are owned by `anydesk.service` or another desktop/user-session cgroup; the experimental `--anydesk-fallback` covers only the former. If the table is absent but AnyDesk is still disconnected, after recording logs try:

```bash
sudo journalctl -u anydesk -b -n 100 --no-pager
sudo systemctl restart anydesk
systemctl status anydesk --no-pager
```

If a service restart restores connectivity, that is diagnostic evidence but not proof of the underlying root cause. An earlier v1.4 test required a reboot; do not mark recovery fixed until a full lockdown → restore → reconnect cycle passes repeatedly. Never assume allowing arbitrary TCP 443 is acceptable: it permits general browser HTTPS.

### E. Tailscale SSH/VNC or AnyDesk breaks after daemon restart

```bash
systemctl is-active tailscaled
systemctl show -P ControlGroup tailscaled.service
tailscale status
tailscale netcheck
sudo nft -a list table inet ares_internet_lockdown
sudo journalctl -u tailscaled -b -n 100 --no-pager
```

Check connectivity **from a second online tailnet device**. If cgroup identity changed after a restart, from local console or reliable LAN path: `restore-internet`; restart Tailscale/AnyDesk as appropriate; `lockdown-internet --tailscale --check`; then test temporary lockdown again. The default UDP port is 41641; only override `ARES_TAILSCALE_UDP_PORT` when the daemon actually uses another local port. Do not hardcode tailnet hostnames/IPs into the generic package.

### F. ARES web apps work by IP but `ares.local` fails

```bash
ip -br address
systemctl is-active avahi-daemon
sudo tcpdump -ni <REAL_LAN_INTERFACE> 'udp port 5353'
```

Replace `<REAL_LAN_INTERFACE>` with the verified client-facing NIC. Confirm both client and ARES are in the same subnet/layer-2 domain, client isolation is disabled, and mesh nodes bridge multicast. Test direct `http://<ARES_IP>/` separately from `http://ares.local/`. A name-resolution failure does not necessarily mean Nginx or the firewall blocked HTTP. Record results for every Tenda MW6 node, including any wireless backhaul segment.

### G. DHCP/DNS or client internet forwarding differs from expectation

Identify which device runs DHCP/DNS; inspect the client's actual address, mask, router/default gateway and DNS server. When ARES is not students' gateway, their traffic through a standalone router is not under ARES firewall control. When ARES is meant to be gateway, separately check Linux forwarding, return routes/NAT if applicable and IPv6 router advertisements. The current `--mode gateway` flag **does not configure those services**. Do not solve missing DHCP by allowing all inbound traffic from every interface.

### H. Reboot service fails / fails to apply policy

```bash
sudo systemctl is-enabled ares-internet-lockdown.service
sudo systemctl status ares-internet-lockdown.service --no-pager
sudo journalctl -u ares-internet-lockdown.service -b --no-pager
sudo nft list table inet ares_internet_lockdown
systemctl status tailscaled --no-pager
```

The service is a systemd `Type=oneshot` unit with `Requires=tailscaled.service`, `After=network-online.target tailscaled.service`, and `ExecStartPre` waiting for `tailscale0` to appear (up to 90 seconds). It calls `lockdown_internet.sh --permanent --tailscale`. **Critical failure mode:** if this unit fails at startup, the server may boot **without** the ARES firewall table and therefore without the expected lockdown. The unit does **not** guarantee fail-closed boot isolation. For high-assurance deployments, engineer/test a separate fail-closed bootstrap policy before relying on unattended reboot protection.

To turn off future boot lockdown from safe access:

```bash
sudo systemctl disable ares-internet-lockdown.service
restore-internet
```

`systemctl disable --now` may report `not-found` when the optional service was never installed. Do not interpret that as evidence of a firewall failure.

## 9. GitHub repository import and synchronization

**No destination repository URL/path, branch, or repo policy was provided. Nothing has been pushed or modified in GitHub.** Prefer an isolated subtree inside the existing repository, for example:

```text
<existing-repo>/
  tools/
    ares-internet-lockdown/
      STATUS.md
      ares-lockdown-v1.4.2/
        install.sh
        install_lockdown_commands.sh
        lockdown_internet.sh
        restore_internet.sh
        ares_anydesk_diagnose.sh
        README.md
        ARES_Internet_Lockdown_README_v1.4.2.pdf
        RELEASE_NOTES.txt
        SHA256SUMS
```

Do **not** overwrite a pre-existing repository-root `STATUS.md` or `CLAUDE.md`. Keep this handoff at `tools/ares-internet-lockdown/STATUS.md`, and add a short link from the repository's existing project status if desired. If there is already an ARES lockdown directory, compare and merge manually rather than overwriting it.

### Windows PowerShell — import from the supplied handoff ZIP

The companion **GitHub handoff ZIP** is structured with a top-level `ares-internet-lockdown/` folder, so extraction directly into `tools/` produces the layout above. Adjust the download and repository locations:

```powershell
cd 'C:\path\to\existing-repo'
git status --short                 # review; do not overwrite uncommitted work
git pull --ff-only                 # only if current branch/upstream is correct
git switch -c feat/ares-internet-lockdown-1.4.2

# Refuse to overwrite an existing destination.
if (Test-Path '.\tools\ares-internet-lockdown') {
    throw 'Destination exists; compare and merge manually.'
}
New-Item -ItemType Directory -Force '.\tools' | Out-Null
Expand-Archive -LiteralPath 'C:\path\to\ARES_Internet_Lockdown_v1.4.2_GitHub_Handoff.zip' -DestinationPath '.\tools'

Push-Location '.\tools\ares-internet-lockdown\ares-lockdown-v1.4.2'
# Verify every release file against the included SHA256SUMS manifest.
Get-Content SHA256SUMS | ForEach-Object {
    if ($_ -notmatch '^([a-fA-F0-9]{64})  (.+)$') { throw "Malformed manifest entry: $_" }
    $expected = $matches[1].ToLowerInvariant()
    $filename = $matches[2]
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $filename).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "Checksum mismatch: $filename" }
}
Write-Host 'Release SHA256 checks passed.' 
Pop-Location

git add -- tools/ares-internet-lockdown/
git diff --cached --check
git diff --cached --stat
git commit -m 'Import ARES internet lockdown v1.4.2 and handoff status'
git push -u origin feat/ares-internet-lockdown-1.4.2
```

If using a different repository layout or a branch with ongoing work, follow that repository's `AGENTS.md`, `CLAUDE.md`, review and branch-protection rules. Open a pull request if required; do not push directly to protected `main`.

### Linux — equivalent import

```bash
cd /path/to/existing-repo
git status --short
git pull --ff-only
git switch -c feat/ares-internet-lockdown-1.4.2
test ! -e tools/ares-internet-lockdown || { echo 'Directory exists: review first'; exit 1; }
mkdir -p tools
unzip /path/to/ARES_Internet_Lockdown_v1.4.2_GitHub_Handoff.zip -d tools
(cd tools/ares-internet-lockdown/ares-lockdown-v1.4.2 && sha256sum -c SHA256SUMS)
git add -- tools/ares-internet-lockdown/
git diff --cached --check
git diff --cached --stat
git commit -m 'Import ARES internet lockdown v1.4.2 and handoff status'
git push -u origin feat/ares-internet-lockdown-1.4.2
```

**Synchronizing another clone** after a PR is merged: use `git fetch`, then `git switch <target-branch>` and `git pull --ff-only` (or `git pull` according to your repo's policy). A `git pull` into Windows or Ubuntu updates the **repository checkout only**. It does **not** replace active `/usr/local/sbin/` scripts, `/etc/ares/` configuration, `/usr/local/bin/` wrappers, or the systemd service. A server deployment remains a **separate, deliberately authorized** `bash install.sh` action followed by safety testing.

**Security:** never commit `/etc/ares` site-specific secrets, AnyDesk credentials, Tailscale authentication material, private student data, `/run/` state, full `nft list ruleset` containing sensitive local identifiers, or raw socket logs with remote IPs unless reviewed and sanitized. Store verified release scripts/docs and sanitized test reports only.

## 10. Lasting lessons and open risks

1. **LAN interface names drift.** NICs like `wlx...` change across adapters. Auto-discover and validate interface+subnet; do not trust a placeholder or every RFC1918 address.
2. **Port 443 cannot be opened globally for Tailscale while claiming to block browsing.** The v1.3 service-cgroup restriction was introduced to prevent this exact mistake, but it adds a daemon-restart dependency.
3. **A running AnyDesk service does not prove its traffic is covered.** Desktop-session sockets can differ from `anydesk.service`; test actual remote connectivity and successful reconnection after restore.
4. **`restore-internet` is a firewall-table rollback, not an application reset.** If AnyDesk remains disconnected with the table absent, capture diagnostics and consider a service restart; don't reboot as the only initial troubleshooting step.
5. **Boot persistence and fail-closed boot are not the same.** The included service runs after network/Tailscale readiness; if it fails, an unfiltered network may remain. Verify after every significant OS/network service change.
6. **Mode A cannot control an independent school gateway.** Student internet privileges through a separate router remain a school policy; not an ARES firewall defect.
7. **mDNS requires a working layer-2 multicast path, not just matching IPv4 prefixes.** Flat subnet is the design rule; each mesh model/backhaul still needs verification.
8. **Docker services and IPv6 need explicit smoke tests.** An additional `nftables` chain can interact with existing Docker/UFW behavior and with untested IPv6 paths.
9. **Installer upgrades are not atomic.** Stop when encountering a command conflict; inventory what changed and review backup copies before retrying.
10. **Version accuracy matters.** v1.4.2 packages v1.4.1 firewall code. Do not assume the banner's `v1.4.1` text means the new installer was not installed.

### Still open — proposed next actions

- [ ] Record full v1.4.2 live acceptance results for AnyDesk (lockdown and restore), Tailscale SSH/VNC, server HTTPS blocked, student apps, DNS/DHCP and IPv6 on `tsavo3`.
- [ ] Test automatic reboot lockdown with alternate access, and explicitly verify the firewall table after reboot; decide whether fail-closed boot is required for school policy.
- [ ] Conduct the user's Tenda Nova MW6 mDNS test, including remote mesh node and wireless backhaul.
- [ ] Test a USB hotspot and a separate student-facing Ethernet mesh interface on a representative school build.
- [ ] Investigate AnyDesk user-session socket ownership; if confirmed mismatch, design/review a more reliable application-aware exception rather than opening general HTTPS.
- [ ] Decide how to detect and refresh service-scoped nft rules when `tailscaled`/`anydesk` restarts.
- [ ] Decide whether Mode B needs a separate dedicated gateway profile and validation; avoid pretending the current `--mode` flag configures actual routing.
- [ ] Choose destination GitHub repository, branch/review policy, import subtree, verify checksums, commit/push, and cross-link to any pre-existing root `STATUS.md`.

## 11. Handoff verification log — 2026-11-02

**Local evidence checked during this handoff:** extracted the actual v1.4.2 ZIP; inspected `README.md`, `RELEASE_NOTES.txt`, `SHA256SUMS`, installer, firewall, restore and AnyDesk diagnostic scripts; ran package integrity, SHA-256 manifest verification and `bash -n` for all five `.sh` files. All passed. The source package contains eight manifested files plus the checksum manifest. There was **no** project repository or prior project `STATUS.md` supplied for in-place modification, so this is a **new standalone** status/handoff artifact. No Git operations, kernel/nftables activation, production login or network tests were performed by this handoff.

**User field observation:** On 2026-11-02, user reported that v1.4.2 “appears to be working ok” following the simplified installation. Do not expand that report into claims that the reboot, full AnyDesk recovery, all AP nodes, or both profiles have been formally validated.

**Still open at session close:** complete field acceptance, perform GitHub import to the chosen repository, and resolve operational caveats above.
