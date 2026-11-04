"""Disconnected network setup and cloned AnyDesk lifecycle, without host changes."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_profiles import BASH, BUILDER, load


class SchoolSetupTests(unittest.TestCase):
    def test_small_update_packages_reviewed_helpers_with_automatic_inventory_check(self):
        packager = load('package_school_setup_update')
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'update.zip'
            packager.package(output)
            with zipfile.ZipFile(output) as archive:
                for target in packager.TARGETS:
                    data = archive.read(packager.NAME + '/' + target)
                    self.assertEqual(data, (BUILDER / packager.verifier.REVIEWED[target]).read_bytes().replace(b'\r\n', b'\n'))
                self.assertEqual(archive.getinfo(packager.NAME + '/apply_school_setup_updates.sh').external_attr >> 16 & 0o777, 0o755)
            with self.assertRaisesRegex(ValueError, 'existing'):
                packager.package(output)

    def test_alias_publisher_retries_after_a_child_exits_with_the_same_address(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            commands = {
                'python3': 'echo "enp2s0 169.254.4.5"',
                'hostname': 'echo tsavo3',
                'sleep': 'exec /usr/bin/sleep 0.15',
                'avahi-publish': '''echo "$*" >> "$CALLS"
if [[ ! -e "$ONCE" ]]; then touch "$ONCE"; exit 1; fi
exec /usr/bin/sleep 10''',
            }
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            for name, body in commands.items():
                path = bin_dir / name
                path.write_text('#!/bin/bash\n' + body + '\n', newline='\n')
                path.chmod(0o755)
            script = root / 'publisher.sh'
            text = (BUILDER / 'templates/ares_mdns_alias.sh').read_text()
            text = text.replace('source /etc/ares/mdns-profile.conf', 'ARES_ALIAS=ares.local')
            text = text.replace('while true; do', 'for iteration in {1..4}; do')
            script.write_text(text, newline='\n')
            prefix = 'export PATH="$(cygpath -u "$1"):$PATH"; ' if os.name == 'nt' else 'export PATH="$1:$PATH"; '
            result = subprocess.run([BASH, '-c', prefix + 'exec bash "$2"', 'fixture',
                                     bin_dir.as_posix(), script.as_posix()],
                                    capture_output=True, text=True, timeout=15,
                                    env=dict(os.environ, CALLS=(root / 'calls').as_posix(),
                                             ONCE=(root / 'once').as_posix()))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            calls = (root / 'calls').read_text().splitlines()
            self.assertGreaterEqual(len(calls), 2)
            self.assertTrue(all(line == '-a -R -f ares.local 169.254.4.5' for line in calls))
            self.assertIn('retaining tsavo3.local', result.stdout)

    def test_school_and_generic_nginx_names_coexist_in_each_profile(self):
        nginx = load('configure_nginx')
        for alias in ('ares.local', 'ares-test.local'):
            result = nginx.configure('server_name ares old.local;', alias, 'tsavo3.local')
            self.assertIn('tsavo3.local', result)
            self.assertIn(alias, result)
            self.assertEqual(result, nginx.configure(result, alias, 'tsavo3.local'))

    def test_lockdown_selection_waits_for_lan_and_never_auto_trusts_an_uplink(self):
        helper = load('configure_lockdown')
        devs = [dict(ifname='enp2s0', flags=['UP'], addr_info=[dict(
            family='inet', local='192.168.12.113', prefixlen=24)]),
            dict(ifname='docker0', flags=['UP'], addr_info=[dict(
                family='inet', local='172.17.0.1', prefixlen=16)])]
        options = helper.candidates(devs)
        self.assertEqual(options, ['enp2s0=192.168.12.0/24'])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'internet-lockdown.conf'
            self.assertEqual(helper.configure([], path=path), 2)
            self.assertFalse(path.exists())
            self.assertEqual(helper.configure(options, ask=lambda _: '', path=path), 2)
            self.assertFalse(path.exists())
            self.assertEqual(helper.configure(options, ask=lambda _: '1', path=path), 0)
            self.assertTrue(helper.current_matches(path, options))
            self.assertFalse(helper.current_matches(path, ['enp2s0=192.168.13.0/24']))
            self.assertEqual(helper.configure(options, ask=lambda _: '2', path=path), 2)
            self.assertTrue(helper.current_matches(path, options))

    def fixture(self, root, *, interactive=True, active=False, password_failure=False, no_id=False):
        bin_dir = root / 'bin'
        bin_dir.mkdir()
        state = root / 'state'
        config = root / 'config'
        config.mkdir()
        (config / 'system.conf').write_text('cloned system')
        (config / 'service.conf').write_text('cloned service and identity')
        idfile = root / 'id'
        idfile.write_text('123456789')
        calls = root / 'calls'
        commands = {
            'flock': 'exit 0',
            'pkill': 'echo "pkill $*" >> "$CALLS"\nexit 1',
            'getent': 'exit 0',
            'nft': '[[ "$ACTIVE" == yes ]]',
            'systemctl': '''echo "systemctl $*" >> "$CALLS"
if [[ "$1" == is-enabled ]]; then exit 1; fi
if [[ "$1" == enable ]]; then
  if [[ "$NO_ID" == yes ]]; then printf 0 > "$IDFILE"; else printf 987654321 > "$IDFILE"; fi
fi
exit 0''',
            'anydesk': '''echo "anydesk $*" >> "$CALLS"
if [[ "$1" == --get-id ]]; then cat "$IDFILE"; exit 0; fi
if [[ "$1" == --set-password ]]; then
  cat > "$PASSWORD_CAPTURE"
  [[ "$PASSWORD_FAILURE" != yes ]]; exit $?
fi
exit 1''',
            'sleep': 'exit 0',
        }
        for name, body in commands.items():
            file = bin_dir / name
            file.write_text('#!/bin/bash\n' + body + '\n', newline='\n')
            file.chmod(0o755)
        text = (BUILDER / 'templates/setup_anydesk.sh').read_text()
        text = text.replace("[[ ${EUID} == 0 ]] || { echo 'Run AnyDesk setup with sudo.' >&2; exit 1; }", '')
        text = text.replace('STATE=/var/lib/ares/anydesk-setup', 'STATE="' + state.as_posix() + '"')
        text = text.replace('CONFIG=/etc/anydesk', 'CONFIG="' + config.as_posix() + '"')
        if os.name == 'nt':
            # NTFS/Git Bash cannot apply Linux root-only directory ownership.
            # Ubuntu CI runs the real permissions; only this fixture adapts them.
            text = text.replace('install -d -m 0700', 'mkdir -p')
        if interactive:
            text = text.replace('[[ -t 0 ]]', 'true')
        script = root / 'setup.sh'
        script.write_text(text, newline='\n')
        env = dict(os.environ, SUDO_USER='root', CALLS=calls.as_posix(), IDFILE=idfile.as_posix(),
                   ACTIVE='yes' if active else 'no', PASSWORD_CAPTURE=(root / 'password-input').as_posix(),
                   PASSWORD_FAILURE='yes' if password_failure else 'no', NO_ID='yes' if no_id else 'no')
        prefix = 'export PATH="$(cygpath -u "$1"):$PATH"; ' if os.name == 'nt' else 'export PATH="$1:$PATH"; '
        def run(*args, text='RESET\nprivate-password\nprivate-password\n'):
            result = subprocess.run([BASH, '-c', prefix + 'exec bash "$2" "${@:3}"', 'fixture',
                                   bin_dir.as_posix(), script.as_posix(), *args],
                                  input=text.encode(), capture_output=True, env=env)
            result.stdout = result.stdout.decode()
            result.stderr = result.stderr.decode()
            return result
        return run, state, config, calls

    def test_anydesk_reset_archives_both_files_sets_password_and_rerun_keeps_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run, state, config, calls = self.fixture(root)
            result = run('ARES-S0035')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(config.exists())
            backups = list(state.glob('backup-*/system'))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / 'service.conf').read_text(), 'cloned service and identity')
            self.assertEqual((backups[0] / 'system.conf').read_text(), 'cloned system')
            self.assertIn('AnyDesk ID: 987654321', result.stdout)
            self.assertEqual((root / 'password-input').read_text(), 'private-password\n')
            self.assertNotIn('private-password', result.stdout + result.stderr + calls.read_text())
            self.assertEqual((state / 'anydesk-id.txt').read_text().strip(), '987654321')
            result = run('ARES-S0035', text='')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(calls.read_text().count('systemctl stop anydesk.service'), 1)
            result = run('ARES-S0040', text='')
            self.assertEqual(result.returncode, 2)
            self.assertEqual(calls.read_text().count('systemctl stop anydesk.service'), 1)

    def test_anydesk_offline_id_pending_and_password_retry_do_not_reset_twice(self):
        for failure in ('no_id', 'password_failure'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                run, state, config, calls = self.fixture(Path(temp), **{failure: True})
                result = run('ARES-S0035')
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertTrue((state / 'reset-done').is_file())
                self.assertIn('Pending', result.stdout)
                result = run('ARES-S0035', text='private-password\nprivate-password\n')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(calls.read_text().count('systemctl stop anydesk.service'), 1)

    def test_anydesk_defer_bad_password_active_lockdown_and_no_terminal_preserve_clone(self):
        for flags, answer in (({}, '\n'), ({}, 'RESET\nshort\nshort\n'),
                              ({'active': True}, ''), ({'interactive': False}, '')):
            with self.subTest(flags=flags, answer=answer), tempfile.TemporaryDirectory() as temp:
                run, state, config, calls = self.fixture(Path(temp), **flags)
                result = run('ARES-S0035', text=answer)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertTrue((config / 'system.conf').exists())
                if calls.exists():
                    self.assertNotIn('systemctl stop', calls.read_text())
                self.assertFalse((state / 'reset-done').exists())


if __name__ == '__main__':
    unittest.main()
