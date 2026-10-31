#!/usr/bin/env python3
"""Validate pinned TsavoTrust build-source content without downloading media.

Detailed MP4 structure inspection is build-side only. School-side callers use
the same inventory, size, hash and reference checks without media inspection.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import shutil


def read_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    files = manifest["files"]
    paths = [item["path"] for item in files]
    if (len(paths) != 8 or len(set(paths)) != 8
            or set(p for p in paths if not p.startswith("Videos/"))
            != {"index.htmlf", "tsavo_trust_logo.jpg"}
            or sum(p.startswith("Videos/") and p.endswith(".mp4") for p in paths) != 6):
        raise ValueError("TsavoTrust requires its page, JPG and exactly six videos")
    for item in files:
        path = PurePosixPath(item["path"])
        if (path.is_absolute() or ".." in path.parts or "\\" in str(path)
                or len(path.parts) > 2 or str(path) != item["path"]
                or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
                or not isinstance(item["bytes"], int) or item["bytes"] <= 0):
            raise ValueError("Invalid pinned TsavoTrust manifest entry")
    return manifest


def mp4_sample_types(path):
    """Inspect MP4 box boundaries and sample descriptions on the build machine."""
    def boxes(stream, start, end):
        offset = start
        while offset + 8 <= end:
            stream.seek(offset)
            size, kind = struct.unpack(">I4s", stream.read(8))
            header = 8
            if size == 1:
                size = struct.unpack(">Q", stream.read(8))[0]
                header = 16
            if size == 0:
                size = end - offset
            if size < header or offset + size > end:
                raise ValueError("Invalid MP4 box: " + str(path))
            yield kind, offset + header, offset + size
            offset += size
        if offset != end:
            raise ValueError("Truncated MP4 box: " + str(path))

    def walk(stream, start, end, depth=0):
        if depth > 16:
            raise ValueError("Excessive MP4 nesting")
        result = set()
        for kind, first, last in boxes(stream, start, end):
            if kind in (b"moov", b"trak", b"mdia", b"minf", b"stbl"):
                result.update(walk(stream, first, last, depth + 1))
            elif kind == b"stsd":
                stream.seek(first + 4)
                count = struct.unpack(">I", stream.read(4))[0]
                entries = list(boxes(stream, first + 8, last))
                if len(entries) != count:
                    raise ValueError("Invalid MP4 sample count")
                result.update(kind for kind, _, _ in entries)
        return result

    with path.open("rb") as stream:
        top = list(boxes(stream, 0, path.stat().st_size))
        if not {b"ftyp", b"moov", b"mdat"} <= {kind for kind, _, _ in top}:
            raise ValueError("Missing required MP4 boxes: " + str(path))
        types = walk(stream, 0, path.stat().st_size)
    if not {b"avc1", b"mp4a"} <= types:
        raise ValueError("Expected AVC video and AAC audio: " + str(path))
    return types


def validate(root, manifest, *, inspect_media=False):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("TsavoTrust source must be a real normalized directory")
    expected = {item["path"]: item for item in manifest["files"]}
    entries = list(root.rglob("*"))
    if any(p.is_symlink() for p in entries):
        raise ValueError("TsavoTrust symlinks are forbidden")
    actual = {p.relative_to(root).as_posix() for p in entries if p.is_file()}
    if actual != set(expected) or any(not p.is_file() and not p.is_dir() for p in entries):
        raise ValueError("TsavoTrust inventory mismatch (missing or unexpected files)")
    if {p.relative_to(root).as_posix() for p in entries if p.is_dir()} != {"Videos"}:
        raise ValueError("TsavoTrust must contain only the Videos subdirectory")
    for name, item in expected.items():
        path = root / name
        if path.stat().st_size != item["bytes"]:
            raise ValueError("TsavoTrust size mismatch: " + name)
        with path.open("rb") as stream:
            digest = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
            digest = digest.hexdigest()
        if digest != item["sha256"]:
            raise ValueError("TsavoTrust checksum mismatch: " + name)
        if inspect_media and path.suffix == ".mp4":
            mp4_sample_types(path)
    page = (root / "index.htmlf").read_text(encoding="utf-8")
    references = re.findall(r'<\?php echo \$dir \?>([^"\n]+)', page)
    if (len(references) != 7
            or {ref.lstrip("/") for ref in references} != set(expected) - {"index.htmlf"}):
        raise ValueError("TsavoTrust page must reference exactly the pinned JPG and six videos")
    return manifest


def prepare(source, destination, manifest_path):
    """Validate external input, then copy and correct only the approved page."""
    source, destination = Path(source), Path(destination)
    manifest = read_manifest(manifest_path)
    validate(source, manifest, inspect_media=True)
    if destination.exists() or destination.is_symlink():
        raise ValueError("TsavoTrust staging destination must not already exist")
    shutil.copytree(source, destination)
    page_path = destination / "index.htmlf"
    page = page_path.read_text(encoding="utf-8")
    for old, new in (("Ol Pejeta Conservancy", "Tsavo Trust"),
                     ("Presented vy", "Presented by"),
                     ('data-module-id="olpejetaconservancy_index"', 'data-module-id="TsavoTrust"')):
        if page.count(old) != 1:
            raise ValueError("Expected exactly one reviewed page correction: " + old)
        page = page.replace(old, new)
    page_path.write_text(page, encoding="utf-8", newline="\n")
    for item in manifest["files"]:
        if item["path"] == "index.htmlf":
            value = page_path.read_bytes()
            item.update(bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
    manifest["tracking_key"] = "module:TsavoTrust"
    manifest["display_name"] = "Tsavo Trust"
    manifest["source_manifest_sha256"] = hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()
    validate(destination, manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--inspect-media", action="store_true")
    parser.add_argument("--prepare", type=Path, metavar="DESTINATION")
    args = parser.parse_args()
    if args.prepare:
        manifest = prepare(args.root, args.prepare, args.manifest)
        (args.prepare.parent / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    else:
        validate(args.root, read_manifest(args.manifest), inspect_media=args.inspect_media)
    print("TsavoTrust: all eight pinned files and references verified")
