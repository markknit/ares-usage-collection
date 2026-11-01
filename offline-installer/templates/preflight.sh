#!/usr/bin/env bash
set -Eeuo pipefail

preflight_main() {
  SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  SCHOOL_CODE="${1:-}"
  FAILURES=0
  WARNINGS=0

  pass() { printf 'PASS  %s\n' "$*"; }
  warn() { printf 'WARN  %s\n' "$*"; WARNINGS=$((WARNINGS+1)); }
  fail() { printf 'FAIL  %s\n' "$*"; FAILURES=$((FAILURES+1)); }

  [[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "FAIL  Run preflight as root"; exit 2; }
  [[ -n "$SCHOOL_CODE" ]] || { echo "Usage: sudo bash preflight.sh ARES-S00XX"; exit 2; }
  [[ "$SCHOOL_CODE" =~ ^[A-Z0-9_-]+$ ]] || { echo "FAIL  Invalid school code: $SCHOOL_CODE"; exit 2; }

  # One complete-package check. Detailed component validation is build-side.
  # Stop here on a bad copy, before any installation step can change the host.
  python3 -B "$SCRIPT_DIR/package_integrity.py" package "$SCRIPT_DIR" || return 1
  source "$SCRIPT_DIR/ares_config.sh" "$SCRIPT_DIR/package.conf"

  echo "ARES Q4 OFFLINE PRE-FLIGHT"
  echo "School: $SCHOOL_CODE"
  echo "Host:   $(hostname)"
  echo

  case "$(uname -m)" in
    x86_64|amd64) pass "64-bit x86 server architecture" ;;
    *) fail "unsupported architecture $(uname -m); this bundle contains linux/amd64 Lesson3 images" ;;
  esac

  [[ -d /mnt/sda3 ]] && pass "/mnt/sda3 exists" || fail "/mnt/sda3 is missing"

  for cmd in bash nginx php python3 rsync avahi-publish avahi-resolve docker openssl sha256sum tar curl systemctl \
    ss tee grep awk df find flock install stat sed ip timeout; do
    if command -v "$cmd" >/dev/null 2>&1; then pass "$cmd available"; else fail "$cmd not found"; fi
  done

  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    pass "Docker Compose v2 available"
  else
    fail "Docker Compose v2 is unavailable"
  fi

  if id ares >/dev/null 2>&1; then pass "ares user exists"; else fail "ares user does not exist"; fi
  if id www-data >/dev/null 2>&1; then pass "www-data user exists"; else fail "www-data user does not exist"; fi

  if nginx -t >/dev/null 2>&1; then pass "current Nginx configuration validates"; else fail "current Nginx configuration does not validate"; fi

  for f in \
    "$SCRIPT_DIR/package.conf" \
    "$SCRIPT_DIR/SHA256SUMS" \
    "$SCRIPT_DIR/install_offline.sh" \
    "$SCRIPT_DIR/package_integrity.py" \
    "$SCRIPT_DIR/lesson_plan/payload/SHA256SUMS" \
    "$SCRIPT_DIR/teacher-app/APPROVAL.json" \
    "$SCRIPT_DIR/teacher-app/SHA256SUMS" \
    "$SCRIPT_DIR/teacher-app/verify_profile.py" \
    "$SCRIPT_DIR/lesson3/images/SHA256SUMS" \
    "$SCRIPT_DIR/ares_config.sh" \
    "$SCRIPT_DIR/optional_remote_support.sh" \
    "$SCRIPT_DIR/lesson_plan/configure_nginx.py" \
    "$SCRIPT_DIR/lesson3/configure_url.py" \
    "$SCRIPT_DIR/lesson_plan/install.sh" \
    "$SCRIPT_DIR/lesson_plan/payload/index.htmlf" \
    "$SCRIPT_DIR/lesson_plan/payload/index.html" \
    "$SCRIPT_DIR/lesson_plan/payload/index_bu.htmlf" \
    "$SCRIPT_DIR/lesson_plan/payload/ARES-Logo.png" \
    "$SCRIPT_DIR/lesson_plan/payload/PDF/index.html" \
    "$SCRIPT_DIR/lesson_plan/payload/generate_teacher_index.js" \
    "$SCRIPT_DIR/lesson_plan/payload/LESSON3_USER_GUIDE.pdf" \
    "$SCRIPT_DIR/tracking/install_lesson_plan_tracking.sh" \
    "$SCRIPT_DIR/tsavo/install.sh" \
    "$SCRIPT_DIR/tsavo/tsavo_install.py" \
    "$SCRIPT_DIR/tsavo/tsavo_content.py" \
    "$SCRIPT_DIR/tsavo/MANIFEST.json" \
    "$SCRIPT_DIR/tsavo/SHA256SUMS" \
    "$SCRIPT_DIR/lesson3/release/lesson3-online-deploy.tar.gz" \
    "$SCRIPT_DIR/lesson3/release/lesson3-online-deploy.tar.gz.sha256" \
    "$SCRIPT_DIR/lesson3/images/lesson3-${LESSON3_VERSION}-amd64-images.tar.gz" \
    "$SCRIPT_DIR/lesson3/corpus/install_lesson3_corpus.sh" \
    "$SCRIPT_DIR/lesson3/corpus/MANIFEST.json" \
    "$SCRIPT_DIR/lesson3/corpus/taxonomy.tsv" \
    "$SCRIPT_DIR/lesson3/corpus/SHA256SUMS" \
    "$SCRIPT_DIR/ARES_Sync_Rollout_Package/server-installer/update_school_server.sh" \
    "$SCRIPT_DIR/teacher-app/install_teacher_app.sh" \
    "$SCRIPT_DIR/teacher-app/ares-sync.apk" \
    "$SCRIPT_DIR/teacher-app/ares-sync.apk.sha256" \
    "$SCRIPT_DIR/teacher-app/install-page.html"; do
      [[ -f "$f" ]] && pass "package file present: ${f#$SCRIPT_DIR/}" || fail "package file missing: ${f#$SCRIPT_DIR/}"
  done

  if [[ -f /mnt/sda3/var/www/tracker/key_map.csv ]]; then pass "tracker key_map.csv exists"; else fail "tracker key_map.csv is missing"; fi
  if [[ -f /mnt/sda3/var/www/tracker/local_launch.html ]]; then pass "local tracker launcher exists"; else fail "tracker/local_launch.html is missing"; fi
  if [[ -f /mnt/sda3/var/www/tracker/external_launch.html ]]; then pass "external tracker launcher exists"; else fail "tracker/external_launch.html is missing"; fi
  if [[ -x /usr/local/sbin/ares_build_reports.sh ]]; then pass "ARES report builder is executable"; else fail "/usr/local/sbin/ares_build_reports.sh is missing or not executable"; fi
  if [[ -s /mnt/sda3/var/www/tracker/reports/combined_usage.csv ]]; then
    USAGE_BYTES=$(stat -c %s /mnt/sda3/var/www/tracker/reports/combined_usage.csv)
    if (( USAGE_BYTES <= 2097152 )); then
      pass "combined_usage.csv exists and is within the 2 MiB ARES Sync limit"
    else
      fail "combined_usage.csv exceeds the 2 MiB ARES Sync limit"
    fi
  else
    fail "combined_usage.csv is missing or empty; build ARES reports before installing ARES Sync"
  fi

  if grep -RqsE 'server_name[^;]*ares' /etc/nginx/sites-enabled /etc/nginx/conf.d 2>/dev/null; then
    pass "active Nginx configuration contains an ARES server_name"
  else
    fail "could not find an active Nginx configuration containing an ARES server_name"
  fi

  FREE_KB=$(df -Pk /mnt/sda3 | awk 'NR==2 {print $4}')
  MIN_KB=$((12 * 1024 * 1024))
  if [[ "$FREE_KB" =~ ^[0-9]+$ ]] && (( FREE_KB >= MIN_KB )); then
    pass "at least 12 GiB free on /mnt/sda3"
  else
    fail "less than 12 GiB free on /mnt/sda3"
  fi

  if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)3001$'; then
    if curl -fsS --max-time 4 http://127.0.0.1:3001/login >/dev/null 2>&1; then
      warn "port 3001 is already in use by a healthy HTTP service; Lesson3 installer will preserve a healthy existing installation"
    else
      fail "port 3001 is already in use, but /login is not healthy"
    fi
  else
    pass "port 3001 is available"
  fi

  # SeaVuria logo is decorative and intentionally non-fatal.
  if find "$SCRIPT_DIR/lesson_plan/payload" -maxdepth 1 -type f \( -iname 'seavuria-logo-2.jpg' -o -iname 'seavuria-logo2.jpg' \) | grep -q .; then
    pass "SeaVuria logo present"
  else
    warn "SeaVuria logo is absent; module will install without that decorative image"
  fi

  echo
  if (( FAILURES > 0 )); then
    echo "NOT READY: $FAILURES failure(s), $WARNINGS warning(s). No installation should be attempted."
    exit 1
  fi

  echo "READY TO INSTALL: 0 failures, $WARNINGS warning(s)."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then preflight_main "$@"; fi
