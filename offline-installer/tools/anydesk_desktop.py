#!/usr/bin/env python3
"""Relaunch AnyDesk in the existing local X11 desktop without resetting identity."""
import argparse
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

ENVIRONMENT = ('DISPLAY', 'XAUTHORITY', 'DBUS_SESSION_BUS_ADDRESS',
               'XDG_RUNTIME_DIR', 'XDG_SESSION_TYPE')


def repair_profile(user):
    profile = Path(user.pw_dir).resolve() / '.anydesk'
    if profile.is_symlink():
        raise ValueError('User AnyDesk folder is a symlink; no ownership change performed.')
    profile.mkdir(mode=0o700, exist_ok=True)
    for path in [profile, *profile.rglob('*')]:
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat().st_mode) | stat.S_IRUSR | stat.S_IWUSR
        if path.is_dir():
            mode |= stat.S_IXUSR
        os.chown(path, user.pw_uid, user.pw_gid, follow_symlinks=False)
        path.chmod(mode)


def processes(uid, proc=Path('/proc')):
    for path in proc.iterdir():
        if not path.name.isdigit():
            continue
        try:
            if path.stat().st_uid != uid:
                continue
            environment = dict(item.split('=', 1) for item in
                               (path / 'environ').read_bytes().decode(errors='replace').split('\0')
                               if '=' in item)
            arguments = (path / 'cmdline').read_bytes().decode(errors='replace').split('\0')
            yield environment, arguments
        except (OSError, ValueError):
            continue


def select_desktop(records, exists=lambda path: Path(path).is_file()):
    candidates = {}
    running = set()
    for environment, arguments in records:
        display = environment.get('DISPLAY', '')
        authority = environment.get('XAUTHORITY', '')
        if (environment.get('XDG_SESSION_TYPE') != 'x11'
                or not re.fullmatch(r':\d+(?:\.\d+)?', display)
                or not authority or not exists(authority)):
            continue
        key = display, authority
        selected = {name: environment[name] for name in ENVIRONMENT if name in environment}
        if len(selected) > len(candidates.get(key, {})):
            candidates[key] = selected
        if arguments and Path(arguments[0]).name == 'anydesk' and '--service' not in arguments:
            running.add(key)
    if len(candidates) != 1:
        raise ValueError('No single local X11 desktop could be selected. Log into the ARES Xorg desktop and retry; no desktop or identity was changed.')
    key, environment = next(iter(candidates.items()))
    return environment, key in running


def recover(user, *, check=False):
    environment, running = select_desktop(list(processes(user.pw_uid)))
    if not check:
        repair_profile(user)
    if running:
        print('AnyDesk desktop client is already running; retaining it.')
        return 0
    if check:
        print('X11 desktop found, but the AnyDesk desktop client is absent.')
        return 2
    binary = shutil.which('anydesk')
    if not binary:
        raise ValueError('AnyDesk is not installed; no download attempted.')
    environment.update(HOME=user.pw_dir, USER=user.pw_name, LOGNAME=user.pw_name)
    # Do not inherit root's desktop, authentication socket or shell environment.
    command = ['runuser', '-u', user.pw_name, '--', 'env', '-i',
               'PATH=/usr/local/bin:/usr/bin:/bin']
    command += [key + '=' + value for key, value in environment.items()]
    command.append(binary)
    path = '/var/log/ares-anydesk-desktop.log'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'ab') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True, close_fds=True)
        try:
            status = process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            status = None
        if status not in (None, 0):
            raise ValueError(f'Desktop client exited with status {status}; see {path}. ID/password retained.')
    print('AnyDesk desktop client launch requested on ' + environment['DISPLAY'] + '.')
    print('ID/password retained. Verify an actual unattended connection; launch is not a connection test.')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if os.geteuid() != 0:
        sys.exit('Run with sudo so the existing desktop environment can be read.')
    import pwd
    try:
        sys.exit(recover(pwd.getpwnam('ares'), check=args.check))
    except (OSError, KeyError, ValueError) as error:
        print('AnyDesk desktop recovery Pending: ' + str(error), file=sys.stderr)
        print('No ID reset, display-manager restart or firewall change performed.', file=sys.stderr)
        sys.exit(2)
