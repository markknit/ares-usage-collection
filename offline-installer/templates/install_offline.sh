#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCHOOL_CODE="${1:-}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="/var/log/ares-offline-install-${STAMP}.log"

[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "ERROR: run as root" >&2; exit 1; }
[[ -n "$SCHOOL_CODE" ]] || { echo "Usage: sudo bash install_offline.sh ARES-S00XX" >&2; exit 2; }
[[ "$SCHOOL_CODE" =~ ^[A-Z0-9_-]+$ ]] || { echo "ERROR: invalid school code" >&2; exit 2; }

exec > >(tee -a "$LOG_FILE") 2>&1

run_step() {
  local label=$1
  shift
  echo
  echo "============================================================"
  echo "$label"
  echo "============================================================"
  "$@"
}

install_lesson3_corpus_guided() {
  local corpus_script="$SCRIPT_DIR/lesson3/corpus/install_lesson3_corpus.sh"
  local status_output status confirmation

  status_output="$(bash "$corpus_script" --status)"
  printf '%s\n' "$status_output"
  status="$(printf '%s\n' "$status_output" | sed -n 's/^LESSON3_CORPUS_STATUS=//p' | tail -n 1)"

  case "$status" in
    installed)
      echo "Lesson3 corpus is already installed and its database counts are correct."
      return 0
      ;;
    empty)
      ;;
    partial)
      echo "ERROR: Lesson3 contains unexpected or partial content." >&2
      echo "The fresh-install corpus importer will not overwrite it." >&2
      echo "Stop and obtain technical review before continuing." >&2
      return 1
      ;;
    *)
      echo "ERROR: could not determine Lesson3 corpus status." >&2
      return 1
      ;;
  esac

  cat <<EOF

ACTION REQUIRED: create the first Lesson3 Site Administrator.

1. Leave this installer open.
2. In a browser, open: http://ares.local:3001/login
3. Create the first Site Administrator and store its credentials securely.
4. Return to this terminal.

EOF
  [[ -t 0 ]] || {
    echo "ERROR: interactive terminal input is required to complete Lesson3 setup." >&2
    return 1
  }
  read -r -p "Type READY after the Site Administrator exists: " confirmation
  [[ "$confirmation" == "READY" ]] || {
    echo "ERROR: confirmation was not READY; no corpus data was imported." >&2
    return 1
  }

  bash "$corpus_script"

  status_output="$(bash "$corpus_script" --status)"
  printf '%s\n' "$status_output"
  grep -q '^LESSON3_CORPUS_STATUS=installed$' <<<"$status_output" || {
    echo "ERROR: Lesson3 corpus verification did not report installed." >&2
    return 1
  }
}

echo "ARES Q4 OFFLINE INSTALLER"
echo "School: $SCHOOL_CODE"
echo "Host:   $(hostname)"
echo "Log:    $LOG_FILE"

run_step "0) Preflight - verify server and package before changes" \
  bash "$SCRIPT_DIR/preflight.sh" "$SCHOOL_CODE"

run_step "1) Install/update Lesson Plan module + ares.local" \
  bash "$SCRIPT_DIR/lesson_plan/install.sh"

run_step "2) Install Lesson Plan Editor from offline images" \
  bash "$SCRIPT_DIR/lesson3/install_lesson3_offline.sh"

run_step "3) Install Lesson Plan tracking mappings" \
  bash "$SCRIPT_DIR/tracking/install_lesson_plan_tracking.sh"

run_step "4) Install/update ARES Sync usage collection" \
  bash "$SCRIPT_DIR/ARES_Sync_Rollout_Package/server-installer/update_school_server.sh" \
    --school-code "$SCHOOL_CODE"

run_step "5) Deploy offline ARES Sync teacher APK + install page" \
  bash "$SCRIPT_DIR/teacher-app/install_teacher_app.sh"

run_step "6) Install dormant remote-access components" \
  bash "$SCRIPT_DIR/remote-access/prepare_remote_access.sh"

run_step "7) Create Lesson3 administrator and install the packaged corpus" \
  install_lesson3_corpus_guided

run_step "8) Post-install verification" bash -c '
  set -e
  nginx -t
  systemctl is-active --quiet nginx
  curl -fsS --max-time 8 -H "Host: ares.local" http://127.0.0.1/ >/dev/null
  curl -fsS --max-time 8 http://127.0.0.1:3001/login >/dev/null
  grep -q "module:lesson_plans_directory" /mnt/sda3/var/www/tracker/key_map.csv
  grep -q "module:lesson_plan_editor" /mnt/sda3/var/www/tracker/key_map.csv
  test -f /mnt/sda3/var/www/modules/Lesson_Plans/index.htmlf
  test -f /mnt/sda3/var/www/modules/Lesson_Plans/PDF/index.html
  test -s /mnt/sda3/var/www/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf
  test "$(head -c 5 /mnt/sda3/var/www/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf)" = "%PDF-"
  test -s /mnt/sda3/var/www/downloads/ares-sync.apk
  test -f /mnt/sda3/var/www/downloads/ares-sync.apk.sha256
  test -f /mnt/sda3/var/www/app_install/index.html
  curl -fsS --max-time 8 -H "Host: ares.local" http://127.0.0.1/app_install/ >/dev/null
  curl -fsS --max-time 8 -H "Host: ares.local" http://127.0.0.1/downloads/ares-sync.apk -o /dev/null
  curl -fsS --max-time 8 -H "Host: ares.local" http://127.0.0.1/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf -o /dev/null
  test -x "$0/lesson3/corpus/install_lesson3_corpus.sh"
  test -s "$0/lesson3/corpus/MANIFEST.json"
  test -s /mnt/sda3/var/www/lesson3-download/lesson3-deploy/CORPUS_INSTALLED.txt
  command -v tigervncserver >/dev/null
  command -v tigervncpasswd >/dev/null
  command -v tailscale >/dev/null
  command -v tailscaled >/dev/null
  test -x /usr/local/sbin/ares-enable-remote-access
  test -x /usr/local/sbin/ares-disable-remote-access
  ! systemctl is-active --quiet tailscaled.service
  ! systemctl is-active --quiet "tigervncserver@:1.service"
  ! pgrep -x x11vnc >/dev/null
  ! ss -ltn | awk "{print \$4}" | grep -Eq "(^|:)5901$"
  echo "PASS: Nginx, ARES root, Lesson3, tracking, Lesson Plans, and offline teacher APK verified"
' "$SCRIPT_DIR"

echo
echo "ARES Q4 offline installation completed successfully for $SCHOOL_CODE."
echo "Lesson Plan Editor: http://ares.local:3001/login"
echo "Lesson3 User Guide: http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf"
echo "Teacher ARES Sync installer: http://ares.local/app_install/"
echo "Direct teacher APK: http://ares.local/downloads/ares-sync.apk"
echo "Installation log: $LOG_FILE"
echo "Lesson3 corpus: installed and verified (95 plans / 806 lessons)"
echo "Remote access: Tailscale and TigerVNC are installed but stopped, disabled, and unregistered."
echo "Later activation: sudo ares-enable-remote-access"
