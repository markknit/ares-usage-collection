#!/usr/bin/env bash
# Shared non-secret SSH baseline handling. Caller holds the remote-support lock.
ssh_unit_snapshot() {
  local prefix=$1 unit=$2 enabled active=no present=no
  if systemctl cat "$unit" >/dev/null 2>&1; then
    present=yes
    systemctl is-active --quiet "$unit" && active=yes
    enabled="$(systemctl is-enabled "$unit" 2>/dev/null)" || true
    case "$enabled" in enabled|enabled-runtime|disabled|static|indirect|masked|masked-runtime) ;;
      *) echo "ERROR: unsupported enabled state for $unit" >&2; return 1 ;;
    esac
  else
    enabled=not-found
  fi
  printf -v "${prefix}_PRESENT" '%s' "$present"
  printf -v "${prefix}_ACTIVE" '%s' "$active"
  printf -v "${prefix}_ENABLED" '%s' "$enabled"
}

load_ssh_baseline() {
  local file=$1 key value
  SSH_STATE_VERSION=0
  SSH_SERVICE_PRESENT=; SSH_SERVICE_ACTIVE=; SSH_SERVICE_ENABLED=
  SSH_SOCKET_PRESENT=; SSH_SOCKET_ACTIVE=; SSH_SOCKET_ENABLED=
  SSH_WAS_ACTIVE=; SSH_WAS_ENABLED=
  while IFS='=' read -r key value; do
    case "$key" in
      SSH_STATE_VERSION) [[ "$value" == 2 ]] || return 1 ;;
      SSH_SERVICE_PRESENT|SSH_SERVICE_ACTIVE|SSH_SOCKET_PRESENT|SSH_SOCKET_ACTIVE|SSH_WAS_ACTIVE|SSH_WAS_ENABLED)
        [[ "$value" == yes || "$value" == no ]] || return 1 ;;
      SSH_SERVICE_ENABLED|SSH_SOCKET_ENABLED)
        case "$value" in enabled|enabled-runtime|disabled|static|indirect|masked|masked-runtime|not-found) ;; *) return 1 ;; esac ;;
      '') continue ;;
      *) echo "ERROR: invalid SSH baseline key" >&2; return 1 ;;
    esac
    printf -v "$key" '%s' "$value"
  done < "$file"
  if [[ "$SSH_STATE_VERSION" == 2 ]]; then
    [[ -n "$SSH_SERVICE_PRESENT" && -n "$SSH_SERVICE_ACTIVE" && -n "$SSH_SERVICE_ENABLED" \
      && -n "$SSH_SOCKET_PRESENT" && -n "$SSH_SOCKET_ACTIVE" && -n "$SSH_SOCKET_ENABLED" ]]
  else
    [[ -n "$SSH_WAS_ACTIVE" && -n "$SSH_WAS_ENABLED" ]]
  fi
}

capture_ssh_baseline() {
  local file=$1 legacy_active= legacy_enabled= key
  if [[ -f "$file" ]]; then
    load_ssh_baseline "$file" || { echo "ERROR: invalid saved SSH baseline" >&2; return 1; }
    [[ "$SSH_STATE_VERSION" == 2 ]] && return 0
    legacy_active=$SSH_WAS_ACTIVE; legacy_enabled=$SSH_WAS_ENABLED
    # The older activator never changed ssh.socket. Retain its service booleans,
    # capture the socket now, and preserve the old record for review.
    cp -a "$file" "$file.v1" || return 1
    echo "Migrating legacy SSH baseline: retaining service booleans and recording current socket state."
  fi
  ssh_unit_snapshot SSH_SERVICE ssh.service || return 1
  ssh_unit_snapshot SSH_SOCKET ssh.socket || return 1
  if [[ -n "$legacy_active" ]]; then
    SSH_SERVICE_ACTIVE=$legacy_active
    SSH_SERVICE_ENABLED=disabled
    [[ "$legacy_enabled" == no ]] || SSH_SERVICE_ENABLED=enabled
  fi
  (
    umask 077
    printf 'SSH_STATE_VERSION=2\n'
    for key in SSH_SERVICE_PRESENT SSH_SERVICE_ACTIVE SSH_SERVICE_ENABLED SSH_SOCKET_PRESENT SSH_SOCKET_ACTIVE SSH_SOCKET_ENABLED; do
      printf '%s=%s\n' "$key" "${!key}"
    done
  ) > "$file.tmp" || return 1
  chmod 0600 "$file.tmp" && mv -f "$file.tmp" "$file"
}

