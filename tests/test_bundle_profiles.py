"""Scaffold builds exercise real packaging/checksum logic with only rsync adapted on Windows.

These tests do not exercise a clean Ubuntu installation or real payloads.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_profiles import BASH, BUILDER


class BundleProfileTests(unittest.TestCase):
    def test_two_scaffolds_seal_urls_exclude_wrappers_and_verify_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            payload = source / "lesson_plan/payload"
            payload.mkdir(parents=True)
            for name in ("index.htmlf", "index.html", "index_bu.htmlf", "ARES-Logo.png", "generate_teacher_index.js", "PDF/index.html"):
                path = payload / name
                path.parent.mkdir(exist_ok=True)
                path.write_text("http://ares.local/fixture\n", encoding="utf-8")
            for name in ("install_offline_no_sha_checks.sh", "tsavo_trust_module_install.sh"):
                (source / name).write_text("exit 99\n")
            shim = root / "bin"
            shim.mkdir()
            # Git Bash ships coreutils but no rsync or python3 on this Windows host.
            # Keep all real builder behavior except this source-copy adapter.
            if os.name == "nt":
                copier = shim / "copy.py"
                copier.write_text('''import shutil, sys
from pathlib import Path
src, dst = map(Path, sys.argv[-2:])
excluded = {arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--exclude=")}
shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*excluded))
''')
                (shim / "python3").write_text('#!/bin/bash\nexec "' + Path(sys.executable).as_posix() + '" "$@"\n', newline="\n")
                (shim / "rsync").write_text('#!/bin/bash\nexec "' + Path(sys.executable).as_posix() + '" "' + copier.as_posix() + '" "$@"\n', newline="\n")
            for path in shim.iterdir():
                path.chmod(0o755)
            for profile, alias in (("production", "ares.local"), ("test", "ares-test.local")):
                output = root / profile
                script = 'export PATH="$(cygpath -u "$1"):$PATH"; shift; exec bash "$@"' if os.name == "nt" else 'export PATH="$1:$PATH"; shift; exec bash "$@"'
                result = subprocess.run([BASH, "-c", script, "test", shim.as_posix(),
                                         (BUILDER / "build_offline_bundle.sh").as_posix(), "--source", source.as_posix(),
                                         "--output", output.as_posix(), "--profile", profile, "--scaffold-only"],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                stage = next(path for path in output.iterdir() if path.is_dir())
                self.assertTrue((stage / "NOT_FIELD_READY.txt").exists())
                if profile == "test":
                    self.assertNotIn("ares.local", (stage / "lesson_plan/payload/index.htmlf").read_text(encoding="utf-8"))
                self.assertIn(alias, (stage / "teacher-app/install-page.html").read_text(encoding="utf-8"))
                for name in ("install_offline_no_sha_checks.sh", "tsavo_trust_module_install.sh"):
                    self.assertFalse((stage / name).exists())
                for line in (stage / "SHA256SUMS").read_text().splitlines():
                    digest, name = line.split(maxsplit=1)
                    self.assertEqual(digest, hashlib.sha256((stage / name.lstrip("*")).read_bytes()).hexdigest(), name)
                # Tampering must fail actual sha256sum verification.
                with (stage / "package.conf").open("a") as stream:
                    stream.write("# tampered\n")
                result = subprocess.run([BASH, "-c", 'cd "$1"; sha256sum -c SHA256SUMS', "test", stage.as_posix()], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
