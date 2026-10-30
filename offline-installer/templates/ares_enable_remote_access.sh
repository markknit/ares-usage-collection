#!/usr/bin/env bash
# Canonical Ubuntu 24.04 activation command. No mDNS alias is changed here.
set -Eeuo pipefail
VNC_SERVICE='tigervncserver@:1.service'
CONFIG_TOOL=/usr/local/lib/ares/remote_support_config.py
STATE_DIR=/var/lib/ares/remote-support
COMPLETE=0
STARTED=0
HOST_CHANGED=0
die() { echo "ERROR: $*" >&2; exit 1; }

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

restore_ssh() {
  [[ "$SSH_WAS_ACTIVE" == yes ]] || systemctl stop ssh.service || return 1
  [[ "$SSH_WAS_ENABLED" == yes ]] || systemctl disable ssh.service || return 1
}

cleanup() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if (( STARTED && ! COMPLETE )); then
    echo "Activation failed; stopping remote services." >&2
    systemctl disable --now "$VNC_SERVICE" tailscaled.service || echo "ERROR: service cleanup failed" >&2
    restore_ssh || echo "ERROR: OpenSSH state restoration failed" >&2
    if (( HOST_CHANGED )); then
      cp -a "$WORK/hosts" /etc/hosts || true
      hostnamectl set-hostname "$OLD_HOSTNAME" || true
      systemctl try-restart avahi-daemon.service || true
    fi
    if systemctl is-active --quiet "$VNC_SERVICE" || systemctl is-active --quiet tailscaled.service; then
      echo "ERROR: remote service remains active; manual cleanup required" >&2
    fi
    (( rc != 0 )) || rc=1
  fi
  [[ -z "${WORK:-}" ]] || rm -rf -- "$WORK"
  exit "$rc"
}

main() {
  [[ ${EUID:-$(id -u)} -eq 0 ]] || die "run sudo ares-enable-remote-access"
  [[ -t 0 ]] || die "interactive terminal required"
  for cmd in python3 getent cut flock hostnamectl install runuser systemctl tailscale \
    tigervncpasswd ss awk pgrep mktemp cp chmod chown tee date sleep touch grep; do
    command -v "$cmd" >/dev/null || die "required command missing: $cmd"
  done
  [[ -r "$CONFIG_TOOL" ]] || die "remote-support configuration helper is missing"
  TARGET_HOME="$(getent passwd ares | cut -d: -f6)"
  [[ -d "$TARGET_HOME" ]] || die "ares home is missing"
  [[ -f /usr/share/xsessions/cinnamon2d.desktop ]] || die "Cinnamon 2D is missing"
  for unit in tailscaled.service tigervncserver@.service ssh.service; do
    systemctl cat "$unit" >/dev/null || die "$unit is missing"
  done
  install -d -m 0700 "$STATE_DIR"
  exec 9>"$STATE_DIR/lock"
  flock -n 9 || die "another activation is running"
  local log_file="$STATE_DIR/activation-$(date +%Y%m%d_%H%M%S).log"
  touch "$log_file"; chmod 0600 "$log_file"
  exec > >(tee -a "$log_file") 2>&1
  WORK="$(mktemp -d "$STATE_DIR/work.XXXXXX")"
  trap cleanup EXIT
  trap 'exit 130' HUP INT TERM
  python3 "$CONFIG_TOOL" display /etc/tigervnc/vncserver.users > "$WORK/users"
  if ! systemctl is-active --quiet "$VNC_SERVICE" && ss -H -ltn | awk '{print $4}' | grep -E ':5901$' >/dev/null; then
    die "port 5901 is occupied; resolve the conflict first"
  fi
  OLD_HOSTNAME="$(hostnamectl --static)"
  local school_name reply new_hostname
  read -r -p "Full school name: " school_name
  new_hostname="$(python3 "$CONFIG_TOOL" hostname "$school_name")"
  read -r -p "Use $new_hostname as Linux and Tailscale hostname? [y/N]: " reply
  case "$reply" in y|Y|yes|YES|Yes) ;; *) die "hostname not confirmed; no services changed" ;; esac
  SSH_WAS_ACTIVE=no; SSH_WAS_ENABLED=no
  systemctl is-active --quiet ssh.service && SSH_WAS_ACTIVE=yes
  systemctl is-enabled --quiet ssh.service && SSH_WAS_ENABLED=yes
  if [[ ! -f "$STATE_DIR/ssh-before.conf" ]]; then
    printf 'SSH_WAS_ACTIVE=%s\nSSH_WAS_ENABLED=%s\n' "$SSH_WAS_ACTIVE" "$SSH_WAS_ENABLED" > "$STATE_DIR/ssh-before.conf"
    chmod 0600 "$STATE_DIR/ssh-before.conf"
  fi
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
  tailscale set --ssh=false
  if tailscale status --json | python3 -c 'import json,sys; sys.exit(json.load(sys.stdin).get("BackendState") != "Running")'; then
    tailscale set --hostname="$new_hostname" --ssh=false
  else
    tailscale up --hostname="$new_hostname" --ssh=false
  fi
  tailscale set --ssh=false
  local tailscale_ip
  tailscale_ip="$(tailscale ip -4)"
  [[ "$tailscale_ip" =~ ^100\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "no Tailscale IPv4 address"
  systemctl enable --now ssh.service
  systemctl is-active --quiet ssh.service || die "OpenSSH is not active"
  if systemctl cat x11vnc.service >/dev/null 2>&1; then
    systemctl disable --now x11vnc.service
  fi
  pgrep -x x11vnc >/dev/null && die "x11vnc still running; resolve its launcher first"
  local vnc_dir="$TARGET_HOME/.vnc"
  install -d -o ares -g ares -m 0700 "$vnc_dir"
  if [[ ! -s "$vnc_dir/passwd" ]]; then
    echo "Create a unique TigerVNC password."
    runuser -u ares -- env HOME="$TARGET_HOME" tigervncpasswd "$vnc_dir/passwd"
  fi
  chown ares:ares "$vnc_dir/passwd"; chmod 0600 "$vnc_dir/passwd"
  cat > "$WORK/tigervnc.conf" <<'EOF'
$session = "cinnamon2d";
$geometry = "1280x800";
$depth = "24";
$localhost = "yes";
$alwaysShared = "yes";
$rfbport = "5901";
EOF
  install -o ares -g ares -m 0600 "$WORK/tigervnc.conf" "$vnc_dir/tigervnc.conf"
  install -d -m 0755 /etc/tigervnc
  install -o root -g root -m 0644 "$WORK/users" /etc/tigervnc/vncserver.users
  systemctl enable "$VNC_SERVICE"
  systemctl restart "$VNC_SERVICE"
  local attempt
  for attempt in {1..20}; do
    systemctl is-active --quiet "$VNC_SERVICE" && verify_vnc_listeners && break
    sleep 1
  done
  systemctl is-active --quiet "$VNC_SERVICE" && verify_vnc_listeners || die "TigerVNC localhost verification failed"
  COMPLETE=1
  echo "Remote support active; desktop/client acceptance still requires an actual connection."
  echo "Tailscale SSH disabled. Create a standard OpenSSH tunnel:"
  echo "  ssh -N -L 5901:127.0.0.1:5901 ares@$tailscale_ip"
  echo "Connect the VNC viewer to 127.0.0.1:5901."
  echo "Disable with sudo ares-disable-remote-access."
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
