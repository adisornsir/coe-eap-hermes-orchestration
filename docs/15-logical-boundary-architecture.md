# 15 — Separate durable execution, agent memory and skills

> **Status: proposed logical architecture, not a production implementation.** Applies to the existing six-role, six-stage Hermes workflow without changing the **two-day / 16-hour MVP**. Reviewed against [04 memory/learning](04-memory-learning-mood.md), [08 role/workflow baseline](08-six-stage-role-target.md), [09 MVP](09-mvp-two-day-execution.md), and [10 Full](10-full-implementation-roadmap.md). This design does **not** require four microservices, four persistent agents or separate databases.

## Decision

**Separate four logical responsibilities, share physical infrastructure when appropriate.**

| Logical component | Owns | Must not own |
|---|---|---|
| **WorkflowController** | SDLC transitions; assign task/role; evaluate policy, budgets and approval gates; decide retry or stop | Raw model outputs as authoritative state; learned knowledge; privileged credentials |
| **DurableExecution** | Task/attempt state, checkpoints, leases/locks, idempotency, result and evidence references, crash/restart recovery | Promotion of lessons into memory; skill changes; human authorization decisions |
| **AgentMemory** | Approved **role-scoped** and **project-scoped** knowledge snapshots, retrieval context, candidate lessons, version/promotion/rollback | Executable task state; retry decision; tool/permission grants |
| **SkillManager** | Immutable approved skill definitions and hashes, role/stage selection, skill evaluation/promotion/rollback | Executing arbitrary scripts on load; privilege escalation; autonomous workflow advancement |

**AgentWorker** is the executor, not a fifth control authority. One worker loads an explicit role profile, an immutable memory snapshot, approved skills and bounded task input, calls the approved model/tool adapter, then writes **task evidence** to DurableExecution. It cannot approve its own memory/skill promotion.

### Logical interactions

~~~mermaid
flowchart TB
    H["Human Owner / code owner"] --> WC["WorkflowController<br/>stage · assignment · budget · human gates"]
    WC --> DE["DurableExecution<br/>task state · checkpoint · retry · evidence"]
    WC --> RUN["AgentWorker<br/>Hermes role profile + model/tools"]
    DE -->|"task envelope / checkpoint pointers"| RUN
    AM["AgentMemory<br/>approved role/project knowledge"] -->|"pinned snapshot for this task"| RUN
    SM["SkillManager<br/>approved role/stage procedures"] -->|"pinned skill hashes"| RUN
    RUN -->|"results / immutable evidence refs"| DE
    DE -->|"candidate lesson + verified QA/CI evidence"| EVAL["Evaluation and human review"]
    EVAL -->|"approved candidate only"| AM
    EVAL -->|"approved and versioned skill only"| SM
    WC -->|"explicitly authorizes promotion according to policy"| EVAL
~~~

Arrow semantics: **approving a candidate** is separate from **accepting an SDLC stage**. An AI evaluator can recommend; named human/policy authority must be enforced by trusted control code. Workers may call the same local Python module in the MVP; the diagram is a boundary map, not a networking topology.

## Which data lives where?

