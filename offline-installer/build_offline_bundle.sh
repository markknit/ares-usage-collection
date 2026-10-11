#!/usr/bin/env bash
# Build a field-ready ARES Q4 offline bundle on an Internet-connected machine.
set -Eeuo pipefail

SELF_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE=""
OUTPUT=""
LESSON3_VERSION="v0.93"
PLATFORM="linux/amd64"
SCAFFOLD_ONLY=0
APK_PATH=""
BUNDLE_REVISION="v1.10"
APK_URL=""
APK_SHA256=""
APK_MANIFEST_URL="https://raw.githubusercontent.com/markknit/ares-usage-collection/main/config/approved_apk.json"
CORPUS_REPO="https://github.com/markknit/cbe-generation-system.git"
CORPUS_COMMIT="e07c243da77ad4554a2f404ae7790ef6e9d3e1b0"
CORPUS_EXPECTED_FILES=95
CORPUS_EXPECTED_LESSONS=806
TAILSCALE_VERSION="1.104.1"
TIGERVNC_VERSION="1.13.1+dfsg-2build2"
FILE_READBACKWARDS_VERSION="1.06-2"

usage() {
  cat <<'USAGE'
Usage:
  bash build_offline_bundle.sh --source /path/to/ARES_Q4_Update --output /path/to/output [options]

Options:
  --lesson3-version v0.93   Lesson3 release to pin (default: v0.93)
  --apk /path/ares-sync.apk Approved signed production ARES Sync APK (optional override)
  --apk-url URL             Approved production APK URL (requires --apk-sha256)
  --apk-sha256 HEX          Expected SHA-256 for --apk-url
  --apk-manifest-url URL    Approval manifest JSON (default: ARES GitHub config/approved_apk.json)
  --scaffold-only           Build/test package structure without downloading Lesson3/images/APK.
                            The result is NOT field-ready.

The normal build requires Internet access plus Docker Engine/Compose. It downloads the pinned
Lesson3 release and pinned JSON corpus, pulls the exact linux/amd64 images, saves them into the
bundle, generates SHA256SUMS, audits school-side shell scripts for Internet-dependent commands,
and creates a ZIP.
USAGE
}

die() { echo "builder: ERROR: $*" >&2; exit 1; }
log() { echo "builder: $*"; }

while (($#)); do
  case "$1" in
    --source) SOURCE=${2:-}; shift 2 ;;
    --output) OUTPUT=${2:-}; shift 2 ;;
    --lesson3-version) LESSON3_VERSION=${2:-}; shift 2 ;;
    --apk) APK_PATH=${2:-}; shift 2 ;;
    --apk-url) APK_URL=${2:-}; shift 2 ;;
    --apk-sha256) APK_SHA256=${2:-}; shift 2 ;;
    --apk-manifest-url) APK_MANIFEST_URL=${2:-}; shift 2 ;;
    --scaffold-only) SCAFFOLD_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[[ -n "$SOURCE" && -d "$SOURCE" ]] || die "--source must name the extracted ARES Q4 source directory"
[[ -n "$OUTPUT" ]] || die "--output is required"
SOURCE="$(cd "$SOURCE" && pwd)"
mkdir -p "$OUTPUT"
OUTPUT="$(cd "$OUTPUT" && pwd)"

for cmd in bash rsync sed sha256sum tar gzip python3; do
  command -v "$cmd" >/dev/null 2>&1 || die "required build command not found: $cmd"
done

if (( ! SCAFFOLD_ONLY )); then
  if [[ -n "$APK_PATH" ]]; then
    [[ -f "$APK_PATH" ]] || die "--apk file not found: $APK_PATH"
    APK_PATH="$(cd "$(dirname "$APK_PATH")" && pwd)/$(basename "$APK_PATH")"
  fi
  if [[ -n "$APK_URL" || -n "$APK_SHA256" ]]; then
    [[ -n "$APK_URL" && -n "$APK_SHA256" ]] || die "--apk-url and --apk-sha256 must be supplied together"
  fi
  for cmd in curl docker git apt-get dpkg-deb; do command -v "$cmd" >/dev/null 2>&1 || die "required build command not found: $cmd"; done
  docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required on the build machine"
