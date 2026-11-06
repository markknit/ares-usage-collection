#!/usr/bin/env bash
# Source and call after the core installer has passed all verification.
prepare_optional_remote_support() {
  echo
  echo "Preparing optional LAN desktop and Internet remote support."
  # Replacing/restarting Tailscale can invalidate a live service-cgroup firewall
  # exception. Preserve existing support when lockdown is active or boot-enabled.
  if { command -v nft >/dev/null 2>&1 && nft list table inet ares_internet_lockdown >/dev/null 2>&1; } \
      || systemctl is-enabled --quiet ares-internet-lockdown.service 2>/dev/null; then
    echo "Remote support preparation deferred: existing Internet lockdown is active or enabled at boot."
    echo "Existing remote services are preserved; core installation remains successful."
    return 1
  fi
  # Run as a separate Bash process so failures stop preparation, while the
  # conditional caller preserves the already completed core installation.
  if bash "$SCRIPT_DIR/remote-access/prepare_remote_access.sh"; then
    echo "Remote support prepared; activation is optional."
    return 0
  fi
  echo "WARNING: remote support could not be prepared."
  echo "ARES installation is complete and can be used offline."
  echo "For remote support, send the installation log to ARES support."
  return 1
}

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
    partial) echo "WARNING: optional support is partially configured; read the activation details above; core installation remains successful." ;;
    failed) echo "WARNING: optional remote support failed; core installation remains successful." ;;
    deferred) echo "Internet support deferred; any successfully activated LAN desktop remains available; core installation remains successful." ;;
  esac
  echo "Later activation: sudo ares-enable-remote-access"
  echo "Offline LAN-only activation: sudo ares-enable-remote-access --lan-only"
  return 0
}

optional_remote_support() {
  local reply=N
  if [[ -t 0 ]]; then
    echo "Local desktop access works without Internet. Tailscale enrollment is a separate choice after local access starts."
    read -r -p "Activate LAN desktop and optional Internet support now? [y/N]: " reply || reply=N
  fi
  run_optional_remote_support "$reply"
}
