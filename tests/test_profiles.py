import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile
import struct

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


def compiled_strings(*strings):
    data = b""
    offsets = []
    for value in strings:
        offsets.append(len(data))
        data += bytes([len(value), len(value)]) + value.encode() + b"\0"
    data += b"\0" * ((-len(data)) % 4)
    start = 28 + 4 * len(strings)
    pool = struct.pack("<HHIIIIII", 1, 28, start + len(data), len(strings), 0, 0x100, start, 0)
    pool += b"".join(struct.pack("<I", offset) for offset in offsets) + data
    return struct.pack("<HHI", 3, 8, 8 + len(pool)) + pool


def compiled_policy(*aliases):
    return compiled_strings("network-security-config", "domain-config", "domain",
                            "cleartextTrafficPermitted", *aliases)


class ProfileTests(unittest.TestCase):
    def write_apk(self, apk, profile, resources, *, dex=None, identity=None):
        alias = render.ALIASES[profile]
        if dex is None:
            dex = b"\0".join(("http://" + alias + "/tracker/" + endpoint).encode()
                              for endpoint in ("prepare_due_usage_upload.php", "collection_schedule.json"))
        if identity is None:
            identity = "org.areseducation.sync" + (".test" if profile == "test" else "")
        with zipfile.ZipFile(apk, "w") as archive:
            archive.writestr("classes.dex", dex)
            archive.writestr("AndroidManifest.xml", compiled_strings(identity))
            for name, content in resources.items():
                archive.writestr(name, content)

    def test_apk_accepts_obfuscated_policy_with_unrelated_and_malformed_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"
            for profile, alias in render.ALIASES.items():
                with self.subTest(profile=profile):
                    self.write_apk(apk, profile, {
                        "res/drawable/icon.png": b"\x89PNG\r\n\x1a\n",
                        "res/raw/truncated.xml": struct.pack("<HHI", 3, 8, 16) + struct.pack("<HHI", 1, 8, 8),
                        "res/raw/bad-text.xml": compiled_policy(alias).replace(alias.encode(), b"\xff" * len(alias)),
                        "res/layout/screen.xml": compiled_strings(alias, "domain"),
                        "res/8G.xml": compiled_policy(alias),
                    })
                    render.verify_apk(apk, profile)

    def test_apk_rejects_missing_wrong_or_mixed_obfuscated_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"
            for profile, alias in render.ALIASES.items():
                other = next(value for value in render.ALIASES.values() if value != alias)
                for resources in ({},
                                  {"res/8G.xml": b"not binary XML"},
                                  {"res/8G.xml": compiled_strings(alias)},
                                  {"assets/8G.xml": compiled_policy(alias)},
                                  {"res/8G.xml": compiled_policy(other)},
                                  {"res/8G.xml": compiled_policy(alias, other)},
                                  {"res/8G.xml": compiled_policy(alias), "res/9G.xml": compiled_policy(other)}):
                    with self.subTest(profile=profile, resources=list(resources)):
                        self.write_apk(apk, profile, resources)
                        with self.assertRaisesRegex(ValueError, "cleartext policy"):
                            render.verify_apk(apk, profile)

    def test_obfuscated_policy_does_not_bypass_endpoint_or_identity_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"
            for profile, alias in render.ALIASES.items():
                resources = {"res/8G.xml": compiled_policy(alias)}
                for endpoint in ("prepare_due_usage_upload.php", "collection_schedule.json"):
                    with self.subTest(profile=profile, endpoint=endpoint):
                        self.write_apk(apk, profile, resources,
                                       dex=("http://" + alias + "/tracker/" + endpoint).encode())
                        with self.assertRaisesRegex(ValueError, "lacks compiled endpoint"):
                            render.verify_apk(apk, profile)
                self.write_apk(apk, profile, resources, identity="org.example.wrong")
                with self.assertRaisesRegex(ValueError, "application identity"):
                    render.verify_apk(apk, profile)

    def test_both_sealed_profiles_override_environment(self):
        for profile, alias in render.ALIASES.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                conf = Path(directory) / "package.conf"
                conf.write_text("LESSON3_VERSION=v0.94\nLESSON3_SERVER_URL=\nARES_PROFILE=" + profile + "\n")
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
        with self.assertRaises(ValueError):
            nginx.configure("# server_name ares.local;\nserver_name other.example;", "ares-test.local")

    def test_apk_rejects_wrong_cleartext_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("classes.dex", b"http://ares-test.local/tracker/prepare_due_usage_upload.php\0http://ares-test.local/tracker/collection_schedule.json")
                archive.writestr("res/xml/network_security_config.xml", compiled_policy("ares.local"))
                archive.writestr("AndroidManifest.xml", compiled_policy("org.areseducation.sync.test"))
            with self.assertRaisesRegex(ValueError, "cleartext policy"):
                render.verify_apk(apk, "test")

    def test_apk_rejects_wrong_profile_and_mixed_endpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "app.apk"
            for profile, alias in render.ALIASES.items():
                dex = b"\0".join(("http://" + alias + "/tracker/" + endpoint).encode()
                                  for endpoint in ("prepare_due_usage_upload.php", "collection_schedule.json"))
                with zipfile.ZipFile(apk, "w") as archive:
                    archive.writestr("classes.dex", dex)
                    archive.writestr("res/xml/network_security_config.xml", compiled_policy(alias))
                    archive.writestr("AndroidManifest.xml", compiled_policy("org.areseducation.sync" + (".test" if profile == "test" else "")))
                render.verify_apk(apk, profile)
                with self.assertRaises(ValueError):
                    render.verify_apk(apk, "test" if profile == "production" else "production")
                with zipfile.ZipFile(apk, "w") as archive:
                    archive.writestr("classes.dex", dex + b"http://ares.local/tracker/" + b"http://ares-test.local/tracker/")
                    archive.writestr("res/xml/network_security_config.xml", compiled_policy(alias))
                    archive.writestr("AndroidManifest.xml", compiled_policy("org.areseducation.sync" + (".test" if profile == "test" else "")))
                with self.assertRaises(ValueError):
                    render.verify_apk(apk, profile)


if __name__ == "__main__":
    unittest.main()
