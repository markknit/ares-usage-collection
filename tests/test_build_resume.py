"""Run the resume workflow on disposable payloads without Docker or host changes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_profiles import BASH, BUILDER
from test_package_integrity import manifest


class BuildResumeTests(unittest.TestCase):
    def exercise(self, fail_verification):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            builder = base / "builder"
            (builder / "tools").mkdir(parents=True)
            shutil.copyfile(BUILDER / "tools/package_integrity.py", builder / "tools/package_integrity.py")
            script = (BUILDER / "run_tsavo3_build.sh").read_text(encoding="utf-8")
            # Adapt only machine location/identity and repository metadata queries.
            script = script.replace('BASE=/mnt/sda3/home/ares/Downloads', 'BASE="' + base.as_posix() + '"')
            script = script.replace('$(hostname -s)', 'tsavo3').replace('$(uname -m)', 'x86_64')
            script = script.replace('test -z "$(git -C "$SELF_DIR" status --porcelain --untracked-files=all)"', ':')
            script = script.replace('git -C "$SELF_DIR" rev-parse HEAD', 'printf "%s\\n" fixture-resume-commit')
            shim_dir = base / "bin"
            shim_dir.mkdir()
            shim = shim_dir / "python3"
            shim.write_text('#!/bin/bash\nexec "' + Path(sys.executable).as_posix() + '" "$@"\n', newline="\n")
            shim.chmod(0o755)
            path = '$(cygpath -u "' + shim_dir.as_posix() + '")' if os.name == "nt" else shim_dir.as_posix()
            script = script.replace('PATH=/usr/sbin:/usr/bin:/sbin:/bin', 'PATH="' + path + ':/usr/sbin:/usr/bin:/sbin:/bin"')
            (builder / "run.sh").write_text(script, encoding="utf-8", newline="\n")
            (builder / "build_offline_bundle.sh").write_text('echo UNEXPECTED_BUILDER\nexit 99\n', newline="\n")
            # Full component semantics have separate tests. This verifier fixture
            # exercises actual ZIP extraction and root checks before success/failure.
            (builder / "verify_offline_bundle.py").write_text('''import os, sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'tools'))
from package_integrity import verify_package
with tempfile.TemporaryDirectory(dir=Path(sys.argv[1]).parent) as temp:
    with zipfile.ZipFile(sys.argv[1]) as archive:
        archive.extractall(temp)
    root = next(Path(temp).iterdir())
    verify_package(root)
if os.environ['RESUME_FAIL'] == '1':
    raise SystemExit('FIXTURE_VERIFICATION_FAILED')
''', encoding="utf-8", newline="\n")
            work = base / ".ARES_Q4_Update_offline_v1.13.building-simplified-r3"
            bundle = "ARES_Q4_Offline_v0.94_amd64_v1.13"
            stage = work / "output" / bundle
            stage.mkdir(parents=True)
            (work / "tmp").mkdir()
            (work / "BUILD_INCOMPLETE").write_text("retain until verified")
            evidence = base / "ARES_Q4_v1.13_build_evidence_728741b-r2"
            run = evidence / "phase-c2-simplified-r3"
            run.mkdir(parents=True)
            (run / "builder-commit.txt").write_text("ed5052a128152166bc3bdb08a051cb21875944c9\n")
            approved = {}
            for name in ["lesson3_uninstall.sh", *(f"payload-{i}.txt" for i in range(132))]:
                data = b"fixture inherited bytes\n"
                (stage / name).write_bytes(data)
                approved[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            (evidence / "approved-inherited.json").write_text(json.dumps(approved))
            (evidence / "inheritance_policy.py").write_text(
                'def final_forbidden(name): return False\n'
                'def generated(name): return name in {"SHA256SUMS", "package_integrity.py"}\n')
            (stage / "package_integrity.py").write_bytes(b"# original helper fixture\n")
            manifest(stage)
            candidate = work / "output" / (bundle + ".zip")
            with zipfile.ZipFile(candidate, "w") as archive:
                for item in stage.iterdir():
                    archive.write(item, item.relative_to(stage.parent))
            original_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            env = dict(os.environ, RESUME_FAIL="1" if fail_verification else "0")
            result = subprocess.run([BASH, str(builder / "run.sh"), "--resume"],
                                    capture_output=True, text=True, env=env)
            self.assertNotIn("UNEXPECTED_BUILDER", result.stdout + result.stderr)
            self.assertEqual(hashlib.sha256((work / "original-candidate.zip").read_bytes()).hexdigest(), original_digest)
            final = base / "ARES_Q4_Update_offline_v1.13"
            if fail_verification:
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(final.exists())
                self.assertTrue((work / "BUILD_INCOMPLETE").exists())
                self.assertIn("FIXTURE_VERIFICATION_FAILED", result.stdout)
                self.assertEqual(result.stderr.count("Build stopped."), 1)
            else:
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((final / (bundle + ".zip")).is_file())
                self.assertFalse((work / "BUILD_INCOMPLETE").exists())
                self.assertEqual((final / bundle / "package_integrity.py").read_bytes(),
                                 (builder / "tools/package_integrity.py").read_bytes())
                for name, value in approved.items():
                    self.assertEqual(hashlib.sha256((final / bundle / name).read_bytes()).hexdigest(), value["sha256"])
                self.assertTrue((run / "resume-verification.log").is_file())
                self.assertFalse((run / "build.log").exists())

    def test_resume_reuses_payload_preserves_original_and_promotes_after_checks(self):
        self.exercise(False)

    def test_failed_resume_verification_keeps_candidate_and_never_promotes(self):
        self.exercise(True)


if __name__ == "__main__":
    unittest.main()
