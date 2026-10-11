#!/usr/bin/env bash
# Install offline remote-access components but leave them stopped and disabled.
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
for cmd in awk dpkg dpkg-query find grep install mktemp pgrep rm sha256sum ss systemctl tar; do
  command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done

[[ -f "$TIGERVNC_DIR/SHA256SUMS" ]] || die "TigerVNC checksum manifest is missing"
[[ -f "$TAILSCALE_DIR/SHA256SUMS" ]] || die "Tailscale checksum manifest is missing"
[[ -n "$TAILSCALE_ARCHIVE" && -f "$TAILSCALE_ARCHIVE" ]] || die "Tailscale amd64 archive is missing"
[[ -x "$ACTIVATE_SOURCE" && -x "$DISABLE_SOURCE" ]] || die "remote-access control scripts are missing"

log "verifying offline remote-access payload"
(cd "$TIGERVNC_DIR" && sha256sum -c SHA256SUMS)
(cd "$TAILSCALE_DIR" && sha256sum -c SHA256SUMS)

mapfile -t tiger_debs < <(find "$TIGERVNC_DIR" -maxdepth 1 -type f -name '*.deb' -print | sort)
((${#tiger_debs[@]} >= 4)) || die "expected TigerVNC package set is incomplete"

log "installing TigerVNC packages from the offline bundle"
if ! dpkg -i "${tiger_debs[@]}"; then
  die "TigerVNC package installation failed; do not use apt-get -f install while offline"
fi
command -v tigervncserver >/dev/null 2>&1 || die "tigervncserver was not installed"
command -v tigervncpasswd >/dev/null 2>&1 || die "tigervncpasswd was not installed"

log "disabling the TigerVNC template until deliberate activation"
systemctl disable --now 'tigervncserver@:1.service' >/dev/null 2>&1 || true

mapfile -t x11_units < <(
  systemctl list-unit-files --type=service --no-legend 2>/dev/null \
    | awk '$1 ~ /x11vnc.*\.service$/ {print $1}'
)
for unit in "${x11_units[@]}"; do
  log "disabling superseded console-sharing service $unit"
  systemctl disable --now "$unit" >/dev/null 2>&1 || die "could not disable $unit"
done
pgrep -x x11vnc >/dev/null 2>&1 \
  && die "x11vnc is still running after its service units were disabled"

tailscale_tmp="$(mktemp -d /tmp/ares-tailscale.XXXXXX)"
cleanup() { rm -rf -- "$tailscale_tmp"; }
trap cleanup EXIT
tar -xzf "$TAILSCALE_ARCHIVE" -C "$tailscale_tmp"
tailscale_binary="$(find "$tailscale_tmp" -type f -name tailscale -perm -u+x -print -quit)"
tailscaled_binary="$(find "$tailscale_tmp" -type f -name tailscaled -perm -u+x -print -quit)"
[[ -n "$tailscale_binary" && -n "$tailscaled_binary" ]] || die "Tailscale archive did not contain both binaries"

if dpkg-query -W -f='${Status}' tailscale 2>/dev/null | grep -q '^install ok installed$'; then
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

install -m 0755 "$ACTIVATE_SOURCE" /usr/local/sbin/ares-enable-remote-access
install -m 0755 "$DISABLE_SOURCE" /usr/local/sbin/ares-disable-remote-access
systemctl daemon-reload
systemctl disable --now tailscaled.service >/dev/null 2>&1 || true

systemctl is-active --quiet tailscaled.service && die "tailscaled unexpectedly remained active"
systemctl is-active --quiet 'tigervncserver@:1.service' && die "TigerVNC unexpectedly remained active"
if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)5901$'; then
  die "port 5901 is listening even though TigerVNC should be dormant"
fi

log "preparation complete; Tailscale and TigerVNC are installed but inactive"
log "later activation command: sudo ares-enable-remote-access"
