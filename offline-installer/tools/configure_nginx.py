#!/usr/bin/env python3
"""Replace only the two ARES mDNS aliases in existing Nginx server_name lists."""
import re
import sys
from pathlib import Path


def configure(value, alias, hostname=None):
    if alias not in ("ares.local", "ares-test.local"):
        raise ValueError("Unsupported ARES alias")
    if hostname is not None and not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.local", hostname):
        raise ValueError("Invalid school hostname")
    matches = 0

    def replace(match):
        nonlocal matches
        if match.group(2) is None:  # A comment is never an active directive.
            return match.group(0)
        names = match.group(2).split()
        if not any("ares" in name for name in names):
            return match.group(0)
        matches += 1
        names = [name for name in names if name not in ("ares.local", "ares-test.local", hostname)]
        names.append(alias)
        if hostname and hostname not in names:
            names.append(hostname)
        return "server_name " + " ".join(names) + ";"

    result = re.sub(r"(#[^\n]*|\bserver_name\s+([^;]+);)", replace, value)
    if not matches:
        raise ValueError("No ARES server_name found")
    return result


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(configure(path.read_text(), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None), encoding="utf-8")
