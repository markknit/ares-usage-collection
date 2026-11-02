#!/usr/bin/env bash
# ARES Internet Lockdown v1.4.1 - interface AND subnet scoped LAN permissions.
#
# Modes:
#   lockdown_internet.sh --tailscale                      # 5-minute rollback test
#   lockdown_internet.sh --permanent --tailscale          # Manual restore / until reboot
#   lockdown_internet.sh --confirm                        # Cancel an active test timer
#   lockdown_internet.sh --anydesk-fallback --tailscale  # AnyDesk service-scoped TCP 80/443
#
# /etc/ares/internet-lockdown.conf defines interface=subnet pairs and profile.
# Optional ARES_TAILSCALE_UDP_PORT environment variable (default 41641).
# Tailscale HTTPS and optional AnyDesk fallback are matched by the originating
# systemd service cgroup (Linux cgroup v2 + nftables socket cgroupv2 required).
# Important: cgroup identity can change after a daemon restart. Fail closed;
# restore/reapply lockdown from a local console if a service restarts.
set -Eeuo pipefail

TABLE="ares_internet_lockdown"
STATE_DIR="/run/ares-internet-lockdown"
ROLLBACK_FILE="$STATE_DIR/rollback-unit"
RESTORE_SCRIPT="/usr/local/sbin/restore_internet.sh"
TAILSCALE_UDP_PORT="${ARES_TAILSCALE_UDP_PORT:-41641}" # Override only if tailscaled uses a different --port.

usage() {
    cat >&2 <<USAGE
Usage: $0 [--confirm | --permanent] [--tailscale] [--anydesk-fallback] [--mode server|gateway] [--check]
  (no options)          5-minute rollback test (no Tailscale exception)
  --tailscale           Keep Tailscale transport + SSH/VNC over tailscale0
  --anydesk-fallback    EXPERIMENTAL: TCP 80/443 from anydesk.service only
  --permanent           No rollback; manually restore or reboot
  --confirm             Cancel pending rollback for a currently active test
  --mode server|gateway  Label the intended role; public forwarding is denied in BOTH modes
  --check               Validate config and nft rules without applying lockdown
USAGE
    exit 2
}

