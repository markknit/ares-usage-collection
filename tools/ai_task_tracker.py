#!/usr/bin/env python3
"""Track AI-assisted ARES development work in Git commit metadata.

Usage:
  python3 tools/ai_task_tracker.py commit \
      --model terra --recommended-model terra --routing-policy-version 1 \
      --type implementation --retries 0 \
      --message "Implement school sync validation"

  python3 tools/ai_task_tracker.py export --output ai-task-log.csv

The commit subcommand creates a normal Git commit whose message includes
machine-readable trailers. The export subcommand converts those trailers into
CSV for later comparison with OpenAI usage/credit exports.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

MODELS = ("terra", "sol", "astra", "other")
OUTCOMES = ("success", "partial", "failed")


def run_git(args: list[str], *, capture: bool = True) -> str:
    result = subprocess.run(["git", *args], check=True, text=True, capture_output=capture)
    return result.stdout if capture else ""


def make_task_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"ares-{stamp}-{uuid.uuid4().hex[:6]}"


def cmd_commit(args: argparse.Namespace) -> int:
    status = run_git(["status", "--porcelain"]).strip()
    if not status:
        print("No staged or unstaged changes to commit.", file=sys.stderr)
        return 2

    task_id = args.task_id or make_task_id()
    escalated = "yes" if args.escalated_from else "no"
    trailers = [
        f"AI-Task-ID: {task_id}",
        f"AI-Model: {args.model}",
        f"AI-Recommended-Model: {args.recommended_model or args.model}",
        f"AI-Routing-Policy-Version: {args.routing_policy_version}",
        f"AI-Task-Type: {args.type}",
        f"AI-Retries: {args.retries}",
        f"AI-Escalated: {escalated}",
        f"AI-Outcome: {args.outcome}",
    ]
    if args.override_reason:
        trailers.append(f"AI-Model-Override-Reason: {args.override_reason}")
    if args.escalated_from:
        trailers.append(f"AI-Escalated-From: {args.escalated_from}")
    if args.reason:
        trailers.append(f"AI-Escalation-Reason: {args.reason}")

    git_args = ["commit"]
    if args.all:
        git_args.append("-a")
    git_args.extend(["-m", args.message, "-m", "\n".join(trailers)])
    run_git(git_args, capture=False)

    commit_sha = run_git(["rev-parse", "HEAD"]).strip()
    print(f"AI task {task_id} committed as {commit_sha}")
    return 0


def parse_trailers(message: str) -> dict[str, str]:
    wanted = {
        "AI-Task-ID", "AI-Model", "AI-Recommended-Model", "AI-Routing-Policy-Version",
        "AI-Model-Override-Reason", "AI-Task-Type", "AI-Retries", "AI-Escalated",
        "AI-Escalated-From", "AI-Escalation-Reason", "AI-Outcome",
    }
    found: dict[str, str] = {}
    for line in message.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key in wanted:
            found[key] = value.strip()
    return found


def cmd_export(args: argparse.Namespace) -> int:
    raw = run_git(["log", "--format=%H%x1f%cI%x1f%B%x1e"])
    rows = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f", 2)
        if len(parts) != 3:
            continue
        sha, committed_at, message = parts
        trailers = parse_trailers(message)
        if "AI-Task-ID" not in trailers:
            continue
        subject = message.splitlines()[0] if message.splitlines() else ""
        rows.append({
            "task_id": trailers.get("AI-Task-ID", ""),
            "committed_at": committed_at,
            "commit_sha": sha,
            "task": subject,
            "task_type": trailers.get("AI-Task-Type", ""),
            "recommended_model": trailers.get("AI-Recommended-Model", ""),
            "actual_model": trailers.get("AI-Model", ""),
            "routing_policy_version": trailers.get("AI-Routing-Policy-Version", ""),
            "model_override_reason": trailers.get("AI-Model-Override-Reason", ""),
            "retries": trailers.get("AI-Retries", ""),
            "escalated": trailers.get("AI-Escalated", ""),
            "escalated_from": trailers.get("AI-Escalated-From", ""),
            "escalation_reason": trailers.get("AI-Escalation-Reason", ""),
            "outcome": trailers.get("AI-Outcome", ""),
        })

    fields = ["task_id", "committed_at", "commit_sha", "task", "task_type",
              "recommended_model", "actual_model", "routing_policy_version",
              "model_override_reason", "retries", "escalated", "escalated_from",
              "escalation_reason", "outcome"]
    if args.output == "-":
        handle, close = sys.stdout, False
    else:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, close = path.open("w", newline="", encoding="utf-8"), True
    try:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if close:
            handle.close()
    if args.output != "-":
        print(f"Exported {len(rows)} AI task records to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    commit = subparsers.add_parser("commit", help="Commit staged work with AI task metadata")
    commit.add_argument("--model", choices=MODELS, required=True, help="Model actually used")
    commit.add_argument("--recommended-model", choices=MODELS, help="Router recommendation; defaults to actual model")
    commit.add_argument("--routing-policy-version", type=int, default=1)
    commit.add_argument("--override-reason", help="Why actual model differed from router recommendation")
    commit.add_argument("--type", required=True)
    commit.add_argument("--retries", type=int, default=0)
    commit.add_argument("--outcome", choices=OUTCOMES, default="success")
    commit.add_argument("--escalated-from", choices=MODELS)
    commit.add_argument("--reason", help="Short escalation reason")
    commit.add_argument("--task-id", help="Reuse a task ID when a task spans multiple commits")
    commit.add_argument("--message", required=True)
    commit.add_argument("--all", action="store_true", help="Pass -a to git commit")
    commit.set_defaults(func=cmd_commit)
    export = subparsers.add_parser("export", help="Export AI-tagged commits as CSV")
    export.add_argument("--output", default="-", help="CSV path, or - for stdout")
    export.set_defaults(func=cmd_export)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "retries", 0) < 0:
        parser.error("--retries cannot be negative")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
