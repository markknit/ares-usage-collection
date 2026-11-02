#!/usr/bin/env python3
"""Reject network-install commands in field scripts, with one sealed diagnostic."""
from pathlib import Path
import re
import sys

NETWORK = re.compile(r"github\.com|tailscale\.com|apt-get\s+(update|install)|docker(?:\s+compose)?\s+pull|wget\s")
VENDOR_SCRIPT = "remote-access/internet-lockdown/ares-lockdown-v1.4.2/lockdown_internet.sh"
VENDOR_DIAGNOSTIC = 'echo "ERROR: nftables is missing. Install: sudo apt-get install nftables" >&2'


def forbidden_lines(text, relative):
    issues = []
    for number, line in enumerate(text.splitlines(), 1):
        # This exact upstream line only prints an error; it executes no install.
        # Its release script is separately checked against the unchanged source.
        if relative == VENDOR_SCRIPT and line.strip() == VENDOR_DIAGNOSTIC:
            continue
        if NETWORK.search(line):
            issues.append(f"{relative}:{number}: {line.strip()}")
    return issues


def audit(root):
    root = Path(root)
    issues = []
    for path in root.rglob("*.sh"):
        issues.extend(forbidden_lines(path.read_text(encoding="utf-8"), path.relative_to(root).as_posix()))
    if issues:
        raise ValueError("Internet-dependent field script:\n" + "\n".join(issues))


if __name__ == "__main__":
    try:
        audit(sys.argv[1])
    except ValueError as error:
        raise SystemExit(str(error))
