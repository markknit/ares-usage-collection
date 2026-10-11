#!/usr/bin/env bash
# Install the pinned ARES JSON corpus into a fresh Lesson3 v0.93 database.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="$SCRIPT_DIR/files"
MANIFEST="$SCRIPT_DIR/MANIFEST.json"
TAXONOMY="$SCRIPT_DIR/taxonomy.tsv"
CHECKSUMS="$SCRIPT_DIR/SHA256SUMS"
DEPLOY_DIR="${LESSON3_DEPLOY_DIR:-/mnt/sda3/var/www/lesson3-download/lesson3-deploy}"
COMPOSE_FILE="$DEPLOY_DIR/compose.offline.yaml"
APP_URL="${LESSON3_LOCAL_URL:-http://127.0.0.1:3001}"
EXPECTED_CORPUS_COMMIT="e07c243da77ad4554a2f404ae7790ef6e9d3e1b0"
BACKUP_ROOT="/var/backups/ares-lesson3-corpus"
MODE="install"

log() { printf 'lesson3-corpus: %s\n' "$*"; }
die() { printf 'lesson3-corpus: ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
Usage:
  sudo bash install_lesson3_corpus.sh
  sudo bash install_lesson3_corpus.sh --status

The default mode imports the packaged corpus into an empty Lesson3 database.
--status performs read-only validation and reports installed, empty, or partial.
USAGE
}

case "${1:-}" in
  "") ;;
  --status) MODE="status"; shift ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; die "unknown argument: $1" ;;
