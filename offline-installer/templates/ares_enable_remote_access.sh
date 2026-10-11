#!/usr/bin/env bash
# Deliberately activate Tailscale plus localhost-only TigerVNC for user ares.
set -Eeuo pipefail

VNC_USER="ares"
VNC_DISPLAY=":1"
VNC_PORT=5901
VNC_HOME="$(getent passwd "$VNC_USER" 2>/dev/null | cut -d: -f6 || true)"
VNC_CONFIG_DIR="$VNC_HOME/.config/tigervnc"
VNC_CONFIG="$VNC_CONFIG_DIR/config"
VNC_PASSWORD="$VNC_CONFIG_DIR/passwd"
USER_MAP="/etc/tigervnc/vncserver.users"
SCHOOL_CONF="/etc/ares/usage-upload.conf"
requested_hostname="${1:-}"
if [[ -z "$requested_hostname" && -r "$SCHOOL_CONF" ]]; then
  requested_hostname="$(awk -F= '$1 == "SCHOOL_CODE" {print $2; exit}' "$SCHOOL_CONF")"
fi
requested_hostname="${requested_hostname:-$(hostname)}"
TAILSCALE_HOSTNAME="$(
  printf '%s' "$requested_hostname" \
    | tr '[:upper:]_' '[:lower:]-' \
    | sed -E 's/[^a-z0-9-]+/-/g; s/^-+//; s/-+$//' \
    | cut -c1-63
)"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "==> $*"; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
[[ -n "$VNC_HOME" && -d "$VNC_HOME" ]] || die "user $VNC_USER does not have a usable home directory"
[[ "$TAILSCALE_HOSTNAME" =~ ^[a-z0-9][a-z0-9-]{0,62}$ ]] || die "invalid Tailscale hostname: $TAILSCALE_HOSTNAME"
for cmd in awk cut python3 runuser sed ss systemctl tailscale tailscaled tigervncpasswd tr; do
  command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done
command -v cinnamon-session-cinnamon2d >/dev/null 2>&1 || die "Cinnamon 2D session is not installed"

ACTIVATION_COMPLETE=0
rollback_activation() {
  local rc=$?
  trap - ERR HUP INT TERM
  if (( ! ACTIVATION_COMPLETE )); then
    systemctl disable --now "tigervncserver@${VNC_DISPLAY}.service" >/dev/null 2>&1 || true
    systemctl disable --now tailscaled.service >/dev/null 2>&1 || true
    echo "ERROR: activation did not complete; both remote-access services were stopped." >&2
  fi
  exit "$rc"
}
trap rollback_activation ERR HUP INT TERM

install -d -m 0700 -o "$VNC_USER" -g "$VNC_USER" "$VNC_CONFIG_DIR"
cat > "$VNC_CONFIG" <<'EOF'
session=cinnamon2d
geometry=1280x800
depth=24
localhost=yes
alwaysshared
EOF
chown "$VNC_USER:$VNC_USER" "$VNC_CONFIG"
chmod 0600 "$VNC_CONFIG"

log "create a unique VNC password; do not reuse an ARES or Tailscale password"
runuser -u "$VNC_USER" -- env HOME="$VNC_HOME" tigervncpasswd "$VNC_PASSWORD"
chmod 0600 "$VNC_PASSWORD"
chown "$VNC_USER:$VNC_USER" "$VNC_PASSWORD"

install -d -m 0755 /etc/tigervnc
python3 - "$USER_MAP" "$VNC_DISPLAY" "$VNC_USER" <<'PY'
from pathlib import Path
import os
import sys

path = Path(sys.argv[1])
display = sys.argv[2]
user = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
result = []
found = False
for line in lines:
    stripped = line.strip()
    if stripped.startswith(display + "="):
        existing = stripped.split("=", 1)[1]
        if existing != user:
            raise SystemExit(f"{display} is already assigned to {existing}")
        if not found:
            result.append(f"{display}={user}")
            found = True
    else:
        result.append(line)
if not found:
    result.append(f"{display}={user}")
temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
temporary.write_text("\n".join(result) + "\n", encoding="utf-8")
os.chmod(temporary, 0o644)
os.replace(temporary, path)
PY

log "starting localhost-only TigerVNC display $VNC_DISPLAY"
systemctl enable --now "tigervncserver@${VNC_DISPLAY}.service"
sleep 5
ss -ltn | awk '{print $4}' | grep -Eq '127\.0\.0\.1:5901$|\[::1\]:5901$' \
  || die "TigerVNC did not create a localhost listener on port $VNC_PORT"
if ss -ltn | awk '{print $4}' | grep -Eq '0\.0\.0\.0:5901$|\[::\]:5901$'; then
  systemctl disable --now "tigervncserver@${VNC_DISPLAY}.service" || true
  die "TigerVNC exposed port $VNC_PORT beyond localhost; it has been stopped"
fi

log "starting Tailscale; browser authentication or an approved auth key will be required"
systemctl enable --now tailscaled.service
tailscale up --hostname "$TAILSCALE_HOSTNAME" --ssh
ACTIVATION_COMPLETE=1
trap - ERR HUP INT TERM

cat <<EOF

Remote access is active.
TigerVNC display: $VNC_DISPLAY (localhost only, port $VNC_PORT)
Tailscale hostname: $TAILSCALE_HOSTNAME

From the authorized support computer, create an SSH tunnel:
  ssh -L 5901:127.0.0.1:5901 ares@$TAILSCALE_HOSTNAME

Then point the VNC viewer to:
  127.0.0.1:5901

To stop both services without deleting their configuration:
  sudo ares-disable-remote-access
EOF
