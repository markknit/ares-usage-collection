#!/usr/bin/env bash
# Fully offline Lesson3 installer for the ARES field bundle.
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LESSON3_VERSION="${LESSON3_VERSION:-v0.94}"
LESSON3_URL="${LESSON3_URL:-http://ares.local:3001}"
BASE_DIR="${LESSON3_BASE_DIR:-/mnt/sda3/var/www/lesson3-download}"
INSTALL_DIR="$BASE_DIR/lesson3-deploy"
RELEASE_DIR="$SCRIPT_DIR/release"
IMAGE_DIR="$SCRIPT_DIR/images"
BUNDLE="$RELEASE_DIR/lesson3-online-deploy.tar.gz"
CHECKSUM="$RELEASE_DIR/lesson3-online-deploy.tar.gz.sha256"
IMAGE_ARCHIVE="$IMAGE_DIR/lesson3-${LESSON3_VERSION}-amd64-images.tar.gz"
PG_VOLUME="lesson3_lesson3_pgdata"
ARTIFACT_VOLUME="lesson3_lesson3_artifact_cache"

log() { printf 'lesson3-offline: %s\n' "$*"; }
die() { printf 'lesson3-offline: ERROR: %s\n' "$*" >&2; exit 1; }

[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"
for cmd in sha256sum tar openssl docker curl sed; do
    command -v "$cmd" >/dev/null 2>&1 || die "required command '$cmd' was not found"
done
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required"

[[ -f "$BUNDLE" ]] || die "offline release bundle is missing: $BUNDLE"
[[ -f "$CHECKSUM" ]] || die "release checksum is missing: $CHECKSUM"
[[ -f "$IMAGE_ARCHIVE" ]] || die "offline Docker image archive is missing: $IMAGE_ARCHIVE"

mkdir -p "$BASE_DIR"

# A healthy existing installation is left alone. An unhealthy one must be
# diagnosed explicitly rather than overwritten with newly generated secrets.
if [[ -f "$INSTALL_DIR/.env" && -f "$INSTALL_DIR/compose.yaml" ]]; then
    log "existing Lesson3 deployment found at $INSTALL_DIR"
    if curl -fsS --max-time 5 http://127.0.0.1:3001/login >/dev/null 2>&1; then
        log "existing Lesson3 is healthy; no fresh install is needed"
        exit 0
    fi
    die "existing Lesson3 deployment is not healthy; repair it or remove it explicitly if disposable"
fi

if docker volume inspect "$PG_VOLUME" >/dev/null 2>&1; then
    die "orphaned Lesson3 Postgres volume exists without matching $INSTALL_DIR/.env; remove it only if its data is disposable"
fi

log "verifying bundled Lesson3 release"
(
    cd "$RELEASE_DIR"
    sha256sum -c "$(basename "$CHECKSUM")"
)

log "loading bundled Docker images (no network access)"
docker load -i "$IMAGE_ARCHIVE"

workdir="$(mktemp -d "$BASE_DIR/.lesson3-offline.XXXXXX")"
cleanup() { rm -rf "$workdir"; }
trap cleanup EXIT

tar -xzf "$BUNDLE" -C "$workdir"
[[ -d "$workdir/lesson3-deploy" ]] || die "release archive did not contain lesson3-deploy/"
[[ -f "$workdir/lesson3-deploy/VERSION" ]] || die "release archive is missing VERSION"
[[ "$(cat "$workdir/lesson3-deploy/VERSION")" == "$LESSON3_VERSION" ]] \
    || die "release VERSION does not match expected $LESSON3_VERSION"

rm -rf "$INSTALL_DIR"
cp -a "$workdir/lesson3-deploy" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# The upstream checked release pins images by tag+digest. docker save/load
# reliably restores tags, while digest aliases are not guaranteed to survive
# an offline archive round-trip. The bundle itself is checksummed, so for the
# offline copy we strip only the @sha256 suffixes and run with --pull never.
sed -E 's#(@sha256:[0-9a-f]{64})##g' compose.yaml > compose.offline.yaml

on_error() {
    rc=$?
    printf '\nlesson3-offline: installation failed (exit %s)\n' "$rc" >&2
    docker compose -f compose.offline.yaml ps >&2 || true
    printf '\n--- migrate log ---\n' >&2
    docker compose -f compose.offline.yaml logs migrate --tail 120 >&2 || true
    printf '\n--- postgres log ---\n' >&2
    docker compose -f compose.offline.yaml logs postgres --tail 80 >&2 || true
    exit "$rc"
}
trap on_error ERR

log "preparing configuration with ADMIN_URL=$LESSON3_URL"
LESSON3_URL="$LESSON3_URL" ./install.sh --prepare-only

log "starting Lesson3 from locally loaded images"
docker compose -f compose.offline.yaml up -d --no-build --pull never

for _ in $(seq 1 60); do
    if curl -fsS --max-time 5 http://127.0.0.1:3001/login >/dev/null 2>&1; then
        trap - ERR
        log "Lesson3 $LESSON3_VERSION is ready"
        log "teacher URL: ${LESSON3_URL%/}/login"
        exit 0
    fi
    sleep 5
done

die "Lesson3 did not become ready within five minutes"
