import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "offline-installer"
BASH = shutil.which("bash") or "C:/Program Files/Git/bin/bash.exe"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BUILDER / "tools" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render = load("render_profile")
nginx = load("configure_nginx")


class ProfileTests(unittest.TestCase):
    def test_both_sealed_profiles_override_environment(self):
        for profile, alias in render.ALIASES.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                conf = Path(directory) / "package.conf"
                conf.write_text("LESSON3_VERSION=v0.94\nARES_PROFILE=" + profile + "\n")
                result = subprocess.run([BASH, "-c", 'source "$1" "$2"; printf "%s|%s" "$ARES_ALIAS" "$LESSON3_URL"',
                                         "test", (BUILDER / "templates/ares_config.sh").as_posix(), conf.as_posix()],
                                        capture_output=True, text=True, check=True,
                                        env={**os.environ, "ARES_ALIAS": "wrong.local"})
                self.assertEqual(result.stdout, alias + "|http://" + alias + ":3001")

    def test_render_links_including_encoded_targets_and_preserve_binary(self):
        for profile, alias in render.ALIASES.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                page = root / "index.htmlf"
                page.write_bytes((BUILDER / "templates/index.htmlf").read_bytes())
                pdf = root / "guide.pdf"
                pdf.write_bytes(b"PDF:ares.local")
                render.render(root, profile)
                self.assertIn("http%3A%2F%2F" + alias + "%3A3001", page.read_text(encoding="utf-8"))
                self.assertEqual(pdf.read_bytes(), b"PDF:ares.local")

    def test_nginx_switch_keeps_other_names_and_is_idempotent(self):
        original = "server { server_name ares.edu ares.local; }\nserver { server_name other.example; }"
        for alias in render.ALIASES.values():
            changed = nginx.configure(original, alias)
            self.assertIn("server_name ares.edu " + alias + ";", changed)
            self.assertIn("server_name other.example;", changed)
            self.assertEqual(nginx.configure(changed, alias), changed)
        self.assertNotIn("ares-test.local", nginx.configure(original, "ares.local"))

    def test_apk_rejects_wrong_profile_and_mixed_endpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"
            for profile, alias in render.ALIASES.items():
                dex = b"\0".join(("http://" + alias + "/tracker/" + endpoint).encode()
                                  for endpoint in ("prepare_due_usage_upload.php", "collection_schedule.json"))
                with zipfile.ZipFile(apk, "w") as archive:
                    archive.writestr("classes.dex", dex)
                render.verify_apk(apk, profile)
                with self.assertRaises(ValueError):
                    render.verify_apk(apk, "test" if profile == "production" else "production")
                with zipfile.ZipFile(apk, "w") as archive:
                    archive.writestr("classes.dex", dex + b"http://ares.local/tracker/" + b"http://ares-test.local/tracker/")
                with self.assertRaises(ValueError):
                    render.verify_apk(apk, profile)


if __name__ == "__main__":
    unittest.main()
