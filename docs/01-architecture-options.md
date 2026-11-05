# 01 — Architecture options and decision

## Constraints and target

- 1 human Owner; AI PM, BA/Tester, SA, Dev and Tech Specialist; one software project for the first pilot.
- Target infrastructure: AWS ECS Fargate; reuse existing LiteLLM, OpenProject, GitHub and CloudWatch.
- Memory survives restart; skills evolve only through review; simulated mood reflects **validated success and fit of assigned workload**.
- Keep first deployment small, auditable and reversible. No custom AI agent framework.

| Choice | Shape | Good for | Cost/complexity | Trade-off |
|---|---|---|---|---|
| **A — Single container** | One Hermes runtime, 5 profiles, sequential tasks | Fast local POC | Lowest | Shared failure domain, long-running work blocks operations, weak worker isolation |
| **B — Lean Fargate Team** | Persistent PM Gateway; on-demand isolated ECS RunTask workers; DDB + S3 | **Recommended MVP** | Low-to-medium | ECS cold starts; requires a small controller and snapshot wrapper |
| **C — Platform / Workflow Engine** | Event-driven queue, workflow engine, separate services and UI | Many projects, high concurrency | Highest | Too many services for first vertical slice |

## ADR-001: Adopt B, retain A as local prototype, defer C

**Decision:** One always-on gateway/PM service; control logic dispatches tasks directly via ECS RunTask, stores status/leases in DynamoDB and outputs in S3. Initially one task per role at a time. **Do not add SQS or Step Functions until task throughput, reliability or fan-out measurements justify them.**

- **Why B:** Separates long-running coding/test workloads; respects 1 execution = 1 work item; preserves the prior Fargate approach.
- **What stays simple:** PM orchestrates a deterministic state machine, not free-form agent-to-agent swarms. No separate Team Lead, no per-role permanent service.
- **Why A is not target:** Profile separation alone does not provide IAM/process isolation; Gateway availability coupled to Dev sessions.
- **Why C deferred:** Overengineering before there is a proven workflow or measured queue pressure.
- **Consequence:** Worker cold start is acceptable for batch tasks. If interactive response speed becomes important, introduce a bounded warm-worker pool later.
- **Hard limit:** One active writer per role/project Hermes home. Use conditional locks and versioned snapshots; isolation must be enforced by runtime.
- **Evidence before scale:** End-to-end feature demo; restore test; retry/idempotency; zero cross-role profile overlap.

## Exit criteria to reconsider architecture

Move toward C when one or more are true: >1 active customer/tenant requiring strong tenant isolation; >20 concurrent jobs; robust human-wait steps; frequent task retries and dead-letter handling; or audit/availability obligations beyond MVP. These are review triggers, not automatically accepted sizing limits.

## Open technical validation

Validate the chosen Hermes version's non-interactive execution, CLI exit codes, session/file storage and approval flows inside a throwaway Fargate task. Validate ECS image boot time, IAM access, S3 snapshot restore and gateway recovery before production work.

**Status:** Proposed MVP baseline, requires infrastructure POC.
