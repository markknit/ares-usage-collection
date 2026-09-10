#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TRACKER_DIR=/mnt/sda3/var/www/tracker
REPORT_BUILD_COMMAND=/usr/local/sbin/ares_build_reports.sh
SOURCE_CSV=
WEB_USER=www-data
SCHOOL_CODE=
RETENTION_DAYS=60
SCHEDULE_FILE="$SCRIPT_DIR/collection_schedule.json"
INSTALL_ROOT=
SKIP_SMOKE_TEST=0
REPLACE_SCHEDULE=0

usage() {
  cat <<'USAGE'
Usage:
  sudo bash local-server/install_usage_collection.sh --school-code ARES-S00XX [options]

Required:
  --school-code CODE           Stable school/export code. Prefer the canonical ARES-S00XX ID.

Options:
  --tracker-dir PATH           Tracker web directory (default: /mnt/sda3/var/www/tracker)
  --report-build-command PATH  Existing ARES report builder (default: /usr/local/sbin/ares_build_reports.sh)
  --source-csv PATH            Existing combined usage CSV (default: TRACKER_DIR/reports/combined_usage.csv)
  --web-user USER              PHP-FPM/web account allowed to run the export wrapper (default: www-data)
  --schedule-file PATH         Collection schedule to install (default: repository collection_schedule.json)
  --retention-days DAYS        Local export retention (default: 60)
  --replace-schedule           Replace an existing tracker/collection_schedule.json after backing it up
  --skip-smoke-test            Install and syntax-check only; do not generate an AUTO export
  --install-root PATH          Testing only: prefix system destinations with PATH
  -h, --help                   Show this help
USAGE
}

die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "==> $*"; }
warn() { echo "WARNING: $*" >&2; }

while (($#)); do
  case "$1" in
    --school-code) SCHOOL_CODE=${2:-}; shift 2 ;;
    --tracker-dir) TRACKER_DIR=${2:-}; shift 2 ;;
    --report-build-command) REPORT_BUILD_COMMAND=${2:-}; shift 2 ;;
    --source-csv) SOURCE_CSV=${2:-}; shift 2 ;;
    --web-user) WEB_USER=${2:-}; shift 2 ;;
    --schedule-file) SCHEDULE_FILE=${2:-}; shift 2 ;;
    --retention-days) RETENTION_DAYS=${2:-}; shift 2 ;;
    --replace-schedule) REPLACE_SCHEDULE=1; shift ;;
    --skip-smoke-test) SKIP_SMOKE_TEST=1; shift ;;
    --install-root) INSTALL_ROOT=${2:-}; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