fi

BUNDLE_NAME="ARES_Q4_Offline_${LESSON3_VERSION}_amd64_${BUNDLE_REVISION}"
STAGE="$OUTPUT/$BUNDLE_NAME"
ZIPFILE="$OUTPUT/$BUNDLE_NAME.zip"
if [[ -e "$STAGE" ]]; then
  chmod -R u+rwX "$STAGE" || die "could not make prior staging directory removable: $STAGE"
fi
rm -rf "$STAGE" "$ZIPFILE"
mkdir -p "$STAGE"

log "copying ARES source package"
rsync -a --chmod=Du+w,Fu+w \
  --exclude='setup-ares-tailscale-vnc-v2.sh' \
  "$SOURCE/" "$STAGE/"
chmod -R u+rwX "$STAGE"

# The Q4 source archive predates the reviewed school-code reassignment command.
# Always replace its rollout directory with the vetted copy shipped with this
# builder so an older source folder cannot silently remove current safeguards.
[[ -d "$SELF_DIR/rollout/ARES_Sync_Rollout_Package/server-installer" ]] \
  || die "embedded ARES Sync rollout package is missing"
mkdir -p "$STAGE/ARES_Sync_Rollout_Package"
rsync -a --delete \
  "$SELF_DIR/rollout/ARES_Sync_Rollout_Package/" \
  "$STAGE/ARES_Sync_Rollout_Package/"

# Do not ship stale/backup installer scripts into the field bundle.
# The offline audit intentionally scans every remaining .sh file, even if it is not
# called by install_offline.sh, so obsolete online installers must be removed here.
while IFS= read -r -d '' stale; do
  log "removing obsolete source artifact: ${stale#$STAGE/}"
  rm -f "$stale"
done < <(find "$STAGE" -type f \( -name '*-old.sh' -o -name '*_old.sh' -o -name '*.old.sh' -o -name '*.bak' -o -name '*.bak.*' -o -name '*~' \) -print0)

# Remove old online entrypoints and obsolete proxy installer.
rm -f "$STAGE/ares_q4_update.sh" "$STAGE/lesson3.sh"
rm -f "$STAGE/lesson_plan/install_ares_lesson_plan_editor_proxy.sh"

