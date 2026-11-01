#!/usr/bin/env bash
# Continue the sealed C1 checkpoint. Build/verify only; never install on tsavo3.
set -Eeuo pipefail
umask 022
export PATH=/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8
unset PYTHONOPTIMIZE PYTHONPATH

SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BASE=/mnt/sda3/home/ares/Downloads
NORMALIZED="$BASE/ARES_Q4_Source_v1.13_normalized-728741b-r2"
EVIDENCE="$BASE/ARES_Q4_v1.13_build_evidence_728741b-r2"
OUT="$BASE/ARES_Q4_Update_offline_v1.13"
WORK="$BASE/.ARES_Q4_Update_offline_v1.13.building-simplified-r3"
RUN="$EVIDENCE/phase-c2-simplified-r3"
BUNDLE=ARES_Q4_Offline_v0.94_amd64_v1.13
APK="$NORMALIZED/teacher-app/ares-sync.apk"
APK_SHA=16e5eef24b56dde1db3fbd0e5be542c5853f329841ae056bc1dd7afb6bf773a8
RESUME=0
case "${1:-}" in
  "") ;;
  --resume) RESUME=1 ;;
  *) echo "Usage: bash run_tsavo3_build.sh [--resume]" >&2; exit 2 ;;
esac
(( $# <= 1 )) || { echo "Unexpected extra arguments" >&2; exit 2; }

[[ "$(hostname -s)" == tsavo3 && "$(uname -m)" == x86_64 ]] \
  || { echo "Run this continuation on tsavo3 (Ubuntu x86_64)." >&2; exit 1; }
test -z "$(git -C "$SELF_DIR" status --porcelain --untracked-files=all)"
if (( RESUME )); then
  [[ -d "$WORK/output/$BUNDLE" && -d "$RUN" && -f "$WORK/BUILD_INCOMPLETE" ]]
  [[ ! -e "$OUT" && ! -L "$OUT" ]]
  [[ "$(cat "$RUN/builder-commit.txt")" == ed5052a128152166bc3bdb08a051cb21875944c9 ]] \
    || { echo "This resume is for the recorded simplified-r3 candidate only." >&2; exit 1; }
  LOG="$RUN/resume-verification.log"
else
for path in "$WORK" "$RUN" "$OUT"; do
  [[ ! -e "$path" && ! -L "$path" ]] || { echo "Path already exists; retain it and obtain build support: $path" >&2; exit 1; }
done
(cd "$EVIDENCE" && sha256sum --strict -c source-review.sha256)
cmp "$EVIDENCE/normalized-source.jsonl" "$EVIDENCE/normalized-prebuild.jsonl"
docker info >/dev/null

# Check the existing seal, not the B1/B2 review process again.
python3 -B - "$NORMALIZED" "$EVIDENCE/normalized-source.jsonl" "$BASE" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import sys

root, inventory, base = map(Path, sys.argv[1:])
records = [json.loads(line) for line in inventory.read_text(encoding="utf-8").splitlines()]
expected = {item["path"]: item for item in records}
assert len(expected) == len(records) == 295, "Unexpected sealed inventory"
entries = list(root.rglob("*"))
assert all(not p.is_symlink() and (p.is_file() or p.is_dir()) for p in entries), "Unsupported source entry"
files = {p.relative_to(root).as_posix(): p for p in entries if p.is_file()}
assert files.keys() == expected.keys(), "Normalized inventory changed"
for name, path in files.items():
    record = expected[name]
    assert path.stat().st_size == record["bytes"], name
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    assert value.hexdigest() == record["sha256"], name
space = os.statvfs(base)
assert space.f_bavail * space.f_frsize >= 40 * 1024**3, "Less than 40 GiB available on the build disk"
print("PASS: sealed source unchanged; build storage available")
PY
[[ "$(sha256sum "$APK" | awk '{print $1}')" == "$APK_SHA" ]]

mkdir "$WORK"
mkdir "$WORK/tmp" "$WORK/output" "$RUN"
printf 'Not yet verified or promoted.\n' > "$WORK/BUILD_INCOMPLETE"
git -C "$SELF_DIR" rev-parse HEAD > "$RUN/builder-commit.txt"
date -u +%FT%TZ > "$RUN/started-utc.txt"
LOG="$RUN/build.log"
fi
export TMPDIR="$WORK/tmp" PYTHONDONTWRITEBYTECODE=1
trap 'if (( BASH_SUBSHELL == 0 )); then echo "Build stopped. Retain candidate files and send ARES support the log under: $RUN" >&2; fi' ERR

{
  if (( RESUME )); then
    echo "Resuming existing payload; no downloads, Docker pulls or image saves."
    STAGE="$WORK/output/$BUNDLE"
    # Validate the retained staging tree before updating the one reviewed helper.
    python3 -B "$SELF_DIR/tools/package_integrity.py" package "$STAGE"
    git -C "$SELF_DIR" rev-parse HEAD > "$RUN/resume-commit.txt"
    if [[ ! -e "$WORK/original-candidate.zip" ]]; then
      [[ -s "$WORK/output/$BUNDLE.zip" ]]
      cp -p "$STAGE/SHA256SUMS" "$WORK/original-SHA256SUMS"
      cp -p "$STAGE/package_integrity.py" "$WORK/original-package_integrity.py"
      mv -n -- "$WORK/output/$BUNDLE.zip" "$WORK/original-candidate.zip"
      sha256sum "$WORK/original-candidate.zip" > "$RUN/original-candidate.sha256"
    fi
    install -m 0644 "$SELF_DIR/tools/package_integrity.py" "$STAGE/package_integrity.py"
    (cd "$STAGE"; find . -type f ! -path './SHA256SUMS' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
    python3 -B - "$STAGE" "$WORK/output/$BUNDLE.zip" <<'PY'
from pathlib import Path
import sys
import zipfile

stage, output = map(Path, sys.argv[1:])
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
    for path in sorted(stage.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(stage.parent))
print("Repackaged existing payload with corrected archive checker")
PY
    python3 -B "$SELF_DIR/verify_offline_bundle.py" "$WORK/output/$BUNDLE.zip" \
      --profile production --apk-sha256 "$APK_SHA"
  else
    bash "$SELF_DIR/build_offline_bundle.sh" --source "$NORMALIZED" \
      --output "$WORK/output" --profile production --apk "$APK"
  fi

  # The builder has independently extracted and verified the ZIP. Check the
  # retained files against the sealed B2 allowlist as the final promotion gate.
  python3 -B - "$WORK/output/$BUNDLE" "$EVIDENCE" \
    "$WORK/final-content-classification.json" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

root, evidence, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(evidence))
from inheritance_policy import final_forbidden, generated

approved = json.loads((evidence / "approved-inherited.json").read_text(encoding="utf-8"))
assert len(approved) == 133 and "lesson3_uninstall.sh" in approved
inherited = set()
classification = []
for path in sorted(root.rglob("*")):
    if not path.is_file():
        continue
    name = path.relative_to(root).as_posix()
    assert not final_forbidden(name), "Forbidden legacy file: " + name
    category = "regenerated" if generated(name) else "inherited"
    if category == "inherited":
        assert name in approved, "Unreviewed inherited file: " + name
        assert path.stat().st_size == approved[name]["bytes"], name
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        assert value == approved[name]["sha256"], "Inherited file changed: " + name
        inherited.add(name)
    classification.append({"path": name, "category": category})
assert inherited == approved.keys(), "Approved inherited files are missing"
with output.open("w" if output.exists() else "x", encoding="utf-8") as stream:
    json.dump(classification, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print("PASS: 133 approved inherited files retained; final inventory classified")
PY

  sha256sum "$WORK/final-content-classification.json" > "$RUN/qualification.sha256"
  (cd "$WORK/output" && sha256sum "$BUNDLE.zip") > "$RUN/release.sha256"
  # No replacement of an existing output is permitted, including at promotion.
  [[ ! -e "$OUT" && ! -L "$OUT" ]]
  mv -Tn -- "$WORK/output" "$OUT"
  [[ ! -e "$WORK/output" && -s "$OUT/$BUNDLE.zip" ]]
  rm -- "$WORK/BUILD_INCOMPLETE"
  date -u +%FT%TZ > "$RUN/completed-utc.txt"
  echo "BUILD AND INDEPENDENT VERIFICATION PASSED"
  echo "Verified artifact: $OUT/$BUNDLE.zip"
  cat "$RUN/release.sha256"
  echo "No installer was run. Live installation and field acceptance remain Pending."
} 2>&1 | tee -a "$LOG"
