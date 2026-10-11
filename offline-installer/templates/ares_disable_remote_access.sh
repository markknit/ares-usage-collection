#!/usr/bin/env bash
set -Eeuo pipefail

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "ERROR: run as root" >&2; exit 1; }

systemctl disable --now 'tigervncserver@:1.service' >/dev/null 2>&1 || true
systemctl disable --now tailscaled.service >/dev/null 2>&1 || true

if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)5901$'; then
  echo "ERROR: port 5901 is still listening" >&2
  exit 1
fi

echo "Remote-access services are stopped and disabled."
echo "Tailscale registration, VNC password, and configuration were retained."
