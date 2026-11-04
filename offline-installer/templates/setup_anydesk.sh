#!/usr/bin/env bash
# Personalize a cloned, already-installed AnyDesk client; never download it.
set -Eeuo pipefail
set +x
umask 077
[[ ${EUID} == 0 ]] || { echo 'Run AnyDesk setup with sudo.' >&2; exit 1; }
STATE=/var/lib/ares/anydesk-setup
CONFIG=/etc/anydesk
ACTION=setup
case "${1:-}" in
  --show-id) ACTION=show; shift ;;
  --reset) ACTION=reset; shift ;;
esac
SCHOOL=${1:-}
for command in anydesk systemctl timeout flock pkill getent; do
  command -v "$command" >/dev/null || { echo "AnyDesk setup deferred: missing $command; no download attempted."; exit 2; }
done
install -d -m 0700 "$STATE"
exec 9>"$STATE/setup.lock"
flock -n 9 || { echo 'Another AnyDesk setup is running.'; exit 2; }
get_id() {
  local value
  value=$(timeout 5 anydesk --get-id 9>&- 2>/dev/null | tr -d '[:space:]') || value=''
  [[ "$value" =~ ^[0-9]{9,10}$ ]] || return 1
  printf '%s' "$value"
}
report_id() {
  local value old=''
  [[ ! -f "$STATE/previous-id" ]] || old=$(cat "$STATE/previous-id")
  if value=$(get_id) && [[ -f "$STATE/reset-done" && "$value" != "$old" ]]; then
    printf '%s\n' "$value" > "$STATE/anydesk-id.txt"
    printf 'AnyDesk ID: %s\nSave this ID with the school record.\n' "$value"
    echo "Saved locally: $STATE/anydesk-id.txt"
    if [[ ! -f "$STATE/password-set" ]]; then
      echo 'Unattended password setup is still pending; rerun ares-setup-anydesk with the school code.'
    fi
    return 0
  fi
  echo 'New AnyDesk ID is Pending; no new ID has been verified yet.'
  echo 'When AnyDesk is connected and ready, run: sudo ares-show-anydesk-id'
  return 2
}
if [[ "$ACTION" == show ]]; then report_id; exit $?; fi
[[ "$SCHOOL" =~ ^[A-Z0-9_-]+$ ]] || { echo 'Usage: sudo ares-setup-anydesk [--reset] ARES-S00XX'; exit 2; }
if { command -v nft >/dev/null && nft list table inet ares_internet_lockdown >/dev/null 2>&1; } \
    || systemctl is-enabled --quiet ares-internet-lockdown.service 2>/dev/null; then
  echo 'AnyDesk setup deferred: active/boot lockdown may depend on the existing AnyDesk service.'
  echo 'Arrange local access and restore/disable lockdown before resetting AnyDesk.'
  exit 2
fi
if [[ -f "$STATE/school-code" && "$(cat "$STATE/school-code")" != "$SCHOOL" ]]; then
  echo 'This server has an AnyDesk setup record for a different school. Use --reset to personalize it again.'
  [[ "$ACTION" == reset ]] || exit 2
fi
if [[ -f "$STATE/reset-done" && -f "$STATE/password-set" && "$ACTION" != reset ]]; then
  echo 'AnyDesk was already personalized; preserving its identity and password.'
  report_id
  exit $?
fi
[[ -t 0 ]] || { echo "AnyDesk setup deferred. Later, run: sudo ares-setup-anydesk $SCHOOL"; exit 2; }
reset=no
if [[ ! -f "$STATE/reset-done" || "$ACTION" == reset ]]; then
  echo 'This resets the cloned AnyDesk identity and disconnects existing AnyDesk sessions.'
  echo 'Use the local console or another independent connection. Old settings will be backed up.'
  read -r -p 'Type RESET to prepare this school, or press Enter to defer: ' answer || answer=''
  [[ "$answer" == RESET ]] || { echo 'AnyDesk setup deferred; identity unchanged.'; exit 2; }
  reset=yes
fi
read -r -s -p 'Enter the standard ARES unattended-access password (8+ characters): ' password || password=''
printf '\n'
read -r -s -p 'Enter it again: ' confirmation || confirmation=''
printf '\n'
[[ ${#password} -ge 8 && "$password" == "$confirmation" ]] || {
  unset password confirmation
  echo 'Passwords did not match or were shorter than 8 characters; no identity reset performed.'
  exit 2
}
unset confirmation
stopped=no
restart_on_error() {
  local rc=$?
  unset password
  if [[ "$stopped" == yes ]]; then systemctl start anydesk.service || true; fi
  exit "$rc"
}
trap restart_on_error EXIT
if [[ "$reset" == yes ]]; then
  old=$(get_id) || old=''
  backup="$STATE/backup-$(date +%Y%m%d-%H%M%S)-$$"
  install -d -m 0700 "$backup"
  [[ ! -L "$CONFIG" ]] || { echo 'AnyDesk configuration is a symlink; review before resetting.'; exit 2; }
  user_config=''
  desktop_user=${SUDO_USER:-ares}
  if [[ "$desktop_user" != root ]]; then
    desktop_home=$(getent passwd "$desktop_user" | cut -d: -f6) || desktop_home=''
    [[ -n "$desktop_home" && "$desktop_home" != / ]] || { echo 'Desktop user home not found; identity unchanged.'; exit 2; }
    user_config="$desktop_home/.anydesk"
    [[ ! -L "$user_config" ]] || { echo 'User AnyDesk configuration is a symlink; identity unchanged.'; exit 2; }
  fi
  systemctl stop anydesk.service
  stopped=yes
  # Close remaining GUI clients so they cannot restore a cloned configuration.
  pkill -x anydesk || [[ $? == 1 ]]
  if [[ -e "$CONFIG" ]]; then mv -- "$CONFIG" "$backup/system"; fi
  # Installed Linux clients may also retain per-user configuration.
  if [[ -n "$user_config" && -e "$user_config" ]]; then mv -- "$user_config" "$backup/user"; fi
  printf '%s\n' "$old" > "$STATE/previous-id"
  printf '%s\n' "$SCHOOL" > "$STATE/school-code"
  rm -f -- "$STATE/password-set" "$STATE/anydesk-id.txt"
  touch "$STATE/reset-done"
  echo "Cloned configuration archived at $backup (includes system.conf and service.conf)."
fi
systemctl enable --now anydesk.service
stopped=no
if ! printf '%s\n' "$password" | timeout 20 anydesk --set-password 9>&- >/dev/null 2>&1; then
  unset password
  echo "AnyDesk is reset; unattended password is Pending. Rerun: sudo ares-setup-anydesk $SCHOOL"
  exit 2
fi
unset password
touch "$STATE/password-set"
echo 'Unattended-access password configured. The password was not saved in the installer or log.'
for attempt in {1..6}; do
  if report_id >/dev/null; then report_id; exit 0; fi
  sleep 2
done
report_id || true
echo 'Identity reset is retained. A later retry will not reset it again.'
exit 2
