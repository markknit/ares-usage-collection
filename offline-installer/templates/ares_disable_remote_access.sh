#!/usr/bin/env bash
set -Eeuo pipefail
STATE_DIR=/var/lib/ares/remote-support
COMMON_TOOL=/usr/local/lib/ares/remote_support_common.sh

disable_remote_services() {
  local failures=0
  systemctl disable --now 'tigervncserver@:1.service' tailscaled.service || failures=1
  if [[ -f "$STATE_DIR/ssh-before.conf" ]]; then
    if ! capture_ssh_baseline "$STATE_DIR/ssh-before.conf" \
        || ! restore_ssh_baseline "$STATE_DIR/ssh-before.conf"; then
      echo "ERROR: original SSH service/socket configuration was not fully restored" >&2
      failures=1
    fi
  fi
  if systemctl is-active --quiet 'tigervncserver@:1.service' || systemctl is-active --quiet tailscaled.service; then
    echo "ERROR: a remote service is still active" >&2
    failures=1
  fi
  if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)5901$'; then
    echo "ERROR: port 5901 is still listening" >&2
    failures=1
  fi
  (( failures == 0 )) || return 1
  echo "Tailscale and TigerVNC are stopped and disabled."
  echo "Original ssh.service and ssh.socket active/enabled states were restored."
  echo "Tailscale identity, normal-access VNC password, configuration and SSH baseline were retained."
}
main() {
  [[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "ERROR: run as root" >&2; return 1; }
  [[ -r "$COMMON_TOOL" ]] || { echo "ERROR: SSH state helper missing" >&2; return 1; }
  source "$COMMON_TOOL"
  install -d -m 0700 "$STATE_DIR"
  exec 9>"$STATE_DIR/lock"
  flock -n 9 || { echo "ERROR: another remote-support operation is running" >&2; return 1; }
  disable_remote_services
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
