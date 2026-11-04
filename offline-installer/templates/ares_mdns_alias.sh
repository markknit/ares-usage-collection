#!/usr/bin/env bash
# Avahi keeps hostname.local; publish the additional profile alias for the LAN.
set -u
source /etc/ares/mdns-profile.conf
declare -a publishers=()
last_endpoints=''
cleanup_publishers() {
  local pid
  for pid in "${publishers[@]}"; do
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  done
  publishers=()
}
trap 'cleanup_publishers; exit 0' TERM INT
trap cleanup_publishers EXIT
while true; do
  if ! endpoints=$(python3 /usr/local/lib/ares/mdns_addresses.py); then
    echo 'Cannot read network addresses; retrying.'
    sleep 5
    continue
  fi
  retry=no
  for pid in "${publishers[@]}"; do
    kill -0 "$pid" 2>/dev/null || retry=yes
  done
  if [[ "$endpoints" != "$last_endpoints" || "$retry" == yes ]]; then
    cleanup_publishers
    last_endpoints="$endpoints"
    if [[ -z "$endpoints" ]]; then
      echo 'No LAN address yet; alias will publish automatically when connected.'
    elif [[ "$ARES_ALIAS" != "$(hostname -s).local" ]]; then
      while read -r interface address; do
        [[ -n "$interface" && -n "$address" ]] || continue
        echo "Publishing $ARES_ALIAS on $interface ($address); retaining $(hostname -s).local."
        avahi-publish -a -R -f "$ARES_ALIAS" "$address" &
        publishers+=("$!")
      done <<< "$endpoints"
    fi
  fi
  sleep 5
done
