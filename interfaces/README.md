# Interfaces (v0.1)

This folder defines the minimal “felt sense” interface of Guardian Layer.

## Signal
A **Signal** is an observed deviation or noteworthy event (errors, perf regressions, drift, UX friction).
It is *not* a decision — it is evidence.

Schema: `signals.schema.json`

Required fields:
- `schema_version`: "0.1"
- `id`: UUID
- `timestamp`: ISO 8601
- `source`: origin ("web-client", "github-actions", "sentry", "lighthouse", ...)
- `severity`: info | warn | fail
- `tension`: 0..1
- `system`: { name, env, version }
- `kind`: category ("web-perf", "error-rate", ...)
- `summary`: short text

Optional:
- `details`: structured payload
- `trace_ref`: link to trace/commit/run id
- `links`: supporting URLs

## Care-Case
A **Care-Case** is a Guardian decision container: it binds signals, sets a policy gate, and recommends the next action.
It is the unit of gentle continuity.

Schema: `care-case.schema.json`

Core fields:
- `policy_gate`: green | yellow | red
- `recommended_action`: observe | propose_patch | rollback | human_review
- `constraints[]`: enforcement hints (e.g. "reversibility-first", "canary-required", "no-secrets")
- `signals[]`: linked signals by `signal_id` (optional snapshot allowed)
- `proposed_transition`: optional intent for LTP transition

## Examples
See `/examples` for sample JSON payloads.