mkdir -p "$STAGE/lesson3/release" "$STAGE/lesson3/images" "$STAGE/lesson3/corpus" "$STAGE/tracking" "$STAGE/teacher-app"
mkdir -p "$STAGE/remote-access/tigervnc" "$STAGE/remote-access/tailscale"
install -m 0755 "$SELF_DIR/templates/install_offline.sh" "$STAGE/install_offline.sh"
install -m 0755 "$SELF_DIR/templates/preflight.sh" "$STAGE/preflight.sh"
install -m 0755 "$SELF_DIR/templates/lesson3_offline.sh" "$STAGE/lesson3/install_lesson3_offline.sh"
install -m 0755 "$SELF_DIR/templates/install_lesson3_corpus.sh" "$STAGE/lesson3/corpus/install_lesson3_corpus.sh"
install -m 0755 "$SELF_DIR/templates/install_lesson_plan_tracking.sh" "$STAGE/tracking/install_lesson_plan_tracking.sh"
install -m 0755 "$SELF_DIR/templates/install_teacher_app.sh" "$STAGE/teacher-app/install_teacher_app.sh"
install -m 0644 "$SELF_DIR/templates/teacher_install_page.html" "$STAGE/teacher-app/install-page.html"
install -m 0755 "$SELF_DIR/templates/lesson_plan_install.sh" "$STAGE/lesson_plan/install.sh"
install -m 0755 "$SELF_DIR/templates/prepare_remote_access.sh" "$STAGE/remote-access/prepare_remote_access.sh"
install -m 0755 "$SELF_DIR/templates/ares_enable_remote_access.sh" "$STAGE/remote-access/ares_enable_remote_access.sh"
install -m 0755 "$SELF_DIR/templates/ares_disable_remote_access.sh" "$STAGE/remote-access/ares_disable_remote_access.sh"
install -m 0644 "$SELF_DIR/templates/index.htmlf" "$STAGE/lesson_plan/payload/index.htmlf"
install -m 0644 "$SELF_DIR/templates/index.html" "$STAGE/lesson_plan/payload/index.html"
mkdir -p "$STAGE/docs"
install -m 0644 "$SELF_DIR/docs/TECHNICIAN_PHONE_INSTALL.md" "$STAGE/docs/TECHNICIAN_PHONE_INSTALL.md"
install -m 0644 "$SELF_DIR/docs/TEACHER_PHONE_GUIDE.md" "$STAGE/docs/TEACHER_PHONE_GUIDE.md"
install -m 0644 "$SELF_DIR/docs/LESSON3_CORPUS_INSTALL.md" "$STAGE/docs/LESSON3_CORPUS_INSTALL.md"
install -m 0644 "$SELF_DIR/docs/REMOTE_ACCESS.md" "$STAGE/docs/REMOTE_ACCESS.md"
mkdir -p "$STAGE/docs/pdf"
install -m 0644 "$SELF_DIR/docs/pdf/ARES_Sync_Technician_Guide.pdf" "$STAGE/docs/pdf/ARES_Sync_Technician_Guide.pdf"
install -m 0644 "$SELF_DIR/docs/pdf/ARES_Sync_Teacher_Guide.pdf" "$STAGE/docs/pdf/ARES_Sync_Teacher_Guide.pdf"
install -m 0644 "$SELF_DIR/docs/LESSON3_USER_GUIDE.pdf" "$STAGE/docs/LESSON3_USER_GUIDE.pdf"
install -m 0644 "$SELF_DIR/docs/LESSON3_USER_GUIDE.pdf" "$STAGE/lesson_plan/payload/LESSON3_USER_GUIDE.pdf"

# If the source has a SeaVuria logo under any historic spelling, canonicalize it.
for candidate in \
  "$SOURCE/lesson_plan/payload/SeaVuria-Logo-2.jpg" \
  "$SOURCE/lesson_plan/payload/SeaVuria-Logo2.jpg" \
  "$SOURCE/lesson_plan/payload/Seavuria-Logo-2.jpg" \
  "$SOURCE/lesson_plan/payload/Seavuria-Logo2.jpg"; do
  if [[ -f "$candidate" ]]; then
    install -m 0644 "$candidate" "$STAGE/lesson_plan/payload/SeaVuria-Logo-2.jpg"
    break
  fi
done

# Normalize all shell scripts to Unix line endings.
while IFS= read -r -d '' f; do sed -i 's/\r$//' "$f"; done < <(find "$STAGE" -type f -name '*.sh' -print0)

if (( SCAFFOLD_ONLY )); then
  cat > "$STAGE/NOT_FIELD_READY.txt" <<TXT
