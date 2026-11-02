#!/usr/bin/env bash
# Read-only AnyDesk connectivity diagnostics; no firewall or service changes.
set -u
printf '\n=== AnyDesk connectivity snapshot - %s ===\n' "$(date -Is)"
printf '\nAnyDesk service state and cgroup:\n'
systemctl is-active anydesk.service 2>&1 || true
systemctl show -P ControlGroup anydesk.service 2>&1 || true
printf '\nAnyDesk processes (PIDs and identities only):\n'
ps -C anydesk -o pid=,uid=,comm= 2>&1 || true
for pid in $(ps -C anydesk -o pid= 2>/dev/null); do
    printf 'PID %s cgroup: ' "$pid"
    tr '\n' ' ' < "/proc/$pid/cgroup" 2>/dev/null || true
    printf '\n'
done
printf '\nAnyDesk-owned TCP/UDP sockets (may reveal remote IPs):\n'
ss -tunap 2>&1 | grep -i -E '(anydesk|State)' || true
printf '\nAnyDesk-related firewall counters (if active):\n'
nft -a list table inet ares_internet_lockdown 2>&1 | grep -E '(cgroupv2|dport|counter|drop)' | tail -n 55 || true
printf '\nFirewall table status:\n'
if nft list table inet ares_internet_lockdown >/dev/null 2>&1; then echo ACTIVE; else echo ABSENT; fi
printf '\nNote: This tool does not restart AnyDesk or change firewall rules.\n'
