#!/usr/bin/env bash
# Canonical Ubuntu 24.04 activation. Never roll back a working command-line path.
set +x
set -Eeuo pipefail
VNC_SERVICE='tigervncserver@:1.service'
CONFIG_TOOL=/usr/local/lib/ares/remote_support_config.py
COMMON_TOOL=/usr/local/lib/ares/remote_support_common.sh
STATE_DIR=/var/lib/ares/remote-support
VNC_USERS_FILE=/etc/tigervnc/vncserver.users
ENROLL_TIMEOUT_SECONDS=120
COMPLETE=0; STARTED=0; CLI_READY=0; VNC_PHASE=0; VNC_OWNED=0; SSH_TOUCHED=0; HOST_CHANGED=0

retry_instructions() { echo "Retry when ready: sudo ares-enable-remote-access"; }
die() { echo "ERROR: $*" >&2; exit 1; }

choose_remote_hostname() {
  local school_name candidate reply attempt
  for attempt in {1..3}; do
    printf 'School name for remote support [keep %s]: ' "$OLD_HOSTNAME" >&3
    if ! IFS= read -r -u 4 school_name; then
      echo 'Name entry cancelled; existing hostname and services retained.'
      return 3
    fi
    if [[ -z "${school_name//[[:space:]]/}" ]]; then
      candidate=$OLD_HOSTNAME
    elif ! candidate=$(python3 "$CONFIG_TOOL" hostname "$school_name" 2>/dev/null); then
      printf 'Use letters or numbers for the school name, or press Enter to keep %s.\n' "$OLD_HOSTNAME" >&3
      continue
    fi
    if [[ "$candidate" == "$OLD_HOSTNAME" ]]; then
      printf 'Keep Linux/Tailscale name %s? [Y/n]: ' "$candidate" >&3
      IFS= read -r -u 4 reply || return 3
      case "$reply" in ''|y|Y|yes|YES|Yes) ;; *) return 3 ;; esac
    else
      printf 'Change Linux/Tailscale name to %s? [y/N]: ' "$candidate" >&3
      IFS= read -r -u 4 reply || return 3
      case "$reply" in y|Y|yes|YES|Yes) ;; *) return 3 ;; esac
    fi
    SELECTED_HOSTNAME=$candidate
    return 0
  done
  echo 'No usable school name entered; activation deferred without changing the hostname.'
  return 3
}

verify_vnc_listeners() {
  local listener seen=0
  while IFS= read -r listener; do
    [[ -n "$listener" ]] || continue
    seen=1
    case "$listener" in
      127.0.0.1:5901|'[::1]:5901') ;;
      *) echo "Unsafe VNC listener: $listener" >&2; return 1 ;;
    esac
  done < <(ss -H -ltn | awk '$4 ~ /:5901$/ {print $4}')
  [[ $seen -eq 1 ]]
}

tailscale_connected() {
  timeout 10s tailscale status --json 2>/dev/null | python3 "$CONFIG_TOOL" connected
}

enroll_tailscale() {
  local new_hostname=$1 reply
  echo "The ARES server needs outbound Internet access for Tailscale enrollment and connectivity."
  echo "Open the authentication URL on a technician phone using cellular data; the phone need not be on the ARES network."
  if tailscale_connected; then
    echo "Tailscale is already enrolled and connected; reusing its identity."
    timeout 10s tailscale set --hostname="$new_hostname" --ssh=false || return 1
  else
    printf 'Begin or resume enrollment now (maximum %s seconds)? [y/N]: ' "$ENROLL_TIMEOUT_SECONDS" >&3
    IFS= read -r -u 4 reply || reply=N
    case "$reply" in y|Y|yes|YES|Yes) ;; *) echo "Tailscale enrollment deferred."; retry_instructions; return 3 ;; esac
    printf '\n=== Tailscale browser authorization: open the URL shown below ===\n' >&3
    # /dev/tty is independent of this script's tee AND any parent installer tee.
    # Neither an auth URL nor command output containing it is written to a file.
    if ! timeout --foreground --kill-after=5s "$((ENROLL_TIMEOUT_SECONDS + 5))s" \
        tailscale up --hostname="$new_hostname" --ssh=false --timeout="${ENROLL_TIMEOUT_SECONDS}s" >&3 2>&3; then
      echo "Tailscale enrollment did not finish (offline, timed out, or not approved)."
      retry_instructions
      return 3
    fi
  fi
  if ! tailscale_connected; then
    echo "Tailscale is not connected. Check outbound Internet and tailnet approval."
    retry_instructions
    return 3
  fi
  timeout 10s tailscale set --ssh=false
}

