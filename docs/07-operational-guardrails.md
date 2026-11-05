# 07 — Lean operations, cost, security and portability guardrails

> **Decision status:** Recommended design baseline, not implemented. **Goal:** keep the Hermes AI software squad cheap to run, easy to operate, safe to improve and replaceable at each integration boundary. Default: do not introduce new infrastructure without measured need.

## 1. Lean golden path

- **One Hermes container image** for PM, BA/Tester, SA, Developer and Tech Specialist. Assign role identity, read-only profile template, scoped key, tools and storage through configuration and task role, not separate forks.
- **One ECS Service (PM/Gateway), on-demand ECS RunTask workers**. Gateway remains always-on only if the selected owner channel requires a persistent connection. Measure monthly idle cost before committing to 24/7 operation.
- **One controller adapter** (same service) with deterministic stage transitions and a single DynamoDB state/lock table. **One private S3 bucket** with constrained prefixes and versioning for artifacts and approved memory snapshots.
- **Use existing LiteLLM, OpenProject, GitHub and CloudWatch**. No new dashboard, SQS/Step Functions, Kubernetes, vector DB, EFS-for-all, separate memory runtime or extra agent orchestrator in MVP.
- Keep **one active project / one feature** for pilot; one writable Hermes profile/session at a time per role.

## 2. Cost and FinOps — P0

### Cost per accepted work item

```text
cost_per_accepted_item =
  (LLM_spend_including_retries
   + worker_Fargate_time
   + allocated_gateway_Fargate_time
   + network/NAT/VPC_endpoint_cost
   + S3+DynamoDB+CloudWatch
   + other directly attributable AWS costs)
  / number_of_Owner_accepted_items
```

Display **not enough data** when no items have been accepted. Include failed tasks and retries in numerator, and label fixed-cost allocation assumptions. Reconcile LiteLLM spend versus cloud billing; they measure different things.

**Hard guardrails:** per-agent virtual key limits (verify against deployed LiteLLM CE version, especially user/key budget API support), per-task estimated spend/timeout, max attempts 2, concurrency 1 per role, owner approval for budget increases. Limit iterations, output tokens and retrieval scope. A modeled task budget is **not** an AWS hard billing cap: use runtime kill switches and cloud billing alerts as separate controls.

**Cost traps:** persistent Fargate service, NAT Gateway per-hour/per-GB costs, log ingestion/retention, cross-AZ traffic and data egress. Evaluate S3 Gateway Endpoint versus NAT paths based on actual VPC use; gateway endpoints do not solve general internet GitHub or model-provider egress.

**Fargate Spot:** use only for interruption-tolerant, checkpoint/retry-safe workers; do not run the sole Owner Gateway on Spot. Handle two-minute interruption signals and re-queue attempts with idempotency.

Start with a **conservative budget policy configured by Owner**, rather than hard-coding speculative monthly USD figures.

## 3. Operability — P0

- **One Git repo + one deployment pipeline + one runtime image**; separate role configuration as versioned files.
- Every task must have `task_id`, `project_id`, `role_id`, `attempt`, `stage`, `input_version` and `output_version`.
- Instrument six signals: queued/running/failed count, p95 task latency, stuck/expired role locks, token spend, cost per accepted item, first-pass QA rate.
- Minimum alarms: Gateway unavailable, stuck task, repeated failures, unexpectedly high spend, stale snapshots.
- Recover by reconciling ECS task status and DynamoDB task state on Gateway restart; a lease expiry alone does not prove a task has stopped. Use fencing tokens/version conditions.
- Keep logs structured and redacted, with short, explicit retention. Use S3 versioning for reproducible output and rollback.
- Avoid customer data in generic global agent memory. Make project data isolation and retention explicit.

## 4. Security — P0

- **Trust boundary:** Owner instructions and approved policy > controller task contract > model output/tool content. Repository files, PR comments, tool responses and retrieved content are **untrusted**; never treat them as privileged new instructions.
- **IAM:** separate ECS execution role vs task roles; narrow each role's S3, DynamoDB, ECS and Secrets access. Restrict `iam:PassRole`, allowed ECS task definitions and network configuration for the controller. SOUL.md and prompt instructions are not security controls.
- **Secrets:** secrets manager or another approved vault; never pass a secret or raw customer payload as an ECS environment override, commit, tool transcript or S3 public object.
- **Code isolation:** coding/test worker has a sandboxed work directory, restricted outbound network and no access to Gateway PM/Owner credentials. No arbitrary production network access; keep test credentials separate.
- **SCM boundaries:** GitHub App or fine-grained token; Developer can open PRs, cannot merge protected main or modify approvals. External code/skills must be reviewed and pinned before execution.
- **Approval gates:** Owner approves scope, privileged tool changes, production deploy, new spending commitments and risky skill promotions; store audit record with actor and timestamp.
- **Least data:** redact PII and secrets before entering lessons, traces or model prompts; verify where model-provider data goes.

