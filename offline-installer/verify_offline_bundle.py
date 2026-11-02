#!/usr/bin/env python3
"""Independently check a finished ZIP. Does not install or start any services."""
import argparse
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

SELF = Path(__file__).resolve().parent
sys.path.insert(0, str(SELF / "tools"))
import package_integrity as integrity
import tsavo_content

# Compare the generated entry points/helpers with the reviewed builder sources.
REVIEWED = {
    "install_offline.sh": "templates/install_offline.sh",
    "preflight.sh": "templates/preflight.sh",
    "ares_config.sh": "templates/ares_config.sh",
    "optional_remote_support.sh": "templates/optional_remote_support.sh",
    "package_integrity.py": "tools/package_integrity.py",
    "lesson3/install_lesson3_offline.sh": "templates/lesson3_offline.sh",
    "lesson3/corpus/install_lesson3_corpus.sh": "templates/install_lesson3_corpus.sh",
    "lesson3/configure_url.py": "tools/configure_lesson3_url.py",
    "lesson_plan/install.sh": "templates/lesson_plan_install.sh",
    "lesson_plan/configure_nginx.py": "tools/configure_nginx.py",
    "tracking/install_lesson_plan_tracking.sh": "templates/install_lesson_plan_tracking.sh",
    "teacher-app/install_teacher_app.sh": "templates/install_teacher_app.sh",
    "teacher-app/install_admin_content.sh": "templates/install_admin_content.sh",
    "teacher-app/verify_profile.py": "tools/render_profile.py",
    "tsavo/install.sh": "templates/install_tsavo_trust.sh",
    "tsavo/tsavo_content.py": "tools/tsavo_content.py",
    "tsavo/tsavo_install.py": "tools/tsavo_install.py",
    "remote-access/prepare_remote_access.sh": "templates/prepare_remote_access.sh",
    "remote-access/ares_enable_remote_access.sh": "templates/ares_enable_remote_access.sh",
    "remote-access/ares_disable_remote_access.sh": "templates/ares_disable_remote_access.sh",
    "remote-access/remote_support_common.sh": "templates/remote_support_common.sh",
    "remote-access/remote_support_config.py": "tools/remote_support_config.py",
}

# These owner-supplied files must retain their exact approved bytes, including
# line endings and the supplied PDF. Do not normalize or regenerate them.
APPROVED_ADMIN_CONTENT = {
    "teacher-app/admin-content/" + name: "admin-content/" + name
    for name in ("admin.html", "index.htmlf", "ARES_Sync_User_Guide.pdf")
}


def extract(archive, destination, bundle):
    """Validate names/types before extraction; ZIP reads also verify member CRCs."""
    names = set()
    files = 0
    with zipfile.ZipFile(archive) as source:
        for item in source.infolist():
            name = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (not name.parts or name.parts[0] != bundle or name.is_absolute()
                    or ".." in name.parts or "\\" in item.filename
                    or name.as_posix() != item.filename.rstrip("/")
                    or name.as_posix() in names
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or (not item.is_dir() and (len(name.parts) < 2 or stat.S_ISDIR(mode)))):
                raise ValueError("Unexpected ZIP entry: " + item.filename)
            names.add(name.as_posix())
            files += not item.is_dir()
        source.extractall(destination)
        for item in source.infolist():
            if not item.is_dir():
                (destination / item.filename).chmod((item.external_attr >> 16) & 0o777 or 0o644)
    return files


def verify(archive, profile="production", apk_sha256=None):
    archive = Path(archive).resolve()
    bundle = "ARES_Q4_Offline_v0.94_amd64_v1.13" + ("_test" if profile == "test" else "")
    alias = "ares-test.local" if profile == "test" else "ares.local"
    # Use the build disk rather than the host's possibly small /tmp filesystem.
    with tempfile.TemporaryDirectory(prefix=".ares-verify-", dir=archive.parent) as temp:
        extracted = Path(temp)
        count = extract(archive, extracted, bundle)
        root = extracted / bundle
        integrity.verify_package(root)
        manifest_count = len((root / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
        if count != manifest_count + 1:
            raise ValueError("ZIP and checksum inventories disagree")
        for target, reviewed in REVIEWED.items():
            if (root / target).read_bytes() != (SELF / reviewed).read_bytes().replace(b"\r\n", b"\n"):
                raise ValueError("Generated installer/helper differs from reviewed source: " + target)
        for target, approved in APPROVED_ADMIN_CONTENT.items():
            if (root / target).read_bytes() != (SELF / approved).read_bytes():
                raise ValueError("Admin content differs from the owner-approved file: " + target)
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if ("TsavoTrust" in path.relative_to(root).parts
                    or path.name in {"install_offline_no_sha_checks.sh", "install_offline_no_root_sha.sh",
                                     "recovery_installer.py", "install_offline2.sh",
                                     "tsavo_trust_module_install.sh", "setup-ares-tailscale-vnc-v2.sh"}):
                raise ValueError("Obsolete source artifact: " + relative)
            if path.suffix == ".sh":
                subprocess.run([shutil.which("bash") or "bash", "-n", str(path)], check=True)
                if re.search(r"github\.com|tailscale\.com|apt-get\s+(update|install)|docker(?:\s+compose)?\s+pull|wget\s",
                             path.read_text(encoding="utf-8")):
                    raise ValueError("Internet-dependent field script: " + relative)
        configuration = (root / "package.conf").read_text(encoding="utf-8")
        if configuration != f"LESSON3_VERSION=v0.94\nLESSON3_SERVER_URL=\nARES_PROFILE={profile}\n":
            raise ValueError("Package release/profile configuration mismatch")
        description = (root / "MANIFEST.txt").read_text(encoding="utf-8")
        for expected in ("Lesson3: v0.94", "Offline bundle revision: v1.13",
                         f"Profile: {profile} ({alias})", "Target architecture: linux/amd64"):
            if expected not in description.splitlines():
                raise ValueError("Release manifest mismatch: " + expected)
        if apk_sha256 and integrity.digest(root / "teacher-app/ares-sync.apk") != apk_sha256.lower():
            raise ValueError("APK differs from the supplied approved hash")
        integrity.verify_components(root, profile, "v0.94")
        source_pin = SELF / "manifests/tsavo-trust-source.json"
        pinned = tsavo_content.read_manifest(source_pin)
        packaged = tsavo_content.read_manifest(root / "tsavo/MANIFEST.json")
        if packaged.get("source_manifest_sha256") != integrity.digest(source_pin):
            raise ValueError("Tsavo source pin mismatch")
        unchanged = lambda data: [item for item in data["files"] if item["path"] != "index.htmlf"]
        if unchanged(packaged) != unchanged(pinned):
            raise ValueError("Tsavo logo/video pins changed")
        tsavo_content.validate(root / "tsavo/payload", packaged, inspect_media=True)
        page = (root / "tsavo/payload/index.htmlf").read_text(encoding="utf-8")
        if ('data-module-id="TsavoTrust"' not in page or "Ol Pejeta Conservancy" in page or "Presented vy" in page):
            raise ValueError("Tsavo page corrections are missing")
    digest = integrity.digest(archive)
    print(f"PASS: independently extracted and verified {count} ZIP files")
    print(f"ZIP SHA-256: {digest}")
    print("Release candidate verified. Live installation and field acceptance remain Pending.")
    return digest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip", type=Path)
    parser.add_argument("--profile", choices=("production", "test"), default="production")
    parser.add_argument("--apk-sha256")
    args = parser.parse_args()
    try:
        verify(args.zip, args.profile, args.apk_sha256)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release verification failed: {error}\nDo not distribute this candidate.\n")
