#!/usr/bin/env bash
# Update only the installed support controls; no content or identity changes.
set -Eeuo pipefail
[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo 'Run: sudo bash apply_lan_support_update.sh'; exit 1; }
[[ -t 0 ]] || { echo 'Run from a normal terminal or interactive SSH session.'; exit 1; }
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
sha256sum -c SHA256SUMS
for cmd in tigervncserver tigervncpasswd cinnamon-session-cinnamon2d; do
  command -v "$cmd" >/dev/null || { echo "Missing $cmd; use the complete installer to prepare support first."; exit 1; }
done
backup=$(mktemp -d /var/tmp/ares-lan-support-before.XXXXXXXX)
for file in /usr/local/sbin/ares-enable-remote-access /usr/local/sbin/ares-disable-remote-access \
    /usr/local/lib/ares/remote_support_config.py /usr/local/lib/ares/remote_support_common.sh; do
  [[ ! -e "$file" ]] || cp -a -- "$file" "$backup/"
done
echo "Previous support controls retained in: $backup"
install -d -m 0755 /usr/local/sbin /usr/local/lib/ares
install -m 0755 remote-access/ares_enable_remote_access.sh /usr/local/sbin/ares-enable-remote-access
install -m 0755 remote-access/ares_disable_remote_access.sh /usr/local/sbin/ares-disable-remote-access
install -m 0644 remote-access/remote_support_config.py /usr/local/lib/ares/remote_support_config.py
install -m 0644 remote-access/remote_support_common.sh /usr/local/lib/ares/remote_support_common.sh
exec /usr/local/sbin/ares-enable-remote-access --lan-only
