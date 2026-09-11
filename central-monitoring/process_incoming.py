#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import re

PATTERN = re.compile(
    r'^ARES_USAGE_([A-Z0-9_-]+)_((?:20\d{2}-Q[1-4]-(?:MID|END))|AUTO)_(20\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.csv$'
)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def plausible_csv(path: pathlib.Path) -> bool:
    try:
        with path.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.reader(handle)
            first = next(reader, None)
            if first is None or len(first) < 2:
                return False
            return any(row for row in reader)
    except (OSError, UnicodeDecodeError, csv.Error):
        return False


def load_state(path: pathlib.Path) -> dict:
    if not path.exists():
        return {'version': 1, 'sha256': {}}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('sha256'), dict):
        raise ValueError('invalid processor state')
    data.setdefault('version', 1)
    return data


def write_state(path: pathlib.Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def unique_reject_path(directory: pathlib.Path, name: str) -> pathlib.Path:
    target = directory / name
    if not target.exists():
        return target
    stem = pathlib.Path(name).stem
    suffix = pathlib.Path(name).suffix
    counter = 1
    while True:
        candidate = directory / f'{stem}.{counter}{suffix}'
        if not candidate.exists():
            return candidate
        counter += 1


def quarantine(path: pathlib.Path, rejected_dir: pathlib.Path, reason: str, rejected: list) -> None:
    rejected_dir.mkdir(parents=True, exist_ok=True)
    target = unique_reject_path(rejected_dir, path.name)
    shutil.move(str(path), str(target))
    rejected.append({'file': path.name, 'reason': reason, 'quarantined_as': target.name})


def archive_file(source: pathlib.Path, destination: pathlib.Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=destination.name + '.', suffix='.tmp', dir=str(destination.parent))
    os.close(fd)
    temp_path = pathlib.Path(temp_name)
    try:
        shutil.copy2(source, temp_path)
        if sha256_file(source) != sha256_file(temp_path):
            raise OSError('archive copy verification failed')
        os.replace(temp_path, destination)
        source.unlink()
    finally:
        if temp_path.exists():
            temp_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Process ARES usage CSV files uploaded to a local HTTPS incoming directory.'
    )
    parser.add_argument('--incoming', required=True, help='Local directory populated by the HTTPS upload service.')
    parser.add_argument('--archive', required=True, help='Local archive root for accepted files.')
    parser.add_argument('--state', default='processed.json', help='Processor state file. Default: processed.json')
    parser.add_argument('--rejected', help='Quarantine directory. Default: sibling rejected directory next to incoming.')
    parser.add_argument('--report-command', help='Shell command to run once after one or more new files are accepted.')
    args = parser.parse_args()

    incoming = pathlib.Path(args.incoming)
    archive = pathlib.Path(args.archive)
    state_path = pathlib.Path(args.state)
    rejected_dir = pathlib.Path(args.rejected) if args.rejected else incoming.parent / 'rejected'

    if not incoming.is_dir():
        print(f'incoming directory does not exist: {incoming}', file=sys.stderr)
        return 1

    state = load_state(state_path)
    processed = []
    duplicates = []
    rejected = []

    for path in sorted(incoming.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            continue

        match = PATTERN.match(path.name)
        if not match:
            quarantine(path, rejected_dir, 'invalid filename', rejected)
            continue

        digest = sha256_file(path)
        if digest in state['sha256']:
            path.unlink()
            duplicates.append(path.name)
            continue

        if not plausible_csv(path):
            quarantine(path, rejected_dir, 'not a plausible CSV', rejected)
            continue

        school, collection, stamp = match.groups()
        destination = archive / collection / school / path.name
        if destination.exists():
            if sha256_file(destination) == digest:
                path.unlink()
                state['sha256'][digest] = {
                    'file': path.name,
                    'school': school,
                    'collection': collection,
                    'timestamp': stamp,
                }
                write_state(state_path, state)
                duplicates.append(path.name)
                continue
            quarantine(path, rejected_dir, 'archive filename conflict', rejected)
            continue

        archive_file(path, destination)
        state['sha256'][digest] = {
            'file': destination.name,
            'school': school,
            'collection': collection,
            'timestamp': stamp,
        }
        write_state(state_path, state)
        processed.append(destination.name)

    if processed and args.report_command:
        subprocess.run(args.report_command, shell=True, check=True)

    print(json.dumps({'processed': processed, 'duplicates': duplicates, 'rejected': rejected}, indent=2))
    return 2 if rejected else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
