#!/usr/bin/env python3
"""Guardian policy evaluation primitives shared by CLI/scripts."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PACK = ROOT / "policy" / "default.policy.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def derive_case_id(signal_id: str) -> str:
    ns = uuid.UUID("00000000-0000-0000-0000-000000000000")
    return str(uuid.uuid5(ns, f"carecase:{signal_id}"))


def load_policy_pack(path: Path | None = None) -> Dict[str, Any]:
    policy_path = path or DEFAULT_POLICY_PACK
    with policy_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def gate_from_tension(tension: float, policy: Dict[str, Any]) -> str:
    gates = policy.get("gates", {})
    green_max = float(gates.get("green_max_tension", 0.4))
    yellow_max = float(gates.get("yellow_max_tension", 0.75))

    if tension < green_max:
        return "green"
    if tension < yellow_max:
        return "yellow"
    return "red"


def recommended_action(
    gate: str,
    kind: str,
    severity: str,
    policy: Dict[str, Any],
) -> str:
    action_cfg = policy.get("recommended_actions", {})

    for override in action_cfg.get("overrides", []):
        if (
            override.get("gate") == gate
            and override.get("kind") == kind
            and override.get("severity") == severity
        ):
            return str(override.get("action", "human_review"))

    fallback = action_cfg.get("default", {})
    return str(fallback.get(gate, "human_review"))


def constraints_for(signal: Dict[str, Any], gate: str, policy: Dict[str, Any]) -> List[str]:
    constraints = policy.get("constraints", {})
    items = list(constraints.get("base", []))

    if gate != "green":
        items.extend(constraints.get("non_green_append", []))

    kind_extra = constraints.get("kind_append", {}).get(signal.get("kind", ""), [])
    items.extend(kind_extra)

    # de-dup while preserving order
    seen = set()
    deduped = []
    for item in items:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def build_carecase(signal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    tension = float(signal["tension"])
    gate = gate_from_tension(tension, policy)
    action = recommended_action(gate, signal.get("kind", ""), signal.get("severity", "info"), policy)

    carecase: Dict[str, Any] = {
        "schema_version": "0.1",
        "id": derive_case_id(signal["id"]),
        "created_at": now_iso(),
        "system": signal["system"],
        "policy_gate": gate,
        "recommended_action": action,
        "tension": tension,
        "summary": f"{signal['summary']}",
        "constraints": constraints_for(signal, gate, policy),
        "signals": [{"signal_id": signal["id"]}],
        "status": "open",
    }

    if signal.get("kind") == "web-perf" and action in ("propose_patch", "human_review"):
        template = dict(policy.get("web_perf_transition_template", {}))
        carecase["root_cause_hypothesis"] = (
            "Potentially heavier assets or blocking scripts introduced recently."
        )
        carecase["proposed_transition"] = {
            "intent": template.get(
                "intent",
                "Reduce LCP/TTFB by optimizing critical assets and deferring non-critical scripts",
            ),
            "scope": template.get("scope", "critical rendering path"),
            "reversibility": template.get("reversibility", "reversible"),
            "verification": template.get("verification", []),
            "trace_ref": signal.get("trace_ref", "pending"),
        }

    return carecase


def explain_decision(signal: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    tension = float(signal["tension"])
    gate = gate_from_tension(tension, policy)
    action = recommended_action(gate, signal.get("kind", ""), signal.get("severity", "info"), policy)

    return {
        "policy_pack": policy.get("id", "unknown"),
        "signal_id": signal.get("id"),
        "tension": tension,
        "gate": gate,
        "action": action,
        "constraints": constraints_for(signal, gate, policy),
        "reasoning": [
            f"tension={tension:.3f} -> gate={gate}",
            f"kind={signal.get('kind', 'n/a')}, severity={signal.get('severity', 'n/a')} -> action={action}",
        ],
    }
