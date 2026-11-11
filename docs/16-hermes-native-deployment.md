# 16 — Hermes-native operations and deployment architecture

> **Target design / NOT DEPLOYED.** Decision dated 2026-11-11. This document updates the runtime choices in older [02 AWS architecture](02-target-architecture.md) and the Fargate-first proposal in [10 roadmap](10-full-implementation-roadmap.md). It is stacked on [15 four logical boundaries](15-logical-boundary-architecture.md). The six AI roles, six SDLC stages, evidence requirements, and human approval boundaries do **not** change.

## Architecture decision record: Hermes-native first

**Recommended first operational target: one private AWS EC2 host + local EBS volume + one Hermes gateway-embedded Kanban dispatcher + six distinct Hermes profiles + a small external SDLC policy/approval adapter.**

Use Hermes's native worker/board/run lifecycle rather than introducing another custom queue, worker dispatcher, role spawn API, or cloud-native task engine. Keep the current lightweight Python workflow implementation as **contract-test/demo reference**, not as a second competing production dispatcher. No automatic import of third-party skills.

Why EC2 over Fargate initially? Native Hermes Kanban is a **single-host SQLite/PID-local dispatcher** that spawns managed local worker processes, and user/system service-manager integration matters. A persistent EC2 host with EBS is a simpler fit for local mutable SQLite and process lifecycle than pretending ECS replicas can share the same Kanban database. **EC2 does not provide autoscaling of a single Kanban board**; add hosts only by sharding independent projects/workloads.

## Deployment topology — single host

~~~mermaid
flowchart TB
  H["Human Owner / Teams / Web (authenticated)"] --> CH["Hermes messaging/API channel"]
  subgraph VPC["AWS private VPC — one Hermes host (EC2)"]
    CH --> GW["1 Hermes Gateway<br/>profile multiplex + Kanban dispatcher"]
    GW --> KB[("EBS local Hermes home<br/>Kanban SQLite + profiles/sessions")]
    GW --> A["Hermes Kanban workers<br/>6 role profiles, bounded concurrent OS processes"]
    GW --> PG["Thin SDLC Policy Adapter<br/>External Approval + CI evidence checks"]
    PG --> A
    A --> KB
    A --> TOOLS["Restricted local workspace and approved tools"]
  end
  GW --> LM["Gosoft LiteLLM gateway"]
  PG --> GH["GitHub protected PR and CI"]
  PG --> OP["OpenProject business work"]
  KB -. "consistent backup/export, not a live shared mount" .-> S3[("Private S3 backups/evidence")]
  VPC --> CW["CloudWatch logs/alarms / SSM administration"]
~~~

**One Hermes host** has one dispatcher owner. A Hermes **profile is a separate home**, not a security sandbox. Profiles can share the same OS service principal; external least-privilege GitHub credentials, tool policy, filesystem permissions and account boundaries must enforce real authority. For untrusted tenants/projects requiring hard isolation, separate **host/OS security domains**, not merely Kanban boards or profile folders.

### Actual boundaries

| Responsibility | Native Hermes | Our thin control | Persisted where |
|---|---|---|---|
| Task queue, dependencies, profile dispatch | Kanban boards, gateway dispatcher | Create/link cards using deterministic 6-stage plan | Local Kanban SQLite on EBS |
| Local task retry/crash tracking | Kanban worker/run lifecycle | Verify external side-effects before retry | Kanban SQLite + GitHub evidence refs |
| 6 SDLC acceptance, severity, budgets | Kanban cards represent work | **Enforceable policy/approval adapter** validates AC/CI/review/human identity | External approval system, CI/PR and audit evidence |
| Agent identity / private working memory | Per-role Hermes profiles, sessions | Data classification and versioned approved memory promotion | Hermes profile home; approved S3/Git snapshots |
| Agent skills | Hermes Skill handling | Reviewed source/version allowlist + independent promotion | Git source, optional approved S3 artifact |
| GitHub code/CI & OpenProject | Agent/MCP tools | External SCM protections and business source of truth | GitHub and OpenProject |
| Model routing and caps | Per-profile model settings | Central budgets, credentials, egress restrictions | Gosoft LiteLLM |
| Backups and operational recovery | Local SQLite and run logs | Consistent backup, restore rehearsal, alarms | EBS snapshots and S3 export |

**No second distributed workflow engine in phase 1.** The SDLC policy adapter does not schedule Hermes workers itself: it checks trustworthy evidence and creates/authorizes subsequent Kanban cards or keeps them blocked. Kanban's built-in "review" is an agent coordination state, **not** a named code-owner approval or proof of policy compliance.

## SDLC mapping: Kanban tasks rather than duplicate scheduler

