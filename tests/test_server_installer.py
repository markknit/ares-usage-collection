import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "local-server" / "install_usage_collection.sh"
UPDATER = REPO_ROOT / "local-server" / "update_school_server.sh"
REASSIGNER = Path("usr/local/sbin/ares-set-school-code")
PRODUCTION_SCHEDULE = REPO_ROOT / "local-server" / "collection_schedule.json"
TRACKER = Path("mnt/sda3/var/www/tracker")


class ServerInstallerTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "root"
        self.root.mkdir()
        self.test_bin = Path(self.tempdir.name) / "bin"
        self.test_bin.mkdir()
        php = self.test_bin / "php"
        php.write_text("#!/usr/bin/env bash\n[[ ${1:-} == -l ]]\n", encoding="utf-8")
        php.chmod(0o755)
        self._create_existing_report_path()

    def tearDown(self):
        self.tempdir.cleanup()

    def _create_existing_report_path(self):
        builder = self.root / "usr/local/sbin/ares_build_reports.sh"
        builder.parent.mkdir(parents=True)
        builder.write_text("#!/usr/bin/env bash\nset -euo pipefail\nexit 0\n", encoding="utf-8")
        builder.chmod(0o755)

        source = self.root / TRACKER / "reports/combined_usage.csv"
        source.parent.mkdir(parents=True)
        source.write_text("device,minutes\nclassroom-1,42\n", encoding="utf-8")

    def _run(self, *args, expected=0):
        result = subprocess.run(
            ["bash", *map(str, args)],
            cwd=REPO_ROOT,
            env={**os.environ, "PATH": f"{self.test_bin}:{os.environ['PATH']}"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stdout)
        return result.stdout

    def _common_args(self):
        return ["--school-code", "ARES-S0099", "--install-root", self.root]

    def test_update_installs_all_components_runs_smoke_test_and_measures_csv(self):
        expected_bytes = (self.root / TRACKER / "reports/combined_usage.csv").stat().st_size
        output = self._run(UPDATER, *self._common_args())

        self.assertIn(f"AUTO export smoke test passed: {expected_bytes} bytes", output)
        self.assertIn(f"Measured usage CSV: {expected_bytes}", output)

        wrapper = self.root / "usr/local/sbin/ares_prepare_usage_upload.sh"
        self.assertTrue(wrapper.is_file())
        self.assertTrue(wrapper.stat().st_mode & stat.S_IXUSR)
        reassigner = self.root / REASSIGNER
        self.assertTrue(reassigner.is_file())
        self.assertTrue(reassigner.stat().st_mode & stat.S_IXUSR)
        self.assertTrue((self.root / TRACKER / "prepare_usage_upload.php").is_file())
        self.assertTrue((self.root / TRACKER / "prepare_due_usage_upload.php").is_file())
        self.assertEqual(
            PRODUCTION_SCHEDULE.read_text(encoding="utf-8"),
            (self.root / TRACKER / "collection_schedule.json").read_text(encoding="utf-8"),
        )

        config = (self.root / "etc/ares/usage-upload.conf").read_text(encoding="utf-8")
        self.assertIn("SCHOOL_CODE=ARES-S0099", config)
        self.assertIn(str(self.root / TRACKER / "reports/combined_usage.csv"), config)
        self.assertIn(str(self.root / TRACKER / "uploads"), config)

        exports = list((self.root / TRACKER / "uploads").glob("ARES_USAGE_*_AUTO_*.csv"))
        self.assertEqual(1, len(exports))
        self.assertEqual(expected_bytes, exports[0].stat().st_size)

    def test_update_replaces_and_backs_up_existing_schedule(self):
        schedule = self.root / TRACKER / "collection_schedule.json"
        schedule.parent.mkdir(parents=True, exist_ok=True)
        previous = '{"previous":"school schedule"}\n'
        schedule.write_text(previous, encoding="utf-8")

        self._run(UPDATER, *self._common_args())

        self.assertEqual(PRODUCTION_SCHEDULE.read_text(encoding="utf-8"), schedule.read_text(encoding="utf-8"))
        backups = list(
            (self.root / "var/backups/ares-usage-collection").glob(
                "*/mnt/sda3/var/www/tracker/collection_schedule.json"
            )
        )
        self.assertEqual(1, len(backups))
        self.assertEqual(previous, backups[0].read_text(encoding="utf-8"))

    def test_provisional_install_can_be_reassigned_to_canonical_school(self):
        self._run(
            UPDATER,
            "--school-code",
            "PENDING-SRV001",
            "--install-root",
            self.root,
        )

        output = self._run(
            self.root / REASSIGNER,
            "ARES-S0007",
            "--install-root",
            self.root,
        )

        self.assertIn("ARES school-code reassignment complete", output)
        self.assertIn("Previous school code: PENDING-SRV001", output)
        self.assertIn("New school code: ARES-S0007", output)
        config = (self.root / "etc/ares/usage-upload.conf").read_text(encoding="utf-8")
        self.assertIn("SCHOOL_CODE=ARES-S0007", config)
        self.assertNotIn("SCHOOL_CODE=PENDING-SRV001", config)
        backups = list(
            (self.root / "var/backups/ares-usage-collection").glob(
                "*_school-code_*/etc/ares/usage-upload.conf"
            )
        )
        self.assertEqual(1, len(backups))
        self.assertIn("SCHOOL_CODE=PENDING-SRV001", backups[0].read_text(encoding="utf-8"))
        exports = list(
            (self.root / TRACKER / "uploads").glob("ARES_USAGE_ARES-S0007_AUTO_*.csv")
        )
        self.assertEqual(1, len(exports))

    def test_reassignment_rejects_noncanonical_school_code_without_changes(self):
        self._run(UPDATER, *self._common_args())
        config_path = self.root / "etc/ares/usage-upload.conf"
        before = config_path.read_text(encoding="utf-8")

        output = self._run(
            self.root / REASSIGNER,
            "PENDING-SRV002",
            "--install-root",
            self.root,
            expected=1,
        )

        self.assertIn("Final school code must match ARES-S0000", output)
        self.assertEqual(before, config_path.read_text(encoding="utf-8"))

    def test_reassignment_restores_old_code_when_smoke_test_fails(self):
        self._run(UPDATER, *self._common_args())
        builder = self.root / "usr/local/sbin/ares_build_reports.sh"
        builder.write_text("#!/usr/bin/env bash\nexit 9\n", encoding="utf-8")
        builder.chmod(0o755)

        output = self._run(
            self.root / REASSIGNER,
            "ARES-S0008",
            "--install-root",
            self.root,
            expected=9,
        )

        self.assertIn("restored the prior school code ARES-S0099", output)
        config = (self.root / "etc/ares/usage-upload.conf").read_text(encoding="utf-8")
        self.assertIn("SCHOOL_CODE=ARES-S0099", config)
        self.assertNotIn("SCHOOL_CODE=ARES-S0008", config)

    def test_base_installer_preserves_existing_schedule_without_replace_flag(self):
        schedule = self.root / TRACKER / "collection_schedule.json"
        schedule.parent.mkdir(parents=True, exist_ok=True)
        previous = '{"locally_reviewed":true}\n'
        schedule.write_text(previous, encoding="utf-8")

        output = self._run(INSTALLER, *self._common_args())

        self.assertIn("Existing collection schedule preserved", output)
        self.assertEqual(previous, schedule.read_text(encoding="utf-8"))

    def test_preflight_failure_does_not_replace_existing_component(self):
        endpoint = self.root / TRACKER / "prepare_usage_upload.php"
        endpoint.parent.mkdir(parents=True, exist_ok=True)
        endpoint.write_text("existing endpoint\n", encoding="utf-8")
        (self.root / "usr/local/sbin/ares_build_reports.sh").unlink()

        output = self._run(UPDATER, *self._common_args(), expected=1)

        self.assertIn("Report builder is not executable", output)
        self.assertEqual("existing endpoint\n", endpoint.read_text(encoding="utf-8"))
        self.assertFalse((self.root / "var/backups/ares-usage-collection").exists())

    def test_oversize_source_csv_is_rejected_before_changes(self):
        source = self.root / TRACKER / "reports/combined_usage.csv"
        with source.open("wb") as stream:
            stream.truncate(2 * 1024 * 1024 + 1)

        output = self._run(UPDATER, *self._common_args(), expected=1)

        self.assertIn("central upload limit is 2097152 bytes", output)
        self.assertFalse((self.root / "var/backups/ares-usage-collection").exists())

    def test_invalid_production_schedule_is_rejected_before_changes(self):
        bad_schedule = Path(self.tempdir.name) / "bad-schedule.json"
        bad_schedule.write_text(
            json.dumps(
                {
                    "school_year": "2026",
                    "timezone": "Africa/Nairobi",
                    "collections": [
                        {"id": "TEST-DUE", "label": "Unsafe test", "due_date": "2026-10-15"}
                    ],
                }
            ),
            encoding="utf-8",
        )

        output = self._run(
            INSTALLER,
            *self._common_args(),
            "--schedule-file",
            bad_schedule,
            "--skip-smoke-test",
            expected=1,
        )

        self.assertIn("invalid production collection id", output)
        self.assertFalse((self.root / "var/backups/ares-usage-collection").exists())


if __name__ == "__main__":
    unittest.main()