PERMANENT=false
CONFIRM=false
FALLBACK=false
TAILSCALE=false
CHECK=false
MODE_OVERRIDE=""
while (( $# )); do
    arg="$1"; shift
    case "$arg" in
        --permanent)       $PERMANENT && usage; PERMANENT=true ;;
        --confirm)         $CONFIRM && usage; CONFIRM=true ;;
        --anydesk-fallback) $FALLBACK && usage; FALLBACK=true ;;
        --tailscale)       $TAILSCALE && usage; TAILSCALE=true ;;
        --check)           $CHECK && usage; CHECK=true ;;
        --mode)            [[ -z "$MODE_OVERRIDE" && $# -gt 0 ]] || usage; MODE_OVERRIDE="$1"; shift ;;
        *) usage ;;
    esac
done
if $CONFIRM && { $PERMANENT || $FALLBACK || $TAILSCALE || $CHECK || [[ -n "$MODE_OVERRIDE" ]]; }; then usage; fi
if $CHECK && $PERMANENT; then usage; fi
ANYDESK_TCP_PORTS="6568"

if [[ ${EUID} -ne 0 ]]; then
    echo "ERROR: Run as root (sudo)." >&2
    exit 1
fi
if ! command -v nft >/dev/null 2>&1; then
    echo "ERROR: nftables is missing. Install: sudo apt-get install nftables" >&2
    exit 1
fi

if $CONFIRM; then
    if ! nft list table inet "$TABLE" >/dev/null 2>&1; then
        echo "ERROR: No active lockdown exists to confirm." >&2
        exit 1
    fi
    if [[ ! -f "$ROLLBACK_FILE" ]]; then
        echo "ERROR: No pending rollback timer. Lockdown is already permanent, or the test timer is missing." >&2
        exit 1
    fi
    read -r unit < "$ROLLBACK_FILE"
    if ! systemctl stop "${unit}.timer"; then
        echo "ERROR: Could not cancel rollback timer. Lockdown not confirmed." >&2
        exit 1
    fi
    if systemctl is-active --quiet "${unit}.timer"; then
        echo "ERROR: Rollback timer is still active; not confirmed." >&2
        exit 1
    fi
    rm -f "$ROLLBACK_FILE"
    if ! nft list table inet "$TABLE" >/dev/null 2>&1; then
        echo "ERROR: Lockdown was already restored (rollback may have fired)." >&2
        exit 1
    fi
    echo "Lockdown CONFIRMED; test rollback cancelled. To restore: sudo $RESTORE_SCRIPT"
    exit 0
fi

# Interface roles are explicit. Do NOT trust every RFC1918 source on every NIC:
# an upstream Ethernet modem often uses RFC1918 as well. This file must be
# installed by the interactive installer as root:root 0600.
CONFIG=/etc/ares/internet-lockdown.conf
if [[ ! -f "$CONFIG" ]]; then
    echo "ERROR: $CONFIG missing. Run install_lockdown_commands.sh and identify student LAN interface(s)." >&2
    exit 1
fi
if [[ "$(stat -c %u "$CONFIG")" != 0 ]] || [[ "$(stat -c %a "$CONFIG")" != 600 ]]; then
    echo "ERROR: $CONFIG must be owned by root and have mode 600." >&2
    exit 1
fi
# shellcheck source=/dev/null
source "$CONFIG"
: "${ARES_LAN_INTERFACES:=}"
: "${ARES_MODE:=server}"
MODE="${MODE_OVERRIDE:-$ARES_MODE}"
if [[ "$MODE" != server && "$MODE" != gateway ]]; then
    echo 'ERROR: ARES_MODE must be server or gateway.' >&2; exit 1
fi
# v1.4.1 explicitly couples each client-facing interface with its IPv4 subnet.
# This is required on systems where one NIC carries LAN traffic and also the
# default route. Never accept every private address on that NIC.
: "${ARES_LAN_NETWORKS:=}"
if [[ -z "$ARES_LAN_NETWORKS" ]]; then
    echo 'ERROR: ARES_LAN_NETWORKS missing. Rerun v1.4.1 installer; v1.4 settings are not sufficient.' >&2
    exit 1
fi
command -v python3 >/dev/null 2>&1 || { echo 'ERROR: python3 required to validate IPv4 subnets.' >&2; exit 1; }
read -r -a LAN_PAIRS <<< "${ARES_LAN_NETWORKS//,/ }"
LAN_INPUT=''
LAN_OUTPUT=''
LAN_FORWARD=''
LAN_DESCR=''
for pair in "${LAN_PAIRS[@]}"; do
    [[ "$pair" == *=* ]] || { echo "ERROR: Expected interface=IPv4/CIDR, got $pair" >&2; exit 1; }
    iface="${pair%%=*}"; cidr="${pair#*=}"
    [[ "$iface" =~ ^[a-zA-Z0-9_.:@-]{1,15}$ ]] || { echo "ERROR: Bad interface $iface" >&2; exit 1; }
    case "$iface" in lo|tailscale0|docker0|br-*|veth*) echo "ERROR: $iface cannot be a student-facing interface" >&2; exit 1;; esac
    subnet=$(python3 - "$cidr" <<'IP'
import ipaddress,sys
try:
    n=ipaddress.ip_network(sys.argv[1], strict=True)
    if n.version!=4 or n.prefixlen==0 or n.is_multicast or n.is_loopback or n.is_link_local:
        raise ValueError('not a permitted IPv4 LAN network')
    print(n)
except ValueError as e:
    sys.exit('ERROR: invalid subnet '+sys.argv[1]+': '+str(e))
IP
) || exit 1
    if ! ip link show dev "$iface" >/dev/null 2>&1; then
        echo "ERROR: Configured student interface $iface is absent. Correct /etc/ares/internet-lockdown.conf first." >&2
        exit 1
    fi
    # Require the interface to have an IPv4 address in that subnet. Prevents
    # accidentally blessing a placeholder interface or unrelated uplink.
    if ! ip -o -4 addr show dev "$iface" | awk '{print $4}' | python3 -c '
