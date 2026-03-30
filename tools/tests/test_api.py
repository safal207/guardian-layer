import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app

ROOT = Path(__file__).resolve().parents[2]
SIGNAL_PATH = ROOT / "examples" / "signal.web-perf.json"


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())
        cls.signal = json.loads(SIGNAL_PATH.read_text(encoding="utf-8"))

    def test_healthz(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_evaluate_happy_path(self) -> None:
        response = self.client.post("/v1/evaluate", json=self.signal)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("care_case", body)
        self.assertEqual(body["care_case"]["summary"], self.signal["summary"])

    def test_explain_happy_path(self) -> None:
        response = self.client.post("/v1/explain", json=self.signal)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("explanation", body)
        self.assertEqual(body["explanation"]["signal_id"], self.signal["id"])

    def test_evaluate_validation_error(self) -> None:
        bad_signal = {"id": "bad"}
        response = self.client.post("/v1/evaluate", json=bad_signal)
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail["type"], "signal_validation")
        self.assertTrue(detail["errors"])


if __name__ == "__main__":
    unittest.main()
