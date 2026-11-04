#!/usr/bin/env bash
# Apply only the three school-setup updates to an already installed v1.13 host.
set -Eeuo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ ${EUID} == 0 ]] || { echo 'Run with sudo from the local console.' >&2; exit 1; }
[[ "${1:-}" =~ ^[A-Z0-9_-]+$ ]] || { echo 'Usage: sudo bash apply_school_setup_updates.sh ARES-S00XX'; exit 2; }
python3 "$HERE/package_integrity.py" package "$HERE"
install -d -m 0755 /usr/local/sbin /usr/local/lib/ares
install -m 0755 "$HERE/remote-access/ares_enable_remote_access.sh" /usr/local/sbin/ares-enable-remote-access
install -m 0755 "$HERE/remote-access/ares_disable_remote_access.sh" /usr/local/sbin/ares-disable-remote-access
for helper in remote_support_config.py remote_support_common.sh; do
  install -m 0644 "$HERE/remote-access/$helper" "/usr/local/lib/ares/$helper"
done
bash "$HERE/lesson_plan/configure_mdns.sh"
backup="/root/ares_deploy_backups/school-setup-$(date +%Y%m%d_%H%M%S)"
install -d -m 0700 "$backup"
found=no
for candidate in /etc/nginx/sites-enabled/*; do
  [[ -L "$candidate" ]] || continue
  target=$(readlink -f "$candidate")
  if [[ -f "$target" ]] && grep -q 'server_name.*ares' "$target"; then
    cp -a -- "$target" "$backup/nginx.conf"
    if python3 "$HERE/lesson_plan/configure_nginx.py" "$target" ares.local "$(hostname -s).local" && nginx -t; then
      systemctl reload nginx
    else
      cp -a -- "$backup/nginx.conf" "$target"
      echo 'Nginx change failed; original configuration restored.' >&2
      exit 1
    fi
    found=yes
    break
  fi
done
[[ "$found" == yes ]] || { echo 'ARES Nginx site not found; ask ARES support to review it.' >&2; exit 1; }
if bash "$HERE/remote-access/prepare_internet_lockdown.sh"; then :; else
  echo 'Lockdown setup deferred; see the preceding explanation.'
fi
if bash "$HERE/remote-access/prepare_anydesk.sh" "$1"; then :; else
  echo "AnyDesk setup Pending. Later: sudo ares-setup-anydesk $1"
fi
echo 'School-setup update finished. Core ARES content/database were not reinstalled.'
echo 'Check both local names from another LAN device and save the new AnyDesk ID.'
