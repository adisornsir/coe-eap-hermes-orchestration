> **SUPERSEDED MVP PLAN — 2026-11-05:** This multi-sprint five-role implementation plan is historical, **not the active MVP commitment**. The active scope is **a strict two-working-day/16-engineer-hour local/sandbox MVP**, documented in [09 — two-day execution](09-mvp-two-day-execution.md); the remainder moves to [10 — Full roadmap](10-full-implementation-roadmap.md). The six-role design is [08](08-six-stage-role-target.md).

---

# 05 — MVP delivery plan, acceptance and guardrails

## Outcome

Demonstrate **one fully traceable feature**, from Owner request → PM plan → BA requirements → SA + Specialist design → Dev PR/CI → BA QA → Owner acceptance, with 5 persistent role identities, evidence-based learning and simulated mood. This repo is a **design baseline**, not working software.

## Scope / priority

| Priority | Deliverable | Acceptance evidence |
|---|---|---|
| P0 | Hermes image and 5 profile templates | Every role starts independently with required model alias, tools and permissions |
| P0 | PM Gateway + Owner interaction | Goal accepted; OpenProject Story created; approval decision recorded |
| P0 | Thin controller + ECS RunTask | Valid state transitions, role lock, retries, timeouts, failure recovery |
| P0 | Worker bootstrap + S3 versioned snapshots | Restart loads same identity; concurrent writer rejected; crash restores prior version |
| P0 | Role contracts + artifacts + CI | BA AC, SA design, Specialist review, Dev PR, BA test evidence |
| P0 | Security and spend controls | Least-privilege IAM/keys; task budgets; no prod merge/deploy |
| P1 | Memory reflection + skill proposal | Successful task yields traceable suggestion, human review, versioned promotion |
| P1 | Mood from measured data | Explainable state, small-sample neutrality, over-capacity flag |
| P1 | Basic summary UI | Telegram/Markdown report with task status, spend, failures, mood; **not** new web dashboard |
| P2 | SQS, Step Functions, dedicated dashboard, vector memory | Deferred by measurement |

## Suggested implementation order

### Sprint 0: validation (1–2 working days, planning estimate only)
- Pin Hermes version and build image; prove CLI non-interactive task runner with a disposable profile.
- Check LiteLLM alias/API compatibility and memory/skills approval settings.
- Validate S3 snapshot + restore + lock, OpenProject API and GitHub access model.
- Estimate Fargate warm/cold start, NAT/e-gress, gateway baseline and model cost.

### Sprint 1: working delivery path
- Deploy Gateway/PM, controller, DynamoDB table, S3 private bucket, restricted Fargate worker task definition, CloudWatch.
- Provision 4 role identities, scoped credentials, prompts, task contracts and state machine.
- Complete one Story through PR/CI/QA/Owner review with manual supervision.

### Sprint 2: identity and behavior
- Save approved memory and skills as versions; prove resume after Fargate termination.
- Compute success, utilization and simulated mood from objective completion/QA data.
- Add retry/idempotency, crash tests, audit trail, spend summary and runbook.

## MVP Definition of Done

- [ ] Owner can submit feature and approve/reject scope and release.
- [ ] PM creates linked OpenProject tasks and reports actual status.
- [ ] Five roles are visibly distinct; each task has one role owner.
- [ ] BA writes AC, SA design, Specialist risk notes, Dev PR + CI, BA QA evidence.
- [ ] No task completion is accepted from agent text without artifacts.
- [ ] No shared writable Hermes profile among concurrently running workers.
- [ ] Every role's approved memory/skills survive task restart and roll back on crash.
- [ ] Failed task retries do not duplicate commits, PRs or status updates.
- [ ] Spend and failure events are traceable by `project_id, task_id, role_id`.
- [ ] Mood shows validated success/workload with insufficient-data handling.
- [ ] No agent can merge main, apply production changes or widen IAM privileges.
- [ ] Demo finishes with a reproducible Owner-approved PR, **not** automatic production deploy.

## Initial operational defaults (tune after pilot)

- One active project; one active worker per role; PM service desired count = 1.
- Max 2 retry attempts with exponential backoff and hard task timeout.
- Scoped model aliases: PM `gothink2`, BA `gothink1`, SA `gothink2`, Dev `godev1`, Specialist `gothink1`.
- Initial task spend cap as a configurable value; notify Owner if predicted spend crosses remaining allowance.
- Keep CloudWatch logs minimal and redact secrets, user/customer payloads. Version S3 snapshots; set lifecycle/retention.
- Daily digest: throughput, 1st-pass pass rate, blocked tasks, OpenProject status, AI spend, learning proposals, mood states.

## Known risks / next decisions

1. **Hermes Fargate wrapper:** CLI invocation, snapshot consistency and skill-approval UX must be proven on pinned Hermes release.
2. **Cold start:** Batch work acceptable; if Owner experiences long waits, keep Gateway interactive and evaluate warm workers.
3. **Single controller failure:** Persist state in DynamoDB; on Gateway restart reconcile ECS tasks before redispatch.
4. **EFS vs S3:** EFS only for PM local home where necessary; no cross-process writable state.db; worker state via isolated S3 snapshots.
5. **GitHub/API security:** Worker tokens are scoped; webhook/manual-approval enforcement belongs outside prompts.
6. **Mood scoring:** With few completed tasks show 'insufficient data' and do not infer meaningful trends.
7. **Budget:** Verify AWS and model spend from real billing, not from illustrative architecture figures.

## V2 only after validated MVP

Multi-project/team concurrency, tenant boundaries, durable queue orchestration, smart scheduler, skill regression suite, vector/graph memory, browser-based company dashboard and optional GPU inference.