create_vnc_password() {
  set +x
  local destination=$1 password confirmation attempt
  echo "Use a unique 6-8 character TigerVNC password. TigerVNC uses only the first eight characters."
  for attempt in {1..3}; do
    printf 'Enter TigerVNC password: ' >&3
    IFS= read -r -s -u 4 password || { echo "Password entry cancelled." >&2; return 1; }
    printf '\nRe-enter TigerVNC password to confirm: ' >&3
    IFS= read -r -s -u 4 confirmation || { unset password; echo "Password confirmation cancelled." >&2; return 1; }
    printf '\n' >&3
    if [[ ${#password} -lt 6 || ${#password} -gt 8 || "$password" != "$confirmation" ]]; then
      unset password confirmation
      echo "Passwords must match and contain 6-8 characters (attempt $attempt of 3)." >&2
      continue
    fi
    # One input line generates exactly one normal-access record, never view-only.
    if ! printf '%s\n' "$password" | runuser -u ares -- env HOME="$TARGET_HOME" tigervncpasswd -f > "$WORK/passwd" 2>/dev/null; then
      unset password confirmation
      echo "ERROR: TigerVNC password generation failed." >&2
      return 1
    fi
    unset password confirmation
    [[ "$(stat -c %s "$WORK/passwd")" == 8 ]] || { echo "ERROR: invalid normal-access password record" >&2; return 1; }
    install -o ares -g ares -m 0600 "$WORK/passwd" "$destination"
    return $?
  done
  echo "ERROR: password retry limit reached; TigerVNC was not activated." >&2
  return 1
}

configure_vnc() {
  local vnc_dir="$TARGET_HOME/.vnc" file cmd
  python3 "$CONFIG_TOOL" display "$VNC_USERS_FILE" > "$WORK/users" || return 1
  VNC_OWNED=1
  for cmd in tigervncpasswd tigervncserver runuser stat journalctl tail dbus-run-session cinnamon-session-cinnamon2d; do
    command -v "$cmd" >/dev/null || { echo "ERROR: TigerVNC prerequisite missing: $cmd" >&2; return 1; }
  done
  systemctl cat tigervncserver@.service >/dev/null || { echo "ERROR: TigerVNC unit is missing" >&2; return 1; }
  [[ ! -L "$vnc_dir" ]] || { echo "ERROR: refusing a symlinked VNC configuration directory" >&2; return 1; }
  for file in passwd tigervnc.conf Xtigervnc-session; do
    [[ ! -L "$vnc_dir/$file" ]] || { echo "ERROR: refusing a symlinked VNC configuration file" >&2; return 1; }
  done
  if ! systemctl is-active --quiet "$VNC_SERVICE" && ss -H -ltn | awk '{print $4}' | grep -E ':5901$' >/dev/null; then
    echo "ERROR: port 5901 is occupied; not terminating its owner." >&2
    return 1
  fi
  install -d -o ares -g ares -m 0700 "$vnc_dir" || return 1
  if [[ ! -s "$vnc_dir/passwd" || "$(stat -c %s "$vnc_dir/passwd")" != 8 ]]; then
    create_vnc_password "$vnc_dir/passwd" || return 1
  else
    echo "Retaining the existing normal-access TigerVNC password."
  fi
  chown ares:ares "$vnc_dir/passwd" && chmod 0600 "$vnc_dir/passwd" || return 1
  cat > "$WORK/tigervnc.conf" <<'EOF'
$geometry = "1280x800";
$depth = "24";
$localhost = "yes";
$AlwaysShared = "yes";
$rfbport = "5901";
$vncStartup = "$ENV{HOME}/.vnc/Xtigervnc-session";
EOF
  cat > "$WORK/Xtigervnc-session" <<'EOF'
#!/bin/sh
unset SESSION_MANAGER DBUS_SESSION_BUS_ADDRESS WAYLAND_DISPLAY
export XDG_SESSION_TYPE=x11
exec dbus-run-session -- cinnamon-session-cinnamon2d
EOF
  install -o ares -g ares -m 0600 "$WORK/tigervnc.conf" "$vnc_dir/tigervnc.conf" || return 1
  install -o ares -g ares -m 0700 "$WORK/Xtigervnc-session" "$vnc_dir/Xtigervnc-session" || return 1
  install -d -m 0755 "$(dirname "$VNC_USERS_FILE")" || return 1
  install -o root -g root -m 0644 "$WORK/users" "$VNC_USERS_FILE"
}

start_vnc() {
  local attempt stable=0
  systemctl enable "$VNC_SERVICE" && systemctl restart "$VNC_SERVICE" || return 1
  for attempt in {1..20}; do
    if systemctl is-active --quiet "$VNC_SERVICE" && verify_vnc_listeners; then
      stable=$((stable + 1))
      (( stable < 3 )) || return 0
    else
      stable=0
    fi
    sleep 1
  done
  echo "ERROR: TigerVNC did not remain active with loopback-only port 5901." >&2
  return 1
}

vnc_diagnostics() {
  echo "TigerVNC diagnostics (before stopping its unit):"
  systemctl status --no-pager --full "$VNC_SERVICE" || true
  journalctl --no-pager -u "$VNC_SERVICE" -n 60 || true
  local file
  for file in "$TARGET_HOME"/.vnc/*:1.log "$TARGET_HOME"/.vnc/*:5901.log; do
    [[ -f "$file" && ! -L "$file" ]] || continue
    echo "Current VNC log: $file"
    runuser -u ares -- tail -n 80 -- "$file" || true
  done
}

print_ssh_instructions() {
  local address
  address="$(timeout 10s tailscale ip -4 2>/dev/null)" || address='<TAILSCALE-IP>'
  printf 'Standard OpenSSH: ssh ares@%s\n' "$address" >&3
  if (( COMPLETE )); then
    printf 'Tunnel: ssh -N -L 5901:127.0.0.1:5901 ares@%s\nConnect VNC to 127.0.0.1:5901.\n' "$address" >&3
  fi
}

cleanup() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if (( STARTED && ! COMPLETE )); then
    if (( VNC_PHASE )); then
      vnc_diagnostics
      if (( VNC_OWNED )); then
        systemctl disable --now "$VNC_SERVICE" || echo "ERROR: TigerVNC could not be disabled" >&2
      else
        echo "VNC display ownership is unresolved; the existing unit was left untouched." >&2
      fi
    fi
    if (( CLI_READY )); then
      rc=2
      echo "PARTIAL FAILURE: Tailscale and standard OpenSSH remain operational; ARES TigerVNC was not activated."
      print_ssh_instructions || true
    else
      if (( SSH_TOUCHED )); then restore_ssh_baseline "$STATE_DIR/ssh-before.conf" || echo "ERROR: SSH baseline restoration needs attention" >&2; fi
      if (( HOST_CHANGED )); then
        cp -a "$WORK/hosts" /etc/hosts || true
        hostnamectl set-hostname "$OLD_HOSTNAME" || true
        systemctl try-restart avahi-daemon.service || true
      fi
      # Leave Tailscale's daemon/identity intact even after enrollment failure.
      (( rc != 0 )) || rc=1
    fi
    retry_instructions
  fi
  [[ -z "${WORK:-}" ]] || rm -rf -- "$WORK"
  exit "$rc"
}

main() {
  [[ ${EUID:-$(id -u)} -eq 0 ]] || die "run sudo ares-enable-remote-access"
  [[ -t 0 ]] || die "interactive terminal required; retry: sudo ares-enable-remote-access"
  for cmd in python3 getent cut flock hostnamectl install systemctl tailscale timeout \
    ss awk mktemp cp mv chmod chown tee date sleep touch grep dirname; do
    command -v "$cmd" >/dev/null || die "required command missing: $cmd"
  done
  [[ -r "$CONFIG_TOOL" && -r "$COMMON_TOOL" ]] || die "remote-support helpers are missing"
  source "$COMMON_TOOL"
  TARGET_HOME="$(getent passwd ares | cut -d: -f6)"
  [[ -d "$TARGET_HOME" ]] || die "ares home is missing"
  for unit in tailscaled.service ssh.service; do
    systemctl cat "$unit" >/dev/null || die "$unit is missing"
  done
  install -d -m 0700 "$STATE_DIR"
  exec 9>"$STATE_DIR/lock"
  flock -n 9 || die "another remote-support operation is running"
  # The controlling terminal avoids both our log and a parent installer's log.
  exec 3>/dev/tty 4</dev/tty
  local log_file="$STATE_DIR/activation-$(date +%Y%m%d_%H%M%S).log"
  touch "$log_file"; chmod 0600 "$log_file"
  exec > >(python3 -u "$CONFIG_TOOL" redact | tee -a "$log_file") 2>&1
  WORK="$(mktemp -d "$STATE_DIR/work.XXXXXX")"
  trap cleanup EXIT
  trap 'exit 130' HUP INT TERM
  OLD_HOSTNAME="$(hostnamectl --static)"
  local new_hostname
  choose_remote_hostname || { retry_instructions; exit 3; }
  new_hostname=$SELECTED_HOSTNAME
  capture_ssh_baseline "$STATE_DIR/ssh-before.conf"
  STARTED=1
  cp -a /etc/hosts "$WORK/hosts"
  if [[ "$OLD_HOSTNAME" != "$new_hostname" ]]; then
    python3 "$CONFIG_TOOL" hosts /etc/hosts "$OLD_HOSTNAME" "$new_hostname" > "$WORK/hosts.new"
    HOST_CHANGED=1
    hostnamectl set-hostname "$new_hostname"
    install -o root -g root -m 0644 "$WORK/hosts.new" /etc/hosts
    systemctl try-restart avahi-daemon.service
  fi
  systemctl enable --now tailscaled.service
  enroll_tailscale "$new_hostname" || exit $?
  SSH_TOUCHED=1
  ensure_ssh || die "standard OpenSSH could not be started"
  CLI_READY=1
  echo "Tailscale and standard OpenSSH are operational; Tailscale SSH is disabled."
  VNC_PHASE=1
  configure_vnc || die "TigerVNC configuration failed"
  start_vnc || die "TigerVNC startup/localhost verification failed"
  COMPLETE=1
  echo "Remote support active; actual client SSH/VNC and desktop acceptance remain Pending."
  print_ssh_instructions
  echo "Disable with sudo ares-disable-remote-access."
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then main "$@"; fi