import ipaddress,sys
net=ipaddress.ip_network(sys.argv[1])
ips=[ipaddress.ip_interface(x).ip for x in sys.stdin.read().split()]
sys.exit(0 if any(x in net for x in ips) else 1)' "$subnet"; then
        echo "ERROR: $iface has no current IPv4 address within $subnet. Do not lock down with this configuration." >&2
        exit 1
    fi
    LAN_DESCR+="$iface=$subnet "
    # Same-subnet application access, DHCP, and mDNS. The interface may also
    # carry Internet traffic; PUBLIC destinations remain blocked.
    LAN_INPUT+="iifname \"$iface\" ip saddr $subnet accept"$'\n'
    LAN_INPUT+="iifname \"$iface\" ip6 saddr { fc00::/7, fe80::/10 } accept"$'\n'
    LAN_INPUT+="iifname \"$iface\" ip daddr 255.255.255.255 meta l4proto udp udp dport { 67, 68 } accept"$'\n'
    LAN_INPUT+="iifname \"$iface\" ip daddr 224.0.0.0/24 accept"$'\n'
    LAN_INPUT+="iifname \"$iface\" ip6 daddr ff02::/16 accept"$'\n'
    LAN_OUTPUT+="oifname \"$iface\" ip daddr $subnet accept"$'\n'
    LAN_OUTPUT+="oifname \"$iface\" ip6 daddr { fc00::/7, fe80::/10 } accept"$'\n'
    LAN_OUTPUT+="oifname \"$iface\" ip daddr 255.255.255.255 meta l4proto udp udp dport { 67, 68 } accept"$'\n'
    LAN_OUTPUT+="oifname \"$iface\" ip daddr 224.0.0.0/24 accept"$'\n'
    LAN_OUTPUT+="oifname \"$iface\" ip daddr 239.255.102.18 meta l4proto udp udp dport 50001-50003 accept"$'\n'
    LAN_OUTPUT+="oifname \"$iface\" ip6 daddr ff02::/16 accept"$'\n'
    # Forwarding only for local Docker published services; not the WAN.
    LAN_FORWARD+="iifname \"$iface\" ip saddr $subnet oifname \"docker0\" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept"$'\n'
    LAN_FORWARD+="iifname \"$iface\" ip saddr $subnet oifname \"br-*\" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept"$'\n'
    LAN_FORWARD+="iifname \"docker0\" oifname \"$iface\" ip daddr $subnet ct state established,related accept"$'\n'
    LAN_FORWARD+="iifname \"br-*\" oifname \"$iface\" ip daddr $subnet ct state established,related accept"$'\n'
done
if nft list table inet "$TABLE" >/dev/null 2>&1; then
    echo "ERROR: Lockdown already active. Restore first, or use --confirm during a test." >&2
    exit 1
fi
if ! $PERMANENT && ! $CHECK; then
    if ! command -v systemd-run >/dev/null 2>&1 || ! command -v systemctl >/dev/null 2>&1; then
        echo "ERROR: systemd-run/systemctl required for rollback." >&2
        exit 1
    fi
    if [[ ! -x "$RESTORE_SCRIPT" ]]; then
        echo "ERROR: Install the executable $RESTORE_SCRIPT before running a test." >&2
        exit 1
    fi
fi

