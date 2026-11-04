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
            manifest = release / "SHA256SUMS"
            for name, source in {"lockdown_dispatch.sh": "templates/lockdown_dispatch.sh",
                                 "configure_lockdown.py": "tools/configure_lockdown.py"}.items():
                shutil.copyfile(BUILDER / source, remote / name)
            helper = remote / "prepare_internet_lockdown.sh"
            text = (BUILDER / "templates/prepare_internet_lockdown.sh").read_text()
            text = text.replace('[[ ${EUID:-$(id -u)} -eq 0 ]] || { log \'run as root\'; exit 1; }', '')
            # Keep every host path in this disposable fixture.
            text = text.replace('/usr/local/', (root / 'local').as_posix() + '/')
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
            if not active and not boot:
                for command in ('lockdown-internet', 'restore-internet', 'ares-configure-lockdown'):
                    self.assertTrue((root / 'local/bin' / command).is_file(), command)
                self.assertEqual((root / 'local/sbin/lockdown_internet.sh').read_bytes(),
                                 (release / 'lockdown_internet.sh').read_bytes())
            return result, calls

    def test_unplugged_preparation_installs_commands_without_network_selection(self):
        result, calls = self.run_preparation(terminal=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("VENDOR_INSTALL", calls)
        self.assertIn("no adapter or Internet connection", result.stdout)
        self.assertNotIn("ip ", calls)

    def test_active_or_boot_lockdown_preserves_commands_and_configuration(self):
        for flags in ({"active": True}, {"boot": True}):
            with self.subTest(flags=flags):
                result, calls = self.run_preparation(**flags)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn("VENDOR_INSTALL", calls)


if __name__ == "__main__":
    unittest.main()
