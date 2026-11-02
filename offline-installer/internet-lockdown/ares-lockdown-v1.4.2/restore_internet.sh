#!/usr/bin/env bash
# Remove only the firewall table created by lockdown_internet.sh.
# All pre-existing UFW, nftables and Docker rules remain untouched.
set -Eeuo pipefail

TABLE="ares_internet_lockdown"
ROLLBACK_FILE="/run/ares-internet-lockdown/rollback-unit"

if [[ ${EUID} -ne 0 ]]; then
    echo "ERROR: Run as root using sudo." >&2
    exit 1
fi
if ! command -v nft >/dev/null 2>&1; then
    echo "ERROR: nftables command is missing; cannot remove lockdown table." >&2
    exit 1
fi

if nft list table inet "$TABLE" >/dev/null 2>&1; then
    nft delete table inet "$TABLE"
    echo "Lockdown removed. Prior firewall behavior is restored."
else
    echo "No lockdown table present; prior firewall behavior is already in effect."
fi

# Cancel a pending test rollback, if one exists.
if [[ -f "$ROLLBACK_FILE" ]]; then
    read -r unit < "$ROLLBACK_FILE"
    if command -v systemctl >/dev/null 2>&1; then
        systemctl stop "${unit}.timer" >/dev/null 2>&1 || true
    fi
    rm -f "$ROLLBACK_FILE"
fi
