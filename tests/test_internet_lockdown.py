"""Exercise the integration with fake services; never apply real firewall rules."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_profiles import BASH, BUILDER, load


class InternetLockdownTests(unittest.TestCase):
    def test_printed_dependency_hint_is_not_an_executed_network_install(self):
        audit = load("audit_offline_scripts")
        source = (BUILDER / "internet-lockdown/ares-lockdown-v1.4.2/lockdown_internet.sh").read_text()
        self.assertEqual(audit.forbidden_lines(source, audit.VENDOR_SCRIPT), [])
        self.assertTrue(audit.forbidden_lines(source + "\napt-get install nftables\n", audit.VENDOR_SCRIPT))
        self.assertTrue(audit.forbidden_lines(audit.VENDOR_DIAGNOSTIC, "unreviewed.sh"))

    def run_preparation(self, *, active=False, boot=False, terminal=True, vendor_status=0):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            remote = root / "remote-access"
            remote.mkdir()
            shutil.copytree(BUILDER / "internet-lockdown", remote / "internet-lockdown")
            release = remote / "internet-lockdown/ares-lockdown-v1.4.2"
            # Substitute only the vendor's privileged installer and its fixture
            # checksum. All original imported files remain unchanged in source.
            (release / "install.sh").write_text(
                '#!/bin/bash\necho "VENDOR_INSTALL $*" >> "$CALLS"\nexit "$VENDOR_STATUS"\n', newline="\n")
            manifest = release / "SHA256SUMS"
            manifest.write_text("".join(
                hashlib.sha256((release / line[66:]).read_bytes()).hexdigest() + "  " + line[66:] + "\n"
                for line in manifest.read_text().splitlines()), newline="\n")
            helper = remote / "prepare_internet_lockdown.sh"
            text = (BUILDER / "templates/prepare_internet_lockdown.sh").read_text()
            text = text.replace('[[ ${EUID:-$(id -u)} -eq 0 ]] || { log \'run as root\'; exit 1; }', '')
            if terminal:
                # Model an interactive operator without needing a Windows PTY.
                text = text.replace('if [[ ! -t 0 ]]; then', 'if false; then')
            helper.write_text(text, newline="\n")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            commands = {
                "nft": 'echo "nft $*" >> "$CALLS"\n[[ "$ACTIVE" == yes ]]',
                "systemctl": 'echo "systemctl $*" >> "$CALLS"\n[[ "$BOOT" == yes ]]',
                "ip": 'exit 0',
                "python3": 'exit 0',
            }
            for name, body in commands.items():
                path = bin_dir / name
                path.write_text('#!/bin/bash\n' + body + '\n', newline="\n")
                path.chmod(0o755)
            prefix = 'export PATH="$(cygpath -u "$1"):$PATH"; ' if os.name == "nt" else 'export PATH="$1:$PATH"; '
            env = {**os.environ, "CALLS": (root / "calls").as_posix(),
                   "ACTIVE": "yes" if active else "no", "BOOT": "yes" if boot else "no",
                   "VENDOR_STATUS": str(vendor_status), "ARES_LOCKDOWN_HOME": (root / "installed").as_posix()}
            result = subprocess.run([BASH, "-c", prefix + 'exec bash "$2"', "fixture",
                                     bin_dir.as_posix(), helper.as_posix()], env=env,
                                    stdin=subprocess.DEVNULL, capture_output=True, text=True)
            calls = (root / "calls").read_text() if (root / "calls").exists() else ""
            installed = root / "installed/ares-lockdown-v1.4.2"
            self.assertEqual((installed / "SHA256SUMS").read_bytes(), manifest.read_bytes())
            self.assertEqual((installed / "ARES_Internet_Lockdown_README_v1.4.2.pdf").read_bytes(),
                             (release / "ARES_Internet_Lockdown_README_v1.4.2.pdf").read_bytes())
            self.assertNotIn("nft -f", calls)
            self.assertNotIn("systemctl enable", calls)
            self.assertNotIn("systemctl stop", calls)
            return result, calls

    def test_preparation_invokes_only_no_boot_installer(self):
        result, calls = self.run_preparation()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("VENDOR_INSTALL --no-boot", calls)

    def test_active_or_boot_lockdown_preserves_commands_and_configuration(self):
        for flags in ({"active": True}, {"boot": True}):
            with self.subTest(flags=flags):
                result, calls = self.run_preparation(**flags)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn("VENDOR_INSTALL", calls)

    def test_noninteractive_install_leaves_project_for_later(self):
        result, calls = self.run_preparation(terminal=False)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("VENDOR_INSTALL", calls)

    def test_vendor_failure_is_reported(self):
        result, calls = self.run_preparation(vendor_status=23)
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn("VENDOR_INSTALL --no-boot", calls)


if __name__ == "__main__":
    unittest.main()
