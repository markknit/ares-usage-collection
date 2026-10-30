#!/usr/bin/env python3
"""Render inherited web payloads and Markdown guides for a sealed field profile.

Never rewrite binaries, shell source, or PDFs. PDFs are production references;
the package profile guide explicitly documents their production-only examples.
"""
import argparse
from pathlib import Path
import zipfile

ALIASES = {"production": "ares.local", "test": "ares-test.local"}


def render(root, profile):
    alias = ALIASES[profile]
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".html", ".htmlf", ".js", ".json", ".md"}:
            old = path.read_text(encoding="utf-8")
            value = old.replace("ares-test.local", "ares.local").replace("ares.local", alias)
            if value != old:
                path.write_text(value, encoding="utf-8", newline="\n")


def verify_apk(path, profile):
    """Fail closed if the APK's compiled endpoints do not match this profile."""
    expected = ("http://" + ALIASES[profile] + "/tracker/").encode()
    other = ("http://" + ALIASES["test" if profile == "production" else "production"] + "/tracker/").encode()
    with zipfile.ZipFile(path) as apk:
        dex = b"".join(apk.read(name) for name in apk.namelist() if name.endswith(".dex"))
    for endpoint in (b"prepare_due_usage_upload.php", b"collection_schedule.json"):
        if expected + endpoint not in dex:
            raise ValueError("APK lacks compiled endpoint for " + profile + ": " + endpoint.decode())
    if other in dex:
        raise ValueError("APK contains endpoints for the other profile")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--profile", choices=ALIASES, required=True)
    parser.add_argument("--apk", type=Path)
    args = parser.parse_args()
    if args.apk:
        verify_apk(args.apk, args.profile)
    if args.root:
        render(args.root, args.profile)