This scaffold was built without Lesson3 release assets or Docker images.
Run build_offline_bundle.sh normally on an Internet-connected Docker machine before field deployment.
TXT
else
  APK_WORK="$(mktemp -d)"
  trap 'rm -rf "$APK_WORK"' EXIT
  APK_SOURCE_DESC=""
  APPROVED_SHA=""

  if [[ -n "$APK_PATH" ]]; then
    log "using explicitly supplied approved ARES Sync APK"
    cp "$APK_PATH" "$APK_WORK/ares-sync.apk"
    APPROVED_SHA="$(sha256sum "$APK_WORK/ares-sync.apk" | awk '{print $1}')"
    APK_SOURCE_DESC="local file: $APK_PATH"
  else
    if [[ -z "$APK_URL" ]]; then
      log "loading approved APK manifest from $APK_MANIFEST_URL"
      curl -fsSL --retry 3 --connect-timeout 20 -o "$APK_WORK/approved_apk.json" "$APK_MANIFEST_URL" \
        || die "could not download approved APK manifest; use --apk or --apk-url/--apk-sha256"
      readarray -t manifest_fields < <(python3 - "$APK_WORK/approved_apk.json" <<'PYMAN'
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    d=json.load(f)
print((d.get('download_url') or '').strip())
print((d.get('sha256') or '').strip().lower())
print((d.get('app_id') or '').strip())
print((d.get('channel') or '').strip())
PYMAN
)
      APK_URL="${manifest_fields[0]:-}"
      APK_SHA256="${manifest_fields[1]:-}"
      [[ "${manifest_fields[2]:-}" == "org.areseducation.sync" ]] || die "approved APK manifest has unexpected app_id"
      [[ "${manifest_fields[3]:-}" == "production" ]] || die "approved APK manifest is not production channel"
      [[ -n "$APK_URL" && -n "$APK_SHA256" ]] || die "approved APK manifest is not configured yet; provide --apk or --apk-url/--apk-sha256"
    fi
    [[ "$APK_SHA256" =~ ^[0-9a-fA-F]{64}$ ]] || die "approved APK SHA-256 must be exactly 64 hex characters"
    log "downloading approved production ARES Sync APK"
    curl -fL --retry 3 --connect-timeout 20 -o "$APK_WORK/ares-sync.apk" "$APK_URL" \
      || die "could not download approved production APK"
    ACTUAL_APK_SHA="$(sha256sum "$APK_WORK/ares-sync.apk" | awk '{print $1}')"
    [[ "${ACTUAL_APK_SHA,,}" == "${APK_SHA256,,}" ]] \
      || die "downloaded APK SHA-256 mismatch (expected $APK_SHA256, got $ACTUAL_APK_SHA)"
    APPROVED_SHA="${APK_SHA256,,}"
    APK_SOURCE_DESC="URL: $APK_URL"
  fi

  log "validating approved ARES Sync APK"
  python3 - "$APK_WORK/ares-sync.apk" <<'PYAPK'
from pathlib import Path
import sys, zipfile
p=Path(sys.argv[1])
if not p.is_file() or p.stat().st_size < 1024:
    raise SystemExit("APK is missing or unexpectedly small")
try:
    with zipfile.ZipFile(p) as z:
        names=set(z.namelist())
        if "AndroidManifest.xml" not in names:
            raise SystemExit("file is a ZIP but does not contain AndroidManifest.xml")
except zipfile.BadZipFile:
    raise SystemExit("file is not a valid APK/ZIP archive")
