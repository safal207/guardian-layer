# Guardian Layer — Roadmap 2026 (30/60/90 + 12 months)

## Цель
Сделать из текущего policy-MVP коммерчески применимый продукт класса "AI Change Governance" для engineering/platform команд.

## North Star
- Снижение Change Failure Rate минимум на 20% у пилотных клиентов.
- Снижение MTTR минимум на 15% на контролируемом наборе инцидентов.
- Доля auto-approved reversible changes (green gate) >= 25% без роста инцидентности.

## Принципы
- Reversibility-first.
- Human-in-the-loop для yellow/red.
- Traceability by default.
- Policy as code + policy explainability.

## План 30/60/90

### Первые 30 дней (Foundation)
1. Productization basics
   - Добавить API-слой ingest/evaluate (FastAPI) поверх текущих schema + rules.
   - Ввести versioned policy-pack (JSON/YAML), чтобы уйти от hardcoded правил.
2. Reliability
   - Покрыть ключевые сценарии unit/integration тестами.
   - Добавить CI workflow с проверками схем, линтингом и smoke test.
3. UX for operators
   - Добавить CLI `guardian case evaluate` и `guardian case explain`.

**Критерии завершения (D30):**
- Можно отправить Signal через API и получить валидный Care-Case + explanation.
- >= 70% core logic покрыто тестами.

### 60 дней (Pilot readiness)
1. Integrations
   - GitHub App mode (webhooks + PR checks) вместо чисто скриптового режима.
   - Коннектор к Sentry/Datadog (минимум один источник сигналов).
2. Governance
   - Approval matrix (кто может override policy gate).
   - Audit trail событий в append-only формате.
3. Observability
   - Метрики качества решений (precision/false positives, rollback rate).

**Критерии завершения (D60):**
- Минимум 1 end-to-end pilot на реальном репозитории.
- Дашборд базовых метрик по кейсам и policy outcomes.

### 90 дней (First paid design partner)
1. Security & Enterprise readiness
   - SSO/SAML (или подготовка совместимости).
   - RBAC (viewer/operator/admin).
2. Commercial packaging
   - Тарифы: Team / Business / Enterprise.
   - SLA и support-процедуры.
3. Customer success motion
   - Onboarding playbook (2 недели).
   - ROI report template.

**Критерии завершения (D90):**
- 1 платящий design partner ИЛИ подписанный pilot с clear conversion criteria.

## 12-месячный план

### Q3 2026
- Multi-repo / multi-tenant архитектура.
- Policy simulation (what-if) перед применением.

### Q4 2026
- Marketplace policy packs (web-perf, reliability, security-lite).
- Integrations: GitLab + Jira.

### Q1 2027
- Semi-autonomous remediation workflows (под жёсткими guardrails).
- Enterprise reporting (compliance-ready exports).

## Что делаем прямо сейчас (старт реализации)
1. Документируем monetization-модель и сценарии выручки.
2. Добавляем CLI-калькулятор монетизации для быстрого пересчёта unit economics.
3. Фиксируем допущения и KPI, которые нужно начать собирать из пилотов.
