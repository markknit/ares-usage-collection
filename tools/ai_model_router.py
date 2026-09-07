#!/usr/bin/env python3
"""Recommend an OpenAI model for an ARES development task.

This tool is intentionally deterministic. It does not call an LLM or the
OpenAI API. Routing rules live in config/ai_model_routing.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "ai_model_routing.json"
MODEL_RANK = {"terra": 1, "sol": 2, "astra": 3}


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def max_model(left: str, right: str) -> str:
    return left if MODEL_RANK[left] >= MODEL_RANK[right] else right


def route(args: argparse.Namespace, config: dict) -> tuple[str, list[str], str | None]:
    model = config.get("task_type_defaults", {}).get(args.type, config["default_model"])
    reasons = [f"{args.type} defaults to {model}"]

    sol = config["sol_triggers"]
    sol_reasons = []
    if args.architecture_impact in sol.get("architecture_impact", []):
        sol_reasons.append(f"architecture impact is {args.architecture_impact}")
    if args.components >= sol.get("minimum_components", 999999):
        sol_reasons.append(f"task spans {args.components} components")
    if args.files >= sol.get("minimum_files", 999999):
        sol_reasons.append(f"task affects about {args.files} files")
    if args.previous_failures >= sol.get("minimum_previous_failures", 999999):
        sol_reasons.append(f"{args.previous_failures} previous attempt(s) failed")
    if args.cross_boundary and sol.get("cross_boundary", False):
        sol_reasons.append("task crosses a system boundary")
    if sol_reasons:
        model = max_model(model, "sol")
        reasons.extend(sol_reasons)

    astra = config["astra_triggers"]
    astra_reasons = []
    if args.architecture_impact in astra.get("architecture_impact", []):
        astra_reasons.append(f"architecture impact is {args.architecture_impact}")
    if args.risk in astra.get("risk", []):
        astra_reasons.append(f"risk is {args.risk}")
    if args.previous_sol_failures >= astra.get("minimum_previous_sol_failures", 999999):
        astra_reasons.append(f"Sol has failed {args.previous_sol_failures} time(s)")
    if args.irreversible_design and astra.get("irreversible_design", False):
        astra_reasons.append("design is difficult to reverse")
    if astra_reasons:
        model = "astra"
        reasons.extend(astra_reasons)

    review_model = None
    mandatory = config.get("mandatory_review", {})
    if args.area and args.area in mandatory.get("areas", []):
        review_model = mandatory.get("minimum_review_model", "sol")
        reasons.append(f"{args.area} requires at least {review_model} review")

    return model, reasons, review_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", required=True, help="Task type, e.g. implementation, debugging, config")
    parser.add_argument("--files", type=int, default=1, help="Approximate number of affected files")
    parser.add_argument("--components", type=int, default=1, help="Number of interacting components/systems")
    parser.add_argument("--architecture-impact", choices=("low", "medium", "high"), default="low")
    parser.add_argument("--risk", choices=("low", "medium", "high"), default="low")
    parser.add_argument("--previous-failures", type=int, default=0)
    parser.add_argument("--previous-sol-failures", type=int, default=0)
    parser.add_argument("--cross-boundary", action="store_true")
    parser.add_argument("--irreversible-design", action="store_true")
    parser.add_argument("--area", help="Sensitive area such as collection-integrity or reporting-semantics")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    for name in ("files", "components", "previous_failures", "previous_sol_failures"):
        if getattr(args, name) < 0:
            parser.error(f"--{name.replace('_', '-')} cannot be negative")

    config = load_config(args.config)
    model, reasons, review_model = route(args, config)
    result = {
        "recommended_model": model,
        "mandatory_review_model": review_model,
        "reason": "; ".join(reasons),
        "policy_version": config.get("version", 1),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"MODEL={model}")
        if review_model:
            print(f"REVIEW_MODEL={review_model}")
        print(f"REASON={result['reason']}")
        print(f"POLICY_VERSION={result['policy_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
