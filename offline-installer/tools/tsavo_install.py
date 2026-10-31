#!/usr/bin/env python3
"""Transactional offline TsavoTrust deployment; only Python's standard library."""
import argparse
import csv
import io
import os
from pathlib import Path
import shutil
import signal
import tempfile
from urllib.parse import quote
from urllib.request import Request, build_opener, ProxyHandler
import uuid

from tsavo_content import read_manifest, validate

KEY = "module:TsavoTrust"
LABEL = "Tsavo Trust"
BASE = Path("mnt/sda3/var/www")


def mapping_bytes(original):
    """Append one mapping; leave all historical bytes and rows untouched."""
    rows = list(csv.reader(io.StringIO(original.decode("utf-8-sig"))))
    matches = [row for row in rows if row and row[0].strip() == KEY]
    if matches:
        if len(matches) != 1 or len(matches[0]) < 2 or matches[0][1].strip() != LABEL:
            raise ValueError("Conflicting or duplicate TsavoTrust tracking mapping")
        return original
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    separator = b"" if not original or original.endswith((b"\r", b"\n")) else newline
    return original + separator + b"module:TsavoTrust,Tsavo Trust," + newline


def paths(root):
    base = Path(root).resolve() / BASE
    return base / "modules/TsavoTrust", base / "www2/modules/TsavoTrust", base / "tracker/key_map.csv"


def check_parents(path, root):
    root = Path(root).resolve()
    for parent in (path.parent, *path.parent.parents):
        if parent == root:
            break
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("Missing or symlinked destination parent: " + str(parent))


def preflight(package, root):
    manifest = read_manifest(package / "MANIFEST.json")
    if manifest.get("tracking_key") != KEY or manifest.get("display_name") != LABEL:
        raise ValueError("Unexpected packaged tracking identity")
    validate(package / "payload", manifest)
    target, link, keymap = paths(root)
    for path in (target, link, keymap):
        check_parents(path, root)
    if keymap.is_symlink() or not keymap.is_file():
        raise ValueError("Expected a real tracker key map file")
    original = keymap.read_bytes()
    updated = mapping_bytes(original)
    # Replacing arbitrary devices/FIFOs is forbidden; directories and links are
    # retained as backups without following them.
    for path in (target, link):
        if os.path.lexists(path) and not (path.is_symlink() or path.is_dir() or path.is_file()):
            raise ValueError("Unsupported existing destination: " + str(path))
    required = sum(item["bytes"] for item in manifest["files"])
    if shutil.disk_usage(target.parent).free < required + 16 * 1024 * 1024:
        raise ValueError("Insufficient free space for staged TsavoTrust content")
    return manifest, updated, original


def verify_installed(package, root, manifest=None):
    manifest = manifest or read_manifest(package / "MANIFEST.json")
    target, link, keymap = paths(root)
    validate(target, manifest)
    if not link.is_symlink() or link.resolve() != target.resolve():
        raise ValueError("TsavoTrust portal link does not resolve to the installed module")
    original = keymap.read_bytes()
    if mapping_bytes(original) != original:
        raise ValueError("TsavoTrust tracking mapping is absent")


def verify_http(manifest, host, origin="http://127.0.0.1"):
    """Check real byte-range delivery; do not download whole videos."""
    if host not in ("ares.local", "ares-test.local"):
        raise ValueError("Unexpected profile alias")
    opener = build_opener(ProxyHandler({}))
    request = Request(origin + "/www2/index.php", headers={"Host": host})
    with opener.open(request, timeout=10) as response:
        if response.status != 200 or b'data-module-id="TsavoTrust"' not in response.read(4 * 1024 * 1024):
            raise ValueError("TsavoTrust card missing from the rendered www2 portal")
    for prefix in ("/modules/TsavoTrust/", "/www2/modules/TsavoTrust/"):
        request = Request(origin + prefix + "tsavo_trust_logo.jpg", headers={"Host": host})
        with opener.open(request, timeout=10) as response:
            expected_size = next(item["bytes"] for item in manifest["files"] if item["path"] == "tsavo_trust_logo.jpg")
            if response.status != 200 or len(response.read(expected_size + 1)) != expected_size:
                raise ValueError("TsavoTrust logo HTTP verification failed")
    for item in manifest["files"]:
        if not item["path"].endswith(".mp4"):
            continue
        for prefix in ("/modules/TsavoTrust/", "/www2/modules/TsavoTrust/"):
            request = Request(origin + prefix + quote(item["path"], safe="/"),
                              headers={"Host": host, "Range": "bytes=0-31"})
            with opener.open(request, timeout=10) as response:
                if (response.status != 206
                        or response.headers.get("Content-Range") != f'bytes 0-31/{item["bytes"]}'
                        or len(response.read(33)) != 32):
                    raise ValueError("TsavoTrust HTTP byte-range verification failed")


