# guardian-layer
Guardian Layer — keeper of gentle continuity: care-first policy layer for LTP systems (non-coercive, traceable, reversible).

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

## Planning & business
- [Roadmap 2026](docs/ROADMAP_2026.md)
- Monetization calculator: `python tools/guardian_monetization.py --scenario base`
