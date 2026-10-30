#!/usr/bin/env python3
"""Set/check Lesson3 offline URLs without printing secrets or enabling public mode."""
import argparse
from pathlib import Path


def configure(value, admin_url, server_url):
    if server_url:
        raise ValueError("Offline first installation requires empty SERVER_URL")
    expected = {"ADMIN_URL": admin_url, "SERVER_URL": server_url}
    result = []
    found = set()
    for line in value.splitlines():
        key = line.split("=", 1)[0]
        if key in expected:
            if key in found:
                raise ValueError("Duplicate URL configuration: " + key)
            line = key + "=" + expected[key]
            found.add(key)
        result.append(line)
    result.extend(key + "=" + expected[key] for key in expected if key not in found)
    return "\n".join(result) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("set", "check"))
    parser.add_argument("path", type=Path)
    parser.add_argument("admin_url")
    parser.add_argument("server_url")
    args = parser.parse_args()
    value = args.path.read_text()
    result = configure(value, args.admin_url, args.server_url)
    if args.mode == "check":
        if result != value:
            raise SystemExit("Existing Lesson3 URLs differ from packaged profile; explicit migration required")
    else:
        args.path.write_text(result, encoding="utf-8")
