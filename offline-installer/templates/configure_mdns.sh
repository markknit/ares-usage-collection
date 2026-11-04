#!/usr/bin/env bash
# Install offline; no hostname rename and no address required during setup.
set -Eeuo pipefail
HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$HERE/../ares_config.sh" "$HERE/../package.conf"
[[ ${EUID} == 0 ]] || { echo 'Run mDNS setup as root.' >&2; exit 1; }
install -d -m 0755 /etc/ares /usr/local/lib/ares /usr/local/bin
install -m 0644 "$HERE/mdns_addresses.py" /usr/local/lib/ares/mdns_addresses.py
install -m 0755 "$HERE/ares_mdns_alias.sh" /usr/local/bin/ares-mdns-alias.sh
printf 'ARES_ALIAS=%s\n' "$ARES_ALIAS" > /etc/ares/mdns-profile.conf
chmod 0644 /etc/ares/mdns-profile.conf
cat > /etc/systemd/system/ares-mdns-alias.service <<'UNIT'
[Unit]
Description=Publish the ARES alias in addition to the school hostname
After=avahi-daemon.service
Requires=avahi-daemon.service
[Service]
ExecStart=/usr/local/bin/ares-mdns-alias.sh
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now avahi-daemon.service
systemctl enable ares-mdns-alias.service
systemctl restart ares-mdns-alias.service
systemctl is-active --quiet ares-mdns-alias.service
echo "Local names: $(hostname -s).local and $ARES_ALIAS (hostname unchanged)."
if [[ -z "$(python3 /usr/local/lib/ares/mdns_addresses.py)" ]]; then
  echo 'mDNS installed; publication waits for a LAN address. No Internet is required.'
else
  echo 'mDNS installed; verify both names from another LAN device.'
  echo "If $ARES_ALIAS is already used on this LAN, disconnect the other ARES server."
fi
