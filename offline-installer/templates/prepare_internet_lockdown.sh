#!/usr/bin/env bash
# Install the bundled tools without activating rules or enabling boot lockdown.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$SCRIPT_DIR/internet-lockdown"
VERSION=ares-lockdown-v1.4.2
DESTINATION="${ARES_LOCKDOWN_HOME:-/opt/ares/internet-lockdown}"
RELEASE="$PROJECT/$VERSION"
log() { printf 'internet-lockdown: %s\n' "$*"; }
[[ ${EUID:-$(id -u)} -eq 0 ]] || { log 'run as root'; exit 1; }

# Keep the upstream release and manifest unchanged, including its operating PDF.
(cd "$RELEASE" && sha256sum -c SHA256SUMS)
install -d -m 0755 "$DESTINATION/$VERSION"
install -m 0644 "$PROJECT/STATUS.md" "$DESTINATION/STATUS.md"
for source in "$RELEASE"/*; do
  install -m 0644 "$source" "$DESTINATION/$VERSION/$(basename "$source")"
done
log "v1.4.2 project and manual available at $DESTINATION/$VERSION"
log "Later setup: sudo bash $DESTINATION/$VERSION/install.sh --no-boot"

for command in nft systemctl ip python3 install cmp date; do
  if ! command -v "$command" >/dev/null 2>&1; then
    log "Setup deferred: missing $command; bundled files remain available."
    exit 2
  fi
done
if nft list table inet ares_internet_lockdown >/dev/null 2>&1; then
  log 'Existing lockdown is active; preserving its rules, commands and configuration.'
  log 'The new project is retained for a separately arranged upgrade.'
  exit 2
fi
if systemctl is-enabled --quiet ares-internet-lockdown.service 2>/dev/null; then
  log 'Existing reboot lockdown is enabled; preserving its service and configuration.'
  exit 2
fi
if [[ ! -t 0 ]]; then
  log 'Setup deferred: an interactive terminal is needed to confirm the student LAN.'
  exit 2
fi

# The supplied installer detects/reuses the actual LAN. It performs only a
# --check of generated rules, and --no-boot suppresses persistence opt-in.
# Run it as a separate shell so its own error handling remains effective.
bash "$DESTINATION/$VERSION/install.sh" --no-boot
log 'Tool installation finished; no firewall was activated or boot service enabled.'
