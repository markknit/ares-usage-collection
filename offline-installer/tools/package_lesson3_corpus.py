#!/usr/bin/env python3
"""Validate and package the pinned ARES JSON corpus for offline Lesson3 import."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


MAX_FILE_BYTES = 5 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"corpus-packager: ERROR: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--expected-files", type=int, required=True)
    parser.add_argument("--expected-lessons", type=int, required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_dir():
        fail(f"source directory does not exist: {source}")

    candidates = sorted(source.rglob("*_data.json"))
    if len(candidates) != args.expected_files:
        fail(
            f"expected {args.expected_files} *_data.json files at pinned commit; "
            f"found {len(candidates)}"
        )

    names: set[str] = set()
    identities: set[tuple[str, int, str]] = set()
    records: list[dict[str, object]] = []
    taxonomy: set[tuple[str, int]] = set()
    total_lessons = 0

    for path in candidates:
        if path.name in names:
            fail(f"duplicate filename would collide in the flat field package: {path.name}")
        names.add(path.name)

        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            fail(f"{path.name} exceeds Lesson3's 5 MiB per-file upload limit")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            fail(f"cannot parse {path}: {exc}")
        if not isinstance(data, dict):
            fail(f"{path.name}: top-level value is not an object")
        if data.get("schemaVersion") != "1.0.0":
            fail(f"{path.name}: schemaVersion is not 1.0.0")

        meta = data.get("META")
        lessons = data.get("LESSONS")
        if not isinstance(meta, dict):
            fail(f"{path.name}: META is not an object")
        if not isinstance(lessons, list) or not lessons:
            fail(f"{path.name}: LESSONS is not a non-empty array")

        subject = meta.get("subject")
        grade = meta.get("grade")
        substrand_id = meta.get("substrand_id")
        if not isinstance(subject, str) or not subject.strip():
            fail(f"{path.name}: META.subject is missing or invalid")
        if isinstance(grade, bool) or not isinstance(grade, int):
            fail(f"{path.name}: META.grade is not an integer")
        if not isinstance(substrand_id, str) or not substrand_id.strip():
            fail(f"{path.name}: META.substrand_id is missing or invalid")

        subject = subject.strip()
        substrand_id = substrand_id.strip()
        identity = (subject, grade, substrand_id)
        if identity in identities:
            fail(
                f"duplicate Lesson3 identity subject={subject!r}, grade={grade}, "
                f"substrand_id={substrand_id!r}"
            )
        identities.add(identity)
        taxonomy.add((subject, grade))
        total_lessons += len(lessons)
        records.append(
            {
                "file": path.name,
                "sha256": sha256(path),
                "bytes": size,
                "subject": subject,
                "grade": grade,
                "substrand_id": substrand_id,
                "lessons": len(lessons),
            }
        )

    if total_lessons != args.expected_lessons:
        fail(
            f"expected {args.expected_lessons} lessons at pinned commit; "
            f"found {total_lessons}"
        )

    if output.exists():
        shutil.rmtree(output)
    files_dir = output / "files"
    files_dir.mkdir(parents=True)
    for path in candidates:
        shutil.copy2(path, files_dir / path.name)

    taxonomy_rows = sorted(taxonomy, key=lambda item: (item[0].casefold(), item[1]))
    (output / "taxonomy.tsv").write_text(
        "".join(f"{subject}\t{grade}\n" for subject, grade in taxonomy_rows),
        encoding="utf-8",
    )

    manifest = {
        "format": "ares-lesson3-offline-corpus-v1",
        "source_repository": args.repo,
        "source_commit": args.commit,
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0.0",
        "file_count": len(records),
        "lesson_count": total_lessons,
        "subject_count": len({subject for subject, _ in taxonomy_rows}),
        "subject_grade_count": len(taxonomy_rows),
        "files": records,
    }
    (output / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    checksummed = [output / "MANIFEST.json", output / "taxonomy.tsv", *sorted(files_dir.iterdir())]
    with (output / "SHA256SUMS").open("w", encoding="utf-8") as handle:
        for path in checksummed:
            handle.write(f"{sha256(path)}  {path.relative_to(output).as_posix()}\n")

    print(
        "corpus-packager: packaged "
        f"{len(records)} files, {total_lessons} lessons, "
        f"{manifest['subject_count']} subjects, {len(taxonomy_rows)} subject-grades"
    )


if __name__ == "__main__":
    main()
