# 09 — Two-day MVP implementation plan (hard timebox)

> **Hermes-native replan 2026-11-11:** [16 deployment decision](16-hermes-native-deployment.md) replaces the earlier custom Python dispatch-first MVP with **one local Hermes gateway/Kanban + six profiles + minimal external policy checker**. Existing PR #10/#11 are scaffold/contract tests and require a fit-gap review. Below, revised Day 1/2 board takes precedence over earlier notes where they conflict.

> **Phase: MVP / 2 working days / 16 engineer-hours maximum**. Planned scope, **not yet built**. Assumption: one experienced engineer, access to this repo and a sandbox/demo repository, working LiteLLM credentials/model aliases, local Docker/Python or equivalent, and permission to create GitHub PRs. If prerequisites are missing, stop/mark blocked; **do not claim completion through mocked output**.

## Measurable outcome

By the end of Day 2, demonstrate **one small bounded feature or bug fix** flowing through **PLAN → DESIGN → BUILD → TEST → DEPLOY → MAINTAIN**, with **six logical roles** (`pm-ba`, `sa`, `dev`, `qa`, `reviewer`, `devops-sre`) and human Owner gates. The DEPLOY stage for MVP means **prepare release + independent AI review + create a PR + optional dev-only smoke execution**, **NOT production deploy**. The MAINTAIN stage means record feedback/incident and generate a new queued intent, **NOT an autonomous live on-call daemon**.

Choose a tiny demo change (example: a read-only status/health endpoint with input validation and tests), **not** login/authorization CRUD or a production-connected integration.

**Success metric:** one real traceable test run + PR; all required artifact IDs linked; human approvals recorded; tests and independent reviewer evidence shown; production access absent. A manual/demo flow that substitutes a mock for any major real integration must be labelled **partial MVP**.

## Skills-enhanced MVP without extra time

[11 — vtno/skills adoption](11-vtno-skills-adoption.md) refines existing P0 tasks; it **does not add hours**. In D1.2, write two small **original, reviewed** SKILL.md-style procedures (`implementation-step` and `two-axis-review`) and load them explicitly by role/stage. If a generic loader is too costly, use pinned local instructions and record the version; do not defer core controller tests. In D2.1, Developer handles **one planned step / one PR**. In D2.2, Reviewer reports **Standards** and **Spec** separately against a pinned base diff while QA independently tests the accepted criteria. Limit the demo to **initial review + one re-review**; if required findings persist, record `BLOCKED` and human escalation rather than looping indefinitely. Keep at least one real test run and negative-gate test; repeated three-pass full-suite runs and parallel sub-review agents are Full enhancements. No runtime download, upstream installer or imported script execution in MVP. Licensing and source review precede any future copying.

## Storage boundaries for the 16-hour MVP

Follow [15 — four logical component contracts](15-logical-boundary-architecture.md), but **do not expand the two-day implementation**. The current `LocalStore` records workflow and execution artifacts; it is a local DurableExecution *approximation*, not enterprise durability. Keep proposed lessons separate from `state.json`, and never auto-load or promote those lessons. The current `skills.py` is a fixed first-party SkillManager *adapter*, not a full registry. `AgentMemory` remains a Full feature. No queues, ECS, DynamoDB, external Memory API or new microservice in this MVP.

## Hermes-native delivery board — revised 2-day target

| Window | Native-first activity | Check |
|---|---|---|
| Day 1 / 0–2h | Pin Hermes version; check Kanban CLI, gateway, LiteLLM, GitHub and approved sandbox | Versioned `preflight.md` |
| Day 1 / 2–4h | Create six Hermes profiles/roles, approved local Skills and bounded tools | Profile/Skill provenance |
| Day 1 / 4–6h | Enable one local gateway-owned dispatcher and single board, manual decomposition, review as explicit role | Actual Kanban cards + dependency and restart evidence |
| Day 1 / 6–8h | Add minimal SDLC human/CI/QA gate checker, run Plan + Design | Real `intent.md`/`spec.md` and recorded Owner decisions |
| Day 2 / 0–3h | Developer BUILD card creates real branch/tests/PR | Commit and GitHub URL verified externally |
| Day 2 / 3–5h | Independent QA and Reviewer cards check actual tests/diff/spec | QA and Standards/Spec reports |
| Day 2 / 5–7h | DevOps/SRE prepares DEV release only; Owner/Code Owner gate; no production | Verifiable release-prep evidence |
| Day 2 / 7–8h | Maintenance feedback, failed-gate tests, gateway restart and final evidence index | Linked six-stage trace, PASS/PARTIAL status |

