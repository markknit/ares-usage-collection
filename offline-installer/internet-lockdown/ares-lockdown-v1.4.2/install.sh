#!/usr/bin/env bash
# ARES Internet Lockdown v1.4.2 - simplified installer.
# Firewall rules remain identical to the field-tested v1.4.1 release.
set -Eeuo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
SUDO=()
if (( EUID != 0 )); then
    command -v sudo >/dev/null || { echo 'ERROR: sudo is required.' >&2; exit 1; }
    SUDO=(sudo)
    sudo -v
fi
CONF=/etc/ares/internet-lockdown.conf
UNIT=/etc/systemd/system/ares-internet-lockdown.service
BOOT_CHOICE=ask
FORCED_LAN=''
MODE_CHOICE=''
while (( $# )); do
    case "$1" in
        --boot) BOOT_CHOICE=yes ;;
        --no-boot) BOOT_CHOICE=no ;;
        --lan) shift; (( $# )) || { echo 'Missing --lan value.' >&2; exit 2; }; FORCED_LAN="$1" ;;
        --mode) shift; (( $# )) || exit 2; MODE_CHOICE="$1" ;;
        -h|--help)
            cat <<'HELP'
Usage: bash install.sh [--boot | --no-boot] [--lan 'iface=network/CIDR ...'] [--mode server|gateway]
Normal installation auto-detects the LAN and asks one optional boot question.
--boot enables reboot persistence only after operator confirms live tests.
--no-boot skips the boot question and preserves existing disabled state.
--lan overrides automatic interface detection when needed.
--mode gateway selects advanced gateway labeling; default is server-only.
HELP
            exit 0 ;;
        *) echo "Unknown installer option: $1" >&2; exit 2 ;;
    esac
    shift
done
[[ "$MODE_CHOICE" == '' || "$MODE_CHOICE" == server || "$MODE_CHOICE" == gateway ]] || { echo 'ERROR: --mode must be server or gateway.' >&2; exit 2; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: Missing '$1'. Install it before continuing." >&2; exit 1; }; }
for c in ip python3 nft systemctl install cmp date; do need "$c"; done
[[ -f "$HERE/lockdown_internet.sh" && -f "$HERE/restore_internet.sh" ]] || { echo 'ERROR: Missing packaged firewall scripts.' >&2; exit 1; }
if "${SUDO[@]}" systemctl is-enabled --quiet ares-internet-lockdown.service 2>/dev/null; then
    echo 'ERROR: Existing boot lockdown is enabled. Do not upgrade live rules.' >&2
    echo 'After arranging alternative access, disable it with:' >&2
    echo '  sudo systemctl disable ares-internet-lockdown.service' >&2
    exit 1
fi
if "${SUDO[@]}" nft list table inet ares_internet_lockdown >/dev/null 2>&1; then
    echo 'ERROR: Lockdown is active. Restore from safe access before upgrading:' >&2
    echo '  restore-internet' >&2
    exit 1
fi

# Candidate discovery uses the actual configured IPv4 networks; no interface names,
# IP addresses, or subnet masks are hardcoded into the installation package.
detect() {
    python3 - <<'PY'
import json,subprocess,ipaddress
obj=json.loads(subprocess.check_output(['ip','-j','-4','addr','show'],text=True))
for dev in obj:
    name=dev['ifname']
    if name in ('lo','tailscale0','docker0') or name.startswith(('br-','veth','virbr','wg','tun')):
        continue
    for addr in dev.get('addr_info',[]):
        if addr.get('family')!='inet' or addr.get('local','').startswith('169.254.'):
            continue
        try:
            local=ipaddress.ip_interface(f"{addr['local']}/{addr['prefixlen']}")
        except (ValueError,KeyError):
            continue
        network=local.network
        if network.is_loopback or network.is_multicast or network.prefixlen==0:
            continue
        print(f'{name}={network}')
PY
}
validate() {
    python3 - "$1" <<'PY'
import json,subprocess,ipaddress,sys,re
pairs=sys.argv[1].replace(',',' ').split()
if not pairs: sys.exit('ERROR: Missing LAN network selection')
addresses=json.loads(subprocess.check_output(['ip','-j','-4','addr','show'],text=True))
bydev={d['ifname']:[a.get('local') for a in d.get('addr_info',[]) if a.get('family')=='inet'] for d in addresses}
seen=set()
for pair in pairs:
    if pair.count('=')!=1: sys.exit('ERROR: Expected interface=subnet/CIDR: '+pair)
    name,nets=pair.split('=')
    if not re.fullmatch('[A-Za-z0-9_.:@-]{1,15}',name): sys.exit('ERROR: Invalid interface: '+name)
    if name in ('lo','tailscale0','docker0') or name.startswith(('br-','veth','virbr','wg','tun')):
        sys.exit('ERROR: Not a student LAN interface: '+name)
    try: network=ipaddress.IPv4Network(nets,strict=True)
    except ValueError: sys.exit('ERROR: Invalid LAN subnet: '+nets)
    if network.prefixlen==0 or network.is_multicast or network.is_loopback:
        sys.exit('ERROR: Invalid or excessively broad LAN subnet: '+nets)
    if (name,nets) in seen: sys.exit('ERROR: Duplicate LAN mapping')
    seen.add((name,nets))
    if name not in bydev or not any(ipaddress.IPv4Address(ip) in network for ip in bydev[name] if ip):
        sys.exit('ERROR: '+name+' has no IPv4 address in '+nets)
print('Validated LAN: '+', '.join(pairs))
PY
}
existing() {
    [[ -f "$CONF" ]] || return 0
    # The existing config is already root-owned and sourced by the lockdown script.
    "${SUDO[@]}" bash -c 'source "$1"; printf "%s" "${ARES_LAN_NETWORKS:-}"' _ "$CONF"
}
read_prompt() { local answer; read -r -p "$1" answer || answer=''; printf '%s' "$answer"; }

LAN=''
if [[ -n "$FORCED_LAN" ]]; then
    LAN="$FORCED_LAN"
else
    OLD=$(existing)
    if [[ -n "$OLD" ]] && validate "$OLD" >/dev/null 2>&1; then
        LAN="$OLD"
        echo "Using existing valid LAN configuration: $LAN"
    else
        FOUND=$(detect)
        mapfile -t OPTIONS <<< "$FOUND"
        if [[ -z "$FOUND" ]]; then
            echo 'ERROR: No eligible IPv4 LAN interface detected. Connect the LAN or use --lan.' >&2
            exit 1
        elif (( ${#OPTIONS[@]} == 1 )); then
            LAN="${OPTIONS[0]}"
            echo "Automatically detected LAN candidate: $LAN"
            default_if=$(ip -4 route show default 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev") {print $(i+1); exit}}' || true)
            if [[ "${LAN%%=*}" == "$default_if" && -n "$default_if" ]]; then
                echo 'This interface ALSO carries the default Internet route.'
                echo 'It is safe to trust as a LAN ONLY when local student devices use its subnet.'
                ans=$(read_prompt 'Is this interface used by student devices to access ARES? [y/N] ')
                [[ "$ans" =~ ^([yY]|[yY][eE][sS])$ ]] || {
                    echo 'ERROR: No LAN approved. Connect the real LAN or specify --lan.' >&2
                    exit 1
                }
            fi
        else
            echo 'Multiple network interfaces detected. Select only the student-facing LAN(s):'
            i=1
            for entry in "${OPTIONS[@]}"; do printf '  %d) %s\n' "$i" "$entry"; ((i+=1)); done
            echo 'Do NOT select a modem-only or upstream network.'
            selected=$(read_prompt 'Enter number(s), separated by commas: ')
            [[ -n "$selected" && "$selected" =~ ^[0-9]+(,[0-9]+)*$ ]] || { echo 'ERROR: Selection required.' >&2; exit 1; }
            LAN=''
            IFS=',' read -r -a CHOSEN <<< "$selected"
            for idx in "${CHOSEN[@]}"; do
                (( 10#$idx >= 1 && 10#$idx <= ${#OPTIONS[@]} )) || { echo 'ERROR: Invalid selection.' >&2; exit 1; }
                LAN+=" ${OPTIONS[$((10#$idx-1))]}"
            done
            LAN=${LAN# }
        fi
    fi
fi
validate "$LAN"
MODE=${MODE_CHOICE:-server}
if [[ -z "$MODE_CHOICE" && -f "$CONF" ]]; then
    OLD_MODE=$("${SUDO[@]}" bash -c 'source "$1"; printf "%s" "${ARES_MODE:-server}"' _ "$CONF")
    [[ "$OLD_MODE" == gateway ]] && MODE=gateway
fi

echo "ARES configuration: mode=$MODE; LAN=$LAN"
"${SUDO[@]}" install -d -m 755 /etc/ares /usr/local/sbin /usr/local/bin
stamp=$(date +%Y%m%d-%H%M%S)
backup() {
    local dst="$1"
    if "${SUDO[@]}" test -e "$dst"; then
        "${SUDO[@]}" cp -a -- "$dst" "${dst}.bak.${stamp}"
    fi
}
if [[ -f "$CONF" ]]; then backup "$CONF"; fi
TEMP=$(mktemp)
trap 'rm -f -- "$TEMP"' EXIT
printf 'ARES_LAN_NETWORKS=%q\nARES_MODE=%q\n' "$LAN" "$MODE" > "$TEMP"
"${SUDO[@]}" install -o root -g root -m 600 "$TEMP" "$CONF"
for script in lockdown_internet.sh restore_internet.sh ares_anydesk_diagnose.sh; do
    dst=/usr/local/sbin/$script
    if ! "${SUDO[@]}" cmp -s "$HERE/$script" "$dst"; then
        backup "$dst"
        "${SUDO[@]}" install -m 700 -- "$HERE/$script" "$dst"
        echo "Installed $script"
    else
        echo "Current $script (unchanged)"
    fi
done

# Preserve commands that already dispatch to the current installed scripts.
# For unknown/conflicting commands, stop rather than silently hijack a name.
make_command() {
    local name="$1" target="$2" mode="$3" dest="/usr/local/bin/$1"
    if [[ -L "$dest" && "$(readlink -f "$dest")" == "$target" ]]; then
        return
    fi
    if [[ -f "$dest" && "$mode" == wrapper ]] && grep -Fq "$target" "$dest" 2>/dev/null; then
        # Existing user-defined sudo wrapper. Don't replace automatically.
        return
    fi
    if [[ -e "$dest" || -L "$dest" ]]; then
        echo "ERROR: Conflicting existing command $dest. No command replaced." >&2
        echo "Review it before using $name (or run sudo $target directly)." >&2
        return 1
    fi
    if [[ "$mode" == link ]]; then
        "${SUDO[@]}" ln -s -- "$target" "$dest"
    else
        cat > "$TEMP" <<WRAP
#!/usr/bin/env bash
set -Eeuo pipefail
if (( EUID == 0 )); then exec $target "\$@"; fi
exec sudo $target "\$@"
WRAP
        "${SUDO[@]}" install -m 755 "$TEMP" "$dest"
    fi
}
make_command lockdown-internet /usr/local/sbin/lockdown_internet.sh wrapper
make_command restore-internet /usr/local/sbin/restore_internet.sh wrapper
make_command lockdown_internet /usr/local/sbin/lockdown_internet.sh link
make_command restore_internet /usr/local/sbin/restore_internet.sh link
make_command ares-anydesk-diagnose /usr/local/sbin/ares_anydesk_diagnose.sh wrapper

# Check nftables syntax and live cgroup membership, without installing rules.
CHECK_OK=no
if "${SUDO[@]}" /usr/local/sbin/lockdown_internet.sh --tailscale --check; then
    CHECK_OK=yes
else
    echo 'WARNING: Tailscale preflight failed. Check Tailscale readiness before lockdown.'
fi

boot() {
    if [[ "$CHECK_OK" != yes ]]; then
        echo 'ERROR: Cannot enable boot lockdown until Tailscale preflight passes.' >&2
        return 1
    fi
    if command -v crontab >/dev/null 2>&1 && "${SUDO[@]}" crontab -l 2>/dev/null | grep -Eq '^[[:space:]]*@reboot[[:space:]].*(lockdown_internet[.]sh|lockdown-internet)'; then
        echo 'ERROR: Legacy root crontab lockdown present. Remove it before enabling systemd boot lockdown.' >&2
        return 1
    fi
    echo 'Boot lockdown can disconnect remote administration if AnyDesk or Tailscale fail.'
    response=$(read_prompt 'Have you tested AnyDesk, Tailscale SSH/VNC, local ARES access, and restore without reboot? Type YES: ')
    [[ "$response" == YES ]] || { echo 'Boot persistence not enabled.'; return 0; }
    cat > "$TEMP" <<'UNIT'
[Unit]
Description=ARES Internet Lockdown (Tailscale)
Wants=network-online.target
Requires=tailscaled.service
After=network-online.target tailscaled.service
ConditionPathExists=/usr/local/sbin/lockdown_internet.sh
[Service]
Type=oneshot
TimeoutStartSec=105
ExecStartPre=/bin/bash -c 'for i in $(seq 1 45); do ip link show tailscale0 >/dev/null 2>&1 && exit 0; sleep 2; done; exit 1'
ExecStart=/usr/local/sbin/lockdown_internet.sh --permanent --tailscale
[Install]
WantedBy=multi-user.target
UNIT
    backup "$UNIT"
    "${SUDO[@]}" install -m 644 "$TEMP" "$UNIT"
    "${SUDO[@]}" systemctl daemon-reload
    "${SUDO[@]}" systemctl enable ares-internet-lockdown.service
    echo 'Reboot persistence enabled (service was not started).'
}
case "$BOOT_CHOICE" in
    ask)
        if [[ "$(read_prompt 'Enable lockdown automatically after every reboot? [y/N] ')" =~ ^([yY]|[yY][eE][sS])$ ]]; then boot; else echo 'Reboot persistence left disabled.'; fi ;;
    yes) boot ;;
    no) echo 'Reboot persistence left disabled.' ;;
esac

echo
if [[ "$CHECK_OK" == yes ]]; then
    echo 'INSTALLATION COMPLETE; firewall preflight passed (not activated).'
else
    echo 'FILES INSTALLED, BUT TAILSCALE PREFLIGHT DID NOT PASS; do not activate boot lockdown.'
fi
echo 'Test first: lockdown-internet --tailscale'
echo 'Restore:    restore-internet'
echo 'After successful test: lockdown-internet --permanent --tailscale'
echo 'To enable reboot persistence later: bash install.sh --boot'
