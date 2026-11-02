#!/usr/bin/env python3
"""Render inherited web payloads and Markdown guides for a sealed field profile.

Never rewrite binaries, shell source, or PDFs. PDFs are production references;
the package profile guide explicitly documents their production-only examples.
"""
import argparse
from pathlib import Path
import zipfile
import struct

ALIASES = {"production": "ares.local", "test": "ares-test.local"}


def binary_xml_strings(value):
    """Read Android's compiled XML string pool (UTF-8 or UTF-16)."""
    if len(value) < 8 or struct.unpack_from("<HHI", value) != (3, 8, len(value)):
        raise ValueError("Invalid compiled XML header")
    strings = []
    offset = 8
    while offset + 8 <= len(value):
        kind, header, size = struct.unpack_from("<HHI", value, offset)
        if header < 8 or header > size or offset + size > len(value):
            raise ValueError("Invalid compiled XML chunk")
        if kind == 1:
            count, _, flags, start, _ = struct.unpack_from("<IIIII", value, offset + 8)
            for index in range(count):
                position = offset + start + struct.unpack_from("<I", value, offset + header + index * 4)[0]
                if flags & 0x100:
                    # Skip UTF-16 length, then read UTF-8 byte length.
                    position += 2 if value[position] & 0x80 else 1
                    length = value[position]
                    position += 1
                    if length & 0x80:
                        length = ((length & 0x7f) << 8) | value[position]
                        position += 1
                    strings.append(value[position:position + length].decode("utf-8"))
                else:
                    length = struct.unpack_from("<H", value, position)[0]
                    position += 2
                    if length & 0x8000:
                        length = ((length & 0x7fff) << 16) | struct.unpack_from("<H", value, position)[0]
                        position += 2
                    strings.append(value[position:position + length * 2].decode("utf-16-le"))
        offset += size
    return strings


def render(root, profile):
    alias = ALIASES[profile]
    for path in root.rglob("*"):
        # Imported versioned scripts/docs have their own unchanged release seal.
        if (root / "remote-access/internet-lockdown") in path.parents:
            continue
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
        # Release builds may rename XML resources (for example to res/8G.xml).
        # Identify policies by their compiled structure, never by filename.
        policies = []
        structure = {"network-security-config", "domain-config", "domain", "cleartextTrafficPermitted"}
        for entry in apk.infolist():
            if entry.is_dir() or not entry.filename.startswith("res/"):
                continue
            try:
                strings = set(binary_xml_strings(apk.read(entry)))
            except (ValueError, struct.error, IndexError):
                # Images, raw assets and malformed binary XML are not policies.
                continue
            if structure <= strings:
                policies.append(strings)
        manifest = binary_xml_strings(apk.read("AndroidManifest.xml"))
    for endpoint in (b"prepare_due_usage_upload.php", b"collection_schedule.json"):
        if expected + endpoint not in dex:
            raise ValueError("APK lacks compiled endpoint for " + profile + ": " + endpoint.decode())
    if other in dex:
        raise ValueError("APK contains endpoints for the other profile")
    if not policies or any(
        ALIASES[profile] not in policy
        or any(alias in policy for name, alias in ALIASES.items() if name != profile)
        for policy in policies
    ):
        raise ValueError("APK cleartext policy does not match profile")
    expected_id = "org.areseducation.sync" + (".test" if profile == "test" else "")
    if expected_id not in manifest:
        raise ValueError("APK application identity does not match profile")


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