esac
(($# == 0)) || { usage >&2; die "unexpected additional arguments"; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
for cmd in curl docker python3 sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || die "required command '$cmd' was not found"
done
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required"

for path in "$FILES_DIR" "$MANIFEST" "$TAXONOMY" "$CHECKSUMS" "$COMPOSE_FILE"; do
  [[ -e "$path" ]] || die "required path is missing: $path"
done

log "verifying packaged corpus checksums and manifest"
(cd "$SCRIPT_DIR" && sha256sum -c "$(basename "$CHECKSUMS")")

readarray -t manifest_values < <(python3 - "$MANIFEST" "$FILES_DIR" "$EXPECTED_CORPUS_COMMIT" <<'PY'
import json, pathlib, sys
manifest_path = pathlib.Path(sys.argv[1])
files_dir = pathlib.Path(sys.argv[2])
expected_commit = sys.argv[3]
data = json.loads(manifest_path.read_text(encoding="utf-8"))
if data.get("format") != "ares-lesson3-offline-corpus-v1":
    raise SystemExit("unsupported corpus manifest format")
if data.get("source_commit") != expected_commit:
    raise SystemExit("corpus source commit does not match this installer")
records = data.get("files")
if not isinstance(records, list):
    raise SystemExit("manifest files is not an array")
actual = sorted(p.name for p in files_dir.glob("*_data.json") if p.is_file())
declared = sorted(str(r.get("file")) for r in records if isinstance(r, dict))
if actual != declared or len(actual) != data.get("file_count"):
    raise SystemExit("corpus file set does not match the manifest")
for key in ("file_count", "lesson_count", "subject_count", "subject_grade_count"):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SystemExit(f"invalid manifest count: {key}")
print(data["source_commit"])
print(data["file_count"])
print(data["lesson_count"])
print(data["subject_count"])
print(data["subject_grade_count"])
PY
)
CORPUS_COMMIT="${manifest_values[0]}"
EXPECTED_FILES="${manifest_values[1]}"
EXPECTED_LESSONS="${manifest_values[2]}"
EXPECTED_SUBJECTS="${manifest_values[3]}"
EXPECTED_SUBJECT_GRADES="${manifest_values[4]}"

cd "$DEPLOY_DIR"
docker compose -f "$COMPOSE_FILE" ps --status running --services | grep -qx app \
  || die "Lesson3 app container is not running"
curl -fsS --max-time 10 "$APP_URL/login" >/dev/null \
  || die "Lesson3 is not responding at $APP_URL/login"

db_query() {
  docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -v ON_ERROR_STOP=1 -U lesson3 -d lesson3 -At -F '|' -c "$1"
}

COUNT_QUERY='SELECT (SELECT count(*) FROM lesson_plans), (SELECT count(*) FROM lesson_bundle_versions), (SELECT count(*) FROM lesson_bundle_versions_lessons), (SELECT count(*) FROM lesson_plans WHERE official_version_id IS NOT NULL), (SELECT count(*) FROM subjects), (SELECT count(*) FROM subject_grades);'
EXPECTED_COUNTS="$EXPECTED_FILES|$EXPECTED_FILES|$EXPECTED_LESSONS|$EXPECTED_FILES|$EXPECTED_SUBJECTS|$EXPECTED_SUBJECT_GRADES"
EMPTY_COUNTS="0|0|0|0|0|0"
CURRENT_COUNTS="$(db_query "$COUNT_QUERY")"

if [[ "$MODE" == "status" ]]; then
  if [[ "$CURRENT_COUNTS" == "$EXPECTED_COUNTS" ]]; then
    echo "LESSON3_CORPUS_STATUS=installed"
  elif [[ "$CURRENT_COUNTS" == "$EMPTY_COUNTS" ]]; then
    echo "LESSON3_CORPUS_STATUS=empty"
  else
    printf 'lesson3-corpus: WARNING: unexpected content counts (plans|versions|lessons|official|subjects|subject-grades=%s)\n' \
      "$CURRENT_COUNTS" >&2
    echo "LESSON3_CORPUS_STATUS=partial"
  fi
  exit 0
fi

[[ "$CURRENT_COUNTS" == "$EMPTY_COUNTS" ]] || die \
  "Lesson3 content is not empty (plans|versions|lessons|official|subjects|subject-grades=$CURRENT_COUNTS). This bootstrap installer will not re-import or overwrite an existing corpus."

echo
echo "The first Lesson3 Site Administrator must already exist."
read -r -p "Site Administrator email: " ADMIN_EMAIL
read -r -s -p "Site Administrator password: " ADMIN_PASSWORD
echo
[[ -n "$ADMIN_EMAIL" && -n "$ADMIN_PASSWORD" ]] || die "email and password are required"

WORK_DIR="$(mktemp -d /tmp/lesson3-corpus.XXXXXX)"
chmod 700 "$WORK_DIR"
cleanup() {
  unset ADMIN_PASSWORD TOKEN
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

printf '%s\n%s\n' "$ADMIN_EMAIL" "$ADMIN_PASSWORD" | python3 -c '
import json, sys
email = sys.stdin.readline().rstrip("\n")
password = sys.stdin.readline().rstrip("\n")
json.dump({"email": email, "password": password}, sys.stdout)
' > "$WORK_DIR/login.json"
chmod 600 "$WORK_DIR/login.json"

LOGIN_STATUS="$(curl -sS --connect-timeout 10 --max-time 60 \
  -o "$WORK_DIR/login-response.json" -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data-binary "@$WORK_DIR/login.json" \
  "$APP_URL/api/users/login")" || die "could not contact Lesson3 login API"
rm -f "$WORK_DIR/login.json"
unset ADMIN_PASSWORD
[[ "$LOGIN_STATUS" == "200" ]] || die \
  "Lesson3 rejected the Site Administrator login (HTTP $LOGIN_STATUS)"

TOKEN="$(python3 - "$WORK_DIR/login-response.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
user = data.get("user") or {}
roles = user.get("roles") or []
if "siteAdmin" not in roles:
    raise SystemExit("the supplied account is not a Site Administrator")
token = data.get("token")
if not isinstance(token, str) or not token:
    raise SystemExit("login response did not contain a token")
print(token)
PY
)" || die "the supplied account is not an authenticated Site Administrator"

printf 'header = "Authorization: JWT %s"\n' "$TOKEN" > "$WORK_DIR/curl-auth.conf"
chmod 600 "$WORK_DIR/curl-auth.conf"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"
BACKUP_FILE="$BACKUP_DIR/pre-corpus.dump"
install -d -m 0700 "$BACKUP_DIR"
log "creating rollback snapshot at $BACKUP_FILE"
docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump -U lesson3 -d lesson3 -Fc > "$BACKUP_FILE"
chmod 600 "$BACKUP_FILE"
[[ -s "$BACKUP_FILE" ]] || die "rollback snapshot was not created"

MUTATION_STARTED=0
rollback() {
  local rc="${1:-1}"
  trap - ERR INT TERM
  if (( MUTATION_STARTED )); then
    printf '\nlesson3-corpus: import failed; restoring the pre-import database snapshot...\n' >&2
    if docker compose -f "$COMPOSE_FILE" stop app >/dev/null \
      && docker compose -f "$COMPOSE_FILE" exec -T postgres dropdb --if-exists --force -U lesson3 lesson3 \
      && docker compose -f "$COMPOSE_FILE" exec -T postgres createdb -U lesson3 lesson3 \
      && docker compose -f "$COMPOSE_FILE" exec -T postgres \
           pg_restore --no-owner --no-privileges -U lesson3 -d lesson3 < "$BACKUP_FILE" \
      && docker compose -f "$COMPOSE_FILE" start app >/dev/null; then
      for _ in $(seq 1 60); do
        if curl -fsS --max-time 5 "$APP_URL/login" >/dev/null 2>&1; then
          printf 'lesson3-corpus: rollback completed; the administrator account was preserved.\n' >&2
          exit "$rc"
        fi
        sleep 2
      done
    fi
    printf 'lesson3-corpus: CRITICAL: automatic rollback did not complete. Keep %s and obtain technical help before retrying.\n' "$BACKUP_FILE" >&2
  fi
  exit "$rc"
}
trap 'rollback $?' ERR
trap 'rollback 130' INT TERM

api_post_json() {
  local path="$1" body="$2" response="$3" status
  if ! status="$(curl -sS --connect-timeout 10 --max-time 120 \
      --config "$WORK_DIR/curl-auth.conf" \
      -o "$response" -w '%{http_code}' \
      -H 'Content-Type: application/json' \
      --data-binary "@$body" \
      "$APP_URL$path")"; then
    printf 'lesson3-corpus: API request %s failed during transport\n' "$path" >&2
    return 1
  fi
  if [[ ! "$status" =~ ^2 ]]; then
    printf 'lesson3-corpus: API request %s failed (HTTP %s): ' "$path" "$status" >&2
    python3 - "$response" <<'PY' >&2
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    print(data.get("message") or data.get("error") or data)
except Exception:
    print("unreadable response")
PY
    return 1
  fi
}

log "creating ${EXPECTED_SUBJECTS} subjects and ${EXPECTED_SUBJECT_GRADES} subject-grade rows"
MUTATION_STARTED=1
declare -A SUBJECT_IDS=()
while IFS=$'\t' read -r subject grade; do
  [[ -n "$subject" && -n "$grade" ]] || continue
  if [[ -z "${SUBJECT_IDS[$subject]+x}" ]]; then
    python3 - "$subject" <<'PY' > "$WORK_DIR/subject.json"
import json, sys
json.dump({"name": sys.argv[1]}, sys.stdout)
PY
    api_post_json "/api/subjects" "$WORK_DIR/subject.json" "$WORK_DIR/subject-response.json"
    subject_id="$(python3 - "$WORK_DIR/subject-response.json" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
doc = data.get("doc") or {}
value = doc.get("id")
if value is None:
    raise SystemExit("subject create response did not contain doc.id")
print(value)
PY
)"
    SUBJECT_IDS["$subject"]="$subject_id"
  fi
  python3 - "${SUBJECT_IDS[$subject]}" "$grade" <<'PY' > "$WORK_DIR/subject-grade.json"
import json, sys
subject_id = int(sys.argv[1]) if sys.argv[1].isdigit() else sys.argv[1]
json.dump({"subject": subject_id, "grade": int(sys.argv[2])}, sys.stdout)
PY
  api_post_json "/api/subject-grades" "$WORK_DIR/subject-grade.json" "$WORK_DIR/subject-grade-response.json"
done < "$TAXONOMY"

mapfile -d '' -t CORPUS_FILES < <(find "$FILES_DIR" -maxdepth 1 -type f -name '*_data.json' -print0 | sort -z)
[[ "${#CORPUS_FILES[@]}" -eq "$EXPECTED_FILES" ]] || {
  echo "lesson3-corpus: packaged file count changed after validation" >&2
  false
}

upload_batch() {
  local batch_number="$1"; shift
  local expected_count="$#" status response="$WORK_DIR/upload-${batch_number}.json"
  local -a args=(
    -sS --connect-timeout 10 --max-time 1800
    --config "$WORK_DIR/curl-auth.conf"
    -o "$response" -w '%{http_code}'
    -X POST
  )
  local file
  for file in "$@"; do
    # curl treats commas in an unquoted @filename as separators between files.
    # Quote the pathname within the multipart form expression.
    args+=( -F "files=@\"${file}\";type=application/json" )
  done
  log "uploading batch $batch_number ($expected_count JSON files)"
  if ! status="$(curl "${args[@]}" "$APP_URL/api/lesson-plans/upload")"; then
    printf 'lesson3-corpus: upload batch %s failed during transport\n' "$batch_number" >&2
    return 1
  fi
  if [[ "$status" != "200" ]]; then
    printf 'lesson3-corpus: upload batch %s failed (HTTP %s): ' "$batch_number" "$status" >&2
    python3 - "$response" <<'PY' >&2
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    print(data.get("error") or data.get("message") or data)
except Exception:
    print("unreadable response")
PY
    return 1
  fi
  python3 - "$response" "$expected_count" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
expected = int(sys.argv[2])
bundles = data.get("bundles")
if data.get("ok") is not True or data.get("count") != expected or not isinstance(bundles, list):
    raise SystemExit("upload response count did not match the submitted batch")
if any(b.get("action") != "created" or b.get("official") is not True or b.get("semver") != "1.0.0" for b in bundles):
    raise SystemExit("fresh import did not create only Official 1.0.0 plans")
PY
}

upload_batch 1 "${CORPUS_FILES[@]:0:50}"
upload_batch 2 "${CORPUS_FILES[@]:50}"

FINAL_COUNTS="$(db_query "$COUNT_QUERY")"
if [[ "$FINAL_COUNTS" != "$EXPECTED_COUNTS" ]]; then
  printf 'lesson3-corpus: database verification mismatch; expected %s, got %s\n' "$EXPECTED_COUNTS" "$FINAL_COUNTS" >&2
  false
fi

RECEIPT="$DEPLOY_DIR/CORPUS_INSTALLED.txt"
{
  echo "ARES Lesson3 corpus installed successfully"
  echo "Installed: $(date -Is)"
  echo "Source commit: $CORPUS_COMMIT"
  echo "Lesson plans: $EXPECTED_FILES"
  echo "Lessons: $EXPECTED_LESSONS"
  echo "Subjects: $EXPECTED_SUBJECTS"
  echo "Subject grades: $EXPECTED_SUBJECT_GRADES"
  echo "Rollback snapshot: $BACKUP_FILE"
} > "$RECEIPT"
chmod 600 "$RECEIPT"

trap - ERR INT TERM
log "installation complete: $EXPECTED_FILES lesson plans / $EXPECTED_LESSONS lessons"
log "all imported plans are Official version 1.0.0"
log "rollback snapshot retained at $BACKUP_FILE"
log "receipt written to $RECEIPT"
