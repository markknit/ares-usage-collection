#!/usr/bin/env python3
"""Select the student LAN when connected; never activate a firewall."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

CONFIG = Path('/etc/ares/internet-lockdown.conf')


def candidates(devices):
    result = set()
    for dev in devices:
        name = dev['ifname']
        if (not re.fullmatch(r'[A-Za-z0-9_.:@-]{1,15}', name)
                or name == 'lo' or name.startswith(('docker', 'br-', 'veth', 'virbr',
                                                     'tailscale', 'tun', 'tap', 'wg'))
                or 'UP' not in dev.get('flags', [])):
            continue
        for address in dev.get('addr_info', []):
            if address.get('family') != 'inet':
                continue
            try:
                network = ipaddress.IPv4Interface(
                    f"{address['local']}/{address['prefixlen']}").network
            except (KeyError, ValueError):
                continue
            if (network.prefixlen == 0 or network.is_loopback or network.is_multicast
                    or network.is_link_local or network.overlaps(ipaddress.ip_network('100.64.0.0/10'))):
                continue
            result.add(f'{name}={network}')
    return sorted(result)


def current_matches(path, options):
    if not path.is_file():
        return False
    # Parse only the installer-owned literal mapping, never execute config here.
    value = path.read_text()
    match = re.search(r'^ARES_LAN_NETWORKS=(.*)$', value, re.M)
    if not match:
        return False
    import shlex
    try:
        words = shlex.split(match[1])
    except ValueError:
        return False
    pairs = ' '.join(words).replace(',', ' ').split()
    return bool(pairs) and all(pair in options for pair in pairs)


def configure(options, ask=input, path=CONFIG):
    if not options:
        print('Lockdown commands are installed. Connect a student LAN with an IPv4 address,')
        print('then run lockdown-internet again. Restore works without a LAN selection.')
        return 2
    print('Select the network(s) used by student devices to reach ARES:')
    for index, pair in enumerate(options, 1):
        print(f'  {index}) {pair}')
    print('Do not select a modem-only uplink. This also applies to a single interface.')
    reply = ask('Student LAN number(s), separated by commas (Enter to defer): ').strip()
    if not re.fullmatch(r'[0-9]+(?:,[0-9]+)*', reply):
        print('LAN selection deferred; no firewall changes made.')
        return 2
    indices = [int(x) - 1 for x in reply.split(',')]
    if len(set(indices)) != len(indices) or any(i < 0 or i >= len(options) for i in indices):
        print('Invalid LAN selection; no configuration changed.')
        return 2
    selected = [options[i] for i in indices]
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep existing gateway labelling when reselecting the LAN.
    mode = 'gateway' if path.is_file() and re.search(
        r'^ARES_MODE=[\'\"]?gateway[\'\"]?$', path.read_text(), re.M) else 'server'
    import shlex
    value = 'ARES_LAN_NETWORKS=' + shlex.quote(' '.join(selected)) + '\nARES_MODE=' + mode + '\n'
    fd, temporary = tempfile.mkstemp(prefix='.lockdown-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(value)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print('Saved student LAN: ' + ', '.join(selected) + '. Firewall not activated by setup.')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-current', action='store_true')
    args = parser.parse_args()
    devices = json.loads(subprocess.check_output(['ip', '-j', '-4', 'addr', 'show'], text=True))
    options = candidates(devices)
    if args.check_current:
        sys.exit(0 if current_matches(CONFIG, options) else 2)
    if os.geteuid() != 0:
        sys.exit('Run LAN configuration as root.')
    if not sys.stdin.isatty():
        print('LAN selection needs a terminal. Run lockdown-internet after connecting the LAN.')
        sys.exit(2)
    try:
        sys.exit(configure(options))
    except (EOFError, KeyboardInterrupt):
        sys.exit(2)
