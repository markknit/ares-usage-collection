#!/usr/bin/env python3
"""Package the canonical LAN support controls for an already installed server."""
import argparse
import hashlib
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parent
FILES = {
    'apply_lan_support_update.sh': 'updates/apply_lan_support_update.sh',
    'remote-access/ares_enable_remote_access.sh': 'templates/ares_enable_remote_access.sh',
    'remote-access/ares_disable_remote_access.sh': 'templates/ares_disable_remote_access.sh',
    'remote-access/remote_support_common.sh': 'templates/remote_support_common.sh',
    'remote-access/remote_support_config.py': 'tools/remote_support_config.py',
    'REMOTE_ACCESS.md': 'docs/REMOTE_ACCESS.md',
}
README = '''ARES LAN desktop update - November 6, 2026

For an ARES v1.13 server with the optional TigerVNC packages already installed.
Extract this ZIP into a fresh folder. From LAN SSH, AnyDesk or a local terminal:

    sudo bash apply_lan_support_update.sh

The virtual VNC desktop will restart. Its existing password is retained;
if none is configured, enter and confirm a VNC password when prompted.
Connect the technician computer to the school LAN and open:

    <SERVER-LAN-IP>::5901

Internet and Tailscale are not required. Use the same VNC password as before.
The service starts automatically at boot and works without a monitor.
Existing Tailscale identity, service state and forwarding are retained.
Existing Tailscale VNC connections remain available when Tailscale is connected.
No Lesson3/content installation, database import or AnyDesk reset is performed.

To add Tailscale access later, with Internet available:

    sudo ares-enable-remote-access

See REMOTE_ACCESS.md for details. Other host firewall rules must allow TCP 5901.
'''


def build(output):
    payload = {name: (ROOT / source).read_bytes().replace(b'\r\n', b'\n')
               for name, source in FILES.items()}
    payload['README.txt'] = README.encode()
    payload['SHA256SUMS'] = ''.join(
        hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
        for name, data in sorted(payload.items())).encode()
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | (0o755 if name.endswith('.sh') else 0o644)) << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(payload)
        for name, data in payload.items():
            assert archive.read(name) == data, name
    return Path(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    print(build(parser.parse_args().output))
