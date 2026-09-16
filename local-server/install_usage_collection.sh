#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TRACKER_DIR=/mnt/sda3/var/www/tracker
REPORT_BUILD_COMMAND=/usr/local/sbin/ares_build_reports.sh
SOURCE_CSV=
WEB_USER=www-data
SCHOOL_CODE=
RETENTION_DAYS=60
MAX_UPLOAD_BYTES=2097152
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

rooted() {
  local logical=$1
  if [[ -n "$INSTALL_ROOT" ]]; then
    printf '%s%s' "$INSTALL_ROOT" "$logical"
  else
    printf '%s' "$logical"
  fi
}

for cmd in bash find flock install php python3 sha256sum stat; do
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
import datetime
import json
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

def ensure(condition, message):
    if not condition:
        raise SystemExit(f'schedule validation failed: {message}')

p = sys.argv[1]
with open(p, encoding='utf-8') as f:
    data = json.load(f)

ensure(isinstance(data, dict), 'schedule root must be an object')
school_year = str(data.get('school_year', ''))
ensure(re.fullmatch(r'\d{4}', school_year), 'schedule has an invalid school_year')
timezone = data.get('timezone')
ensure(isinstance(timezone, str) and timezone, 'schedule has no timezone')
try:
    ZoneInfo(timezone)
except ZoneInfoNotFoundError as exc:
    raise SystemExit(f'schedule validation failed: invalid timezone {timezone!r}') from exc

collections = data.get('collections')
ensure(isinstance(collections, list) and collections, 'schedule has no collections')
ids = set()
dates = []
for row in data['collections']:
    ensure(isinstance(row, dict), 'schedule collection must be an object')
    collection_id = row.get('id')
    label = row.get('label')
    due_date = row.get('due_date')
    ensure(
        isinstance(collection_id, str) and re.fullmatch(
            rf'{re.escape(school_year)}-Q[1-3]-(MID|END)', collection_id
        ),
        f'invalid production collection id: {collection_id!r}',
    )
    ensure(collection_id not in ids, f'duplicate collection id: {collection_id}')
    ensure(isinstance(label, str) and label.strip(), f'{collection_id} has no label')
    try:
        parsed_date = datetime.date.fromisoformat(due_date)
    except (TypeError, ValueError) as exc:
        raise SystemExit(
            f'schedule validation failed: {collection_id} has an invalid due_date'
        ) from exc
    ensure(parsed_date.year == int(school_year), f'{collection_id} due_date is outside school_year')
    ids.add(collection_id)
    dates.append(parsed_date)

ensure(dates == sorted(dates), 'schedule collections are not in chronological order')
ensure(len(dates) == len(set(dates)), 'schedule contains duplicate due dates')
print('schedule JSON validated')
PY

REPORT_BUILD_ACTUAL=$(rooted "$REPORT_BUILD_COMMAND")
SOURCE_CSV_ACTUAL=$(rooted "$SOURCE_CSV")

# Fail before backing up or replacing any component when the live export path
# cannot possibly complete. Sandbox installs can exercise the same preflight by
# placing a fake builder and source CSV below --install-root.
if ((SKIP_SMOKE_TEST == 0)); then
  [[ -x "$REPORT_BUILD_ACTUAL" ]] || die "Report builder is not executable: $REPORT_BUILD_COMMAND"
  [[ -s "$SOURCE_CSV_ACTUAL" ]] || die "Source CSV is missing or empty: $SOURCE_CSV"
  SOURCE_BYTES=$(stat -c %s "$SOURCE_CSV_ACTUAL")
  ((SOURCE_BYTES <= MAX_UPLOAD_BYTES)) || die "Source CSV is $SOURCE_BYTES bytes; central upload limit is $MAX_UPLOAD_BYTES bytes"
fi

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
LOCK_LOGICAL=/run/lock/ares-usage-upload.lock

for logical in "$WRAPPER_LOGICAL" "$CONF_LOGICAL" "$SUDOERS_LOGICAL" \
  "$UPLOAD_ENDPOINT_LOGICAL" "$DUE_ENDPOINT_LOGICAL"; do
  backup_logical "$logical"
done
if ((REPLACE_SCHEDULE)); then
  backup_logical "$SCHEDULE_LOGICAL"
fi

info "Installing ARES usage-collection components for $SCHOOL_CODE"
install -d -m 0755 "$(rooted /usr/local/sbin)" "$(rooted /etc/ares)" \
  "$(rooted /etc/sudoers.d)" "$(rooted /run/lock)" \
  "$(rooted "$TRACKER_DIR")" "$(rooted "$EXPORT_LOGICAL")"
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
  printf 'REPORT_BUILD_COMMAND=%s\n' "$(quote_sh "$REPORT_BUILD_ACTUAL")"
  printf 'SOURCE_CSV=%s\n' "$(quote_sh "$SOURCE_CSV_ACTUAL")"
  printf 'EXPORT_DIR=%s\n' "$(quote_sh "$(rooted "$EXPORT_LOGICAL")")"
  printf 'LOCK_FILE=%s\n' "$(quote_sh "$(rooted "$LOCK_LOGICAL")")"
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
  SMOKE_OUTPUT=$(ARES_UPLOAD_CONF="$(rooted "$CONF_LOGICAL")" "$(rooted "$WRAPPER_LOGICAL")" AUTO)
  LAST_LINE=$(printf '%s\n' "$SMOKE_OUTPUT" | tail -n 1)
  SMOKE_BYTES=$(python3 - "$LAST_LINE" "$MAX_UPLOAD_BYTES" <<'PY'
import json, os, sys
obj = json.loads(sys.argv[1])
max_bytes = int(sys.argv[2])
assert obj.get('collection') == 'AUTO', obj
path = obj.get('path')
assert path and os.path.isfile(path), path
assert os.path.getsize(path) > 0, path
assert obj.get('bytes') == os.path.getsize(path), obj
assert obj['bytes'] <= max_bytes, f"export is {obj['bytes']} bytes; upload limit is {max_bytes} bytes"
print(obj['bytes'])
PY
  )
  info "AUTO export smoke test passed: $SMOKE_BYTES bytes"
else
  info "Smoke test skipped by request"
fi

cat <<EOF2

ARES usage-collection server installation complete.
School code: $SCHOOL_CODE
Tracker directory: $TRACKER_DIR
Backup directory: $BACKUP_LOGICAL
Measured usage CSV: ${SMOKE_BYTES:-not measured (smoke test skipped)}

Next checks:
  1. Confirm the due endpoint returns 204 when called with the phone's latest completed collection and no later collection is due.
  2. Use a controlled due collection to test HTTP 200 download from ARES Sync.
  3. Confirm the phone later uploads to the central HTTPS service when Internet returns.
EOF2