| Data / owner | MVP storage | Full storage | Lifetime and trust |
|---|---|---|---|
| Work item stage, task attempt, retries, pending approvals | \`workitems/<id>/state.json\` | DynamoDB conditional writes | Execution record, controller only |
| Work evidence, checkpoints, tests, review/PR refs and event history | \`workitems/<id>/*.md\`, \`events.jsonl\` | Private S3 versioned task prefixes + DynamoDB index | Evidence; **not automatically personal memory** |
| Role persona, profile and policy references | \`roles/<role>/SOUL.md\` in Git | Pinned Git / approved profile snapshot | Versioned identity; permission remains externally enforced |
| Per-role lessons and preferences | Candidate \`lessons.md\` / runbook notes, **not auto-loaded** | S3 approved \`memory/<project>/<role>/<version>\` snapshots | Proposed → validated → approved; scoped and reversible |
| Shared project knowledge | Explicit Markdown / source files | GitHub/OpenProject references plus scoped S3 snapshots | Project authoritative; no cross-project leakage |
| \`SKILL.md\` definitions | Reviewed first-party local repo folders; fixed role/stage mapping | Git as source + approved, versioned immutable skill package | Procedures, not grants; evaluate changes before promotion |
| Performance/mood | Optional derived audit summary | Validated event aggregates, derived display only | Not memory truth, not permission control |

**Shared S3 or DynamoDB is acceptable.** Use separate namespaces, IAM policy, writer ownership and retention. Do not merge task history and agent memory into one freely editable \`MEMORY.md\`. S3 versioning alone is not an immutable security boundary; enforce write permissions/retention and capture content hashes, and use stronger object-lock controls where policy requires them.

### Proposed Full prefixes (illustrative, not deployed)

~~~text
s3://hermes-private-artifacts/projects/<project>/tasks/<task>/attempts/<attempt>/...
s3://hermes-private-memory/projects/<project>/roles/<role>/approved/<version>.json
s3://hermes-private-memory/projects/<project>/roles/<role>/candidates/<candidate>.json
s3://hermes-private-skills/approved/<skill-id>/<version>/SKILL.md
~~~

Physical buckets can be consolidated if strict prefix-level IAM and lifecycle controls are maintained. The **role/project boundary is part of every memory key**. Controller persists reference IDs/hashes, not secret values.

## Minimal contracts

These are **contracts to implement**, not claims that the current PR code already exposes these interfaces.

| Contract | Representative operations | Invariant |
|---|---|---|
| \`WorkflowController\` | \`plan_next(task)\`, \`check_gate(transition)\`, \`authorize_promotion(candidate)\` | Only trusted policy+human evidence can authorize |
| \`DurableExecution\` | \`start_attempt(idempotency_key)\`, \`checkpoint(attempt, refs)\`, \`finish(attempt, refs)\`, \`resume(task)\` | Conditional update; retries cannot duplicate side effects |
| \`AgentMemory\` | \`get_approved_snapshot(project, role, version)\`, \`propose_lesson(evidence_ref)\`, \`promote(candidate, expected_version)\`, \`rollback(version)\` | Never promote based solely on agent assertion |
| \`SkillManager\` | \`resolve(role, stage, approved_version)\`, \`evaluate(candidate)\`, \`promote(candidate, expected_version)\`, \`revoke(version)\` | No new tool grants from Markdown or model output |
| \`AgentWorker\` | \`run(task_envelope, profile, memory_ref, skill_refs)\` | Worker is isolated and receives pinned, least-privilege input |

**Compatibility:** Existing portability concepts \`WorkItemStore\`, \`TaskRunner\`, \`ModelGateway\`, \`ArtifactMemoryStore\` can remain as adapters temporarily. **Split the previous ambiguous \`ArtifactMemoryStore\` contract** into \`ExecutionArtifactStore\` (evidence) and \`AgentMemoryStore\` (approved knowledge) at the first Full refactor. Avoid creating multiple services for an interface rename.

### Task envelope provenance

~~~json
{
  "project_id": "demo",
  "work_item_id": "DEMO-001",
  "task_id": "task-001",
  "attempt_id": "task-001:1",
  "stage": "BUILD",
  "role_id": "dev",
  "policy_version": "policy-v1",
  "profile_version": "git-commit-sha",
  "memory_snapshot": {
    "scope": "project:demo/role:dev",
    "version": "approved-3",
    "sha256": "content-hash"
  },
  "skills": [{"id": "implementation-step", "version": "git-commit-sha", "sha256": "content-hash"}],
  "input_artifact_refs": ["s3://private-artifact-ref"],
  "checkpoint_ref": null,
  "max_attempts": 2
}
~~~

The literal values are an **illustrative schema**, not real stored data. For a new task, select versions once and pin them across retry/resume. A promoted lesson or skill becomes visible only to **a subsequent task** unless a named owner explicitly starts a new versioned attempt. Persist the reference and hash for an audit trail.

## Controlled growth sequence

1. **Perform:** AgentWorker produces scoped task results and test/build/CI evidence. DurableExecution stores the evidence and task state only.
2. **Propose:** The role may create a candidate learning entry, with a narrow evidence reference and source scope. Never treat an LLM explanation as verified fact.
3. **Evaluate:** Deterministic regression tests, QA/Reviewer checks, policy/PII review and a named human decision verify the candidate. Unapproved candidates remain quarantined.
4. **Promote:** AgentMemory (fact or lesson) or SkillManager (procedure) applies a **compare-and-swap** version update under a per-role/project promotion lock. Store the approving actor, source evidence and content hash.
5. **Consume:** The next assigned task loads the new approved snapshot and Skill version; current running tasks stay pinned. Rejected candidates are retained for audit or deleted per retention policy.
6. **Rollback:** Detect a regression, stop future selection, revert approved version pointer, then re-run evaluations. No rewrite of historical task evidence.

This keeps **execution recovery** separate from **agent development**. Checkpoint resumption should restore the previous task's versioned context, not accidentally load fresh unapproved memory.

## MVP versus Full: non-inflating scope

| Area | MVP Day 1/2 (existing PR #10/#11) | Full plan |
|---|---|---|
| WorkflowController | Existing local deterministic \`core.py\`, manual approval record, one task at a time | Authenticated external gates, robust policy checks |
| DurableExecution | Same \`LocalStore\` JSON/Markdown; best-effort local restart state | F1: DynamoDB conditional state/leases/idempotency, S3 evidence, ECS worker recovery |
| AgentMemory | **No autonomous persistent learning**; optional human-reviewed \`lessons.md\`, kept separate from \`state.json\` | F4: per-role/project versioned snapshots, approved promotion, rollback |
| SkillManager | Reviewed local \`skills/*.md\` and explicit \`skills.py\` allowlist/provenance in PR #10 | F4: registry, eval, secure promotion/revocation and version reconciliation |
| AgentWorker | Existing PLAN/DESIGN LiteLLM adapter + partial Day 2 scaffold | F1/F2: real isolated Hermes workers across six stages |
| Multi-service infrastructure | None | Deploy components together initially; split only on measured operational need |

**MVP code status:** PR #10 and stacked PR #11 are not merged; their local \`LocalStore\` and Skill Loader are **partial implementations**, not an AgentMemory service or authenticated enterprise runtime. Do not add Fargate, queues, network APIs, a vector database or automatic skill learning to the 16-hour MVP.

## Full sequencing and gates

- **F0:** Freeze stable contracts and distinct names; add tests ensuring task history cannot become approved memory/skill without a promotion decision.
- **F1:** Deliver DurableExecution (DynamoDB/S3/ECS) with tasks surviving controller restart, exactly-once *state transitions* via conditional writes and **effectively-once** external side-effects via idempotency/reconciliation. Do **not** promise mathematically exactly-once execution across GitHub/CI/model APIs.
- **F2:** Add complete role execution and actual GitHub/OpenProject references, QA and Reviewer handoffs with read-only memory retrieval and pinned skill versions.
- **F3:** Secure source access, authenticated approval, role/project permissions, restricted promotion credentials, retention, audit and negative security tests. Mandatory control gates precede any production-impact feature.
- **F4:** AgentMemory and SkillManager governed learning: candidate → eval → human authorization → versioned promotion → rollback; measure quality, cost and simulated mood without changing privileges.
- **F5:** Scale and portability only if necessary.

### Acceptance tests to add

1. Controller crash after an accepted stage recovers the same evidence and does not repeat the accepted transition.
2. Worker retry with the same idempotency key does not create two PRs or double-publish an approved skill.
3. A raw failing task log or AI-proposed lesson **cannot** become approved personal memory without an independent promotion event.
4. A skill containing a request to grant itself tool access **cannot** change role/tool policy.
5. Project A's Developer cannot read Project B's memory snapshot; Reviewer cannot write Developer's personal memory.
6. A task running with memory v3 and skill v2 continues with **v3/v2** after memory v4 is promoted; the next task may load v4 only when approved.
7. Reviewer/Owner reject an invalid candidate; the approved pointer remains unchanged and rollback works.

## Non-goals and practical notes

- No new seventh AI role called 'Memory Agent'; controlled learning is a capability that existing roles may propose and a named authority approves.
- No standing full-permission shared Hermes home. A worker operates on a project/role-scoped, pinned snapshot and disposes local scratch on exit.
- No model training or fine-tuning is implied by 'agent growth'. It is versioned knowledge/skill/procedure improvement.
- No simulated feelings or permission changes from 'mood'. Display is derived from verified workload and task outcomes.
- Neither \`SKILL.md\` nor memory text may override controller policy, security gates, IAM or GitHub branch protections.
