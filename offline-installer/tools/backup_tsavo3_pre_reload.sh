#!/usr/bin/env bash
# Private preservation only: no services, firewall or installed content changed.
set -Eeuo pipefail
umask 077
[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo 'Run this helper with sudo.' >&2; exit 1; }
[[ "$(hostname -s)" == tsavo3 ]] || { echo 'This preservation helper is for tsavo3.' >&2; exit 1; }
BASE=/mnt/sda3/home/ares/Downloads
OUT="$BASE/ARES_tsavo3_pre_reload_$(date -u +%Y%m%d_%H%M%S)"
[[ ! -e "$OUT" ]] || { echo 'Backup folder exists; retain it and choose a new run.' >&2; exit 1; }
install -d -m 0700 "$OUT"
exec > >(tee "$OUT/backup.log") 2>&1
trap 'echo "INCOMPLETE: retain $OUT and obtain support before reloading." >&2' ERR

list_paths() {
  local name=$1; shift
  : > "$OUT/$name.paths"
  for path in "$@"; do
    if [[ -e "/$path" || -L "/$path" ]]; then
      printf '%s\n' "$path" >> "$OUT/$name.paths"
    fi
  done
}

ARES_HOME="$(getent passwd ares | cut -d: -f6)"
list_paths configuration etc usr/local opt/ares/internet-lockdown \
  var/lib/tailscale var/lib/anydesk \
  "${ARES_HOME#/}/.ssh" "${ARES_HOME#/}/.anydesk" "${ARES_HOME#/}/.vnc"
tar --acls --xattrs --numeric-owner -czf "$OUT/configuration-private.tar.gz" \
  -C / -T "$OUT/configuration.paths"

list_paths changed-web-content \
  mnt/sda3/var/www/admin mnt/sda3/var/www/modules/Admin_tools \
  mnt/sda3/var/www/modules/Lesson_Plans mnt/sda3/var/www/tracker \
  mnt/sda3/var/www/app_install mnt/sda3/var/www/downloads \
  mnt/sda3/var/www/lesson3-download/lesson3-deploy
tar --acls --xattrs --numeric-owner -czf "$OUT/changed-web-content-private.tar.gz" \
  -C / -T "$OUT/changed-web-content.paths"

DEPLOY=/mnt/sda3/var/www/lesson3-download/lesson3-deploy
if [[ -f "$DEPLOY/compose.offline.yaml" ]]; then
  (
    cd "$DEPLOY"
    docker compose -f compose.offline.yaml exec -T postgres \
      pg_dump -U lesson3 -d lesson3 -Fc > "$OUT/lesson3-private.dump"
    [[ -s "$OUT/lesson3-private.dump" ]]
    docker compose -f compose.offline.yaml exec -T postgres \
      pg_restore --list < "$OUT/lesson3-private.dump" > "$OUT/lesson3-dump-contents.txt"
  )
fi

findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS > "$OUT/mounts.txt"
lsblk -f > "$OUT/disks.txt"
ip -br address > "$OUT/interfaces.txt"
ip route > "$OUT/routes.txt"
systemctl list-unit-files > "$OUT/service-enablement.txt"
nft list ruleset > "$OUT/firewall-private.nft"
crontab -l > "$OUT/root-crontab-private.txt" 2>/dev/null || true
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' > "$OUT/containers.txt"
docker volume ls > "$OUT/docker-volumes.txt"
for log in /var/log/ares-offline-install-*.log; do
  [[ -f "$log" ]] && cp -p "$log" "$OUT/"
done
gzip -t "$OUT/configuration-private.tar.gz" "$OUT/changed-web-content-private.tar.gz"
printf 'Private recovery backup; not a full-disk image. Copy off tsavo3 before reload.\n' > "$OUT/COMPLETED.txt"
(
  cd "$OUT"
  find . -type f ! -name SHA256SUMS ! -name backup.log -print0 \
    | sort -z | xargs -0 sha256sum > SHA256SUMS
)
chown -R ares:ares "$OUT"
echo "PRESERVATION READY: $OUT"
echo 'Copy this private folder off the server and confirm checksums before reload.'