[[ -n "$SCHOOL_CODE" ]] || { usage >&2; die "--school-code is required"; }
[[ "$SCHOOL_CODE" =~ ^[A-Z0-9_-]+$ ]] || die "School code may contain only A-Z, 0-9, underscore, and hyphen"
[[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]] || die "--retention-days must be a non-negative integer"
[[ "$TRACKER_DIR" = /* ]] || die "--tracker-dir must be an absolute path"
[[ "$REPORT_BUILD_COMMAND" = /* ]] || die "--report-build-command must be an absolute path"
SOURCE_CSV=${SOURCE_CSV:-$TRACKER_DIR/reports/combined_usage.csv}
[[ "$SOURCE_CSV" = /* ]] || die "--source-csv must be an absolute path"
[[ "$SCHEDULE_FILE" = /* ]] || SCHEDULE_FILE=$(cd -- "$(dirname -- "$SCHEDULE_FILE")" && pwd)/$(basename -- "$SCHEDULE_FILE")

if [[ -z "$INSTALL_ROOT" && ${EUID:-$(id -u)} -ne 0 ]]; then
  die "Run as root (normally with sudo), or use --install-root for a sandbox test"
fi
if [[ -n "$INSTALL_ROOT" ]]; then
  mkdir -p "$INSTALL_ROOT"
  INSTALL_ROOT=$(cd -- "$INSTALL_ROOT" && pwd)
fi

for cmd in bash install php python3; do
  command -v "$cmd" >/dev/null 2>&1 || die "Required command not found: $cmd"
done
if [[ -z "$INSTALL_ROOT" ]]; then
  command -v visudo >/dev/null 2>&1 || die "visudo is required for safe sudoers validation"
  id "$WEB_USER" >/dev/null 2>&1 || die "Web/PHP user does not exist: $WEB_USER"
fi

for source in \
  "$SCRIPT_DIR/ares_prepare_usage_upload.sh" \
  "$SCRIPT_DIR/prepare_usage_upload.php" \
  "$SCRIPT_DIR/prepare_due_usage_upload.php" \
  "$SCHEDULE_FILE"; do
  [[ -f "$source" ]] || die "Required installation source is missing: $source"
done

# Validate repository sources before touching the server.
bash -n "$SCRIPT_DIR/ares_prepare_usage_upload.sh"
php -l "$SCRIPT_DIR/prepare_usage_upload.php" >/dev/null
php -l "$SCRIPT_DIR/prepare_due_usage_upload.php" >/dev/null
python3 - "$SCHEDULE_FILE" <<'PY'
import json, sys
p = sys.argv[1]
with open(p, encoding='utf-8') as f:
    data = json.load(f)
assert isinstance(data.get('collections'), list) and data['collections'], 'schedule has no collections'
for row in data['collections']:
    assert row.get('id') and row.get('due_date'), 'schedule collection missing id/due_date'
print('schedule JSON validated')
PY

rooted() {
  local logical=$1
  if [[ -n "$INSTALL_ROOT" ]]; then
    printf '%s%s' "$INSTALL_ROOT" "$logical"
  else
    printf '%s' "$logical"
  fi
}

STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_LOGICAL="/var/backups/ares-usage-collection/$STAMP"
BACKUP_DIR=$(rooted "$BACKUP_LOGICAL")
mkdir -p "$BACKUP_DIR"

backup_logical() {
  local logical=$1 actual rel
  actual=$(rooted "$logical")
  [[ -e "$actual" ]] || return 0
  rel=${logical#/}
  mkdir -p "$BACKUP_DIR/$(dirname -- "$rel")"
  cp -a -- "$actual" "$BACKUP_DIR/$rel"
  info "Backed up $logical"
}

WRAPPER_LOGICAL=/usr/local/sbin/ares_prepare_usage_upload.sh
CONF_LOGICAL=/etc/ares/usage-upload.conf
SUDOERS_LOGICAL=/etc/sudoers.d/ares-usage-export
UPLOAD_ENDPOINT_LOGICAL="$TRACKER_DIR/prepare_usage_upload.php"
DUE_ENDPOINT_LOGICAL="$TRACKER_DIR/prepare_due_usage_upload.php"
SCHEDULE_LOGICAL="$TRACKER_DIR/collection_schedule.json"
EXPORT_LOGICAL="$TRACKER_DIR/uploads"

for logical in "$WRAPPER_LOGICAL" "$CONF_LOGICAL" "$SUDOERS_LOGICAL" \
  "$UPLOAD_ENDPOINT_LOGICAL" "$DUE_ENDPOINT_LOGICAL"; do
  backup_logical "$logical"
done
if ((REPLACE_SCHEDULE)); then
  backup_logical "$SCHEDULE_LOGICAL"
fi

info "Installing ARES usage-collection components for $SCHOOL_CODE"
install -d -m 0755 "$(rooted /usr/local/sbin)" "$(rooted /etc/ares)" \
  "$(rooted /etc/sudoers.d)" "$(rooted "$TRACKER_DIR")" "$(rooted "$EXPORT_LOGICAL")"
install -m 0755 "$SCRIPT_DIR/ares_prepare_usage_upload.sh" "$(rooted "$WRAPPER_LOGICAL")"
install -m 0644 "$SCRIPT_DIR/prepare_usage_upload.php" "$(rooted "$UPLOAD_ENDPOINT_LOGICAL")"
install -m 0644 "$SCRIPT_DIR/prepare_due_usage_upload.php" "$(rooted "$DUE_ENDPOINT_LOGICAL")"

if [[ ! -e "$(rooted "$SCHEDULE_LOGICAL")" || $REPLACE_SCHEDULE -eq 1 ]]; then
  install -m 0644 "$SCHEDULE_FILE" "$(rooted "$SCHEDULE_LOGICAL")"
  info "Installed collection schedule"
else
  warn "Existing collection schedule preserved. Use --replace-schedule to replace it intentionally."
fi

quote_sh() { printf '%q' "$1"; }
{
  printf 'SCHOOL_CODE=%s\n' "$(quote_sh "$SCHOOL_CODE")"
  printf 'REPORT_BUILD_COMMAND=%s\n' "$(quote_sh "$REPORT_BUILD_COMMAND")"
  printf 'SOURCE_CSV=%s\n' "$(quote_sh "$SOURCE_CSV")"
  printf 'EXPORT_DIR=%s\n' "$(quote_sh "$EXPORT_LOGICAL")"
  printf 'RETENTION_DAYS=%s\n' "$RETENTION_DAYS"
} > "$(rooted "$CONF_LOGICAL")"
chmod 0644 "$(rooted "$CONF_LOGICAL")"

printf '%s ALL=(root) NOPASSWD: %s *\n' "$WEB_USER" "$WRAPPER_LOGICAL" > "$(rooted "$SUDOERS_LOGICAL")"
chmod 0440 "$(rooted "$SUDOERS_LOGICAL")"

bash -n "$(rooted "$WRAPPER_LOGICAL")"
php -l "$(rooted "$UPLOAD_ENDPOINT_LOGICAL")" >/dev/null
php -l "$(rooted "$DUE_ENDPOINT_LOGICAL")" >/dev/null
if command -v visudo >/dev/null 2>&1; then
  visudo -cf "$(rooted "$SUDOERS_LOGICAL")" >/dev/null
else
  warn "visudo unavailable in sandbox; sudoers syntax was not independently validated"
fi

if ((SKIP_SMOKE_TEST == 0)); then
  info "Running AUTO export smoke test"
  [[ -x "$REPORT_BUILD_COMMAND" ]] || die "Report builder is not executable: $REPORT_BUILD_COMMAND"
  SMOKE_OUTPUT=$(ARES_UPLOAD_CONF="$(rooted "$CONF_LOGICAL")" "$(rooted "$WRAPPER_LOGICAL")" AUTO)
  LAST_LINE=$(printf '%s\n' "$SMOKE_OUTPUT" | tail -n 1)
  python3 - "$LAST_LINE" <<'PY'
import json, os, sys
obj = json.loads(sys.argv[1])
assert obj.get('collection') == 'AUTO', obj
path = obj.get('path')
assert path and os.path.isfile(path), path
assert os.path.getsize(path) > 0, path
print('AUTO export smoke test passed:', obj['filename'])
PY
else
  info "Smoke test skipped by request"
fi

cat <<EOF2

ARES usage-collection server installation complete.
School code: $SCHOOL_CODE
Tracker directory: $TRACKER_DIR
Backup directory: $BACKUP_LOGICAL

Next checks:
  1. Confirm the due endpoint returns 204 when called with the phone's latest completed collection and no later collection is due.
  2. Use a controlled due collection to test HTTP 200 download from ARES Sync.
  3. Confirm the phone later uploads to the central HTTPS service when Internet returns.
EOF2
