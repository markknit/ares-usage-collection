"""Repackage disposable payloads; no Docker, installer or network operations."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import test_package_integrity as fixtures

spec = importlib.util.spec_from_file_location("repackage_v113", fixtures.ROOT / "offline-installer/repackage_verified_v113.py")
repack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repack)


class RepackageTests(unittest.TestCase):
    def fixture(self, root):
        package = fixtures.package(root / "base" / repack.BUNDLE)
        pin = package / "tsavo/MANIFEST.json"
        document = json.loads(pin.read_text())
        document["source_manifest_sha256"] = fixtures.integrity.digest(repack.SELF / "manifests/tsavo-trust-source.json")
        pin.write_text(json.dumps(document), encoding="utf-8")
        fixtures.manifest(package / "tsavo")
        fixtures.write(package, "MANIFEST.txt", "Lesson3: v0.94\nOffline bundle revision: v1.13\nProfile: production (ares.local)\nTarget architecture: linux/amd64\n")
        fixtures.write(package, "package.conf", "LESSON3_VERSION=v0.94\nLESSON3_SERVER_URL=\nARES_PROFILE=production\n")
        fixtures.manifest(package)
        archive = root / "base.zip"
        with zipfile.ZipFile(archive, "w") as output:
            for path in package.rglob("*"):
                if path.is_file():
                    output.write(path, path.relative_to(package.parent))
        return archive

    def test_updates_reviewed_files_preserves_base_payloads_and_verifies_before_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.fixture(root)
            original_hash = fixtures.integrity.digest(archive)
            output = root / "corrected"
            calls = []
            def verify(candidate, profile, apk_hash):
                self.assertFalse((output / (repack.BUNDLE + ".zip")).exists())
                self.assertTrue((output / "BUILD_INCOMPLETE").exists())
                extracted = root / "independent"
                repack.verifier.extract(candidate, extracted, repack.BUNDLE)
                stage = extracted / repack.BUNDLE
                fixtures.integrity.verify_package(stage)
                fixtures.integrity.checksums(stage / "teacher-app")
                fixtures.integrity.checksums(stage / "tsavo")
                for target, source in repack.verifier.APPROVED_ADMIN_CONTENT.items():
                    self.assertEqual((stage / target).read_bytes(), (repack.SELF / source).read_bytes())
                for target, source in repack.verifier.APPROVED_LOCKDOWN_CONTENT.items():
                    self.assertEqual((stage / target).read_bytes(), (repack.SELF / source).read_bytes())
                calls.append(profile)
                return fixtures.integrity.digest(candidate)
            with patch.object(repack, "BASE_SHA", original_hash), patch.object(repack.verifier, "verify", side_effect=verify):
                artifact = repack.repackage(archive, output, "a" * 40)
            self.assertEqual(calls, ["production"])
            self.assertEqual(fixtures.integrity.digest(archive), original_hash)
            self.assertTrue(artifact.exists())
            self.assertFalse((output / "BUILD_INCOMPLETE").exists())
            evidence = json.loads((output / "repack-evidence.json").read_text())
            self.assertIn("teacher-app/ares-sync.apk", evidence["preserved_base_files"])
            self.assertFalse(evidence["installer_run"])
            self.assertFalse(evidence["downloads_or_docker_operations"])

    def test_failed_independent_verification_never_promotes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.fixture(root)
            output = root / "failed"
            with patch.object(repack, "BASE_SHA", fixtures.integrity.digest(archive)), \
                    patch.object(repack.verifier, "verify", side_effect=ValueError("injected independent failure")):
                with self.assertRaisesRegex(ValueError, "independent failure"):
                    repack.repackage(archive, output, "a" * 40)
            self.assertTrue((output / "BUILD_INCOMPLETE").exists())
            self.assertFalse((output / (repack.BUNDLE + ".zip")).exists())

    def test_wrong_base_or_existing_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.fixture(root)
            output = root / "output"
            with self.assertRaisesRegex(ValueError, "previously verified"):
                repack.repackage(archive, output, "a" * 40)
            self.assertFalse(output.exists())
            output.mkdir()
            with self.assertRaisesRegex(ValueError, "already exists"):
                repack.repackage(archive, output, "a" * 40)

    def test_changed_source_pin_is_rejected_before_staging(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.fixture(root)
            other = root / "other-builder"
            (other / "manifests").mkdir(parents=True)
            (other / "manifests/tsavo-trust-source.json").write_text("changed source bytes")
            output = root / "output"
            with patch.object(repack, "BASE_SHA", fixtures.integrity.digest(archive)), patch.object(repack, "SELF", other):
                with self.assertRaisesRegex(ValueError, "canonical LF"):
                    repack.repackage(archive, output, "a" * 40)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
