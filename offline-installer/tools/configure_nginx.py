#!/usr/bin/env python3
"""Replace only the two ARES mDNS aliases in existing Nginx server_name lists."""
import re
import sys
from pathlib import Path


def configure(value, alias):
    if alias not in ("ares.local", "ares-test.local"):
        raise ValueError("Unsupported ARES alias")
    matches = 0

    def replace(match):
        nonlocal matches
        names = match.group(1).split()
        if not any("ares" in name for name in names):
            return match.group(0)
        matches += 1
        names = [name for name in names if name not in ("ares.local", "ares-test.local")]
        return "server_name " + " ".join(names + [alias]) + ";"

    result = re.sub(r"\bserver_name\s+([^;]+);", replace, value)
    if not matches:
        raise ValueError("No ARES server_name found")
    return result


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(configure(path.read_text(), sys.argv[2]), encoding="utf-8")
