#!/usr/bin/env bash
# Prepare offline support without stopping or disabling existing access.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TIGERVNC_DIR="$SCRIPT_DIR/tigervnc"
TAILSCALE_DIR="$SCRIPT_DIR/tailscale"
ACTIVATE_SOURCE="$SCRIPT_DIR/ares_enable_remote_access.sh"
DISABLE_SOURCE="$SCRIPT_DIR/ares_disable_remote_access.sh"
TAILSCALE_ARCHIVE="$(find "$TAILSCALE_DIR" -maxdepth 1 -type f -name 'tailscale_*_amd64.tgz' -print -quit)"

log() { printf 'ares-remote-access: %s\n' "$*"; }
die() { printf 'ares-remote-access: ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
[[ "$(uname -m)" == "x86_64" ]] || die "only x86_64 ARES servers are supported"
source /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 24.04 ]] \
  || die "optional remote-support packages require Ubuntu 24.04"
command -v cinnamon-session-cinnamon2d >/dev/null \
  || die "optional remote desktop requires Cinnamon 2D"
for cmd in awk dpkg dpkg-query find grep install mktemp pgrep rm sha256sum ss systemctl tar; do
  command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done
[[ -f "$TIGERVNC_DIR/SHA256SUMS" ]] || die "TigerVNC checksum manifest is missing"
[[ -f "$TAILSCALE_DIR/SHA256SUMS" ]] || die "Tailscale checksum manifest is missing"
[[ -n "$TAILSCALE_ARCHIVE" && -f "$TAILSCALE_ARCHIVE" ]] || die "Tailscale amd64 archive is missing"
[[ -x "$ACTIVATE_SOURCE" && -x "$DISABLE_SOURCE" ]] || die "remote-access control scripts are missing"
[[ -r "$SCRIPT_DIR/remote_support_config.py" ]] || die "remote-support configuration helper is missing"
[[ -r "$SCRIPT_DIR/remote_support_common.sh" ]] || die "SSH baseline helper is missing"
systemctl cat ssh.service >/dev/null 2>&1 || die "OpenSSH server must be installed in the base image"
[[ -f /usr/share/xsessions/cinnamon2d.desktop ]] || die "Cinnamon 2D must be installed in the base image"

log "verifying offline remote-access payload"
(cd "$TIGERVNC_DIR" && sha256sum -c SHA256SUMS)
(cd "$TAILSCALE_DIR" && sha256sum -c SHA256SUMS)

mapfile -t tiger_debs < <(find "$TIGERVNC_DIR" -maxdepth 1 -type f -name '*.deb' -print | sort)
((${#tiger_debs[@]} >= 4)) || die "expected TigerVNC package set is incomplete"

install -d -m 0755 /usr/local/sbin /usr/local/bin /usr/local/lib/ares
install -m 0755 "$ACTIVATE_SOURCE" /usr/local/sbin/ares-enable-remote-access
install -m 0755 "$DISABLE_SOURCE" /usr/local/sbin/ares-disable-remote-access
install -d -m 0755 /usr/local/lib/ares
install -m 0644 "$SCRIPT_DIR/remote_support_config.py" /usr/local/lib/ares/remote_support_config.py
install -m 0644 "$SCRIPT_DIR/remote_support_common.sh" /usr/local/lib/ares/remote_support_common.sh
# Never take away the current support path merely to prepare an optional one.
# Active services retain their packages, binaries, units and enablement state.
TAILSCALE_ACTIVE=no
VNC_ACTIVE=no
if systemctl is-active --quiet tailscaled.service; then TAILSCALE_ACTIVE=yes; fi
if systemctl is-active --quiet 'tigervncserver@:1.service'; then VNC_ACTIVE=yes; fi
if pgrep -x x11vnc >/dev/null 2>&1; then
  log 'Existing x11vnc console sharing is retained; preparation will not disable it.'
fi
if [[ "$VNC_ACTIVE" != yes ]] && ss -ltn | awk '{print $4}' | grep -E '(^|:)5901$' >/dev/null; then
  die 'port 5901 is occupied; preserving its owner and all current services'
fi

if [[ "$VNC_ACTIVE" == yes ]]; then
  log 'Existing TigerVNC is active; preserving its packages, service and configuration.'
else
  log "installing TigerVNC packages from the offline bundle"
  if ! dpkg -i "${tiger_debs[@]}"; then
    die "TigerVNC package installation failed; no network repair attempted"
  fi
fi
command -v tigervncserver >/dev/null 2>&1 || die "tigervncserver was not installed"
command -v tigervncpasswd >/dev/null 2>&1 || die "tigervncpasswd was not installed"

tailscale_tmp="$(mktemp -d /tmp/ares-tailscale.XXXXXX)"
cleanup() { rm -rf -- "$tailscale_tmp"; }
trap cleanup EXIT
tar -xzf "$TAILSCALE_ARCHIVE" -C "$tailscale_tmp"
tailscale_binary="$(find "$tailscale_tmp" -type f -name tailscale -perm -u+x -print -quit)"
tailscaled_binary="$(find "$tailscale_tmp" -type f -name tailscaled -perm -u+x -print -quit)"
[[ -n "$tailscale_binary" && -n "$tailscaled_binary" ]] || die "Tailscale archive did not contain both binaries"

if [[ "$TAILSCALE_ACTIVE" == yes ]]; then
  log 'Existing Tailscale is active; preserving its binaries, unit and identity.'
elif dpkg-query -W -f='${Status}' tailscale 2>/dev/null | grep -q '^install ok installed$'; then
  log "distribution Tailscale package already exists; preserving its managed binaries and unit"
else
  log "installing pinned Tailscale static binaries"
  install -m 0755 "$tailscale_binary" /usr/local/bin/tailscale
  install -m 0755 "$tailscaled_binary" /usr/local/sbin/tailscaled
  install -d -m 0755 /etc/default
  if [[ ! -f /etc/default/tailscaled ]]; then
    printf 'FLAGS=""\n' > /etc/default/tailscaled
    chmod 0644 /etc/default/tailscaled
  fi
  cat > /etc/systemd/system/tailscaled.service <<'EOF'
[Unit]
Description=Tailscale node agent (ARES offline preparation)
After=network-pre.target
Wants=network-pre.target

[Service]
EnvironmentFile=-/etc/default/tailscaled
ExecStart=/usr/local/sbin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/run/tailscale/tailscaled.sock $FLAGS
ExecStopPost=/usr/local/sbin/tailscaled --cleanup
Restart=on-failure
RuntimeDirectory=tailscale
RuntimeDirectoryMode=0755
StateDirectory=tailscale
StateDirectoryMode=0700

[Install]
WantedBy=multi-user.target
EOF
fi

systemctl daemon-reload
# No service activation or enablement change is needed for preparation.
# The static unit and TigerVNC template remain as configured until activation.
log "preparation complete; existing service states and console-sharing support were preserved"
log "later activation command: sudo ares-enable-remote-access"
