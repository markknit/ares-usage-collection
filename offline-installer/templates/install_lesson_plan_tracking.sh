#!/usr/bin/env bash
set -Eeuo pipefail

KEY_MAP="${ARES_KEY_MAP:-/mnt/sda3/var/www/tracker/key_map.csv}"
BACKUP_ROOT="/var/backups/ares-lesson-plan-tracking"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"

die() { echo "tracking-map: ERROR: $*" >&2; exit 1; }
log() { echo "tracking-map: $*"; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
command -v python3 >/dev/null 2>&1 || die "python3 is required"
[[ -f "$KEY_MAP" ]] || die "tracker key map not found: $KEY_MAP"

mkdir -p "$BACKUP_DIR"
cp -a "$KEY_MAP" "$BACKUP_DIR/key_map.csv.before"

python3 - "$KEY_MAP" <<'PY'
import csv
import sys
from pathlib import Path

path = Path(sys.argv[1])
required = {
    "module:lesson_plans_landing": "CBE Lesson Plans",
    "module:lesson_plans_directory": "CBE Lesson Plan Directory",
    "module:lesson_plan_editor": "CBE Lesson Plan Editor",
}

existing = {}
with path.open("r", encoding="utf-8-sig", newline="") as f:
    for row in csv.reader(f):
        if not row:
            continue
        key = (row[0] or "").strip()
        display = (row[1] if len(row) > 1 else "").strip()
        if key:
            existing[key] = display

for key, display in required.items():
    if key in existing and existing[key] != display:
        raise SystemExit(
            f"ERROR: {key!r} already maps to {existing[key]!r}; expected {display!r}"
        )

missing = [(k, v) for k, v in required.items() if k not in existing]
if missing:
    with path.open("a", encoding="utf-8", newline="") as f:
        for key, display in missing:
            f.write(f"{key},{display},\n")

for key, display in required.items():
    print(f"OK: {key} -> {display}")
PY

log "tracking mappings installed; backup: $BACKUP_DIR"
