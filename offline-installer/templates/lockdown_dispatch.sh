#!/usr/bin/env bash
# Configure the actual LAN on first use, after an unplugged installation.
set -Eeuo pipefail
if (( EUID != 0 )); then exec sudo "$0" "$@"; fi
if [[ "${1:-}" == --confirm ]]; then
  exec /usr/local/sbin/lockdown_internet.sh "$@"
fi
configure=no
[[ "${1:-}" != --configure ]] || { configure=yes; shift; }
if [[ "$configure" == yes ]] || ! python3 /usr/local/lib/ares/configure_lockdown.py --check-current; then
  if nft list table inet ares_internet_lockdown >/dev/null 2>&1 \
      || systemctl is-enabled --quiet ares-internet-lockdown.service 2>/dev/null; then
    echo 'Preserving active/boot lockdown configuration. Arrange safe access and restore/disable it before changing the LAN.' >&2
    exit 2
  fi
  python3 /usr/local/lib/ares/configure_lockdown.py
fi
[[ "$configure" != yes ]] || exit 0
exec /usr/local/sbin/lockdown_internet.sh "$@"