**Cut rule:** reduce demo story and optional integrations, **not** external approval, real test evidence or independent Reviewer. Do not claim a working Hermes board based only on the existing Python unittest CI. If the required Hermes version or credentials are unavailable within the timebox, mark PARTIAL; do not recreate a large custom scheduler.

## Scope lock: IN versus OUT

| Priority | IN: must have to claim complete | OUT: Full phase |
|---|---|---|
| P0 | Six role instruction/profile definitions using one reusable runtime | Six always-on agents, agent social interactions, multi-agent swarm |
| P0 | Native Hermes Kanban task graph + a deterministic external SDLC acceptance/approval adapter | Custom distributed task dispatcher, autoscaling scheduler |
| P0 | Typed task/result JSON and `intent/spec/plan/test/review/release/incident` artifact chain | DynamoDB + S3 durable distributed state/snapshots |
| P0 | Real Hermes Kanban/profile worker invocation via approved LiteLLM, or explicit BLOCKED evidence | Production-scale multi-host deployment |
| P0 | Build/test on local sandbox repo; independent QA and Reviewer evidence | Enterprise security test suite and continuous evals |
| P0 | Git branch + PR (human-reviewed); manually recorded Owner approval | Production deployment, automated production rollback |
| P0 | Minimal tool permissions, secret exclusion, task timeout, spend/checkpoint logging | Full managed IAM/network/branch policies across every environment |
| P1 only if time | OpenProject link using existing API, simple status/usage summary | Full bidirectional OpenProject sync, service dashboard |
| P1 only if time | Human-authored `lessons.md` with next-intent feedback | Persistent automatic skill learning, simulated mood, incident agents |

**Cut rule:** when time slips, cut all P1 and UI work, then reduce demo feature complexity. **Never cut tests, reviewer independence, approval/secret guardrails or audit linkage** to claim a successful P0 demo.

## Historical custom-controller execution board — Day 1 (superseded by native-first board above)

| Block | Task | Deliverable / check |
|---|---|---|
| D1.1 — 0–2h | Preflight: pin Hermes release; validate noninteractive worker invocation, LiteLLM alias, local runtime, GitHub credentials and private/demo sandbox; choose tiny feature | `preflight.md` with pass/fail per dependency, no secrets |
| D1.2 — 2–4h | Define 6 role configs and artifact schemas/templates; implement state transition validator with Owner approval placeholders | Six profiles, validated task/result schemas, transition test |
| D1.3 — 4–6h | Build single-process controller and role runner adapter; sequential dispatch, safe workspace, limits, failure/retry-once, persistent JSON event log | Can execute a dry run across 6 stage labels with no invalid transitions |
| D1.4 — 6–8h | Wire Plan/Design to real role invocations; lock intent/spec and capture approvals; establish evidence manifest | `intent.md`, `spec.md`, approval records with role and timestamps |

**Day 1 exit gate:** controller starts from a single documented command, all six profiles load, a real Plan/Design flow runs with linked artifacts, and Owner can approve/reject before Build. If CLI/API bridge is incompatible, record the blocker and demonstrably separate a mock adapter; do not report a real Hermes success.

## Historical custom-controller execution board — Day 2 (superseded by native-first board above)

| Block | Task | Deliverable / check |
|---|---|---|
| D2.1 — 0–2h | SA/Dev creates `plan.md` and small code branch, runs unit/test/build command; bounded repair loop | Runnable change, test output, commit SHA |
| D2.2 — 2–4h | QA checks original AC with independent command/evidence; reviewer reads diff/plan/test and records severity-ranked findings; failure returns to Build | `test-report.md` + `review-report.md`; failing-case demonstration |
| D2.3 — 4–6h | DevOps prepares DEV/demo-only release record, PR and rollback steps; human Owner explicitly accepts/rejects; record cost and links | GitHub PR URL or blocked reason, `release-record.md`, approval audit |
| D2.4 — 6–8h | Maintenance feedback produces incident/lesson + proposed next `intent.md`; run negative tests, cleanup, README/runbook, final walkthrough | End-to-end evidence index, 6-stage demonstration, stated gaps/next backlog |

