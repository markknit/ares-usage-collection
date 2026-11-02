"""Fresh ZIP extraction and release checks with tiny offline payload fixtures."""
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import test_package_integrity as fixtures
from test_profiles import BUILDER
from test_tsavo_content import content

spec = importlib.util.spec_from_file_location("verify_bundle", BUILDER / "verify_offline_bundle.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class VerifyBundleTests(unittest.TestCase):
    def test_zip_rejects_traversal_duplicates_symlinks_and_other_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            bundle = "bundle"
            for name, link, duplicate in (("bundle/../outside", False, False),
                                          ("other/file", False, False),
                                          ("bundle/link", True, False),
                                          ("bundle/file", False, True)):
                with self.subTest(name=name, duplicate=duplicate):
                    archive = base / "candidate.zip"
                    with zipfile.ZipFile(archive, "w") as output:
                        entry = zipfile.ZipInfo(name)
                        entry.external_attr = (stat.S_IFLNK | 0o777) << 16 if link else (stat.S_IFREG | 0o644) << 16
                        output.writestr(entry, "fixture")
                        if duplicate:
                            import warnings
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", UserWarning)
                                output.writestr(name, "duplicate")
                    with self.assertRaises(ValueError):
                        verifier.extract(archive, base / "extract", bundle)
                    self.assertFalse((base / "extract").exists())

    def test_fresh_extraction_validates_both_profiles_and_rejects_wrong_apk(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            builder = base / "builder"
            shutil.copytree(BUILDER, builder)
            for profile in ("production", "test"):
                with self.subTest(profile=profile):
                    bundle = "ARES_Q4_Offline_v0.94_amd64_v1.13" + ("_test" if profile == "test" else "")
                    root = fixtures.package(base / profile / bundle, profile)
                    for target, reviewed in verifier.REVIEWED.items():
                        fixtures.write(root, target, (BUILDER / reviewed).read_bytes().replace(b"\r\n", b"\n"))
                    for target, approved in verifier.APPROVED_ADMIN_CONTENT.items():
                        fixtures.write(root, target, (BUILDER / approved).read_bytes())
                    for target, approved in verifier.APPROVED_LOCKDOWN_CONTENT.items():
                        fixtures.write(root, target, (BUILDER / approved).read_bytes())
                    fixtures.write(root, "package.conf", f"LESSON3_VERSION=v0.94\nLESSON3_SERVER_URL=\nARES_PROFILE={profile}\n")
                    alias = "ares-test.local" if profile == "test" else "ares.local"
                    fixtures.write(root, "MANIFEST.txt", f"Lesson3: v0.94\nOffline bundle revision: v1.13\nProfile: {profile} ({alias})\nTarget architecture: linux/amd64\n")
                    source = base / (profile + "-tsavo")
                    source.mkdir()
                    pin = fixtures.tsavo.TsavoContentTests().fixture(source)
                    pin_path = builder / "manifests/tsavo-trust-source.json"
                    pin_path.write_text(json.dumps(pin), encoding="utf-8")
                    shutil.rmtree(root / "tsavo/payload")
                    prepared = content.prepare(source, root / "tsavo/payload", pin_path)
                    fixtures.write(root, "tsavo/MANIFEST.json", json.dumps(prepared))
                    # Re-seal only fixture components whose scripts/helpers changed.
                    for name in ("teacher-app", "tsavo"):
                        fixtures.manifest(root / name)
                    fixtures.manifest(root)
                    archive = base / (profile + ".zip")
                    with zipfile.ZipFile(archive, "w") as output:
                        for path in root.rglob("*"):
                            if path.is_file():
                                output.write(path, path.relative_to(root.parent))
                    real_run = subprocess.run
                    def query(cmd, **kwargs):
                        return fixtures.deb_query(cmd, **kwargs) if cmd[0] == "dpkg-deb" else real_run(cmd, **kwargs)
                    with patch.object(verifier, "SELF", builder), patch.object(verifier.integrity.subprocess, "run", side_effect=query):
                        verifier.verify(archive, profile, fixtures.integrity.digest(root / "teacher-app/ares-sync.apk"))
                        with self.assertRaisesRegex(ValueError, "approved hash"):
                            verifier.verify(archive, profile, "0" * 64)
                    self.assertEqual(list(base.glob(".ares-verify-*")), [])


if __name__ == "__main__":
    unittest.main()
