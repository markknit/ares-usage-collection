"""Real filesystem transaction tests; Windows substitutes OS symlink operations.

Ubuntu CI additionally runs native symlink checks. No test is live acceptance.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import test_tsavo_content as fixtures

ROOT, content = fixtures.ROOT, fixtures.content

sys.modules["tsavo_content"] = content
spec = importlib.util.spec_from_file_location("tsavo_install", ROOT / "offline-installer/tools/tsavo_install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class TsavoInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "root"
        self.package = self.base / "package"
        self.package.mkdir()
        self.payload = self.package / "payload"
        self.payload.mkdir()
        self.manifest = fixtures.TsavoContentTests().fixture(self.payload)
        self.manifest.update(tracking_key=installer.KEY, display_name=installer.LABEL)
        (self.package / "MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        self.target, self.link, self.keymap = installer.paths(self.root)
        for path in (self.target, self.link, self.keymap):
            path.parent.mkdir(parents=True, exist_ok=True)
        self.original = b'key,display_name,\r\nmodule:OlpejetaConservancy,OPC,\r\ncustom,Keep exactly,\r\n'
        self.keymap.write_bytes(self.original)
        if os.name == "nt":
            # The Windows account cannot create native symbolic links. Substitute
            # only their creation/inspection; copy, rename, backup and rollback
            # operations still run against the real filesystem.
            self.addCleanup(patch.stopall)
            patch.object(Path, "symlink_to", lambda path, target, **kw: path.write_text(str(target))).start()
            def verify(package, root, manifest=None):
                target, link, keymap = installer.paths(root)
                content.validate(target, manifest or self.manifest)
                if link.read_text() != str(target) or installer.mapping_bytes(keymap.read_bytes()) != keymap.read_bytes():
                    raise ValueError("fixture link or mapping mismatch")
            patch.object(installer, "verify_installed", verify).start()

    def test_clean_install_repeat_and_historical_mapping_preserved(self):
        installer.install(self.package, self.root)
        self.assertEqual(self.keymap.read_bytes(), self.original + b'module:TsavoTrust,Tsavo Trust,\r\n')
        installer.install(self.package, self.root)
        self.assertEqual(self.keymap.read_bytes().count(b"module:TsavoTrust,"), 1)
        installer.verify_installed(self.package, self.root)
        self.assertTrue(list(self.target.parent.glob(".TsavoTrust.tsavo-backup-*")))
        self.assertFalse(list(self.target.parent.glob("TsavoTrust.tsavo-backup-*")))

    def test_existing_module_and_portal_directory_backed_up(self):
        self.target.mkdir()
        (self.target / "old.txt").write_text("old content")
        self.link.mkdir()
        (self.link / "portal.txt").write_text("old portal")
        backups = installer.install(self.package, self.root)
        self.assertEqual(len(backups), 3)
        self.assertTrue(any((Path(p) / "old.txt").is_file() for p in backups))
        self.assertTrue(any((Path(p) / "portal.txt").is_file() for p in backups))

    def test_post_publish_failure_restores_all_original_objects(self):
        self.target.mkdir()
        (self.target / "old.txt").write_text("old content")
        self.link.mkdir()
        (self.link / "portal.txt").write_text("old portal")
        def failure(manifest):
            raise ValueError("injected HTTP verification failure")
        with self.assertRaisesRegex(ValueError, "injected"):
            installer.install(self.package, self.root, after_publish=failure)
        self.assertEqual((self.target / "old.txt").read_text(), "old content")
        self.assertEqual((self.link / "portal.txt").read_text(), "old portal")
        self.assertEqual(self.keymap.read_bytes(), self.original)

    def test_publish_failure_restores_prior_module_and_map(self):
        self.target.mkdir()
        (self.target / "old.txt").write_text("old content")
        original_rename = Path.rename
        def failing_rename(path, dest):
            if path.name.startswith(".tsavo-keymap-") and Path(dest) == self.keymap:
                raise OSError("injected mapping publish failure")
            return original_rename(path, dest)
        with patch.object(Path, "rename", failing_rename), self.assertRaisesRegex(OSError, "injected"):
            installer.install(self.package, self.root)
        self.assertEqual((self.target / "old.txt").read_text(), "old content")
        self.assertEqual(self.keymap.read_bytes(), self.original)
        self.assertFalse(os.path.lexists(self.link))

    def test_interruption_immediately_after_backup_rename_restores_original(self):
        self.target.mkdir()
        (self.target / "old.txt").write_text("old content")
        original_rename = Path.rename
        def interrupted_rename(path, dest):
            result = original_rename(path, dest)
            if path == self.target and ".tsavo-backup-" in Path(dest).name:
                raise KeyboardInterrupt("injected between rename and next statement")
            return result
        with patch.object(Path, "rename", interrupted_rename), self.assertRaises(KeyboardInterrupt):
            installer.install(self.package, self.root)
        self.assertEqual((self.target / "old.txt").read_text(), "old content")
        self.assertEqual(self.keymap.read_bytes(), self.original)

    def test_first_install_failure_removes_new_installation(self):
        with self.assertRaises(ValueError):
            installer.install(self.package, self.root, after_publish=lambda m: (_ for _ in ()).throw(ValueError("failure")))
        self.assertFalse(os.path.lexists(self.target))
        self.assertFalse(os.path.lexists(self.link))
        self.assertEqual(self.keymap.read_bytes(), self.original)

    def test_copy_failure_leaves_existing_content_and_map_untouched(self):
        self.target.mkdir()
        (self.target / "old.txt").write_text("old")
        with patch.object(installer.shutil, "copytree", side_effect=OSError("copy failed")):
            with self.assertRaisesRegex(OSError, "copy failed"):
                installer.install(self.package, self.root)
        self.assertEqual((self.target / "old.txt").read_text(), "old")
        self.assertEqual(self.keymap.read_bytes(), self.original)
        self.assertFalse(list(self.target.parent.glob(".tsavo-stage-*")))

    def test_insufficient_space_fails_before_staging(self):
        from collections import namedtuple
        usage = namedtuple("Usage", "total used free")(100, 99, 1)
        with patch.object(installer.shutil, "disk_usage", return_value=usage):
            with self.assertRaisesRegex(ValueError, "Insufficient"):
                installer.install(self.package, self.root)
        self.assertFalse(list(self.target.parent.glob(".tsavo-stage-*")))
        self.assertEqual(self.keymap.read_bytes(), self.original)

    def test_new_mapping_entries_added_during_staging_are_not_overwritten(self):
        original_link = Path.symlink_to
        changed = self.original + b"module:AnotherNewModule,Preserve me,\r\n"
        def changed_during_staging(path, target, **kwargs):
            self.keymap.write_bytes(changed)
            return original_link(path, target, **kwargs)
        with patch.object(Path, "symlink_to", changed_during_staging):
            with self.assertRaisesRegex(ValueError, "changed during staging"):
                installer.install(self.package, self.root)
        self.assertEqual(self.keymap.read_bytes(), changed)
        self.assertFalse(os.path.lexists(self.target))

    def test_preflight_tamper_and_conflicting_mapping_do_not_mutate(self):
        for original in (self.original + b"module:TsavoTrust,Wrong,\n",
                         self.original + b"module:TsavoTrust,Tsavo Trust,\n" * 2):
            self.keymap.write_bytes(original)
            with self.assertRaises(ValueError):
                installer.install(self.package, self.root)
            self.assertEqual(self.keymap.read_bytes(), original)
            self.assertFalse(os.path.lexists(self.target))
            self.assertFalse(list(self.target.parent.glob(".tsavo-stage-*")))
        self.keymap.write_bytes(self.original)
        (self.payload / "tsavo_trust_logo.jpg").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            installer.install(self.package, self.root)
        self.assertEqual(self.keymap.read_bytes(), self.original)

    def test_script_relative_preflight_from_another_working_directory(self):
        import shutil
        import subprocess
        for name in ("tsavo_content.py", "tsavo_install.py"):
            shutil.copyfile(ROOT / "offline-installer/tools" / name, self.package / name)
        result = subprocess.run([sys.executable, "-B", str(self.package / "tsavo_install.py"),
                                 "--root", str(self.root), "--check"], cwd=self.base,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(os.path.lexists(self.target))

    def test_http_ranges_and_portal_for_both_profiles_and_failure_responses(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        from urllib.parse import unquote
        owner = self
        state = {"bad_range": False, "bad_portal": False, "hosts": []}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                state["hosts"].append(self.headers["Host"])
                if self.path == "/www2/index.php":
                    data = b"missing" if state["bad_portal"] else b'<script data-module-id="TsavoTrust"></script>'
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(data)
                    return
                name = unquote(self.path.split("/TsavoTrust/", 1)[1])
                data = (owner.payload / name).read_bytes()
                ranged = name.endswith(".mp4")
                self.send_response(200 if not ranged or state["bad_range"] else 206)
                if ranged:
                    self.send_header("Content-Range", f"bytes 0-31/{len(data)}")
                self.end_headers()
                self.wfile.write(data[:32] if ranged else data)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.05), daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            for host in ("ares.local", "ares-test.local"):
                installer.verify_http(self.manifest, host, origin)
                self.assertEqual(state["hosts"][-1], host)
            for fault in ("bad_range", "bad_portal"):
                state[fault] = True
                with self.assertRaises(ValueError):
                    installer.verify_http(self.manifest, "ares.local", origin)
                state[fault] = False
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    @unittest.skipIf(os.name == "nt", "Native POSIX symlinks require Linux; Windows uses transaction fixtures")
    def test_existing_wrong_or_broken_links_preserved_on_failure(self):
        self.link.symlink_to(self.base / "missing", target_is_directory=True)
        self.target.symlink_to(self.base / "also-missing", target_is_directory=True)
        with self.assertRaises(ValueError):
            installer.install(self.package, self.root, after_publish=lambda m: (_ for _ in ()).throw(ValueError("failure")))
        self.assertEqual(os.readlink(self.link), str(self.base / "missing"))
        self.assertEqual(os.readlink(self.target), str(self.base / "also-missing"))


if __name__ == "__main__":
    unittest.main()
