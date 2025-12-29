#!/usr/bin/env python3
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SIGNAL = ROOT / "interfaces" / "signals.schema.json"
SCHEMA_CARECASE = ROOT / "interfaces" / "care-case.schema.json"
OUT_DIR = ROOT / "generated"


def _run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, cwd=ROOT, text=True).strip()


def changed_signal_files() -> List[Path]:
    # Compare last commit to previous (works with fetch-depth 2)
    before = os.environ.get("GITHUB_BEFORE")
    after = os.environ.get("GITHUB_SHA")
    if before and after and before != "0000000000000000000000000000000000000000":
        diff = _run(["bash", "-lc", f"git diff --name-only {before} {after}"])
    else:
        diff = _run(["bash", "-lc", "git diff --name-only HEAD~1 HEAD"])
    paths = []
    for line in diff.splitlines():
        p = Path(line.strip())
        if not p:
            continue
        if p.match("examples/signal.*.json") or str(p).startswith("signals/") and p.suffix == ".json":
            paths.append(ROOT / p)
    return paths


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schema(path: Path) -> Dict[str, Any]:
    return load_json(path)


def validate(instance: Dict[str, Any], schema: Dict[str, Any], label: str) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        msg_lines = [f"{label} validation failed:"]
        for e in errors:
            loc = ".".join([str(x) for x in e.absolute_path]) or "(root)"
            msg_lines.append(f"- {loc}: {e.message}")
        raise SystemExit("\n".join(msg_lines))


def gate_from_tension(t: float) -> str:
    if t < 0.40:
        return "green"
    if t < 0.75:
        return "yellow"
    return "red"


def recommended_action(gate: str, kind: str, severity: str) -> str:
    if gate == "green":
        return "propose_patch"
    # optional: if super bad web-perf + fail, suggest rollback
    if gate == "red" and kind == "web-perf" and severity == "fail":
        return "rollback"
    return "human_review"


def constraints_for(signal: Dict[str, Any], gate: str) -> List[str]:
    base = ["reversibility-first", "minimal-intervention", "explainability", "human-seniority"]
    if gate != "green":
        base.append("canary-required")
    if signal.get("kind") == "security":
        base.append("no-secrets")
    return base


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_carecase(signal: Dict[str, Any]) -> Dict[str, Any]:
    t = float(signal["tension"])
    gate = gate_from_tension(t)
    action = recommended_action(gate, signal.get("kind", ""), signal.get("severity", "info"))
    carecase: Dict[str, Any] = {
        "schema_version": "0.1",
        "id": _derive_case_id(signal["id"]),
        "created_at": now_iso(),
        "system": signal["system"],
        "policy_gate": gate,
        "recommended_action": action,
        "tension": t,
        "summary": f"{signal['summary']}",
        "constraints": constraints_for(signal, gate),
        "signals": [{"signal_id": signal["id"]}],
        "status": "open",
    }

    # A small helpful default proposed transition for green/yellow web-perf
    if signal.get("kind") == "web-perf" and action in ("propose_patch", "human_review"):
        carecase["root_cause_hypothesis"] = (
            "Potentially heavier assets or blocking scripts introduced recently."
        )
        carecase["proposed_transition"] = {
            "intent": "Reduce LCP/TTFB by optimizing critical assets and deferring non-critical scripts",
            "scope": "critical rendering path (hero assets, script loading)",
            "reversibility": "reversible",
            "verification": [
                "Lighthouse LCP within budget",
                "No functional regressions (smoke)",
            ],
            "trace_ref": signal.get("trace_ref", "pending"),
        }

    return carecase


def _derive_case_id(signal_id: str) -> str:
    """
    Deterministic, stable UUID using a fixed namespace.
    """
    ns = uuid.UUID("00000000-0000-0000-0000-000000000000")
    return str(uuid.uuid5(ns, f"carecase:{signal_id}"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def set_github_output(name: str, value: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def main() -> None:
    signal_paths = changed_signal_files()
    if not signal_paths:
        set_github_output("has_cases", "false")
        set_github_output("case_files", "")
        print("No changed signal files detected.")
        return

    schema_signal = load_schema(SCHEMA_SIGNAL)
    schema_case = load_schema(SCHEMA_CARECASE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated: List[Path] = []

    for sp in signal_paths:
        signal = load_json(sp)
        validate(signal, schema_signal, f"Signal ({sp.as_posix()})")

        carecase = build_carecase(signal)
        validate(carecase, schema_case, "Care-Case (generated)")

        out_file = OUT_DIR / f"carecase.{signal['id']}.json"
        write_json(out_file, carecase)
        generated.append(out_file)

        print(f"Generated care-case: {out_file.as_posix()}")

    # Expose outputs to workflow
    set_github_output("has_cases", "true")
    set_github_output(
        "case_files",
        "\n".join([p.as_posix().replace(str(ROOT) + "/", "") for p in generated]),
    )


if __name__ == "__main__":
    main()
