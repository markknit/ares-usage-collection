import copy
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import test_profiles as profiles
import test_tsavo_content as tsavo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("package_integrity", ROOT / "offline-installer/tools/package_integrity.py")
integrity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity)
sys.modules["package_integrity"] = integrity


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode() if isinstance(value, str) else value)
    return path


def manifest(root, name="SHA256SUMS", files=None):
    files = files if files is not None else [p for p in root.rglob("*") if p.is_file() and p != root / name]
    (root / name).write_text("".join(integrity.digest(p) + "  " + p.relative_to(root).as_posix() + "\n" for p in sorted(files)), encoding="utf-8", newline="\n")


def archive(path, files):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as output:
        for name, value in files.items():
            value = value.encode() if isinstance(value, str) else value
            info = tarfile.TarInfo(name)
            info.size = len(value)
            info.mode = 0o755
            output.addfile(info, io.BytesIO(value))


def package(root, profile="production"):
    teacher = root / "teacher-app"
    teacher.mkdir(parents=True)
    alias = profiles.render.ALIASES[profile]
    with profiles.zipfile.ZipFile(teacher / "ares-sync.apk", "w") as z:
        z.writestr("classes.dex", b"\0".join(("http://" + alias + "/tracker/" + n).encode()
                                             for n in ("prepare_due_usage_upload.php", "collection_schedule.json")))
        z.writestr("res/8G.xml", profiles.compiled_policy(alias))
        z.writestr("AndroidManifest.xml", profiles.compiled_strings("org.areseducation.sync" + (".test" if profile == "test" else "")))
    manifest(teacher, "ares-sync.apk.sha256", [teacher / "ares-sync.apk"])
    write(teacher, "APPROVAL.json", json.dumps({"profile": profile, "app_id": "org.areseducation.sync" + (".test" if profile == "test" else ""),
                                             "sha256": integrity.digest(teacher / "ares-sync.apk")}))
    shutil.copyfile(ROOT / "offline-installer/tools/render_profile.py", teacher / "verify_profile.py")
    manifest(teacher)
    payload = root / "lesson_plan/payload"
    for name in ("index.htmlf", "index.html", "index_bu.htmlf", "ARES-Logo.png", "PDF/index.html", "generate_teacher_index.js", "LESSON3_USER_GUIDE.pdf"):
        write(payload, name, "fixture")
    manifest(payload)
    rollout = root / "ARES_Sync_Rollout_Package"
    for name in ("update_school_server.sh", "ares_set_school_code.sh"):
        write(rollout, "server-installer/" + name, "fixture")
    manifest(rollout, "SHA256SUMS.txt")
    release = root / "lesson3/release"
    exact = "example/image:v0.94@sha256:" + "a" * 64
    archive(release / "lesson3-online-deploy.tar.gz", {"lesson3-deploy/VERSION": "v0.94\n", "lesson3-deploy/compose.yaml": "services:\n  app:\n    image: " + exact + "\n"})
    manifest(release, "lesson3-online-deploy.tar.gz.sha256")
    images = root / "lesson3/images"
    config = b'{"architecture":"amd64","os":"linux"}'
    identity = hashlib.sha256(config).hexdigest()
    archive(images / "lesson3-v0.94-amd64-images.tar.gz", {"manifest.json": json.dumps([
        {"Config": identity + ".json", "RepoTags": ["example/image:v0.94"], "Layers": ["layer.tar"]}]), identity + ".json": config, "layer.tar": b"fixture"})
    write(images, "IMAGE_REFS.txt", exact + "\texample/image:v0.94\tsha256:" + identity + "\n")
    manifest(images)
    corpus = root / "lesson3/corpus"
    records = []
    for i in range(95):
        value = json.dumps({"schemaVersion": "1.0.0", "META": {}, "LESSONS": [{}] * (9 if i < 46 else 8)})
        path = write(corpus, f"files/Plan{i}_data.json", value)
        records.append({"file": path.name, "sha256": integrity.digest(path), "bytes": path.stat().st_size, "lessons": 9 if i < 46 else 8})
    write(corpus, "MANIFEST.json", json.dumps({"format": "ares-lesson3-offline-corpus-v1", "source_commit": integrity.CORPUS_COMMIT,
          "file_count": 95, "lesson_count": 806, "subject_count": 7, "subject_grade_count": 8, "files": records}))
    write(corpus, "taxonomy.tsv", "fixture\t10\n")
    manifest(corpus)
    tsavo_dir = root / "tsavo"
    (tsavo_dir / "payload").mkdir(parents=True)
    content = tsavo.TsavoContentTests().fixture(tsavo_dir / "payload")
    content.update(tracking_key="module:TsavoTrust", display_name="Tsavo Trust")
    write(tsavo_dir, "MANIFEST.json", json.dumps(content))
    shutil.copyfile(ROOT / "offline-installer/tools/tsavo_content.py", tsavo_dir / "tsavo_content.py")
    manifest(tsavo_dir)
    tail = root / "remote-access/tailscale"
    archive(tail / "tailscale_1.104.1_amd64.tgz", {"tailscale/tailscale": b"\x7fELF\x02\x01fixture", "tailscale/tailscaled": b"\x7fELF\x02\x01fixture"})
    manifest(tail)
    tiger = root / "remote-access/tigervnc"
    for name in integrity.DEBS:
        write(tiger, name + ".deb", b"!<arch>\nfixture")
    manifest(tiger)
    return root


