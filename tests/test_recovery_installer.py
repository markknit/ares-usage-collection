"""Recovery orchestration with real checksums/components and host-stage fixtures."""
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import test_package_integrity as fixtures
from test_profiles import BASH

ROOT = fixtures.ROOT
spec = importlib.util.spec_from_file_location("recovery_installer", ROOT / "offline-installer/tools/recovery_installer.py")
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class Terminal(io.StringIO):
    def fileno(self):
        return 0


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = fixtures.package(self.base / "package")
        for name in ("package_integrity.py", "recovery_installer.py"):
            shutil.copyfile(ROOT / "offline-installer/tools" / name, self.root / name)
        shutil.copyfile(ROOT / "offline-installer/templates/install_offline_no_root_sha.sh", self.root / "install_offline_no_root_sha.sh")
        # Substitute only host installation/preflight stages. The canonical root
        # check and complete component validation execute against real fixtures.
        shutil.copyfile(ROOT / "offline-installer/templates/preflight.sh", self.root / "preflight-canonical.sh")
        (self.root / "preflight.sh").write_text('''#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/preflight-canonical.sh"
preflight_main() {
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  pass() { echo "PASS $*"; }; fail() { echo "FAIL $*"; }; warn() { echo "WARN $*"; }
  check_root_manifest "$1" || return 1
  python3 "$SCRIPT_DIR/check-fixture.py" "$SCRIPT_DIR"
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then preflight_main verified "$@"; fi
''', encoding="utf-8", newline="\n")
        (self.root / "install_offline.sh").write_text('''#!/bin/bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHOOL_CODE=$1
bash "$SCRIPT_DIR/preflight.sh" "$SCHOOL_CODE"
echo HOST_INSTALL_FIXTURE_COMPLETED
''', encoding="utf-8", newline="\n")
        (self.root / "check-fixture.py").write_text('''import sys, subprocess
from pathlib import Path
import package_integrity as integrity
def deb(cmd, **kw):
    name=Path(cmd[-1]).stem
    return subprocess.CompletedProcess(cmd, 0, name+'\\t'+integrity.DEBS[name]+'\\tamd64', '')
integrity.subprocess.run=deb
integrity.verify_components(Path(sys.argv[1]), 'production', 'v0.94')
''', encoding="utf-8")
        self.bin = self.base / "bin"
        self.bin.mkdir()
        if os.name == "nt":
            # Keep subprocess invocation executable on Windows without changing
            # any production path/confirmation flag.
            (self.bin / "python3").write_text('#!/bin/bash\nexec "' + Path(sys.executable).as_posix() + '" "$@"\n', newline="\n")
        else:
            (self.bin / "python3").write_text('#!/bin/bash\nexec "' + sys.executable + '" "$@"\n', newline="\n")
        (self.bin / "python3").chmod(0o755)
        fixtures.manifest(self.root)

    def run_driver(self, recovered):
        original = subprocess.run
        def execute(cmd, *args, **kwargs):
            if cmd[0] == "bash":
                cmd = [BASH, *cmd[1:]]
                if recovered:
                    # Put the Windows python launcher in the actual Bash PATH.
                    prefix = 'export PATH="$(cygpath -u "$4"):$PATH"; ' if os.name == "nt" else 'export PATH="$4:$PATH"; '
                    cmd = [BASH, "-c", prefix + recovery.DRIVER, "recovery-test", self.root.as_posix(), "ARES-S0099", "unused", self.bin.as_posix()]
            self.last_driver = original(cmd, *args, capture_output=True, text=True, **kwargs)
            return self.last_driver
        if recovered:
            with patch.object(recovery.subprocess, "run", execute), patch('os.isatty', return_value=True):
                recovery.confirm_recovery(Terminal(recovery.CONFIRMATION + "\n"), io.StringIO())
                return recovery.run_recovery(self.root, "ARES-S0099", self.base / "receipts", self.base / "logs")
        prefix = 'export PATH="$(cygpath -u "$1"):$PATH"; ' if os.name == "nt" else 'export PATH="$1:$PATH"; '
        return original([BASH, "-c", prefix + 'bash "$2" ARES-S0099', "standard-test", str(self.bin), str(self.root / "install_offline.sh")], capture_output=True, text=True)

    def test_standard_rejects_root_mismatch_recovery_accepts_only_after_confirmation(self):
        baseline = self.run_driver(False)
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        (self.root / "operator-note.txt").write_text("deliberate authorized change")
        # A newly unlisted file is not a GNU checksum mismatch: modify a listed file.
        with (self.root / "install_offline.sh").open("a") as stream:
            stream.write("# reviewed operator modification\n")
        standard = self.run_driver(False)
        self.assertNotEqual(standard.returncode, 0)
        self.assertNotIn("HOST_INSTALL_FIXTURE_COMPLETED", standard.stdout)
        self.assertEqual(self.run_driver(True), 0, self.last_driver.stderr)
        record = json.loads(next((self.base / "receipts").glob('*.json')).read_text())
        self.assertEqual(record["root_sha256"], "intentionally_skipped")
        self.assertEqual(record["phase"], "installation_completed")
        self.assertFalse(record["fully_verified"])
        self.assertIn(recovery.WARNING, next((self.base / "logs").glob('*.log')).read_text())

    def test_component_tampering_and_missing_manifests_still_fail_recovery(self):
        for name in ("tsavo/payload/tsavo_trust_logo.jpg", "lesson3/images/SHA256SUMS", "SHA256SUMS"):
            path = self.root / name
            original = path.read_bytes()
            if path.name == "SHA256SUMS":
                path.unlink()
            else:
                path.write_bytes(original + b"tampered")
            self.assertNotEqual(self.run_driver(True), 0)
            if name == "SHA256SUMS":
                self.assertIn("root SHA256SUMS file is missing", self.last_driver.stdout)
            else:
                self.assertIn("INTENTIONALLY SKIPPED", self.last_driver.stdout)
                self.assertRegex(self.last_driver.stderr, "[Cc]omponent checksum|Missing component")
            path.write_bytes(original)

    def test_recovery_wrapper_rejects_noninteractive_and_piped_exact_confirmation(self):
        prefix = 'export PATH="$(cygpath -u "$1"):$PATH"; ' if os.name == "nt" else 'export PATH="$1:$PATH"; '
        result = subprocess.run([BASH, "-c", prefix + 'bash "$2" ARES-S0099', "test", str(self.bin), str(self.root / "install_offline_no_root_sha.sh")],
                                input=recovery.CONFIRMATION + "\n", capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("interactive terminal", result.stderr)
        self.assertFalse((self.base / "receipts").exists())

    def test_exact_confirmation_wrong_empty_and_whitespace(self):
        for text in ("", "yes\n", "INSTALL UNVERIFIED PACKAGE \n", " INSTALL UNVERIFIED PACKAGE\n"):
            with self.subTest(text=text), patch('os.isatty', return_value=True):
                with self.assertRaisesRegex(ValueError, "confirmation rejected"):
                    recovery.confirm_recovery(Terminal(text), io.StringIO())
        with patch('os.isatty', return_value=True):
            recovery.confirm_recovery(Terminal(recovery.CONFIRMATION + "\n"), io.StringIO())

    def test_public_controller_confirms_before_start_and_has_no_yes_option(self):
        for text, expected in (("wrong\n", 2), (recovery.CONFIRMATION + "\n", 0)):
            with patch.object(sys, "argv", ["recovery_installer.py", "ARES-S0099"]), \
                 patch.object(sys, "stdin", Terminal(text)), patch('os.isatty', return_value=True), \
                 patch.object(os, "geteuid", return_value=0, create=True), \
                 patch.object(recovery, "run_recovery", return_value=0) as run:
                self.assertEqual(recovery.main(), expected)
                self.assertEqual(run.called, expected == 0)
        with patch.object(sys, "argv", ["recovery_installer.py", "ARES-S0099", "--yes"]):
            with self.assertRaises(SystemExit):
                recovery.main()

    def test_normal_entry_point_and_forced_verified_preflight_contract(self):
        source = (ROOT / "offline-installer/templates/install_offline.sh").read_text(encoding="utf-8")
        self.assertEqual(source.count('bash "$SCRIPT_DIR/preflight.sh" "$SCHOOL_CODE"'), 1)
        self.assertNotIn("RECOVERY", source)
        preflight = (ROOT / "offline-installer/templates/preflight.sh").read_text(encoding="utf-8")
        self.assertIn('preflight_main verified "$@"', preflight)
        self.assertNotIn("SKIP_ROOT_SHA", preflight)

    @unittest.skipIf(os.name == "nt", "Native PTY confirmation requires Linux; Windows tests mock the TTY boundary")
    def test_actual_tty_exact_and_incorrect_confirmation(self):
        import pty
        for value, expected in (("wrong", 1), (recovery.CONFIRMATION, 0)):
            master, slave = pty.openpty()
            script = "import sys;sys.path.insert(0,sys.argv[1]);from recovery_installer import confirm_recovery;confirm_recovery()"
            child = subprocess.Popen([sys.executable, "-B", "-c", script, str(ROOT / "offline-installer/tools")], stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                os.write(master, (value + "\n").encode())
                child.communicate(timeout=10)
                self.assertEqual(child.returncode, expected)
            finally:
                os.close(master)
                os.close(slave)


if __name__ == "__main__":
    unittest.main()
