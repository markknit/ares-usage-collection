#!/usr/bin/env python3
"""Create the small offline update for an already-installed v1.13 server."""
import argparse
import hashlib
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import zipfile

SELF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SELF))
import verify_offline_bundle as verifier

NAME = 'ARES_v1.13_School_Setup_Update_20261103'
TARGETS = [
    'ares_config.sh', 'package_integrity.py',
    'lesson_plan/configure_mdns.sh', 'lesson_plan/ares_mdns_alias.sh',
    'lesson_plan/mdns_addresses.py', 'lesson_plan/configure_nginx.py',
    'remote-access/prepare_internet_lockdown.sh', 'remote-access/lockdown_dispatch.sh',
    'remote-access/configure_lockdown.py', 'remote-access/prepare_anydesk.sh',
    'remote-access/setup_anydesk.sh',
]


def package(output):
    output = Path(output)
    if output.exists():
        raise ValueError('Retain the existing update ZIP; choose another output path')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / NAME
        root.mkdir()
        for target in TARGETS:
            path = root / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((SELF / verifier.REVIEWED[target]).read_bytes().replace(b'\r\n', b'\n'))
        shutil.copytree(SELF / 'internet-lockdown', root / 'remote-access/internet-lockdown')
        (root / 'apply_school_setup_updates.sh').write_bytes(
            (SELF / 'tools/apply_school_setup_updates.sh').read_bytes().replace(b'\r\n', b'\n'))
        (root / 'package.conf').write_text('LESSON3_VERSION=v0.94\nLESSON3_SERVER_URL=\nARES_PROFILE=production\n', newline='\n')
        (root / 'docs').mkdir()
        for name in ('ANYDESK_SETUP.md', 'INTERNET_LOCKDOWN.md', 'TECHNICIAN_OVERVIEW.md', 'PROFILES.md'):
            (root / 'docs' / name).write_bytes((SELF / 'docs' / name).read_bytes().replace(b'\r\n', b'\n'))
        (root / 'START_HERE.txt').write_text(
            'Offline update for an already installed ARES v1.13 production server.\n'
            'Copy this ZIP by USB/LAN and extract it into a new folder.\n'
            'From a normal Ubuntu terminal at the local console, run:\n\n'
            'sudo bash apply_school_setup_updates.sh ARES-S0035\n\n'
            'Use the real assigned code at other schools. No Internet/downloads are needed.\n'
            'This keeps the school hostname and adds ares.local, installs disconnected-safe\n'
            'lockdown/restore commands, and offers cloned AnyDesk identity/password setup.\n'
            'Type RESET only from a local console or independent connection: it stops AnyDesk.\n'
            'Enter the standard unattended password twice, and save the new ID. If Pending,\n'
            'follow docs/ANYDESK_SETUP.md later. No reset is repeated on ordinary retries.\n'
            'No firewall is activated or boot lockdown enabled. On first lockdown-internet\n'
            'use, choose the actual student LAN; restore-internet needs no LAN selection.\n'
            'This update does not rerun Lesson3, content installation or database imports.\n', newline='\n')
        manifest = root / 'SHA256SUMS'
        manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
                                   p.relative_to(root).as_posix() + '\n'
                                   for p in sorted(root.rglob('*')) if p.is_file()), newline='\n')
        verifier.integrity.verify_package(root)
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(root.rglob('*')):
                if path.is_file():
                    info = zipfile.ZipInfo(path.relative_to(root.parent).as_posix())
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | (0o755 if path.suffix == '.sh' else 0o644)) << 16
                    archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        extracted = Path(temporary) / 'independent'
        verifier.extract(output, extracted, NAME)
        verifier.integrity.verify_package(extracted / NAME)
        for target in TARGETS:
            if (extracted / NAME / target).read_bytes() != (root / target).read_bytes():
                raise ValueError('Update source mismatch: ' + target)
    checksum = verifier.integrity.digest(output)
    output.with_suffix(output.suffix + '.sha256').write_text(checksum + '  ' + output.name + '\n')
    print('Verified offline update: ' + str(output))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    package(parser.parse_args().output)
