#!/usr/bin/env bash
set -Eeuo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ ${EUID} == 0 ]] || { echo 'Run AnyDesk preparation as root.' >&2; exit 1; }
install -d -m 0755 /usr/local/sbin
install -m 0755 "$HERE/setup_anydesk.sh" /usr/local/sbin/ares-setup-anydesk
cat > /usr/local/sbin/ares-show-anydesk-id <<'COMMAND'
#!/usr/bin/env bash
if (( EUID == 0 )); then exec /usr/local/sbin/ares-setup-anydesk --show-id; fi
exec sudo /usr/local/sbin/ares-setup-anydesk --show-id
COMMAND
chmod 0755 /usr/local/sbin/ares-show-anydesk-id
exec bash /usr/local/sbin/ares-setup-anydesk "$@"
