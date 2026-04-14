import json
import unittest
from pathlib import Path

from tools.guardian_policy import (
    build_carecase,
    explain_decision,
    gate_from_tension,
    load_policy_pack,
    recommended_action,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_SIGNAL = ROOT / "examples" / "signal.web-perf.json"
POLICY = ROOT / "policy" / "default.policy.json"


class GuardianPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.signal = json.loads(EXAMPLE_SIGNAL.read_text(encoding="utf-8"))
        self.policy = load_policy_pack(POLICY)

    def test_gate_thresholds_from_policy_pack(self) -> None:
        self.assertEqual(gate_from_tension(0.39, self.policy), "green")
        self.assertEqual(gate_from_tension(0.40, self.policy), "yellow")
        self.assertEqual(gate_from_tension(0.75, self.policy), "red")

    def test_override_action_applies_for_red_web_perf_fail(self) -> None:
        action = recommended_action("red", "web-perf", "fail", self.policy)
        self.assertEqual(action, "rollback")

    def test_build_carecase_has_expected_shape(self) -> None:
        case = build_carecase(self.signal, self.policy)
        self.assertEqual(case["schema_version"], "0.1")
        self.assertIn(case["policy_gate"], {"green", "yellow", "red"})
        self.assertTrue(case["constraints"])
        self.assertEqual(case["signals"][0]["signal_id"], self.signal["id"])

    def test_explain_contains_reasoning(self) -> None:
        explanation = explain_decision(self.signal, self.policy)
        self.assertEqual(explanation["signal_id"], self.signal["id"])
        self.assertTrue(explanation["reasoning"])


if __name__ == "__main__":
    unittest.main()