print(f"APK validated: {p.name} ({p.stat().st_size} bytes)")
PYAPK
  install -m 0644 "$APK_WORK/ares-sync.apk" "$STAGE/teacher-app/ares-sync.apk"
  (cd "$STAGE/teacher-app" && sha256sum ares-sync.apk > ares-sync.apk.sha256)
  {
    echo "Source: $APK_SOURCE_DESC"
    echo "Bundled filename: ares-sync.apk"
    echo "Build time: $(date -Is)"
    echo "SHA-256: $(sha256sum "$STAGE/teacher-app/ares-sync.apk" | awk '{print $1}')"
    echo "Approved SHA-256: $APPROVED_SHA"
  } > "$STAGE/teacher-app/APK_INFO.txt"
  if command -v apksigner >/dev/null 2>&1; then
    log "verifying APK signature with apksigner"
    apksigner verify --verbose --print-certs "$APK_WORK/ares-sync.apk" > "$STAGE/teacher-app/APK_SIGNATURE.txt" \
      || die "apksigner rejected the approved APK"
  else
    log "WARNING: apksigner is not installed; SHA-256 protects exact-file identity, but signer identity is not independently checked"
    echo "apksigner was unavailable on the build machine. Exact-file integrity is protected by SHA-256, but signer identity was not independently verified." > "$STAGE/teacher-app/APK_SIGNATURE.txt"
  fi
  rm -rf "$APK_WORK"
  trap - EXIT

  CORPUS_WORK="$(mktemp -d)"
  trap 'rm -rf "$CORPUS_WORK"' EXIT
  log "downloading pinned Lesson3 JSON corpus commit $CORPUS_COMMIT"
  git -C "$CORPUS_WORK" init -q
  git -C "$CORPUS_WORK" remote add origin "$CORPUS_REPO"
  git -C "$CORPUS_WORK" fetch -q --depth 1 --filter=blob:none origin "$CORPUS_COMMIT"
  git -C "$CORPUS_WORK" checkout -q --detach FETCH_HEAD
  [[ "$(git -C "$CORPUS_WORK" rev-parse HEAD)" == "$CORPUS_COMMIT" ]] \
    || die "downloaded corpus commit does not match the approved pin"
  python3 "$SELF_DIR/tools/package_lesson3_corpus.py" \
    --source "$CORPUS_WORK/data/outputs/v2" \
    --output "$STAGE/lesson3/corpus" \
    --repo "$CORPUS_REPO" \
    --commit "$CORPUS_COMMIT" \
    --expected-files "$CORPUS_EXPECTED_FILES" \
    --expected-lessons "$CORPUS_EXPECTED_LESSONS"
  install -m 0755 "$SELF_DIR/templates/install_lesson3_corpus.sh" "$STAGE/lesson3/corpus/install_lesson3_corpus.sh"
  rm -rf "$CORPUS_WORK"
  trap - EXIT

  REMOTE_WORK="$(mktemp -d)"
  trap 'rm -rf "$REMOTE_WORK"' EXIT

  TAILSCALE_FILE="tailscale_${TAILSCALE_VERSION}_amd64.tgz"
  TAILSCALE_BASE="https://pkgs.tailscale.com/stable"
  log "downloading pinned Tailscale $TAILSCALE_VERSION static amd64 archive"
  curl -fL --retry 3 --connect-timeout 20 \
    -o "$REMOTE_WORK/$TAILSCALE_FILE" "$TAILSCALE_BASE/$TAILSCALE_FILE"
  curl -fL --retry 3 --connect-timeout 20 \
    -o "$REMOTE_WORK/$TAILSCALE_FILE.sha256" "$TAILSCALE_BASE/$TAILSCALE_FILE.sha256"
  expected_tailscale_sha="$(awk 'NR==1 {print $1}' "$REMOTE_WORK/$TAILSCALE_FILE.sha256")"
  [[ "$expected_tailscale_sha" =~ ^[0-9a-fA-F]{64}$ ]] || die "invalid Tailscale checksum response"
  actual_tailscale_sha="$(sha256sum "$REMOTE_WORK/$TAILSCALE_FILE" | awk '{print $1}')"
  [[ "${actual_tailscale_sha,,}" == "${expected_tailscale_sha,,}" ]] \
    || die "Tailscale archive checksum mismatch"
  # Do not use grep -q here. With pipefail enabled, grep exits after the first
  # match, tar receives SIGPIPE, and the valid archive is reported as missing.
  tar -tzf "$REMOTE_WORK/$TAILSCALE_FILE" | grep -E '(^|/)tailscale$' >/dev/null \
    || die "Tailscale archive does not contain the tailscale client"
  tar -tzf "$REMOTE_WORK/$TAILSCALE_FILE" | grep -E '(^|/)tailscaled$' >/dev/null \
    || die "Tailscale archive does not contain the tailscaled daemon"
  install -m 0644 "$REMOTE_WORK/$TAILSCALE_FILE" "$STAGE/remote-access/tailscale/$TAILSCALE_FILE"
  (cd "$STAGE/remote-access/tailscale" && sha256sum "$TAILSCALE_FILE" > SHA256SUMS)
  cat > "$STAGE/remote-access/tailscale/INFO.txt" <<TXT
