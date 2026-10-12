import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "offline-installer"
ROLLOUT = BUILDER / "rollout" / "ARES_Sync_Rollout_Package"


class OfflineInstallerSourceTests(unittest.TestCase):
    def test_builder_carries_current_guides_and_remote_access_documentation(self):
        guide_pairs = (
            (
                ROOT / "output" / "pdf" / "ARES_Sync_Technician_Guide.pdf",
                BUILDER / "docs" / "pdf" / "ARES_Sync_Technician_Guide.pdf",
                ROLLOUT / "guides" / "ARES_Sync_Technician_Guide.pdf",
            ),
            (
                ROOT / "output" / "pdf" / "ARES_Sync_Teacher_Guide.pdf",
                BUILDER / "docs" / "pdf" / "ARES_Sync_Teacher_Guide.pdf",
                ROLLOUT / "guides" / "ARES_Sync_Teacher_Guide.pdf",
            ),
        )
        for sources in guide_pairs:
            expected = sources[0].read_bytes()
            for path in sources[1:]:
                with self.subTest(path=path):
                    self.assertEqual(expected, path.read_bytes())
        self.assertTrue((BUILDER / "docs" / "REMOTE_ACCESS.md").is_file())
        self.assertTrue((BUILDER / "docs" / "LESSON3_V094_ACCEPTANCE.md").is_file())

    def test_v094_acceptance_gate_covers_discussion_controls(self):
        checklist = (BUILDER / "docs" / "LESSON3_V094_ACCEPTANCE.md").read_text(
            encoding="utf-8"
        )
        for required in (
            "Teacher discussions",
            "blue unread indication",
            "disable Discussions",
            "Moderate discussions",
            "v1.10/v0.93",
        ):
            with self.subTest(required=required):
                self.assertIn(required, checklist)

    def test_embedded_rollout_matches_canonical_server_files(self):
        names = (
            "ares_prepare_usage_upload.sh",
            "ares_set_school_code.sh",
            "collection_schedule.json",
            "install_usage_collection.sh",
            "prepare_due_usage_upload.php",
            "prepare_usage_upload.php",
            "update_school_server.sh",
        )
        for name in names:
            with self.subTest(name=name):
                canonical = ROOT / "local-server" / name
                embedded = ROLLOUT / "server-installer" / name
                self.assertTrue(embedded.is_file(), embedded)
                self.assertEqual(canonical.read_bytes(), embedded.read_bytes())

    def test_embedded_rollout_checksum_manifest(self):
        checksum_file = ROLLOUT / "SHA256SUMS.txt"
        self.assertTrue(checksum_file.is_file())
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            expected, relative = line.split(maxsplit=1)
            relative = relative.lstrip("* ")
            payload = ROLLOUT / relative
            self.assertTrue(payload.is_file(), payload)
            actual = hashlib.sha256(payload.read_bytes()).hexdigest()
            self.assertEqual(expected, actual, relative)

    def test_builder_requires_reassignment_command(self):
        builder = (BUILDER / "build_offline_bundle.sh").read_text(encoding="utf-8")
        self.assertIn(
            "ARES_Sync_Rollout_Package/server-installer/ares_set_school_code.sh",
            builder,
        )
        self.assertIn('BUNDLE_REVISION="v1.11"', builder)
        self.assertIn('LESSON3_VERSION="v0.94"', builder)

    def test_lesson3_runtime_defaults_match_v094(self):
        for relative in (
            "templates/preflight.sh",
            "templates/lesson3_offline.sh",
        ):
            with self.subTest(relative=relative):
                source = (BUILDER / relative).read_text(encoding="utf-8")
                self.assertIn('LESSON3_VERSION="${LESSON3_VERSION:-v0.94}"', source)

    def test_main_installer_guides_and_verifies_corpus_install(self):
        installer = (BUILDER / "templates" / "install_offline.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("install_lesson3_corpus_guided", installer)
        self.assertIn('Type READY after the Site Administrator exists', installer)
        self.assertIn('LESSON3_CORPUS_STATUS=installed', installer)
        self.assertIn('CORPUS_INSTALLED.txt', installer)
        self.assertIn('grep -qx "v0.94"', installer)

    def test_remote_access_is_prepared_but_not_activated(self):
        prepare = (BUILDER / "templates" / "prepare_remote_access.sh").read_text(
            encoding="utf-8"
        )
        activate = (BUILDER / "templates" / "ares_enable_remote_access.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("systemctl disable --now tailscaled.service", prepare)
        self.assertIn("systemctl disable --now 'tigervncserver@:1.service'", prepare)
        self.assertNotIn("tailscale up", prepare)
        self.assertIn('localhost=yes', activate)
        self.assertIn('tailscale up --hostname "$TAILSCALE_HOSTNAME" --ssh', activate)
        self.assertIn("rollback_activation", activate)

    def test_mdns_selector_excludes_non_lan_networks(self):
        installer = (BUILDER / "templates" / "lesson_plan_install.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('str(parsed) == "10.42.0.1"', installer)
        self.assertIn('ipaddress.ip_network("100.64.0.0/10")', installer)
        for prefix in ("docker", "br-", "veth", "tailscale", "tun", "tap", "wg"):
            self.assertIn(f'"{prefix}"', installer)

    def test_builder_pins_remote_access_payloads(self):
        builder = (BUILDER / "build_offline_bundle.sh").read_text(encoding="utf-8")
        self.assertIn('TAILSCALE_VERSION="1.104.1"', builder)
        self.assertIn('TIGERVNC_VERSION="1.13.1+dfsg-2build2"', builder)
        self.assertIn('$TAILSCALE_BASE/$TAILSCALE_FILE.sha256', builder)
        self.assertIn('tigervnc-standalone-server=$TIGERVNC_VERSION', builder)
        self.assertIn("grep -E '(^|/)tailscale$' >/dev/null", builder)
        self.assertIn("grep -E '(^|/)tailscaled$' >/dev/null", builder)
        self.assertNotIn("grep -Eq '(^|/)tailscale$'", builder)
        self.assertNotIn("grep -Eq '(^|/)tailscaled$'", builder)
        self.assertIn('--chmod=Du+w,Fu+w', builder)
        self.assertIn('chmod -R u+rwX "$STAGE"', builder)


class CorpusStatusTests(unittest.TestCase):
    def run_status(self, counts):
        script = BUILDER / "templates" / "install_lesson3_corpus.sh"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            files = corpus / "files"
            deploy = root / "deploy"
            mock_bin = root / "bin"
            files.mkdir(parents=True)
            deploy.mkdir()
            mock_bin.mkdir()

            (deploy / "compose.offline.yaml").write_text("services: {}\n", encoding="utf-8")
            lesson_file = files / "Sample_data.json"
            lesson_file.write_text("{}\n", encoding="utf-8")
            taxonomy = corpus / "taxonomy.tsv"
            taxonomy.write_text("Mathematics\t10\n", encoding="utf-8")
            manifest = corpus / "MANIFEST.json"
            manifest.write_text(
                json.dumps(
                    {
                        "format": "ares-lesson3-offline-corpus-v1",
                        "source_commit": "e07c243da77ad4554a2f404ae7790ef6e9d3e1b0",
                        "file_count": 1,
                        "lesson_count": 1,
                        "subject_count": 1,
                        "subject_grade_count": 1,
                        "files": [{"file": lesson_file.name}],
                    }
                ),
                encoding="utf-8",
            )
            checksums = corpus / "SHA256SUMS"
            checksum_lines = []
            for path in (manifest, taxonomy, lesson_file):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                checksum_lines.append(f"{digest}  {path.relative_to(corpus)}")
            checksums.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
            installed_script = corpus / "install_lesson3_corpus.sh"
            installed_script.write_bytes(script.read_bytes())
            installed_script.chmod(0o755)

            docker = mock_bin / "docker"
            docker.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$*\" == \"compose version\" ]]; then echo 'Docker Compose version mock'; "
                "elif [[ \"$*\" == *' ps --status running --services'* ]]; then echo app; "
                "elif [[ \"$*\" == *' psql '* ]]; then echo \"$MOCK_COUNTS\"; fi\n",
                encoding="utf-8",
            )
            docker.chmod(0o755)

            curl = mock_bin / "curl"
            curl.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            curl.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{mock_bin}:{env['PATH']}",
                    "LESSON3_DEPLOY_DIR": str(deploy),
                    "MOCK_COUNTS": counts,
                }
            )
            result = subprocess.run(
                ["bash", str(installed_script), "--status"],
                text=True,
                capture_output=True,
                env=env,
                check=True,
            )
            return result.stdout, result.stderr

    def test_status_reports_empty_database(self):
        stdout, _ = self.run_status("0|0|0|0|0|0")
        self.assertIn("LESSON3_CORPUS_STATUS=empty", stdout)

    def test_status_reports_installed_corpus(self):
        stdout, _ = self.run_status("1|1|1|1|1|1")
        self.assertIn("LESSON3_CORPUS_STATUS=installed", stdout)

    def test_status_reports_partial_content(self):
        stdout, stderr = self.run_status("1|1|0|0|1|1")
        self.assertIn("LESSON3_CORPUS_STATUS=partial", stdout)
        self.assertIn("unexpected content counts", stderr)


if __name__ == "__main__":
    unittest.main()