def remove_new(path, root):
    # Validate the final absolute parent before any recursive cleanup. Never
    # follow a destination symlink into a different installation tree.
    root = Path(root).resolve()
    if path == root or not path.parent.resolve().is_relative_to(root):
        raise ValueError("Refusing cleanup outside the installation root: " + str(path))
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def install(package, root, *, after_publish=None):
    """Retain old objects on their own filesystems and roll back on failure."""
    manifest, updated, original = preflight(package, root)
    target, link, keymap = paths(root)
    token = uuid.uuid4().hex
    # Every replacement and its backup share a parent filesystem. Backups survive
    # success; they are moved back into place on failure.
    replacements = []
    scratch = []
    try:
        stage = Path(tempfile.mkdtemp(prefix=".tsavo-stage-", dir=target.parent))
        scratch.append(stage)
        new_module = stage / "module"
        shutil.copytree(package / "payload", new_module)
        validate(new_module, manifest)
        for path in (new_module, *new_module.rglob("*")):
            path.chmod(0o755 if path.is_dir() else 0o644)
            if Path(root).resolve() == Path("/"):
                shutil.chown(path, user="ares", group="www-data")
        descriptor, name = tempfile.mkstemp(prefix=".tsavo-keymap-", dir=keymap.parent)
        os.close(descriptor)
        new_map = Path(name)
        scratch.append(new_map)
        shutil.copy2(keymap, new_map)
        new_map.write_bytes(updated)
        if hasattr(os, "chown"):
            stat = keymap.stat()
            os.chown(new_map, stat.st_uid, stat.st_gid)
        new_link = link.parent / (".tsavo-link-" + token)
        scratch.append(new_link)
        new_link.symlink_to(target, target_is_directory=True)
        if keymap.read_bytes() != original:
            raise ValueError("Key map changed during staging; refusing to overwrite new entries")
        for destination, staged in ((target, new_module), (keymap, new_map), (link, new_link)):
            backup = destination.parent / ("." + destination.name + ".tsavo-backup-" + token)
            had_old = os.path.lexists(destination)
            # Register before the first rename. Rollback observes the backup's
            # existence so interruption between rename and the next Python line
            # cannot strand a previous installation.
            replacements.append((destination, backup, had_old))
            if had_old:
                destination.rename(backup)
            staged.rename(destination)
        verify_installed(package, root, manifest)
        if after_publish is not None:
            after_publish(manifest)
    except BaseException as error:
        # Do not delete the backups if restoration fails; report that failure.
        restore_errors = []
        for destination, backup, had_old in reversed(replacements):
            try:
                if had_old and os.path.lexists(backup):
                    remove_new(destination, root)
                    backup.rename(destination)
                elif not had_old:
                    remove_new(destination, root)
            except OSError as restore_error:
                restore_errors.append(str(backup) + ": " + str(restore_error))
        if restore_errors:
            raise RuntimeError("TsavoTrust restore needs attention; retained backups: "
                               + "; ".join(restore_errors)) from error
        raise
    finally:
        for path in scratch:
            remove_new(path, root)
    return [str(backup) for _, backup, had_old in replacements if had_old]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/"), help="Alternate root for disposable integration tests")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--host", choices=("ares.local", "ares-test.local"))
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    if args.check:
        preflight(package, args.root)
    elif args.verify:
        verify_installed(package, args.root)
        if args.host:
            verify_http(read_manifest(package / "MANIFEST.json"), args.host)
    else:
        if args.root.resolve() == Path("/") and os.geteuid() != 0:
            parser.error("run as root")
        if args.root.resolve() == Path("/") and not args.host:
            parser.error("--host is required for deployment verification")
        # Serialize deploys after validation, then validate again under the lock.
        preflight(package, args.root)
        import fcntl
        target, _, _ = paths(args.root)
        with (target.parent / ".tsavo-install.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            def interrupted(signum, frame):
                raise SystemExit("TsavoTrust interrupted; rolling back")
            for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
                signal.signal(signum, interrupted)
            backups = install(package, args.root,
                              after_publish=(lambda manifest: verify_http(manifest, args.host)) if args.host else None)
        for backup in backups:
            print("TsavoTrust retained backup:", backup)
    print("TsavoTrust verification passed")


if __name__ == "__main__":
    main()
