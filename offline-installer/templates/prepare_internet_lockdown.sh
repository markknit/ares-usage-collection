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
log "LAN selection will happen on the first lockdown-internet run after connection."

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
# Install commands now, even with no active adapter and no terminal. Keep the
# supplied rule engine unchanged; defer only LAN selection to first activation.
install -d -m 0755 /usr/local/sbin /usr/local/bin /usr/local/lib/ares
for script in lockdown_internet.sh restore_internet.sh ares_anydesk_diagnose.sh; do
  install -m 0700 "$RELEASE/$script" "/usr/local/sbin/$script"
done
install -m 0644 "$SCRIPT_DIR/configure_lockdown.py" /usr/local/lib/ares/configure_lockdown.py
install -m 0700 "$SCRIPT_DIR/lockdown_dispatch.sh" /usr/local/sbin/ares_lockdown_dispatch.sh

command_wrapper() {
  local name=$1 target=$2 extra=${3:-} dest="/usr/local/bin/$1"
  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ -L "$dest" ]]; then
      case "$(readlink -f "$dest")" in
        /usr/local/sbin/lockdown_internet.sh|/usr/local/sbin/restore_internet.sh|/usr/local/sbin/ares_anydesk_diagnose.sh) ;;
        *) log "Conflicting command $dest; preserving it."; return 1 ;;
      esac
    elif ! grep -Eq '/usr/local/sbin/(ares_lockdown_dispatch|lockdown_internet|restore_internet|ares_anydesk_diagnose)[.]sh' "$dest"; then
      log "Conflicting command $dest; preserving it."
      return 1
    fi
    cp -a -- "$dest" "$dest.bak.$(date +%Y%m%d-%H%M%S)-$$"
    rm -f -- "$dest"
  fi
  printf '#!/usr/bin/env bash\nif (( EUID == 0 )); then exec %s %s "$@"; fi\nexec sudo %s %s "$@"\n' \
    "$target" "$extra" "$target" "$extra" > "$dest"
  chmod 0755 "$dest"
}
for name in lockdown-internet lockdown_internet; do
  command_wrapper "$name" /usr/local/sbin/ares_lockdown_dispatch.sh
done
for name in restore-internet restore_internet; do
  command_wrapper "$name" /usr/local/sbin/restore_internet.sh
done
command_wrapper ares-configure-lockdown /usr/local/sbin/ares_lockdown_dispatch.sh --configure
command_wrapper ares-anydesk-diagnose /usr/local/sbin/ares_anydesk_diagnose.sh
log 'Commands installed; no adapter or Internet connection is required for installation.'
log 'When connected: lockdown-internet (select the student LAN on first use).'
log 'Restore anytime: restore-internet. Reselect LAN later: ares-configure-lockdown.'
log 'No firewall was activated and no boot service was enabled.'