- Each feature/story gets a **project board** and a stable external OpenProject/GitHub ID mapping. Kanban boards provide local workspace/DB separation but **are not IAM isolation**.
- Create explicit, dependency-linked cards for PLAN (pm-ba), DESIGN (sa), BUILD (dev), TEST (qa), REVIEW (reviewer), release preparation (devops-sre), and MAINTAIN (devops-sre). REVIEW is a task within the DEPLOY SDLC stage, not a seventh SDLC stage.
- Start with **manual decomposition** (`kanban.auto_decompose: false`), which makes the six-stage graph and approval checkpoints predictable. Only turn on AI decomposition after cost/quality evaluations.
- Set `kanban.review_dispatch: false` in the first pilot **if explicit separate Reviewer cards are used**. Otherwise a built-in reviewer dispatch may overlap the independent REVIEW card. Re-evaluate against a pinned Hermes release. This setting does not turn off the explicit reviewer profile's tasks.
- **Before creating/unblocking a downstream card**, the policy adapter verifies actual artifact IDs/hashes, accepted Scope/Design where necessary, independent CI/QA reports, review blockers, and external human acceptance. A Kanban `done` status alone does not satisfy these gates.
- A Kanban worker that proposes approval, memory or skill promotion **never** grants itself authority. Leave protected merges and production deploy outside agent credentials.

### Role ownership

| Hermes profile | SDLC activity | Typical output | Forbidden |
|---|---|---|---|
| pm-ba | PLAN | intent.md, AC | protected merge/release |
| sa | DESIGN | spec.md, ADR | self-approve privileged change |
| dev | BUILD | branch, code, tests, PR | approve own code |
| qa | TEST | independent test evidence | weaken AC to force green |
| reviewer | DEPLOY review | Standards + Spec report with severity | edit own reviewed code and self-approve |
| devops-sre | DEPLOY prep + MAINTAIN | DEV release plan, incident evidence | unattended production action |

## Starting configuration (example, not automatically applied)

See [Kanban + multiplex sample](../examples/hermes-native/config.kanban.example.yaml). **Pin the Hermes release and validate the exact configuration syntax, gateway/profile routing, worker spawn and review behavior in an approved sandbox before rollout.**

- One gateway process with `gateway.multiplex_profiles: true` and `kanban.dispatch_in_gateway: true`.
- **Never** run the deprecated standalone Kanban daemon against the same board while gateway dispatcher is enabled.
- Use a conservative initial cap, e.g. `max_in_progress: 2` and `max_in_progress_per_profile: 1`; these are **pilot choices**, not Hermes defaults or guaranteed capacity.
- `failure_limit: 2` is a starting fail-closed bound; model/provider rate-limit behavior and retries need a smoke test.
- Profiles are explicit role-specific configurations; select LiteLLM aliases per role through existing gateway. Do not include production secrets in repo examples or task body.
- Admin via AWS Systems Manager on a **private** host. Keep Hermes Dashboard/API bound to loopback/private ingress with authenticated access; do not bind an unauthenticated Kanban dashboard publicly.

## Deploy and operations: the smallest sustainable production-like pilot

1. **Infrastructure:** one EC2 instance in a private subnet, EBS gp3 for Hermes home/workspaces, encrypted at rest, restricted SG, managed IAM identity, SSM and log shipping. Use approved egress to GitHub, Gosoft LiteLLM and MCP; avoid a public inbound management port.
2. **Hermes:** pin a known version, install under an unprivileged service account, enable the gateway as a long-running systemd service, enable multiplexer and gateway-owned Kanban. Verify profile writes and worker cgroup/scope behavior on this exact OS/image. A Docker container is **optional only after validating** child process management, cgroup/session lifetime and volume semantics; don't assume a stock container equals a safe Kanban host.
3. **Profiles:** provision all six explicit roles with separate homes, SOUL, approved Skills, model credentials and tool allowlists. One service manager owns dispatch. Restrict terminal/GitHub/MCP tools according to actual permission enforcement.
4. **Policy:** separate non-model validation for human approvals, CI/QA results, PR metadata, release/environment limits. A model narrative or Kanban status alone never makes a stage ready.
5. **Recovery:** take **application-consistent** SQLite backups (using a tested SQLite backup mechanism or quiescing writers) and EBS snapshots; export sanitized evidence to restricted S3. Test a restore into a **new isolated** host. Never treat blind copy of a live WAL database as a tested backup.
6. **Observability:** collect gateway/worker failures, stalled cards, blocked/review wait, host disk/memory, model spend, backup age, Kanban board growth, approval latency and cost per accepted task. Alarm on missing gateway or repeated provider failures.
7. **Updates:** pin/review Hermes upstream releases, stage validation (config migration, DB compatibility, profile snapshot), stop or drain active workers, back up, upgrade, smoke test, and roll back if compatibility fails.
8. **Security:** keep task/board text, generated code and third-party Skills as untrusted inputs; do not grant extra privileges by prompt or `SKILL.md`. Limit project data access by actual credentials and host boundaries.