def deb_query(cmd, **kwargs):
    # Windows lacks dpkg-deb; only its metadata query is substituted. All hashes,
    # archives, APK policy and corpus validation execute normally.
    assert cmd[0] == "dpkg-deb"
    name = Path(cmd[-1]).stem
    return subprocess.CompletedProcess(cmd, 0, name + "\t" + integrity.DEBS[name] + "\tamd64", "")


class PackageIntegrityTests(unittest.TestCase):
    def test_docker_shared_layers_accept_internal_symlinks_and_hard_links(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = package(Path(temp))
                images = root / "lesson3/images"
                path = images / "lesson3-v0.94-amd64-images.tar.gz"
                # Preserve the fixture's manifest, config identity and layer bytes;
                # change only how Docker save represents the shared layer.
                with tarfile.open(path, "r:gz") as original:
                    files = {m.name: original.extractfile(m).read() for m in original.getmembers()}
                data = json.loads(files["manifest.json"])
                data[0]["Layers"] = ["image/layer.tar"]
                files["manifest.json"] = json.dumps(data).encode()
                files["blobs/shared.tar"] = files.pop("layer.tar")
                # Reopen uncompressed members through a new gzipped TAR so this
                # models real TAR links, not filesystem link privileges.
                with tarfile.open(path, "w:gz") as saved:
                    for name, value in files.items():
                        info = tarfile.TarInfo(name)
                        info.size = len(value)
                        saved.addfile(info, io.BytesIO(value))
                    link = tarfile.TarInfo("image/layer.tar")
                    link.type = kind
                    link.linkname = "../blobs/shared.tar" if kind == tarfile.SYMTYPE else "blobs/shared.tar"
                    saved.addfile(link)
                manifest(images)
                with patch.object(integrity.subprocess, "run", side_effect=deb_query):
                    integrity.verify_components(root, "production", "v0.94")

    def test_image_links_reject_escape_missing_cycle_and_special_entries(self):
        for target in ("../../outside", "/outside", "missing.tar", "image/layer.tar"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "images.tar.gz"
                with tarfile.open(path, "w:gz") as saved:
                    link = tarfile.TarInfo("image/layer.tar")
                    link.type = tarfile.LNKTYPE
                    link.linkname = target
                    saved.addfile(link)
                with self.assertRaises(ValueError):
                    integrity.archive(path, allow_image_links=True)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "images.tar.gz"
            with tarfile.open(path, "w:gz") as saved:
                entry = tarfile.TarInfo("device")
                entry.type = tarfile.CHRTYPE
                saved.addfile(entry)
            with self.assertRaises(ValueError):
                integrity.archive(path, allow_image_links=True)

    def test_other_payload_archives_still_reject_links(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "release.tar.gz"
            archive(path, {"target": b"fixture"})
            # A valid Docker-style link is still unexpected in release payloads.
            with tarfile.open(path, "w:gz") as saved:
                link = tarfile.TarInfo("link")
                link.type = tarfile.SYMTYPE
                link.linkname = "target"
                saved.addfile(link)
            with self.assertRaises(ValueError):
                integrity.archive(path)

    def test_both_profiles_validate_independent_components(self):
        for profile in ("production", "test"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temp:
                root = package(Path(temp), profile)
                with patch.object(integrity.subprocess, "run", side_effect=deb_query):
                    integrity.verify_components(root, profile, "v0.94")

    def test_each_component_hash_remains_enforced(self):
        names = ["teacher-app/ares-sync.apk", "lesson3/release/lesson3-online-deploy.tar.gz",
                 "lesson3/images/lesson3-v0.94-amd64-images.tar.gz", "lesson3/corpus/files/Plan0_data.json",
                 "tsavo/payload/tsavo_trust_logo.jpg", "remote-access/tailscale/tailscale_1.104.1_amd64.tgz",
                 "remote-access/tigervnc/tigervnc-tools.deb", "lesson_plan/payload/index.htmlf"]
        with tempfile.TemporaryDirectory() as temp:
            root = package(Path(temp))
            for name in names:
                with self.subTest(component=name):
                    path = root / name
                    original = path.read_bytes()
                    path.write_bytes(original + b"tampered")
                    with patch.object(integrity.subprocess, "run", side_effect=deb_query), self.assertRaises(ValueError):
                        integrity.verify_components(root, "production", "v0.94")
                    path.write_bytes(original)

    def test_missing_files_and_component_manifests_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = package(Path(temp))
            for name in ("teacher-app/ares-sync.apk", "lesson3/images/SHA256SUMS", "tsavo/SHA256SUMS", "remote-access/tailscale/SHA256SUMS"):
                path = root / name
                original = path.read_bytes()
                path.unlink()
                with patch.object(integrity.subprocess, "run", side_effect=deb_query), self.assertRaises((ValueError, FileNotFoundError)):
                    integrity.verify_components(root, "production", "v0.94")
                path.write_bytes(original)

    def test_lfs_pointer_and_malformed_payload_fail_even_if_local_hash_is_updated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = package(Path(temp))
            path = root / "teacher-app/ares-sync.apk"
            original = path.read_bytes()
            path.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:fake\nsize 1\n")
            manifest(path.parent, "ares-sync.apk.sha256", [path])
            with self.assertRaisesRegex(ValueError, "LFS"):
                integrity.verify_components(root, "production", "v0.94")
            path.write_bytes(original)
            manifest(path.parent, "ares-sync.apk.sha256", [path])
            release = root / "lesson3/release"
            archive(release / "lesson3-online-deploy.tar.gz", {"wrong-file": "not a Lesson3 release"})
            manifest(release, "lesson3-online-deploy.tar.gz.sha256")
            with self.assertRaises((ValueError, KeyError)):
                integrity.verify_components(root, "production", "v0.94")

    def test_whole_package_rejects_changed_missing_and_unlisted_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write(root, "payload/video.mp4", b"fixture")
            manifest(root)
            integrity.verify_package(root)
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                integrity.verify_package(root)
            path.unlink()
            with self.assertRaises(ValueError):
                integrity.verify_package(root)
            path.write_bytes(b"fixture")
            extra = write(root, "extra.sh", "unexpected")
            with self.assertRaisesRegex(ValueError, "inventory"):
                integrity.verify_package(root)
            extra.unlink()
            integrity.verify_package(root)

    def test_whole_package_rejects_scaffolds_and_lfs_pointers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write(root, "NOT_FIELD_READY.txt", "fixture")
            manifest(root)
            with self.assertRaisesRegex(ValueError, "scaffold"):
                integrity.verify_package(root)
            path.unlink()
            write(root, "payload.bin", "version https://git-lfs.github.com/spec/v1\n")
            manifest(root)
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                integrity.verify_package(root)


if __name__ == "__main__":
    unittest.main()
