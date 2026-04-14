#!/usr/bin/env python3
"""CLI for evaluating and explaining care-cases from a signal."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator

from guardian_policy import build_carecase, explain_decision, load_policy_pack

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SIGNAL = ROOT / "interfaces" / "signals.schema.json"
SCHEMA_CARECASE = ROOT / "interfaces" / "care-case.schema.json"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate(instance: Dict[str, Any], schema_path: Path, label: str) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        message = [f"{label} validation failed:"]
        for err in errors:
            loc = ".".join(str(v) for v in err.absolute_path) or "(root)"
            message.append(f"- {loc}: {err.message}")
        raise SystemExit("\n".join(message))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(p: argparse.ArgumentParser) -> None:
        p.add_argument("--signal", required=True, help="Path to signal JSON")
        p.add_argument(
            "--policy-pack",
            default=str(ROOT / "policy" / "default.policy.json"),
            help="Path to policy pack JSON",
        )

    evaluate = sub.add_parser("evaluate", help="Build care-case JSON from a signal")
    add_common_arguments(evaluate)

    explain = sub.add_parser("explain", help="Explain policy decision for a signal")
    add_common_arguments(explain)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    signal = load_json(Path(args.signal))
    policy = load_policy_pack(Path(args.policy_pack))

    validate(signal, SCHEMA_SIGNAL, "Signal")

    if args.command == "evaluate":
        carecase = build_carecase(signal, policy)
        validate(carecase, SCHEMA_CARECASE, "Care-Case")
        print(json.dumps(carecase, ensure_ascii=False, indent=2))
        return

    explanation = explain_decision(signal, policy)
    print(json.dumps(explanation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
