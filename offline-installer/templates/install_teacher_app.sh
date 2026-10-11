#!/usr/bin/env bash
# Deploy the approved ARES Sync Android APK and a local teacher installation page.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APK_SOURCE="$SCRIPT_DIR/ares-sync.apk"
APK_HASH_SOURCE="$SCRIPT_DIR/ares-sync.apk.sha256"
PAGE_SOURCE="$SCRIPT_DIR/install-page.html"
WEB_ROOT="${ARES_WEB_ROOT:-/mnt/sda3/var/www}"
DOWNLOAD_DIR="$WEB_ROOT/downloads"
INSTALL_DIR="$WEB_ROOT/app_install"
LEGACY_INSTALL_DIR="$WEB_ROOT/install"
APK_TARGET="$DOWNLOAD_DIR/ares-sync.apk"
APK_HASH_TARGET="$DOWNLOAD_DIR/ares-sync.apk.sha256"
PAGE_TARGET="$INSTALL_DIR/index.html"

log() { printf 'teacher-app: %s\n' "$*"; }
die() { printf 'teacher-app: ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
[[ -f "$APK_SOURCE" ]] || die "approved APK is missing: $APK_SOURCE"
[[ -f "$APK_HASH_SOURCE" ]] || die "APK checksum is missing: $APK_HASH_SOURCE"
[[ -f "$PAGE_SOURCE" ]] || die "teacher install page is missing: $PAGE_SOURCE"
[[ -d "$WEB_ROOT" ]] || die "ARES web root does not exist: $WEB_ROOT"

log "verifying bundled APK checksum"
(
  cd "$SCRIPT_DIR"
  sha256sum -c "$(basename "$APK_HASH_SOURCE")"
)

install -d -m 0755 -o ares -g www-data "$DOWNLOAD_DIR" "$INSTALL_DIR"
install -m 0644 -o ares -g www-data "$APK_SOURCE" "$APK_TARGET"
install -m 0644 -o ares -g www-data "$APK_HASH_SOURCE" "$APK_HASH_TARGET"
install -m 0644 -o ares -g www-data "$PAGE_SOURCE" "$PAGE_TARGET"

# Remove the previous generic /install/ ARES Sync page when upgrading from v1.4.
# Leave unrelated content untouched.
if [[ -f "$LEGACY_INSTALL_DIR/index.html" ]] && grep -q "Install ARES Sync" "$LEGACY_INSTALL_DIR/index.html"; then
  rm -rf "$LEGACY_INSTALL_DIR"
  log "removed legacy teacher install page: http://ares.local/install/"
fi

log "deployed APK: $APK_TARGET"
log "teacher install page: http://ares.local/app_install/"
log "direct APK URL: http://ares.local/downloads/ares-sync.apk"
