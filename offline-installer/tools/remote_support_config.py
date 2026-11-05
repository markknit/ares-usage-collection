#!/usr/bin/env python3
"""Pure transformations used by the canonical remote-support command."""
import argparse
import re
import json
import sys
from pathlib import Path


def hostname(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")[:63].rstrip("-")
    if not value:
        raise ValueError("School name cannot form a hostname")
    return value


def hosts(value, old, new):
    result = []
    found = False
    for line in value.splitlines():
        content, separator, comment = line.partition("#")
        fields = content.split()
        if fields and fields[0] == "127.0.1.1":
            aliases = [item for item in fields[1:] if item not in (old, new)]
            line = "127.0.1.1\t" + " ".join([new] + aliases)
            if separator:
                line += " #" + comment
            found = True
        result.append(line)
    if not found:
        result.append("127.0.1.1\t" + new)
    return "\n".join(result) + "\n"


def display_map(value):
    found = False
    result = []
    for line in value.splitlines():
        content = line.split("#", 1)[0].strip()
        if re.match(r"^:1\s*=", content):
            if content.split("=", 1)[1].strip() != "ares":
                raise ValueError("Display :1 belongs to another user")
            if found:
                continue
            found = True
        result.append(line)
    if not found:
        result.append(":1=ares")
    return "\n".join(result) + "\n"


def vnc_route(value):
    """Classify only this node's VNC route; never replace another service."""
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError('Invalid Tailscale Serve configuration')
    configs = [value, *(value.get('Foreground') or {}).values()]
    for entry in configs:
        if any(enabled and target.endswith(':5901')
               for target, enabled in (entry.get('AllowFunnel') or {}).items()):
            return 'conflict'
    if any('5901' in (entry.get('TCP') or {}) for entry in configs[1:]):
        return 'conflict'
    handler = (value.get('TCP') or {}).get('5901')
    if handler is None:
        return 'absent'
    if handler == {'TCPForward': '127.0.0.1:5901'}:
        return 'configured'
    return 'conflict'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("hostname", "hosts", "display", "connected", "vnc-route", "connection-summary", "redact"))
    parser.add_argument("values", nargs="*")
    args = parser.parse_args()
    if args.mode == "hostname":
        try:
            print(hostname(args.values[0] if args.values else ''))
        except ValueError as error:
            parser.exit(2, str(error) + '\n')
    elif args.mode == "hosts":
        print(hosts(Path(args.values[0]).read_text(), args.values[1], args.values[2]), end="")
    elif args.mode == "display":
        path = Path(args.values[0])
        print(display_map(path.read_text() if path.exists() else ""), end="")
    elif args.mode == "connected":
        state = json.load(sys.stdin)
        sys.exit(0 if state.get("BackendState") == "Running" and state.get("Self", {}).get("Online") is True else 1)
    elif args.mode == 'vnc-route':
        try:
            print(vnc_route(json.load(sys.stdin)))
        except (ValueError, AttributeError, TypeError) as error:
            parser.exit(2, 'Cannot check the existing VNC route: ' + str(error) + '\n')
    elif args.mode == 'connection-summary':
        state = json.load(sys.stdin)
        print('Tailscale state:', state.get('BackendState', 'unknown'))
        print('Coordination connection:', 'online' if (state.get('Self') or {}).get('Online') else 'offline')
        for message in state.get('Health') or []:
            print('Tailscale health:', re.sub(r'https?://\S+', '[URL omitted]', message))
    else:
        # Enrollment bypasses logs entirely. Defense in depth for diagnostic
        # output: no HTTP(S) URL from a subprocess is persisted by tee either.
        for line in sys.stdin:
            print(re.sub(r"https?://\S+", "[URL omitted]", line), end="", flush=True)
