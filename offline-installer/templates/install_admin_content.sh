#!/usr/bin/env bash
# Publish the three owner-approved admin files as one content update.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/admin-content"
WEB_ROOT="${ARES_WEB_ROOT:-/mnt/sda3/var/www}"
BACKUP_DIR="/var/backups/ares-admin-content/$(date +%Y%m%d_%H%M%S)-$$"
SOURCES=(admin.html index.htmlf ARES_Sync_User_Guide.pdf)
TARGETS=("$WEB_ROOT/admin/admin.html"
         "$WEB_ROOT/modules/Admin_tools/index.htmlf"
         "$WEB_ROOT/admin/ARES_Sync_User_Guide.pdf")

die() { echo "admin-content: ERROR: $*" >&2; exit 1; }
[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
[[ -d "$WEB_ROOT/admin" && -d "$WEB_ROOT/modules/Admin_tools" ]] \
  || die "existing admin and Admin_tools directories are required"

# Check all inputs before replacing anything. Existing folder permissions and
# authentication configuration are left in place; only these three files change.
for i in "${!SOURCES[@]}"; do
  [[ -f "$PAYLOAD/${SOURCES[$i]}" && ! -L "$PAYLOAD/${SOURCES[$i]}" ]] \
    || die "approved content is missing: ${SOURCES[$i]}"
  [[ ! -L "${TARGETS[$i]}" ]] || die "destination is a symlink: ${TARGETS[$i]}"
  [[ ! -e "${TARGETS[$i]}" || -f "${TARGETS[$i]}" ]] \
    || die "destination is not a regular file: ${TARGETS[$i]}"
done

install -d -m 0700 "$BACKUP_DIR"
for i in "${!SOURCES[@]}"; do
  if [[ -f "${TARGETS[$i]}" ]]; then
    cp -a -- "${TARGETS[$i]}" "$BACKUP_DIR/${SOURCES[$i]}"
  fi
done

for i in "${!SOURCES[@]}"; do
  mode=0644 owner=ares group=www-data
  if [[ -f "${TARGETS[$i]}" ]]; then
    mode="$(stat -c '%a' "${TARGETS[$i]}")"
    owner="$(stat -c '%u' "${TARGETS[$i]}")"
    group="$(stat -c '%g' "${TARGETS[$i]}")"
  fi
  install -m "$mode" -o "$owner" -g "$group" \
    "$PAYLOAD/${SOURCES[$i]}" "${TARGETS[$i]}"
done

echo "admin-content: admin page, Admin_tools entry and user guide installed"
echo "admin-content: previous files retained at $BACKUP_DIR"
