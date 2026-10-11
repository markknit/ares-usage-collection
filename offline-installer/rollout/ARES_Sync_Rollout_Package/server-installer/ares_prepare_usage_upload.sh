#!/usr/bin/env bash
set -euo pipefail
CONF=${ARES_UPLOAD_CONF:-/etc/ares/usage-upload.conf}
[[ -r "$CONF" ]] || { echo "Missing $CONF" >&2; exit 2; }
# shellcheck source=/dev/null
source "$CONF"
COLLECTION=${1:-AUTO}; COLLECTION=$(printf '%s' "$COLLECTION" | tr -cd 'A-Za-z0-9_-')
exec 9>"${LOCK_FILE:-/run/lock/ares-usage-upload.lock}";flock -n 9 || { echo 'Report generation already running' >&2; exit 3; }
${REPORT_BUILD_COMMAND:?REPORT_BUILD_COMMAND required}
[[ -s "${SOURCE_CSV:?SOURCE_CSV required}" ]] || { echo 'Source CSV missing or empty' >&2; exit 4; }
mkdir -p "${EXPORT_DIR:?EXPORT_DIR required}"
STAMP=$(date +%Y-%m-%d_%H-%M-%S);NAME="ARES_USAGE_${SCHOOL_CODE}_${COLLECTION}_${STAMP}.csv";DEST="$EXPORT_DIR/$NAME"
install -m 0644 "$SOURCE_CSV" "$DEST";SHA=$(sha256sum "$DEST"|awk '{print $1}')
find "$EXPORT_DIR" -type f -name 'ARES_USAGE_*.csv' -mtime +"${RETENTION_DAYS:-60}" -delete
printf '{"filename":"%s","path":"%s","sha256":"%s","bytes":%s,"collection":"%s"}\n' "$NAME" "$DEST" "$SHA" "$(stat -c %s "$DEST")" "$COLLECTION"
