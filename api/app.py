#!/usr/bin/env python3
"""FastAPI service for Guardian Layer signal evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from jsonschema import Draft202012Validator

from tools.guardian_policy import build_carecase, explain_decision, load_policy_pack

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SIGNAL = ROOT / "interfaces" / "signals.schema.json"
SCHEMA_CARECASE = ROOT / "interfaces" / "care-case.schema.json"
DEFAULT_POLICY = ROOT / "policy" / "default.policy.json"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validation_errors(instance: Dict[str, Any], schema: Dict[str, Any]) -> List[Dict[str, str]]:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    formatted: List[Dict[str, str]] = []
    for error in errors:
        location = ".".join(str(x) for x in error.absolute_path) or "(root)"
        formatted.append({"location": location, "message": error.message})
    return formatted


def create_app() -> FastAPI:
    app = FastAPI(title="Guardian Layer API", version="0.1.0")

    schema_signal = load_json(SCHEMA_SIGNAL)
    schema_carecase = load_json(SCHEMA_CARECASE)

    @app.get("/healthz")
    def healthz() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/evaluate")
    def evaluate(signal: Dict[str, Any]) -> Dict[str, Any]:
        signal_errors = validation_errors(signal, schema_signal)
        if signal_errors:
            raise HTTPException(status_code=422, detail={"type": "signal_validation", "errors": signal_errors})

        policy = load_policy_pack(DEFAULT_POLICY)
        carecase = build_carecase(signal, policy)
        case_errors = validation_errors(carecase, schema_carecase)
        if case_errors:
            raise HTTPException(status_code=422, detail={"type": "carecase_validation", "errors": case_errors})

        return {"care_case": carecase}

    @app.post("/v1/explain")
    def explain(signal: Dict[str, Any]) -> Dict[str, Any]:
        signal_errors = validation_errors(signal, schema_signal)
        if signal_errors:
            raise HTTPException(status_code=422, detail={"type": "signal_validation", "errors": signal_errors})

        policy = load_policy_pack(DEFAULT_POLICY)
        return {"explanation": explain_decision(signal, policy)}

    return app


app = create_app()
