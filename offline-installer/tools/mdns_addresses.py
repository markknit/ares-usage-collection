#!/usr/bin/env python3
"""List usable local IPv4 endpoints, including a LAN without DHCP."""
import ipaddress
import json
import subprocess


def endpoints(devices):
    result = set()
    for dev in devices:
        name = dev['ifname']
        if (name == 'lo' or name.startswith(('docker', 'br-', 'veth', 'virbr',
                                            'tailscale', 'tun', 'tap', 'wg'))
                or 'UP' not in dev.get('flags', [])):
            continue
        for address in dev.get('addr_info', []):
            if address.get('family') != 'inet':
                continue
            try:
                ip = ipaddress.IPv4Address(address['local'])
            except (ValueError, KeyError):
                continue
            if (ip.is_loopback or ip.is_multicast or ip.is_unspecified
                    or ip in ipaddress.ip_network('100.64.0.0/10')):
                continue
            result.add((name, str(ip)))
    def preference(pair):
        name, address = pair
        ip = ipaddress.IPv4Address(address)
        return (0 if address == '10.42.0.1' else
                4 if ip.is_link_local else
                1 if ip.is_private and name.startswith(('wl', 'en', 'eth')) else
                2 if ip.is_private else 3, name, address)
    return sorted(result, key=preference)


if __name__ == '__main__':
    devices = json.loads(subprocess.check_output(['ip', '-j', '-4', 'addr', 'show'], text=True))
    # avahi-publish registers one alias/address group on all Avahi interfaces.
    # Keep one preferred reachable LAN address, avoiding competing publishers.
    for interface, address in endpoints(devices)[:1]:
        print(interface + ' ' + address)
