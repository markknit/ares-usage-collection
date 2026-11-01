#!/usr/bin/env python3
"""One field-package check, plus detailed build-side release validation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import tarfile

CORPUS_COMMIT = "e07c243da77ad4554a2f404ae7790ef6e9d3e1b0"
DEBS = {"libfile-readbackwards-perl": "1.06-2", "tigervnc-common": "1.13.1+dfsg-2build2",
        "tigervnc-tools": "1.13.1+dfsg-2build2", "tigervnc-standalone-server": "1.13.1+dfsg-2build2"}


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def load_helper(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checksums(directory, name="SHA256SUMS", required=()):
    manifest = directory / name
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("Missing component checksum manifest: " + str(manifest))
    found = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-fA-F]{64}) [ *](.+)", line)
        if not match:
            raise ValueError("Malformed component checksum manifest")
        value, filename = match.groups()
        relative = PurePosixPath(filename)
        if relative.is_absolute() or ".." in relative.parts or "\\" in filename:
            raise ValueError("Unsafe component checksum path")
        path = directory / relative
        if not path.resolve().is_relative_to(directory.resolve()) or path.is_symlink() or not path.is_file():
            raise ValueError("Missing or unsafe component file: " + filename)
        normalized = relative.as_posix()
        if normalized in found or digest(path) != value.lower():
            raise ValueError("Component checksum mismatch or duplicate: " + filename)
        found.add(normalized)
    if not found or not set(required) <= found:
        raise ValueError("Incomplete component checksum coverage: " + str(directory))
    return found


def verify_package(root):
    """Check the complete extracted package once, before installation changes."""
    root = Path(root)
    if (root / "NOT_FIELD_READY.txt").exists():
        raise ValueError("This is a development scaffold. Obtain the complete offline installer.")
    actual = set()
    for path in root.rglob("*"):
        name = path.relative_to(root).as_posix()
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Unexpected package entry: " + name)
        if path.is_file() and name != "SHA256SUMS":
            actual.add(name)
            with path.open("rb") as stream:
                if stream.read(128).startswith(b"version https://git-lfs.github.com/spec/v1"):
                    raise ValueError("Incomplete package file: " + name)
    covered = checksums(root)
    if covered != actual:
        raise ValueError("Package inventory differs from its checksum list")
    print("PASS: complete installation package checked")


def archive_file_member(source, name):
    """Resolve a saved-image file/link using only archive metadata, never disk paths."""
    members = {PurePosixPath(item.name).as_posix(): item for item in source.getmembers()}
    seen = set()
    while True:
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or "\\" in name:
            raise ValueError("Invalid archive file path: " + name)
        name = relative.as_posix()
        if name in seen:
            raise ValueError("Cyclic archive link: " + name)
        seen.add(name)
        if name not in members:
            raise ValueError("Missing archive file/link target: " + name)
        item = members[name]
        if item.isfile():
            return item
        if not (item.issym() or item.islnk()):
            raise ValueError("Archive entry is not a file: " + name)
        if PurePosixPath(item.linkname).is_absolute() or "\\" in item.linkname:
            raise ValueError("Invalid archive link target: " + item.linkname)
        # Symlinks are relative to their parent; hard links are archive-relative.
        target = posixpath.join(posixpath.dirname(name), item.linkname) if item.issym() else item.linkname
        name = posixpath.normpath(target)


def archive(path, *, allow_image_links=False):
    result = tarfile.open(path, "r:gz")
    try:
        for item in result.getmembers():
            relative = PurePosixPath(item.name)
            supported = item.isdir() or item.isfile() or (allow_image_links and (item.issym() or item.islnk()))
            if relative.is_absolute() or ".." in relative.parts or not supported:
                raise ValueError(f"Unsupported payload archive entry in {path.name}: {item.name!r} (type {item.type!r})")
        if allow_image_links:
            for item in result.getmembers():
                if item.issym() or item.islnk():
                    archive_file_member(result, item.name)
    except BaseException:
        result.close()
        raise
    return result


def verify_components(root, profile, version):
    root = Path(root)
    if (root / "NOT_FIELD_READY.txt").exists():
        raise ValueError("Scaffolds are not installable")
    for path in root.rglob("*"):
        if path.is_file():
            with path.open("rb") as stream:
                if stream.read(128).startswith(b"version https://git-lfs.github.com/spec/v1"):
                    raise ValueError("Unhydrated LFS pointer file: " + str(path.relative_to(root)))
    checksums(root / "lesson_plan/payload", required=["index.htmlf", "index.html", "index_bu.htmlf", "ARES-Logo.png",
               "PDF/index.html", "generate_teacher_index.js", "LESSON3_USER_GUIDE.pdf"])
    checksums(root / "ARES_Sync_Rollout_Package", "SHA256SUMS.txt", required=[
        "server-installer/update_school_server.sh", "server-installer/ares_set_school_code.sh"])
    teacher = root / "teacher-app"
    checksums(teacher, required=["ares-sync.apk", "ares-sync.apk.sha256", "APPROVAL.json", "verify_profile.py"])
    checksums(teacher, "ares-sync.apk.sha256", ["ares-sync.apk"])
    approved = json.loads((teacher / "APPROVAL.json").read_text(encoding="utf-8"))
    expected_id = "org.areseducation.sync" + (".test" if profile == "test" else "")
    if (approved.get("profile") != profile or approved.get("app_id") != expected_id
            or approved.get("sha256") != digest(teacher / "ares-sync.apk")):
        raise ValueError("Approved APK identity/hash does not match package")
    load_helper("apk_policy", teacher / "verify_profile.py").verify_apk(teacher / "ares-sync.apk", profile)

    release = root / "lesson3/release"
    release_name = "lesson3-online-deploy.tar.gz"
    checksums(release, release_name + ".sha256", [release_name])
    with archive(release / release_name) as bundle:
        member = bundle.extractfile("lesson3-deploy/VERSION")
        if member is None or member.read().decode().strip() != version:
            raise ValueError("Lesson3 release VERSION mismatch")
        compose = bundle.extractfile("lesson3-deploy/compose.yaml")
        if compose is None:
            raise ValueError("Lesson3 compose file missing")
        images = set(re.findall(r'^\s*image:\s*[\"\']?([^\s\"\']+)', compose.read().decode(), re.M))
        if not images:
            raise ValueError("Lesson3 compose image set is empty")
    image_dir = root / "lesson3/images"
    image_name = f"lesson3-{version}-amd64-images.tar.gz"
    checksums(image_dir, required=[image_name, "IMAGE_REFS.txt"])
    refs = [line.split("\t") for line in (image_dir / "IMAGE_REFS.txt").read_text().splitlines()]
    if not refs or any(len(row) != 3 or not re.fullmatch(r"sha256:[0-9a-f]{64}", row[2]) for row in refs):
        raise ValueError("Malformed Lesson3 image references")
    if {row[0] for row in refs} != images or any(row[1] != row[0].split("@", 1)[0] for row in refs):
        raise ValueError("Lesson3 image references do not match release")
    # Docker save can deduplicate shared layers with internal relative links.
    # Resolve those links inside the TAR; no image contents are extracted here.
    with archive(image_dir / image_name, allow_image_links=True) as saved:
        manifest = saved.extractfile(archive_file_member(saved, "manifest.json"))
        if manifest is None:
            raise ValueError("Docker image archive manifest missing")
        tags = {}
        for item in json.load(manifest):
            config = saved.extractfile(archive_file_member(saved, item["Config"]))
            if config is None:
                raise ValueError("Docker image configuration missing")
            config_bytes = config.read()
            configuration = json.loads(config_bytes)
            if configuration.get("architecture") != "amd64" or configuration.get("os") != "linux":
                raise ValueError("Docker image platform does not match linux/amd64")
            identity = "sha256:" + hashlib.sha256(config_bytes).hexdigest()
            for layer in item["Layers"]:
                archive_file_member(saved, layer)
            for tag in item.get("RepoTags") or []:
                tags[tag] = identity
        if any(tags.get(row[1]) != row[2] for row in refs):
            raise ValueError("Docker image tags/configuration identities mismatch")

    corpus = root / "lesson3/corpus"
    data = json.loads((corpus / "MANIFEST.json").read_text(encoding="utf-8"))
    records = data["files"]
    names = {item["file"] for item in records}
    if (data.get("format") != "ares-lesson3-offline-corpus-v1" or data.get("source_commit") != CORPUS_COMMIT
            or len(records) != 95 or len(names) != 95 or data.get("file_count") != 95
            or data.get("lesson_count") != 806 or data.get("subject_count") != 7 or data.get("subject_grade_count") != 8
            or names != {p.name for p in (corpus / "files").glob("*_data.json")}):
        raise ValueError("Pinned Lesson3 corpus inventory/count mismatch")
    checksums(corpus, required=["MANIFEST.json", "taxonomy.tsv", *("files/" + name for name in names)])
    lesson_count = 0
    for item in records:
        if PurePosixPath(item["file"]).name != item["file"]:
            raise ValueError("Invalid corpus filename")
        path = corpus / "files" / item["file"]
        document = json.loads(path.read_text(encoding="utf-8"))
        lessons = document.get("LESSONS")
        if (document.get("schemaVersion") != "1.0.0" or not isinstance(document.get("META"), dict)
                or not isinstance(lessons, list) or len(lessons) != item["lessons"]
                or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]):
            raise ValueError("Malformed or changed Lesson3 corpus content")
        lesson_count += len(lessons)
    if lesson_count != 806:
        raise ValueError("Lesson3 lesson count mismatch")

    tsavo = root / "tsavo"
    covered = checksums(tsavo, required=["MANIFEST.json", "tsavo_content.py"])
    helper = load_helper("tsavo_validation", tsavo / "tsavo_content.py")
    manifest = helper.read_manifest(tsavo / "MANIFEST.json")
    if not {"payload/" + item["path"] for item in manifest["files"]} <= covered:
        raise ValueError("Incomplete TsavoTrust component checksum coverage")
    helper.validate(tsavo / "payload", manifest)

    tail = root / "remote-access/tailscale"
    tail_name = "tailscale_1.104.1_amd64.tgz"
    checksums(tail, required=[tail_name])
    with archive(tail / tail_name) as bundle:
        for name in ("tailscale", "tailscaled"):
            matches = [m for m in bundle.getmembers() if m.isfile() and PurePosixPath(m.name).name == name]
            if len(matches) != 1 or not matches[0].mode & 0o111:
                raise ValueError("Tailscale binary missing/nonexecutable")
            if bundle.extractfile(matches[0]).read(6) != b"\x7fELF\x02\x01":
                raise ValueError("Malformed Tailscale binary")
    tiger = root / "remote-access/tigervnc"
    files = sorted(tiger.glob("*.deb"))
    if len(files) != 4:
        raise ValueError("TigerVNC package set incomplete")
    checksums(tiger, required=[p.name for p in files])
    packages = {}
    for path in files:
        result = subprocess.run(["dpkg-deb", "--show", "--showformat=${Package}\t${Version}\t${Architecture}", str(path)],
                                capture_output=True, text=True, check=True)
        name, value, arch = result.stdout.strip().split("\t")
        if name in packages or arch not in ("all", "amd64"):
            raise ValueError("Invalid TigerVNC package identity")
        packages[name] = value
    if packages != DEBS:
        raise ValueError("TigerVNC package versions do not match pins")
    print("PASS: APK, Lesson3 release/images/corpus, TsavoTrust, Tailscale and TigerVNC component checks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("components")
    verify.add_argument("root", type=Path)
    verify.add_argument("profile", choices=("production", "test"))
    verify.add_argument("version")
    package = sub.add_parser("package")
    package.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.command == "components":
        verify_components(args.root, args.profile, args.version)
    else:
        try:
            verify_package(args.root)
        except (ValueError, OSError) as error:
            parser.exit(1, "Package check failed: " + str(error) + "\n"
                        "Copy the complete ZIP again and extract it into a new folder.\n")
