from pathlib import Path
import subprocess
import unittest
from test_profiles import BASH, BUILDER, load

config = load("remote_support_config")
urls = load("configure_lesson3_url")


def shell(source, code):
    return subprocess.run([BASH, "-c", 'source "$1"; ' + code, "test",
                           (BUILDER / "templates" / source).as_posix()],
                          capture_output=True, text=True)


class RemoteSupportTests(unittest.TestCase):
    def test_hosts_preserves_aliases_comments_and_actual_separators(self):
        value = "127.0.0.1 localhost\n127.0.1.1 old retained ares.local # comment\n"
        changed = config.hosts(value, "old", "new")
        self.assertEqual(changed, "127.0.0.1 localhost\n127.0.1.1\tnew retained ares.local # comment\n")
        self.assertNotIn("\\t", changed)
        self.assertEqual(config.hosts(changed, "new", "new"), changed)

    def test_display_conflicts_fail_and_other_displays_survive(self):
        with self.assertRaises(ValueError):
            config.display_map(":1 = another-user\n")
        value = config.display_map("# retained\n:2=other\n:1=ares\n:1=ares\n")
        self.assertEqual(value, "# retained\n:2=other\n:1=ares\n")
        self.assertEqual(config.display_map(value), value)

    def test_hostname_normalization_and_limits(self):
        self.assertEqual(config.hostname(" St Jude Nturukhuma Girls "), "st-jude-nturukhuma-girls")
        self.assertLessEqual(len(config.hostname("a" * 100)), 63)
        with self.assertRaises(ValueError):
            config.hostname("!!!")

    def test_lesson3_urls_preserve_secrets_and_offline_posture(self):
        for alias in ("ares.local", "ares-test.local"):
            original = "SECRET=unchanged\nADMIN_URL=http://localhost:3001\nSERVER_URL=\n"
            expected = "http://" + alias + ":3001"
            changed = urls.configure(original, expected, "")
            self.assertIn("SECRET=unchanged\n", changed)
            self.assertIn("ADMIN_URL=" + expected + "\nSERVER_URL=\n", changed)
            self.assertEqual(urls.configure(changed, expected, ""), changed)
            with self.assertRaises(ValueError):
                urls.configure(original, expected, expected)

    def test_vnc_rejects_all_nonloopback_listeners(self):
        for addresses, passes in (("127.0.0.1:5901 [::1]:5901", True),
                                  ("127.0.0.1:5901 192.168.1.2:5901", False),
                                  ("0.0.0.0:5901", False), ("[::]:5901", False), ("", False)):
            rows = "\n".join("LISTEN 0 5 " + value + " *:*" for value in addresses.split())
            result = shell("ares_enable_remote_access.sh", "ss() { printf '%s\\n' '" + rows + "'; }; verify_vnc_listeners")
            self.assertEqual(result.returncode == 0, passes, result.stderr)

    def test_failure_cleanup_stops_both_services_and_restores_owned_ssh(self):
        result = shell("ares_enable_remote_access.sh", '''
systemctl() { if [[ "$1" == is-active ]]; then return 3; fi; printf '%s\\n' "$*"; }
STARTED=1; SSH_WAS_ACTIVE=no; SSH_WAS_ENABLED=no
trap cleanup EXIT
exit 42
''')
        self.assertEqual(result.returncode, 42)
        self.assertIn("disable --now tigervncserver@:1.service tailscaled.service", result.stdout)
        self.assertIn("stop ssh.service", result.stdout)
        self.assertIn("disable ssh.service", result.stdout)

    def test_optional_decline_and_failure_preserve_core_success(self):
        for reply in ("", "N", "y"):
            code = '''function /usr/local/sbin/ares-enable-remote-access() { echo CALLED; return 7; }
run_optional_remote_support "''' + reply + '"'
            result = shell("optional_remote_support.sh", code)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("core installation remains successful", result.stdout)
            self.assertEqual("CALLED" in result.stdout, reply == "y")


if __name__ == "__main__":
    unittest.main()