Source: $TAILSCALE_BASE/$TAILSCALE_FILE
Version: $TAILSCALE_VERSION
Architecture: amd64
Official published SHA-256: ${expected_tailscale_sha,,}
Bundled SHA-256: ${actual_tailscale_sha,,}
Installed state: disabled, stopped, and unregistered
TXT

  log "downloading pinned Ubuntu 24.04 TigerVNC packages"
  mkdir -p "$REMOTE_WORK/tigervnc"
  (
    cd "$REMOTE_WORK/tigervnc"
    apt-get download \
      "libfile-readbackwards-perl=$FILE_READBACKWARDS_VERSION" \
      "tigervnc-common=$TIGERVNC_VERSION" \
      "tigervnc-tools=$TIGERVNC_VERSION" \
      "tigervnc-standalone-server=$TIGERVNC_VERSION"
  )
  mapfile -t downloaded_debs < <(find "$REMOTE_WORK/tigervnc" -maxdepth 1 -type f -name '*.deb' -print | sort)
  ((${#downloaded_debs[@]} == 4)) || die "expected four TigerVNC-related Debian packages"
  declare -A expected_deb_versions=(
    [libfile-readbackwards-perl]="$FILE_READBACKWARDS_VERSION"
    [tigervnc-common]="$TIGERVNC_VERSION"
    [tigervnc-tools]="$TIGERVNC_VERSION"
    [tigervnc-standalone-server]="$TIGERVNC_VERSION"
  )
  for deb in "${downloaded_debs[@]}"; do
    package_name="$(dpkg-deb -f "$deb" Package)"
    package_version="$(dpkg-deb -f "$deb" Version)"
    package_arch="$(dpkg-deb -f "$deb" Architecture)"
    [[ -n "${expected_deb_versions[$package_name]+x}" ]] \
      || die "unexpected Debian package downloaded: $package_name"
    [[ "$package_version" == "${expected_deb_versions[$package_name]}" ]] \
      || die "wrong version for $package_name: $package_version"
    [[ "$package_arch" == "amd64" || "$package_arch" == "all" ]] \
      || die "wrong architecture for $package_name: $package_arch"
    install -m 0644 "$deb" "$STAGE/remote-access/tigervnc/$(basename "$deb")"
  done
  (cd "$STAGE/remote-access/tigervnc" && sha256sum ./*.deb > SHA256SUMS)
  cat > "$STAGE/remote-access/tigervnc/INFO.txt" <<TXT
Source: Ubuntu 24.04 (Noble) repositories
TigerVNC version: $TIGERVNC_VERSION
Architecture: amd64/all
Desktop session: Cinnamon 2D, with Openbox available as manual fallback
Installed state: disabled and stopped; localhost-only when later activated
TXT

  rm -rf "$REMOTE_WORK"
  trap - EXIT

  RELEASE_BASE="https://github.com/james-beep-boop/Lesson3/releases/download/$LESSON3_VERSION"
  RELEASE_DIR="$STAGE/lesson3/release"
  IMAGE_DIR="$STAGE/lesson3/images"
  BUNDLE="lesson3-online-deploy.tar.gz"
  CHECKSUM="$BUNDLE.sha256"

  log "downloading pinned Lesson3 $LESSON3_VERSION release"
  curl -fL --retry 3 --connect-timeout 20 -o "$RELEASE_DIR/$BUNDLE" "$RELEASE_BASE/$BUNDLE"
  curl -fL --retry 3 --connect-timeout 20 -o "$RELEASE_DIR/$CHECKSUM" "$RELEASE_BASE/$CHECKSUM"
  (cd "$RELEASE_DIR" && sha256sum -c "$CHECKSUM")

  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  tar -xzf "$RELEASE_DIR/$BUNDLE" -C "$TMP"
  [[ -f "$TMP/lesson3-deploy/compose.yaml" ]] || die "Lesson3 release is missing compose.yaml"
  [[ -f "$TMP/lesson3-deploy/VERSION" ]] || die "Lesson3 release is missing VERSION"
  [[ "$(cat "$TMP/lesson3-deploy/VERSION")" == "$LESSON3_VERSION" ]] \
    || die "Lesson3 release VERSION does not match requested $LESSON3_VERSION"

  mapfile -t EXACT_IMAGES < <(awk '$1=="image:" {gsub(/"/,"",$2); print $2}' "$TMP/lesson3-deploy/compose.yaml")
  ((${#EXACT_IMAGES[@]} >= 4)) || die "could not discover expected Lesson3 container images"

  SAVE_IMAGES=()
  : > "$IMAGE_DIR/IMAGE_REFS.txt"
  for image in "${EXACT_IMAGES[@]}"; do
    save_ref="${image%@*}"
    log "pulling $image for $PLATFORM"
    docker pull --platform "$PLATFORM" "$image"

    # Digest-pinned pulls do not reliably create the corresponding :tag
    # locally. The offline compose file deliberately strips @sha256 suffixes,
    # so explicitly create and save the tag that compose.offline.yaml will use.
    image_id="$(docker image inspect --format '{{.Id}}' "$image")"
    [[ -n "$image_id" ]] || die "could not resolve pulled image: $image"
    docker tag "$image_id" "$save_ref"
    docker image inspect "$save_ref" >/dev/null 2>&1 \
      || die "failed to create local save tag: $save_ref"

    SAVE_IMAGES+=("$save_ref")
    printf '%s\t%s\t%s\n' "$image" "$save_ref" "$image_id" >> "$IMAGE_DIR/IMAGE_REFS.txt"
  done

  ARCHIVE="$IMAGE_DIR/lesson3-${LESSON3_VERSION}-amd64-images.tar.gz"
  log "saving Lesson3 container images to $(basename "$ARCHIVE")"
  docker save "${SAVE_IMAGES[@]}" | gzip -1 > "$ARCHIVE"
  [[ -s "$ARCHIVE" ]] || die "Docker image archive was not created"
  rm -rf "$TMP"
  trap - EXIT
fi

# Verify expected non-Lesson3 payload before signing the package.
for required in \
  lesson_plan/payload/index.htmlf \
  lesson_plan/payload/index.html \
  lesson_plan/payload/index_bu.htmlf \
  lesson_plan/payload/ARES-Logo.png \
  lesson_plan/payload/PDF/index.html \
  lesson_plan/payload/generate_teacher_index.js \
  ARES_Sync_Rollout_Package/server-installer/update_school_server.sh \
  ARES_Sync_Rollout_Package/server-installer/ares_set_school_code.sh \
  teacher-app/install_teacher_app.sh \
  teacher-app/install-page.html \
  remote-access/prepare_remote_access.sh \
  remote-access/ares_enable_remote_access.sh \
  remote-access/ares_disable_remote_access.sh \
  docs/TECHNICIAN_PHONE_INSTALL.md \
  docs/TEACHER_PHONE_GUIDE.md \
  docs/LESSON3_CORPUS_INSTALL.md \
  docs/REMOTE_ACCESS.md \
  docs/pdf/ARES_Sync_Technician_Guide.pdf \
  docs/pdf/ARES_Sync_Teacher_Guide.pdf \
  docs/LESSON3_USER_GUIDE.pdf \
  lesson_plan/payload/LESSON3_USER_GUIDE.pdf; do
    [[ -f "$STAGE/$required" ]] || die "required source payload is missing: $required"
done

if (( ! SCAFFOLD_ONLY )); then
  [[ -f "$STAGE/teacher-app/ares-sync.apk" ]] || die "field APK missing from bundle"
  [[ -f "$STAGE/teacher-app/ares-sync.apk.sha256" ]] || die "field APK checksum missing from bundle"
  [[ -f "$STAGE/lesson3/corpus/MANIFEST.json" ]] || die "Lesson3 corpus manifest missing from bundle"
  [[ -f "$STAGE/lesson3/corpus/taxonomy.tsv" ]] || die "Lesson3 corpus taxonomy missing from bundle"
  [[ -f "$STAGE/lesson3/corpus/SHA256SUMS" ]] || die "Lesson3 corpus checksums missing from bundle"
  [[ -f "$STAGE/remote-access/tailscale/SHA256SUMS" ]] || die "Tailscale payload checksum missing from bundle"
  [[ -f "$STAGE/remote-access/tigervnc/SHA256SUMS" ]] || die "TigerVNC payload checksums missing from bundle"
  [[ "$(find "$STAGE/remote-access/tigervnc" -maxdepth 1 -type f -name '*.deb' | wc -l)" -eq 4 ]] \
    || die "TigerVNC offline package set has the wrong file count"
  [[ "$(find "$STAGE/lesson3/corpus/files" -maxdepth 1 -type f -name '*_data.json' | wc -l)" -eq "$CORPUS_EXPECTED_FILES" ]] \
    || die "Lesson3 corpus field package has the wrong file count"
fi

# Field-side shell scripts must not install/download from the Internet.
if grep -RInE 'github\.com|tailscale\.com|apt-get[[:space:]]+(update|install)|docker([[:space:]]+compose)?[[:space:]]+pull|wget[[:space:]]' \
    "$STAGE" --include='*.sh' > "$STAGE/.offline-audit.txt"; then
  cat "$STAGE/.offline-audit.txt" >&2
  die "offline audit found Internet-dependent commands in field-side shell scripts"
fi
rm -f "$STAGE/.offline-audit.txt"

cat > "$STAGE/MANIFEST.txt" <<TXT
ARES Q4 Offline Bundle
Built: $(date -Is)
Lesson3: $LESSON3_VERSION
Lesson3 corpus repository: $CORPUS_REPO
Lesson3 corpus commit: $CORPUS_COMMIT
Lesson3 corpus: $CORPUS_EXPECTED_FILES plans / $CORPUS_EXPECTED_LESSONS lessons
Target architecture: linux/amd64
Offline bundle revision: $BUNDLE_REVISION
Teacher APK: bundled approved production APK with SHA-256 verification
Teacher install URL after deployment: http://ares.local/app_install/
Lesson3 User Guide after deployment: http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf
Remote access: Tailscale $TAILSCALE_VERSION and TigerVNC $TIGERVNC_VERSION installed dormant
Source directory: $SOURCE
Field command: sudo bash install_offline.sh ARES-S00XX
Lesson3 corpus: guided installation within install_offline.sh after first Site Administrator creation
Later remote-access activation: sudo ares-enable-remote-access
Tsavo Trust module: not included; use the separately reviewed Tsavo installer
TXT

log "generating SHA256SUMS"
(
  cd "$STAGE"
  find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
)

log "syntax-checking shell scripts"
while IFS= read -r -d '' f; do bash -n "$f" || die "shell syntax failed: $f"; done < <(find "$STAGE" -type f -name '*.sh' -print0)

log "creating $ZIPFILE"
python3 - "$STAGE" "$ZIPFILE" "$OUTPUT" <<'PYZIP'
from pathlib import Path
import sys, zipfile
stage = Path(sys.argv[1])
out = Path(sys.argv[2])
base = stage.parent
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as z:
    for p in sorted(stage.rglob('*')):
        if p.is_file():
            z.write(p, p.relative_to(base))
PYZIP
log "complete: $ZIPFILE"
if (( SCAFFOLD_ONLY )); then log "NOTE: scaffold-only output is not field-ready"; fi