# Restrict HTTPS exceptions to the actual systemd service sockets, not all
# applications using port 443. No Tailscale hostname/IP is hardcoded.
# cgroupv2 paths are translated by nft into kernel group IDs at rule load.
service_socket_match() {
    local service="$1" group path level part
    if [[ "$(stat -fc %T /sys/fs/cgroup)" != 'cgroup2fs' ]]; then
        echo "ERROR: cgroup v2 is required for service-scoped HTTPS." >&2
        return 1
    fi
    if ! systemctl is-active --quiet "${service}.service"; then
        echo "ERROR: ${service}.service is not active." >&2
        return 1
    fi
    group=$(systemctl show -P ControlGroup "${service}.service")
    if [[ ! "$group" =~ ^/[A-Za-z0-9_./@-]+$ || ! -d "/sys/fs/cgroup${group}" ]]; then
        echo "ERROR: ${service} has no active cgroup v2 directory: ${group}" >&2
        return 1
    fi
    path=${group#/}
    level=0
    IFS='/' read -r -a parts <<< "$path"
    for part in "${parts[@]}"; do (( level += 1 )); done
    printf 'socket cgroupv2 level %d "%s"' "$level" "$path"
}

TS_CGROUP_MATCH=''
AD_CGROUP_MATCH=''
if $TAILSCALE || $FALLBACK; then
    command -v systemctl >/dev/null 2>&1 || {
        echo 'ERROR: systemctl required for service-scoped HTTPS.' >&2; exit 1;
    }
fi
if $TAILSCALE; then
    TS_CGROUP_MATCH=$(service_socket_match tailscaled) || exit 1
fi
if $FALLBACK; then
    AD_CGROUP_MATCH=$(service_socket_match anydesk) || exit 1
fi

# Match Tailscale's virtual interface BEFORE the RFC1918/ULA LAN rules.
# In particular, Tailscale IPv6 addresses are within fc00::/7; allowing
# ULA before the interface check would expose all tailnet ports by mistake.
# Tailnet traffic is explicitly blocked when --tailscale is not selected.
TAIL_INPUT='iifname "tailscale0" counter drop'
TAIL_OUTPUT='oifname "tailscale0" counter drop'
TAIL_FORWARD='iifname "tailscale0" counter drop
        oifname "tailscale0" counter drop'
TS_TRANSPORT_INPUT=''
TS_TRANSPORT_OUTPUT=''
if $TAILSCALE; then
    if [[ ! "$TAILSCALE_UDP_PORT" =~ ^[0-9]+$ ]] || (( TAILSCALE_UDP_PORT < 1 || TAILSCALE_UDP_PORT > 65535 )); then
        echo "ERROR: ARES_TAILSCALE_UDP_PORT must be an integer in 1..65535." >&2
        exit 1
    fi
    if ! command -v tailscale >/dev/null 2>&1 || ! command -v systemctl >/dev/null 2>&1; then
        echo "ERROR: Tailscale CLI and systemd are required for --tailscale." >&2
        exit 1
    fi
    if ! systemctl is-active --quiet tailscaled.service; then
        echo "ERROR: tailscaled.service is not running. Restore internet and start Tailscale first." >&2
        exit 1
    fi
    if ! ip link show dev tailscale0 >/dev/null 2>&1; then
        echo "ERROR: tailscale0 interface missing. Bring Tailscale online first." >&2
        exit 1
    fi
    # SSH/VNC in both directions, their return traffic, optional MagicDNS,
    # and ICMP/ICMPv6 path control. No other tailnet application ports.
    TAIL_INPUT='iifname "tailscale0" meta l4proto tcp tcp dport { 22, 5901, 5909 } accept
        iifname "tailscale0" meta l4proto tcp tcp sport { 22, 5901, 5909 } ct state established accept
        iifname "tailscale0" ip saddr 100.100.100.100 meta l4proto udp udp sport 53 ct state established accept
        iifname "tailscale0" ip saddr 100.100.100.100 meta l4proto tcp tcp sport 53 ct state established accept
        iifname "tailscale0" meta l4proto { icmp, ipv6-icmp } accept
        iifname "tailscale0" counter drop'
    TAIL_OUTPUT='oifname "tailscale0" meta l4proto tcp tcp dport { 22, 5901, 5909 } accept
        oifname "tailscale0" meta l4proto tcp tcp sport { 22, 5901, 5909 } ct state established accept
        oifname "tailscale0" ip daddr 100.100.100.100 meta l4proto udp udp dport 53 accept
        oifname "tailscale0" ip daddr 100.100.100.100 meta l4proto tcp tcp dport 53 accept
        oifname "tailscale0" meta l4proto { icmp, ipv6-icmp } accept
        oifname "tailscale0" counter drop'
    # Transport is routed via the physical NIC, not via tailscale0.
    # Tailscale's UDP + HTTPS egress is restricted to tailscaled.service only.
    TS_TRANSPORT_INPUT="meta l4proto udp udp dport ${TAILSCALE_UDP_PORT} accept
        meta l4proto udp udp sport 3478 ct state established accept
        meta l4proto tcp tcp sport 443 ct state established accept"
    TS_TRANSPORT_OUTPUT="meta l4proto udp udp sport ${TAILSCALE_UDP_PORT} ${TS_CGROUP_MATCH} accept
        meta l4proto udp udp dport 3478 ${TS_CGROUP_MATCH} accept
        meta l4proto tcp tcp dport 443 ${TS_CGROUP_MATCH} counter accept"
fi

ANYDESK_FALLBACK_OUTPUT=''
if $FALLBACK; then
    ANYDESK_FALLBACK_OUTPUT="meta l4proto tcp tcp dport { 80, 443 } ${AD_CGROUP_MATCH} counter accept"
fi

RULEFILE=$(mktemp)
trap 'rm -f "$RULEFILE"' EXIT
cat > "$RULEFILE" <<NFT
table inet $TABLE {
    chain input_lockdown {
        type filter hook input priority -150; policy accept;
        iifname "lo" accept

        $TAIL_INPUT

        # Only explicitly configured student-facing interfaces are trusted.
        $LAN_INPUT
        iifname "docker0" ip saddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
        iifname "br-*" ip saddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
        iifname "docker0" ip6 saddr { fc00::/7, fe80::/10 } accept
        iifname "br-*" ip6 saddr { fc00::/7, fe80::/10 } accept

        meta l4proto tcp tcp dport { 22, 5901, 5909 } accept
        meta l4proto tcp tcp sport { 22, 5901, 5909 } ct state established accept
        meta l4proto tcp tcp sport { ${ANYDESK_TCP_PORTS} } ct state established accept
        meta l4proto tcp tcp sport { 80, 443 } ct state established accept

        $TS_TRANSPORT_INPUT

        meta l4proto udp udp sport 53 ct state established accept
        meta l4proto tcp tcp sport 53 ct state established accept
        meta l4proto udp udp dport { 67, 68, 546, 547 } accept
        meta l4proto icmp accept
        meta l4proto ipv6-icmp accept
        counter drop
    }

    chain output_lockdown {
        type filter hook output priority -150; policy accept;
        oifname "lo" accept

        $TAIL_OUTPUT

        $LAN_OUTPUT
        oifname "docker0" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
        oifname "br-*" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
        oifname "docker0" ip6 daddr { fc00::/7, fe80::/10 } accept
        oifname "br-*" ip6 daddr { fc00::/7, fe80::/10 } accept

        meta l4proto tcp tcp dport { 22, 5901, 5909, ${ANYDESK_TCP_PORTS} } accept

        $ANYDESK_FALLBACK_OUTPUT
        meta l4proto tcp tcp sport { 22, 5901, 5909 } ct state established accept

        $TS_TRANSPORT_OUTPUT

        meta l4proto udp udp dport 53 accept
        meta l4proto tcp tcp dport 53 accept
        meta l4proto udp udp dport { 67, 68, 546, 547 } accept
        meta l4proto icmp accept
        meta l4proto ipv6-icmp accept
        counter drop
    }

    chain forward_lockdown {
        type filter hook forward priority -150; policy accept;
        $TAIL_FORWARD
        $LAN_FORWARD
        iifname "docker0" oifname "br-*" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
        iifname "br-*" oifname "docker0" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
        iifname "br-*" oifname "br-*" ip daddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
        counter drop
    }
}
NFT

if ! nft -c -f "$RULEFILE"; then
    echo "ERROR: nftables validation failed; no firewall changes made." >&2
    exit 1
fi

if $CHECK; then
    echo "v1.4.1 preflight PASS: mode=$MODE; LAN=$LAN_DESCR"
    echo 'Generated nftables rules validated; no changes made.'
    exit 0
fi

if ! $PERMANENT; then
    install -d -m 700 "$STATE_DIR"
    if [[ -f "$ROLLBACK_FILE" ]]; then
        read -r old_unit < "$ROLLBACK_FILE"
        systemctl stop "${old_unit}.timer" >/dev/null 2>&1 || true
        rm -f "$ROLLBACK_FILE"
    fi
    ROLLBACK_UNIT="ares-lockdown-rollback-$(date +%s)-$$"
    if ! systemd-run --quiet --unit="$ROLLBACK_UNIT" --on-active=5min "$RESTORE_SCRIPT"; then
        echo "ERROR: Could not schedule rollback; no firewall changes made." >&2
        exit 1
    fi
    if ! systemctl is-active --quiet "${ROLLBACK_UNIT}.timer"; then
        echo "ERROR: Rollback timer not active; no firewall changes made." >&2
        systemctl stop "${ROLLBACK_UNIT}.timer" >/dev/null 2>&1 || true
        exit 1
    fi
    printf '%s\n' "$ROLLBACK_UNIT" > "$ROLLBACK_FILE"
    chmod 600 "$ROLLBACK_FILE"
fi

if ! nft -f "$RULEFILE"; then
    echo "ERROR: Lockdown activation failed." >&2
    if ! $PERMANENT; then
        systemctl stop "${ROLLBACK_UNIT}.timer" >/dev/null 2>&1 || true
        rm -f "$ROLLBACK_FILE"
    fi
    exit 1
fi

echo "Lockdown v1.4.1 ACTIVE (mode=$MODE; LAN=$LAN_DESCR; public forwarding blocked)."
echo "Allowed: trusted student LAN and local Docker, SSH TCP/22, VNC TCP/5901/5909, AnyDesk TCP ${ANYDESK_TCP_PORTS}."
if $TAILSCALE; then
    echo "Tailscale: ON (tailscale0 SSH/VNC only; transport UDP ${TAILSCALE_UDP_PORT}, UDP/3478)."
    echo "HTTPS/443: ONLY tailscaled.service (service-scoped; ordinary browsing blocked)."
else
    echo "Tailscale: OFF. Traffic using tailscale0 is blocked."
fi
if $FALLBACK; then
    echo "AnyDesk experimental fallback: TCP/80 and 443 only from anydesk.service cgroup."
    echo "If AnyDesk uses a desktop process outside this service, fallback WILL NOT cover it. No guarantee until live test."
fi
if $PERMANENT; then
    echo "No rollback timer. To restore: sudo $RESTORE_SCRIPT"
else
    echo "TEST MODE: Automatic firewall restoration in 5 minutes."
    echo "If remote access works, run: sudo /usr/local/sbin/lockdown_internet.sh --confirm"
    echo "Or let it restore, then use --permanent with the same options."
fi
