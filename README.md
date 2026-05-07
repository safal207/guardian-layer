# guardian-layer

Guardian Layer — care-first policy evaluation layer for operational signals and LTP-oriented systems: non-coercive, traceable, reversible.

## Review links

- Grant evidence: [docs/GRANT_EVIDENCE.md](docs/GRANT_EVIDENCE.md)
- Signal schema: [interfaces/signals.schema.json](interfaces/signals.schema.json)
- Care-Case schema: [interfaces/care-case.schema.json](interfaces/care-case.schema.json)
- Interfaces README: [interfaces/README.md](interfaces/README.md)
- Default policy pack: [policy/default.policy.json](policy/default.policy.json)
- Shared policy engine: [tools/guardian_policy.py](tools/guardian_policy.py)
- Operator CLI: [tools/guardian_case.py](tools/guardian_case.py)
- API service: [api/app.py](api/app.py)
- Roadmap 2026: [docs/ROADMAP_2026.md](docs/ROADMAP_2026.md)

## Interfaces
- [Signal schema](interfaces/signals.schema.json)
- [Care-Case schema](interfaces/care-case.schema.json)
- [Interfaces README](interfaces/README.md)

## Implementation progress (phase 1)
- Policy pack is now externalized in JSON: [`policy/default.policy.json`](policy/default.policy.json)
- Shared policy engine utilities: [`tools/guardian_policy.py`](tools/guardian_policy.py)
- Intake supports configurable policy packs:
  - `python tools/guardian_intake.py --policy-pack policy/default.policy.json`
- Operator CLI for day-1 workflows:
  - `python tools/guardian_case.py evaluate --signal examples/signal.web-perf.json`
  - `python tools/guardian_case.py explain --signal examples/signal.web-perf.json`
- API (ingest/evaluate/explain) for service mode:
  - `uvicorn api.app:app --reload --port 8000`
  - `curl -sS http://127.0.0.1:8000/healthz`
  - `curl -sS -X POST http://127.0.0.1:8000/v1/evaluate -H 'content-type: application/json' --data @examples/signal.web-perf.json`

## Planning & business
- [Roadmap 2026](docs/ROADMAP_2026.md)
- Monetization calculator: `python tools/guardian_monetization.py --scenario base`

## Scope boundary

Guardian Layer evaluates operational signals against explicit policy packs and produces reversible, explainable care-cases for human-reviewable action.

It is not a clinical system, not an autonomous authority, not a replacement for incident response teams, and not a production side-effect controller by itself.

Short version:

```text
Signals should not become irreversible actions by default.
Guardian Layer turns signals into explainable, reversible care-cases.
```