## Scale path — measured, not pre-built

| Step | Trigger / action | Hard boundary |
|---|---|---|
| **S1: One Host** | One Hermes installation, six profiles, one gateway dispatcher. Monitor 7–14 days. | A single host is a failure domain; restore must be proven |
| **S2: Vertical Scale** | Increase EC2 CPU/RAM/EBS IOPS and tune Kanban concurrency based on model latency, provider RPM, memory and spend. | More parallel workers share host resources and local DB |
| **S3: Horizontal by shard** | Route distinct projects/workloads to **independent** Hermes EC2 hosts and boards; use project routing registry and external GitHub/OpenProject IDs. | No shared SQLite writer; no replicated live Kanban across hosts |
| **S4: Optional central dispatcher** | Only if cross-host routing, failover or SLA demands it, add a central intake queue/router with stable task ids and idempotent downstream effects. | This is a **new control plane**, not an automatic Hermes feature |

For a high-risk project, create a separate host **before** maximizing tenant density. Process/profile isolation on one host is not hard tenant isolation. Separate project boards on the same host provide organization and workspace scoping, not a dedicated security principal.

## Cost and alternative deployment decisions

- Pilot cost is dominated by **always-on EC2 + EBS + network egress/NAT if needed + LiteLLM spend**, with CloudWatch and backups additive. No per-agent continuously running VM is required.
- If the on-demand workload is extremely intermittent, assess a stop/start schedule **only after** testing gateway recovery, worker drain, notifications and EBS persistence. Do not shut down a host with active tasks.
- **ECS Fargate / AgentCore Runtime** remain future options for isolated external workers or a redesigned control adapter, but are **not drop-in replicas of a local Kanban SQLite dispatcher**.
- Do not introduce DynamoDB distributed leases, SQS, Step Functions, Kubernetes, serverless vector DB or per-worker containers as mandatory first-phase components without a clear reliability/scale requirement.

## MVP 2-day adjustment and current code PRs

The **two-day MVP constraint remains**. Prefer a **local Hermes installation with Kanban + six profiles** and minimal SDLC policy checker, one small feature, real LiteLLM, a real GitHub PR, independent QA, external human approval and evidence. Manual flow is acceptable **only where labelled**.

**PR #10/#11 are existing scaffold code** (local controller, `LocalStore`, `skills.py` and partial Day 2 evidence). Their passed unit tests do not prove Hermes-native execution, and they should **not** be merged under the new architecture without a fit/gap review. Reuse their artifact contracts, negative tests and Skills, but do **not** deploy `LocalStore` as a second production Kanban dispatcher or label fake model/PR evidence as "live". No changes to PR #10/#11 source are made in this design PR.

### Pilot acceptance gates

- [ ] Hermes pinned version's gateway and Kanban start/stop/recovery tested; one dispatcher owner only.
- [ ] Six named profiles load independent SOUL/Skills/credentials; test deny of cross-role privileged tools.
- [ ] One real feature completes PLAN → DESIGN → BUILD → TEST → DEPLOY review/release preparation → MAINTAIN with linked artifacts.
- [ ] Human approval and important review findings block the next card, independent from AI text.
- [ ] Real LiteLLM call and token/cost observations verified without exposing the key.
- [ ] Gateway crash/restart and SQLite restore test preserve board history; ambiguous GitHub side-effects reconciled without duplicate PR.
- [ ] Security checks prove no public dashboard, no self-merge, no production credentials and no cross-project data leak.
- [ ] Report the demo as PARTIAL if any major integration is mocked or manually substituted.

## Sources / assumptions

Hermes official documentation (recheck against pinned release):
- [Kanban — Multi-Agent Board](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban): native board/dispatcher, controls, local SQLite, single-host constraints
- [Profiles](https://hermes-agent.nousresearch.com/docs/user-guide/profiles): independent profile homes and memory; not an OS security boundary
- [Multi-Profile Gateways](https://hermes-agent.nousresearch.com/docs/user-guide/multi-profile-gateways): multiplex configuration
- [Messaging Gateway](https://hermes-agent.nousresearch.com/docs/user-guide/messaging): channel adapters

Architecture decisions (ours): EC2/EBS-first, explicit REVIEW cards, built-in reviewer off in pilot, external six-stage policy checks, host sharding, and no premature DynamoDB/ECS control plane.