ensure_ssh() {
  if systemctl is-active --quiet ssh.socket; then
    echo "OpenSSH is already provided by active ssh.socket; ssh.service is left unchanged."
    return 0
  fi
  if systemctl is-active --quiet ssh.service; then
    echo "OpenSSH service is already active."
    return 0
  fi
  local unit=ssh.service state
  systemctl cat ssh.socket >/dev/null 2>&1 && unit=ssh.socket
  state="$(systemctl is-enabled "$unit" 2>/dev/null)" || true
  case "$state" in masked|masked-runtime) echo "ERROR: $unit is masked; not changing that policy" >&2; return 1 ;; esac
  if [[ "$state" == static ]]; then
    systemctl start "$unit" || return 1
  else
    systemctl enable --now "$unit" || return 1
  fi
  systemctl is-active --quiet "$unit"
}

restore_ssh_baseline() {
  local file=$1 prefix unit active enabled present current
  [[ -f "$file" ]] || return 0
  load_ssh_baseline "$file" || return 1
  [[ "$SSH_STATE_VERSION" == 2 ]] || {
    echo "ERROR: activate once to migrate the legacy SSH baseline before disabling" >&2; return 1;
  }
  # Stop only originally inactive units; never blanket-disable socket activation.
  for prefix in SSH_SOCKET SSH_SERVICE; do
    unit=ssh.service; [[ "$prefix" == SSH_SERVICE ]] || unit=ssh.socket
    present=${prefix}_PRESENT; active=${prefix}_ACTIVE
    [[ "${!present}" == yes ]] || continue
    if [[ "${!active}" == no ]]; then systemctl stop "$unit" || return 1; fi
  done
  for prefix in SSH_SERVICE SSH_SOCKET; do
    unit=ssh.service; [[ "$prefix" == SSH_SERVICE ]] || unit=ssh.socket
    present=${prefix}_PRESENT; enabled=${prefix}_ENABLED; active=${prefix}_ACTIVE
    [[ "${!present}" == yes ]] || continue
    current="$(systemctl is-enabled "$unit" 2>/dev/null)" || true
    if [[ "$current" != "${!enabled}" ]]; then
      # Remove activation-created persistent/runtime enablement before restoring
      # the exact saved kind, rather than leaving both sets of links behind.
      case "$current" in
        enabled-runtime) systemctl disable --runtime "$unit" || return 1 ;;
        enabled) systemctl disable "$unit" || return 1 ;;
      esac
      case "${!enabled}" in
        enabled) systemctl enable "$unit" || return 1 ;;
        enabled-runtime) systemctl enable --runtime "$unit" || return 1 ;;
        masked) systemctl mask "$unit" || return 1 ;;
        masked-runtime) systemctl mask --runtime "$unit" || return 1 ;;
        disabled|static|indirect) systemctl disable "$unit" || return 1 ;;
        *) return 1 ;;
      esac
    fi
    if [[ "${!active}" == yes ]]; then systemctl start "$unit" || return 1; fi
  done
  for prefix in SSH_SERVICE SSH_SOCKET; do
    unit=ssh.service; [[ "$prefix" == SSH_SERVICE ]] || unit=ssh.socket
    present=${prefix}_PRESENT; enabled=${prefix}_ENABLED; active=${prefix}_ACTIVE
    [[ "${!present}" == yes ]] || continue
    current="$(systemctl is-enabled "$unit" 2>/dev/null)" || true
    [[ "$current" == "${!enabled}" ]] || { echo "ERROR: $unit enabled state was not restored" >&2; return 1; }
    current=no; systemctl is-active --quiet "$unit" && current=yes
    [[ "$current" == "${!active}" ]] || { echo "ERROR: $unit active state was not restored" >&2; return 1; }
  done
}
