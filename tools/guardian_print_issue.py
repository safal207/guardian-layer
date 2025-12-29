#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


def load_json(path_str: str) -> Dict[str, Any]:
    p = Path(path_str)
    if not p.is_absolute():
        p = ROOT / p
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def title(case: Dict[str, Any]) -> str:
    gate = case.get("policy_gate", "unknown")
    summary = case.get("summary", "Unnamed care-case")
    return f"Care-Case ({gate}): {summary}"


def body(case: Dict[str, Any]) -> str:
    gate = case.get("policy_gate", "unknown")
    action = case.get("recommended_action", "observe")
    tension = case.get("tension", 0)
    system = case.get("system", {})
    sys_name = system.get("name", "unknown")
    sys_env = system.get("env", "unknown")
    sys_ver = system.get("version", "unknown")

    constraints = case.get("constraints", [])
    signals = case.get("signals", [])
    signal_ids = [s.get("signal_id") for s in signals if isinstance(s, dict)]

    pretty_json = json.dumps(case, ensure_ascii=False, indent=2)

    lines = []
    lines.append(f"**System:** `{sys_name}`  \n**Env:** `{sys_env}`  \n**Version:** `{sys_ver}`")
    lines.append("")
    lines.append(f"**Policy gate:** `{gate}`")
    lines.append(f"**Recommended action:** `{action}`")
    lines.append(f"**Tension:** `{tension}`")
    lines.append("")
    if signal_ids:
        lines.append("**Signals:**")
        for sid in signal_ids:
            lines.append(f"- `{sid}`")
        lines.append("")
    if constraints:
        lines.append("**Constraints:**")
        for c in constraints:
            lines.append(f"- `{c}`")
        lines.append("")
    if case.get("root_cause_hypothesis"):
        lines.append("**Root-cause hypothesis (not a fact):**")
        lines.append(case["root_cause_hypothesis"])
        lines.append("")
    if case.get("proposed_transition"):
        pt = case["proposed_transition"]
        lines.append("**Proposed transition (intent):**")
        lines.append(f"- intent: {pt.get('intent')}")
        lines.append(f"- scope: {pt.get('scope')}")
        lines.append(f"- reversibility: {pt.get('reversibility')}")
        v = pt.get("verification", [])
        if v:
            lines.append("- verification:")
            for item in v:
                lines.append(f"  - {item}")
        lines.append("")
    lines.append("```json")
    lines.append(pretty_json)
    lines.append("```")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", help="Print title for given care-case file")
    ap.add_argument("--body", help="Print body for given care-case file")
    args = ap.parse_args()

    if bool(args.title) == bool(args.body):
        raise SystemExit("Provide exactly one of --title or --body")

    path = args.title or args.body
    case = load_json(path)

    if args.title:
        print(title(case))
    else:
        print(body(case))


if __name__ == "__main__":
    main()
