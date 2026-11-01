"""Exercise the real master workflow with host-changing stages replaced by fixtures."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_profiles import BASH, BUILDER
from test_package_integrity import manifest


class SimpleInstallerTests(unittest.TestCase):
    def run_install(self, *, remote_status=0, broken_package=False, failed_step=""):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "package"
            root.mkdir()
            for name, source in {
                "ares_config.sh": "templates/ares_config.sh",
                "package.conf": "package.conf",
                "package_integrity.py": "tools/package_integrity.py",
                "optional_remote_support.sh": "templates/optional_remote_support.sh",
            }.items():
                shutil.copyfile(BUILDER / source, root / name)
            master = (BUILDER / "templates/install_offline.sh").read_text(encoding="utf-8")
            master = master.replace('[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "ERROR: run as root" >&2; exit 1; }', '')
            master = master.replace('LOG_FILE="/var/log/ares-offline-install-${STAMP}.log"',
                                    'LOG_FILE="' + (base / "install.log").as_posix() + '"')
            start = master.index('run_step "8)')
            end = master.index("' \"$SCRIPT_DIR\"", start) + len("' \"$SCRIPT_DIR\"")
            master = master[:start] + 'echo HOST_POSTCHECK_FIXTURE\n' + master[end:]
            (root / "install_offline.sh").write_text(master, encoding="utf-8", newline="\n")
            # Use the actual preflight through its complete-package gate. Host
            # prerequisite checks are excluded from this portable workflow fixture.
            preflight = (BUILDER / "templates/preflight.sh").read_text(encoding="utf-8")
            preflight = preflight.replace('[[ ${EUID:-$(id -u)} -eq 0 ]] || { echo "FAIL  Run preflight as root"; exit 2; }', '')
            start = preflight.index('  echo "ARES Q4 OFFLINE PRE-FLIGHT"')
            end = preflight.index('\n}\n', start)
            preflight = preflight[:start] + '  echo HOST_PREFLIGHT_FIXTURE\n' + preflight[end:]
            (root / "preflight.sh").write_text(preflight, encoding="utf-8", newline="\n")
            for name in ("lesson_plan/install.sh", "lesson3/install_lesson3_offline.sh",
                         "tracking/install_lesson_plan_tracking.sh",
                         "ARES_Sync_Rollout_Package/server-installer/update_school_server.sh",
                         "teacher-app/install_teacher_app.sh", "tsavo/install.sh"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('#!/bin/bash\necho "' + name + '" >> "$CALLS"\n'
                                '[[ "$FAIL_STEP" != "' + name + '" ]]\n', newline="\n")
            corpus = root / "lesson3/corpus/install_lesson3_corpus.sh"
            corpus.parent.mkdir(parents=True)
            corpus.write_text('#!/bin/bash\necho LESSON3_CORPUS_STATUS=installed\n', newline="\n")
            remote = root / "remote-access/prepare_remote_access.sh"
            remote.parent.mkdir()
            remote.write_text('#!/bin/bash\necho REMOTE_PREPARATION >> "$CALLS"\nexit "$REMOTE_STATUS"\n', newline="\n")
            manifest(root)
            if broken_package == "missing":
                (root / "package.conf").unlink()
            elif broken_package:
                with (root / "package.conf").open("a") as stream:
                    stream.write("# incomplete/changed copy\n")
            bin_dir = base / "bin"
            bin_dir.mkdir()
            shim = bin_dir / "python3"
            shim.write_text('#!/bin/bash\nexec "' + Path(sys.executable).as_posix() + '" "$@"\n', newline="\n")
            shim.chmod(0o755)
            prefix = 'export PATH="$(cygpath -u "$1"):$PATH"; ' if os.name == "nt" else 'export PATH="$1:$PATH"; '
            env = dict(os.environ, CALLS=(base / "calls").as_posix(), REMOTE_STATUS=str(remote_status), FAIL_STEP=failed_step)
            result = subprocess.run([BASH, "-c", prefix + 'bash "$2" ARES-S0099', "test",
                                     bin_dir.as_posix(), (root / "install_offline.sh").as_posix()],
                                    capture_output=True, text=True, env=env)
            calls = (base / "calls").read_text() if (base / "calls").exists() else ""
            return result, calls

    def test_completed_core_prepares_optional_support_after_all_core_stages(self):
        result, calls = self.run_install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("completed successfully", result.stdout)
        self.assertIn("Remote support deferred", result.stdout)
        self.assertTrue(calls.endswith("tsavo/install.sh\nREMOTE_PREPARATION\n"), calls)

    def test_missing_remote_prerequisites_and_preparation_errors_preserve_core_success(self):
        for code in (1, 42):
            with self.subTest(code=code):
                result, calls = self.run_install(remote_status=code)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("completed successfully", result.stdout)
                self.assertIn("remote support could not be prepared", result.stdout)
                self.assertNotIn("Remote support prepared;", result.stdout)
                self.assertIn("REMOTE_PREPARATION", calls)

    def test_bad_package_stops_before_any_installation_stage(self):
        for fault in (True, "missing"):
            with self.subTest(fault=fault):
                result, calls = self.run_install(broken_package=fault)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, "")
                self.assertIn("Copy the complete ZIP again", result.stdout + result.stderr)
                self.assertNotIn("completed successfully", result.stdout)

    def test_core_failure_stops_without_success_or_optional_preparation(self):
        result, calls = self.run_install(failed_step="lesson3/install_lesson3_offline.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("completed successfully", result.stdout)
        self.assertNotIn("REMOTE_PREPARATION", calls)
        self.assertIn("Send this log to ARES support", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
