"""Exercise desktop selection/launch without starting AnyDesk or changing a host."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_profiles import load

desktop = load('anydesk_desktop')


class AnyDeskDesktopTests(unittest.TestCase):
    def environment(self, display=':1'):
        return {'DISPLAY': display, 'XAUTHORITY': '/run/user/1000/gdm/Xauthority',
                'XDG_SESSION_TYPE': 'x11', 'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/1000/bus',
                'XDG_RUNTIME_DIR': '/run/user/1000', 'HOME': '/wrong/root-home',
                'UNRELATED_SECRET': 'not-inherited'}

    def test_selects_actual_x11_display_without_assuming_display_zero(self):
        env = self.environment()
        chosen, running = desktop.select_desktop([(env, ['/usr/bin/gnome-shell'])], exists=lambda _: True)
        self.assertEqual(chosen['DISPLAY'], ':1')
        self.assertEqual(chosen['XAUTHORITY'], env['XAUTHORITY'])
        self.assertNotIn('UNRELATED_SECRET', chosen)
        self.assertNotIn('HOME', chosen)
        self.assertFalse(running)

    def test_refuses_missing_ambiguous_forwarded_or_wayland_desktops(self):
        for records in ([], [(self.environment(':1'), ['gnome-shell']), (self.environment(':2'), ['cinnamon'])],
                        [(self.environment('localhost:10.0'), ['ssh'])],
                        [({**self.environment(), 'XDG_SESSION_TYPE': 'wayland'}, ['gnome-shell'])]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                desktop.select_desktop(records, exists=lambda _: True)
        with self.assertRaises(ValueError):
            desktop.select_desktop([(self.environment(), ['gnome-shell'])], exists=lambda _: False)

    def test_existing_user_client_is_retained_without_launch(self):
        user = SimpleNamespace(pw_uid=1000, pw_dir='/home/ares', pw_name='ares')
        with patch.object(desktop, 'processes', return_value=[(self.environment(), ['/usr/bin/anydesk'])]), \
                patch.object(desktop, 'select_desktop', return_value=(self.environment(), True)), \
                patch.object(desktop, 'repair_profile'), \
                patch.object(desktop.subprocess, 'Popen') as launch:
            self.assertEqual(desktop.recover(user), 0)
            launch.assert_not_called()

    def test_client_launch_uses_user_environment_and_preserves_service_identity(self):
        user = SimpleNamespace(pw_uid=1000, pw_dir='/home/ares', pw_name='ares')
        with tempfile.TemporaryDirectory() as temp:
            fd = os.open(Path(temp) / 'client.log', os.O_WRONLY | os.O_CREAT, 0o600)
            with patch.object(desktop, 'processes', return_value=[]), \
                    patch.object(desktop, 'repair_profile'), \
                    patch.object(desktop, 'select_desktop', return_value=({k:v for k,v in self.environment().items() if k in desktop.ENVIRONMENT}, False)), \
                    patch.object(desktop.shutil, 'which', return_value='/usr/bin/anydesk'), \
                    patch.object(desktop.os, 'open', return_value=fd), \
                    patch.object(desktop.os, 'fchmod', create=True), \
                    patch.object(desktop.subprocess, 'Popen') as launch:
                launch.return_value.wait.return_value = 0
                self.assertEqual(desktop.recover(user), 0)
                args, kwargs = launch.call_args
                command = args[0]
                self.assertEqual(command[:6], ['runuser', '-u', 'ares', '--', 'env', '-i'])
                self.assertIn('DISPLAY=:1', command)
                self.assertIn('HOME=/home/ares', command)
                self.assertEqual(command[-1], '/usr/bin/anydesk')
                self.assertNotIn('--service', command)
                self.assertNotIn('--set-password', command)
                self.assertTrue(kwargs['start_new_session'])

    def test_profile_files_are_owned_by_desktop_user_without_touching_global_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / 'home'
            profile = home / '.anydesk'
            profile.mkdir(parents=True)
            (profile / 'user.conf').write_text('retained user preferences')
            user = SimpleNamespace(pw_uid=1000, pw_gid=1000, pw_dir=str(home), pw_name='ares')
            with patch.object(desktop.os, 'chown', create=True) as chown:
                desktop.repair_profile(user)
                self.assertEqual(chown.call_count, 2)
                for call in chown.call_args_list:
                    self.assertTrue(Path(call.args[0]).is_relative_to(profile))
                    self.assertEqual(call.args[1:], (1000, 1000))
                    self.assertFalse(call.kwargs['follow_symlinks'])
            self.assertEqual((profile / 'user.conf').read_text(), 'retained user preferences')

    def test_aborting_client_is_reported_as_failure_instead_of_ready(self):
        user = SimpleNamespace(pw_uid=1000, pw_dir='/home/ares', pw_name='ares')
        with tempfile.TemporaryDirectory() as temp:
            fd = os.open(Path(temp) / 'abort.log', os.O_WRONLY | os.O_CREAT, 0o600)
            with patch.object(desktop, 'processes', return_value=[]), \
                    patch.object(desktop, 'repair_profile'), \
                    patch.object(desktop, 'select_desktop', return_value=(self.environment(), False)), \
                    patch.object(desktop.shutil, 'which', return_value='/usr/bin/anydesk'), \
                    patch.object(desktop.os, 'open', return_value=fd), \
                    patch.object(desktop.os, 'fchmod', create=True), \
                    patch.object(desktop.subprocess, 'Popen') as launch:
                launch.return_value.wait.return_value = 134
                with self.assertRaisesRegex(ValueError, 'status 134'):
                    desktop.recover(user)


if __name__ == '__main__':
    unittest.main()
