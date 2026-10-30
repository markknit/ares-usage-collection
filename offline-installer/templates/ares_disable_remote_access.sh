#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "ERROR: run as root" >&2; exit 1; }

STATE_DIR=/var/lib/ares/remote-support
install -d -m 0700 "$STATE_DIR"
exec 9>"$STATE_DIR/lock"
flock -n 9 || { echo "ERROR: another remote-support operation is running" >&2; exit 1; }
systemctl disable --now 'tigervncserver@:1.service' tailscaled.service
if [[ -f "$STATE_DIR/ssh-before.conf" ]]; then
  source "$STATE_DIR/ssh-before.conf"
  [[ "$SSH_WAS_ACTIVE" == yes ]] || systemctl stop ssh.service
  [[ "$SSH_WAS_ENABLED" == yes ]] || systemctl disable ssh.service
fi
if systemctl is-active --quiet 'tigervncserver@:1.service' || systemctl is-active --quiet tailscaled.service; then
  echo "ERROR: a remote service is still active" >&2
  exit 1
fi

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)5901$'; then
  echo "ERROR: port 5901 is still listening" >&2
  exit 1
fi

echo "Remote-access services are stopped and disabled."
echo "Tailscale registration, VNC password, and configuration were retained."
echo "Pre-existing OpenSSH service state was preserved; activation-owned SSH was stopped."
