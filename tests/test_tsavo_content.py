import copy
import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tsavo_content", ROOT / "offline-installer/tools/tsavo_content.py")
content = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content)
PIN = ROOT / "offline-installer/manifests/tsavo-trust-source.json"


def box(kind, value):
    return struct.pack(">I4s", len(value) + 8, kind) + value


class TsavoContentTests(unittest.TestCase):
    def fixture(self, root):
        manifest = copy.deepcopy(content.read_manifest(PIN))
        names = [item["path"] for item in manifest["files"]]
        for item in manifest["files"]:
            path = root / item["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.name == "index.htmlf":
                value = ('<img alt="Ol Pejeta Conservancy"><h3>Presented vy Tsavo Trust</h3>'
                         '<script data-module-id="olpejetaconservancy_index"></script>\n'
                         + "\n".join('<a href="<?php echo $dir ?>/' + name + '">link</a>'
                                     for name in names if name != "index.htmlf")).encode()
            elif path.suffix == ".mp4":
                stsd = box(b"stsd", b"\0" * 4 + struct.pack(">I", 2)
                           + box(b"avc1", b"") + box(b"mp4a", b""))
                value = box(b"ftyp", b"isom") + box(b"mdat", b"fixture") + box(b"moov", stsd)
            else:
                value = b"fixture jpg"
            path.write_bytes(value)
            item.update(bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
        return manifest

    def test_pinned_manifest_has_exact_inventory(self):
        manifest = content.read_manifest(PIN)
        self.assertEqual(len(manifest["files"]), 8)
        self.assertEqual(sum(p["path"].endswith(".mp4") for p in manifest["files"]), 6)

    def test_normalized_content_and_build_media_inspection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.fixture(root)
            content.validate(root, manifest, inspect_media=True)

    def test_missing_extra_and_tampered_content_rejected(self):
        for fault in ("missing", "extra", "tampered", "nested"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest = self.fixture(root)
                if fault == "missing":
                    (root / "tsavo_trust_logo.jpg").unlink()
                elif fault == "extra":
                    (root / "unreviewed.txt").write_text("unexpected")
                elif fault == "tampered":
                    (root / "tsavo_trust_logo.jpg").write_bytes(b"wrong bytes")
                else:
                    (root / "Videos").rename(root / "TsavoTrust")
                with self.assertRaises(ValueError):
                    content.validate(root, manifest)

    def test_wrong_reference_rejected_even_when_page_hash_matches(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self.fixture(root)
            page = root / "index.htmlf"
            value = page.read_bytes().replace(b"Videos/", b"Nested/", 1)
            page.write_bytes(value)
            manifest["files"][0].update(bytes=len(value), sha256=hashlib.sha256(value).hexdigest())
            with self.assertRaisesRegex(ValueError, "reference"):
                content.validate(root, manifest)

    def test_invalid_media_rejected_by_build_inspection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.mp4"
            for value in (b"not an MP4", box(b"ftyp", b"isom"), struct.pack(">I4s", 9999, b"moov")):
                path.write_bytes(value)
                with self.assertRaises(ValueError):
                    content.mp4_sample_types(path)

    def test_prepare_corrects_page_without_changing_media_or_external_input(self):
        import json
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "source"
            root.mkdir()
            manifest = self.fixture(root)
            pin = base / "pin.json"
            pin.write_text(json.dumps(manifest), encoding="utf-8")
            original = (root / "index.htmlf").read_bytes()
            result = content.prepare(root, base / "output", pin)
            content.validate(base / "output", result, inspect_media=True)
            self.assertEqual((root / "index.htmlf").read_bytes(), original)
            page = (base / "output/index.htmlf").read_text()
            self.assertIn('data-module-id="TsavoTrust"', page)
            self.assertIn("Presented by", page)
            self.assertNotIn("Ol Pejeta", page)
            self.assertEqual(manifest["files"][1:], result["files"][1:])


if __name__ == "__main__":
    unittest.main()
