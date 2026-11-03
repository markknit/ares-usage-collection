#!/usr/bin/env python3
"""Refresh the verified production ZIP using existing payloads; never install."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

sys.dont_write_bytecode = True
SELF = Path(__file__).resolve().parent
sys.path.insert(0, str(SELF))
import verify_offline_bundle as verifier

BUNDLE = "ARES_Q4_Offline_v0.94_amd64_v1.13"
BASE_SHA = "1f0993a806b41aa7024e0f4af7e634e7186f9d08983669a88d91c45a93b692c9"
APK_SHA = "16e5eef24b56dde1db3fbd0e5be542c5853f329841ae056bc1dd7afb6bf773a8"
DOCUMENTS = (
    "TECHNICIAN_PHONE_INSTALL.md", "TEACHER_PHONE_GUIDE.md", "LESSON3_CORPUS_INSTALL.md",
    "LESSON3_V094_ACCEPTANCE.md", "REMOTE_ACCESS.md", "INTERNET_LOCKDOWN.md",
    "PROFILES.md", "PROFILE_ACCEPTANCE.md", "TSAVO_TRUST.md",
    "TECHNICIAN_OVERVIEW.md", "PRE_RELOAD_PRESERVATION.md",
)


def seal(directory, name="SHA256SUMS", selected=None):
    directory = Path(directory)
    files = selected if selected is not None else sorted(
        p for p in directory.rglob("*") if p.is_file() and p != directory / name)
    lines = []
    for path in files:
        relative = path.relative_to(directory).as_posix()
        if "\n" in relative or "\\" in relative:
            raise ValueError("Unsupported checksum filename: " + relative)
        lines.append(verifier.integrity.digest(path) + "  ./" + relative + "\n")
    (directory / name).write_text("".join(lines), encoding="utf-8", newline="\n")


def repackage(base_zip, output, revision):
    base_zip, output = Path(base_zip).resolve(), Path(output).absolute()
    if not revision or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("A full source Git commit is required")
    if output.exists() or output.is_symlink():
        raise ValueError("Output already exists; retain it and choose a fresh folder")
    if verifier.integrity.digest(base_zip) != BASE_SHA:
        raise ValueError("Base ZIP is not the previously verified production artifact")
    with zipfile.ZipFile(base_zip) as archive:
        required = sum(item.file_size for item in archive.infolist()) * 3 + 2 * 1024**3
    if shutil.disk_usage(output.parent).free < required:
        raise ValueError("Insufficient space for staging, ZIP and independent extraction")
    output.mkdir()
    incomplete = output / "BUILD_INCOMPLETE"
    incomplete.write_text("Not verified or promoted. No installer has run.\n")
    work = output / "work"
    work.mkdir()
    verifier.extract(base_zip, work, BUNDLE)
    stage = work / BUNDLE
    verifier.integrity.verify_package(stage)
    updated = {"SHA256SUMS", "MANIFEST.txt", "teacher-app/SHA256SUMS",
               "ARES_Sync_Rollout_Package/SHA256SUMS.txt"}

    def copy(source, relative, normalize=False):
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = Path(source).read_bytes()
        target.write_bytes(data.replace(b"\r\n", b"\n") if normalize else data)
        target.chmod(0o755 if target.suffix == ".sh" else 0o644)
        updated.add(relative)

    for relative, source in verifier.REVIEWED.items():
        copy(SELF / source, relative, normalize=True)
    for content in (verifier.APPROVED_ADMIN_CONTENT, verifier.APPROVED_LOCKDOWN_CONTENT):
        for relative, source in content.items():
            copy(SELF / source, relative)
    for source in (SELF / "rollout/ARES_Sync_Rollout_Package").rglob("*"):
        if source.is_file():
            copy(source, "ARES_Sync_Rollout_Package/" + source.relative_to(
                SELF / "rollout/ARES_Sync_Rollout_Package").as_posix())
    for name in DOCUMENTS:
        copy(SELF / "docs" / name, "docs/" + name, normalize=True)
    subprocess.run([sys.executable, "-B", str(SELF / "tools/render_rollout_guides.py"),
                    "--source-dir", str(stage / "docs"), "--output-dir", str(stage / "docs/pdf")], check=True)
    for name in ("ARES_Sync_Teacher_Guide.pdf", "ARES_Sync_Technician_Guide.pdf"):
        copy(stage / "docs/pdf" / name, "ARES_Sync_Rollout_Package/guides/" + name)
    for name in ("ARES_Sync_Teacher_Guide.pdf", "ARES_Sync_Technician_Guide.pdf",
                 "ARES_Offline_Installer_Overview.pdf"):
        if not (stage / "docs/pdf" / name).read_bytes().startswith(b"%PDF-"):
            raise ValueError("Missing generated guide: " + name)
        updated.add("docs/pdf/" + name)
    rollout = stage / "ARES_Sync_Rollout_Package"
    seal(rollout, "SHA256SUMS.txt", sorted(
        [rollout / "README.txt", *rollout.glob("guides/*.pdf"), *rollout.glob("server-installer/*")]))
    description = (stage / "MANIFEST.txt").read_text(encoding="utf-8")
    description = description.replace("/app_install/\n", "/app_install/index.html\n")
    description += ("\nRepackaged UTC: " + datetime.now(timezone.utc).isoformat() +
                    "\nPackaging source commit: " + revision + "\nBase ZIP SHA-256: " + BASE_SHA +
                    "\nOwner-approved admin content: bundled\nInternet Lockdown: v1.4.2; no automatic activation\n"
                    "Technician overview: docs/pdf/ARES_Offline_Installer_Overview.pdf\n")
    (stage / "MANIFEST.txt").write_text(description, encoding="utf-8", newline="\n")
    seal(stage / "teacher-app")

    # Compare every untouched original file directly to the pinned ZIP. This
    # retains inherited files, media, image archives, corpus and approved APK.
    preserved = []
    with zipfile.ZipFile(base_zip) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            relative = item.filename.split("/", 1)[1]
            if relative in updated:
                continue
            digest = hashlib.sha256()
            with archive.open(item) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            path = stage / relative
            if not path.is_file() or verifier.integrity.digest(path) != digest.hexdigest():
                raise ValueError("Untouched base file changed: " + relative)
            preserved.append(relative)
    seal(stage)
    candidate = output / ".candidate.zip"
    with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(work).as_posix())
    checksum = verifier.verify(candidate, "production", APK_SHA)
    artifact = output / (BUNDLE + ".zip")
    candidate.rename(artifact)
    (output / (artifact.name + ".sha256")).write_text(checksum + "  " + artifact.name + "\n")
    report = {"source_commit": revision, "base_sha256": BASE_SHA, "zip_sha256": checksum,
              "preserved_base_files": preserved, "updated_files": sorted(updated),
              "installer_run": False, "downloads_or_docker_operations": False}
    (output / "repack-evidence.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "COMPLETED.txt").write_text("Repackaged and independently verified. No installer ran.\n")
    incomplete.unlink()
    print("PASS: corrected release ZIP independently verified: " + str(artifact))
    print("ZIP SHA-256: " + checksum)
    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    repackage(args.base_zip, args.output, args.source_revision)