**Day 2 exit gate:** trace the same `work_item_id` through six stages; show real code/test/PR evidence; QA and Reviewer were not the author of the implementation; demo cannot run production writes.

## Historical custom-controller repo layout (reference only, not the Hermes-native deployment)

```text
src/hermes_orchestration/
  controller.py           # deterministic transition / approval checks
  contracts.py            # task/result schema validation
  runner.py               # provider-neutral run(task) boundary
  adapters/local.py       # local process / CLI task invocation
  adapters/github.py      # branch/PR integration or explicit manual step
  audit.py                # append-only structured local events
roles/{pm-ba,sa,dev,qa,reviewer,devops-sre}/SOUL.md
templates/{intent,spec,plan,test-report,review-report,release-record,incident}.md
examples/demo-work-item/   # sanitized sample only
tests/                     # transition, gates, reviewer isolation, retries
docs/demo-runbook.md
```

Keep integration adapters small. The current AWS operational direction is one EC2/EBS Hermes host with gateway-owned Kanban; optional multi-host shard later (see [16](16-hermes-native-deployment.md)). Do **not** deploy permanent paid infrastructure for the timeboxed MVP unless it is already provisioned and verified.

## Definition of Done (binary: checked only with evidence)

- [ ] A pinned Hermes Gateway with gateway-owned Kanban dispatcher can be started from documented commands; actual cards spawn named profile workers, while the external policy adapter enforces approval gates.
- [ ] Six logical profiles exist, carry distinct role/tool policies, and each is invoked for its stage or explicitly classified as blocked.
- [ ] Six stages are present, including allowed reject/feedback transitions; illegal transitions fail closed.
- [ ] `intent.md`, `spec.md`, `plan.md`, build and test evidence, independent `review-report.md`, `release-record.md` and maintenance feedback exist for **one ID**.
- [ ] Owner decisions include approver, decision, timestamp and artifact hash/link.
- [ ] Developer cannot self-approve; independent review does not substitute for human merge approval.
- [ ] Tests run for real and a forced failure returns the task to Build without marking delivered.
- [ ] GitHub branch/PR link or clearly documented integration blocker; no main push bypass.
- [ ] Credentials are not in repo, traces, task envelopes or artifacts; PII sanitized.
- [ ] Task bound has timeout, fixed retry count (0–1 for MVP), limited model budget and kill/stop path; actual vs estimated cost are labelled.
- [ ] No autonomous production deploy or production credential exposure.
- [ ] Demo runbook reproduces the flow; incomplete integrations and evidence are named clearly.

**Quality gates:** G0 environment credentials preflight; G1 Owner scope accepts Plan; G2 design/plan check; G3 QA tests pass; G4 independent Reviewer findings resolved; G5 Owner/release approver decision; G6 Maintain writes feedback/new intent. Only G0–G4 may be automated through deterministic checks in MVP; G1/G5 remain explicit human decisions.

## Dependency, fallback and risk

1. **Existing integration access is critical path.** If Hermes headless mode, LiteLLM provider mode or model aliases fail in D1.1, record actual failure. A local mock may test state logic but does not satisfy a live-agent MVP.
2. **Git access:** if installation lacks GitHub write permission, generate a patch and evidence file and classify the PR gate blocked; do not fake a PR.
3. **Owner unavailability:** stage can remain `WAITING_APPROVAL`. Do not auto-approve for demo.
4. **PR quality:** sample feature is deliberately small; retain QA/reviewer boundaries. Defer full security scans, IaC deployment and complex test types.
5. **Budget:** cap model calls and set `kanban.max_in_progress: 1` for the two-day demo; a short-lived local gateway is necessary to exercise gateway-embedded dispatch. Do not provision permanent AWS for the timebox; log tokens/cost and verify actual model limits.
6. **Data:** synthetic demo data only. Explicitly prohibit customer/production secrets.

## Handoff to Full

The output of this phase is an **evidence-backed vertical slice**, not a production AI company. Freeze artifact schemas, stage/role IDs, demo fixtures and known gaps; pass them to the [Full roadmap](10-full-implementation-roadmap.md). The architecture can expand without changing the six-stage governance model.

## Completion reporting template

```markdown
MVP status: COMPLETE | PARTIAL | BLOCKED
Date / commit / PR:
Real integrations proven:
Mocked or manual integrations:
6-stage evidence links:
Tests / negative gate tests:
Actual cost and runtime:
Known blockers / security exceptions:
Full-phase handoff:
```