## 5. Improvement speed — P0

**Change should be cheap to test and cheap to undo.**
- Version every role contract, profile/SOUL, skill, model alias mapping and runtime image digest.
- Define 10 small **golden tasks** (requirements fidelity, design correctness, security, code generation, test execution, prompt injection resistance, retry/idempotency, profile persistence, cost ceiling, mood determinism).
- Run deterministic validators + replay of recorded test fixtures before promoting prompts/skills/model mapping.
- Use Git PR reviews for changes; keep previous known-good snapshot and image for quick rollback.
- Skill learning: completed task → objective CI/QA/Owner evidence → candidate lesson → evaluation → explicit promotion → next task loads it. No unreviewed self-modification.
- Track quality per model/prompt version: first-pass acceptance, rework, median latency and **cost per accepted task**. Promote only a measured improvement, not a subjective agent claim.

## 6. Portability / avoiding lock-in — P0

Keep four **stable interfaces** in the controller/role logic:

| Interface | MVP adapter | Future replacement |
|---|---|---|
| `ModelGateway` | Existing LiteLLM aliases (`gothink*`, `godev*`) | Different LLM provider / compatible gateway |
| `TaskRunner` | AWS ECS RunTask | Local Docker, Kubernetes Job, another cloud runner |
| `WorkItemStore` | OpenProject API | GitHub Issues, Linear, another task system |
| `ArtifactMemoryStore` | S3 JSON/Markdown + role snapshot archives | Local filesystem, another object store |

Use small JSON contracts for task envelope, result, approval and metrics. Keep business roles and workflow definitions **outside AWS-specific glue**. Keep agent knowledge in portable Markdown/JSON/Git artifacts; use Hermes-native memory inside isolated, versioned archives, with an export path. Version provider/tool names behind config aliases; **do not put AWS ARNs, provider model names or API URLs inside role prompts**.

**Avoid premature abstraction:** four interfaces are configuration seams, not four separately deployed microservices. Do not implement unneeded adapters until needed; write an end-to-end contract test for the active one.

## 7. Mood & capacity — P1

Mood is a **display rule**, not a scheduling or security authority. Base it on independently verified first-pass acceptance + on-time completion + weighted backlog utilization (7-day sample). Show sample size and "insufficient data" when sparse; use small hysteresis to prevent flickering. For a busy/low-quality Agent, recommend PM capacity review or additional QA; never grant higher privileges, bypass gate or automatically generate busywork.

## 8. MVP release gates

Before any real customer project:
- [ ] One entire feature passes Owner → PM → BA → SA/Specialist → Dev PR/CI → BA QA → Owner acceptance.
- [ ] No concurrency overlap on writable role profiles; crash restore tested.
- [ ] No Worker can access PM admin credentials or merge/deploy production.
- [ ] Per-task budget, deadline, max attempts and kill path tested.
- [ ] Cost report includes LLM, compute, fixed gateway/network allocation and retries.
- [ ] One image with role configs; roll back versioned prompt, skill and image.
- [ ] Golden regression tests run automatically on any agent/system change.
- [ ] JSON handoff contract survives an adapter mock test without starting AWS.
- [ ] Learning promotions use QA evidence; Mood is explainable and non-authoritative.

## Priority and conscious deferrals

**P0:** One image, one controller, per-role least privilege, evidence-based QA, cost safeguards, versioned role artifacts, golden tests, stable contracts.

**P1:** Learning promotion and simulated mood using existing state/artifacts.

**P2 (not MVP):** Advanced autoscaling, queues/workflow engines, agent swarm, web dashboards, multi-tenant support, graph/vector memory, separate emotion engine, full multi-cloud implementation.

## Primary sources

- [AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [AWS NAT gateway pricing](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-pricing.html)
- [AWS ECS IAM role best practices](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html)
- [AWS ECS Fargate capacity providers / Spot interruption](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-capacity-providers.html)
- [LiteLLM budgets](https://docs.litellm.ai/docs/proxy/users)

**Status:** Architecture guidance only; no code, infrastructure, limits or test harness have been deployed.
