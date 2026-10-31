#!/usr/bin/env bash
# Source and call after the core installer has passed all verification.
run_optional_remote_support() {
  local reply="${1:-N}" result=deferred rc
    case "$reply" in
      y|Y|yes|YES|Yes)
        if /usr/local/sbin/ares-enable-remote-access; then
          result=activated
        else
          rc=$?
          case "$rc" in 2) result=partial ;; 3) result=deferred ;; *) result=failed ;; esac
        fi ;;
    esac
  case "$result" in
    activated) echo "Remote support activated; verify the client SSH/VNC connection." ;;
    partial) echo "WARNING: TigerVNC activation failed; Tailscale and SSH remain operational; core installation remains successful." ;;
    failed) echo "WARNING: optional remote support failed; core installation remains successful." ;;
    deferred) echo "Remote support deferred; core installation remains successful." ;;
  esac
  echo "Later activation: sudo ares-enable-remote-access"
  return 0
}

optional_remote_support() {
  local reply=N
  if [[ -t 0 ]]; then
    echo "The ARES server needs outbound Internet. A technician can open the Tailscale URL on a phone using cellular data, off the ARES network."
    read -r -p "Activate remote support now? [y/N]: " reply || reply=N
  fi
  run_optional_remote_support "$reply"
}
