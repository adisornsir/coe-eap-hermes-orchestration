# 06 — Reference project adoption map (MVP)

> **Important: As of this design baseline, NO external project source code has been copied, vendored, installed, or integrated.** These are **design inspirations**, not dependencies. The only planned agent runtime is Hermes; none of the described connectors or adapters are implemented yet.

## Reference → design decision → actual implementation boundary

| Reference | Relevant ideas | Where reflected in our design | MVP adoption | What NOT to do |
|---|---|---|---|---|
| [MetaGPT](https://github.com/FoundationAgents/MetaGPT) | Software-company roles, SOPs, tangible deliverables | `03-agent-team-design.md`: PM → BA/Tester → SA/Specialist → Dev → QA, handoff contracts | **Concept only**; implement role prompts / artifact templates on Hermes | Do not install MetaGPT runtime |
| [ChatDev](https://github.com/OpenBMB/ChatDev) | Multi-role collaboration and review/feedback cycles | `03-agent-team-design.md`: task handoff, review failure loops | **Concept only**; asynchronous controller assignments | Do not introduce free-form agent-to-agent chat as source of truth |
| [Letta Code](https://github.com/letta-ai/letta-code) | Persistent agent identity, evolving memory, reflection | `04-memory-learning-mood.md`: snapshot, per-role episodic lessons, versioned skills | **Concept only**; implement with native Hermes Memory/Skills + S3 versioning | Do not add a second stateful agent runtime or memory service without a demonstrated limitation |
| [SoulLink](https://github.com/miyamoriaoi1997-del/Soul-Llink) | Persona, emotion expression and memory | `04-memory-learning-mood.md`: UI-facing simulated mood | **Evaluate only**; no dependency in MVP | Do not adopt until compatibility, security, license and operational fit have been verified |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Explicit workflows and orchestration | `01-architecture-options.md` + `03-agent-team-design.md`: deterministic stages | **Concept only**; small controller with explicit task states | Do not nest CrewAI inside Hermes for MVP |
| [Emotion Engine](https://github.com/pioneerjeff-labs/emotion-engine) | Explainable emotion/appraisal models | `04-memory-learning-mood.md`: workload and success-driven mood | **Concept only**; simple rules computed from external evidence | No subjective feelings, no agent authority derived from mood |

## What is actually reused in MVP?

**Planned actual dependency:** Hermes runtime and its native profile, memory and skill mechanisms (exact version to be pinned and validated in Sprint 0).

**Planned existing integrations:** LiteLLM (model access, spend), OpenProject (work-item management), GitHub (code, PRs, CI) and AWS ECS/S3/DynamoDB/CloudWatch. These are target design decisions, **not deployed or integrated by this repository**.

**Build small ourselves:** (a) deterministic controller adapter for task assignment, lock, retry and approval; (b) artifact contracts; (c) role-specific Hermes profile templates and permissions; (d) a memory snapshot promotion wrapper; (e) pure rule-based KPI/Mood calculator. These should be small ordinary modules rather than an additional AI framework.

## Recommended adoption sequence

1. **MVP P0 — roles/workflow:** convert MetaGPT/ChatDev patterns to five Hermes role prompts with one artifact-based stage machine. First deliver an Owner-approved PR.
2. **MVP P1 — identity/learning:** use Hermes native memory and skills; persist *approved* snapshots in S3 and keep learning/reflection evidence. Examine Letta concepts for later improvements.
3. **MVP P1 — simulated emotions:** compute first-pass acceptance rate and 7-day workload fit from OpenProject/CI/Owner reviews. Display mood labels and rationale; keep it outside permissions/approvals. Use SoulLink/Emotion Engine as **reading references**, not copied components.
4. **Post-MVP — selective evaluation:** only run a sandbox spike to adopt SoulLink or a dedicated memory engine if actual constraints justify it; review current upstream version, license and dependencies first.

## Before importing code from any upstream project

Create an ADR covering:
- exact commit/tag and license, transitive dependencies, maintenance status, vulnerabilities
- compatibility with pinned Hermes version and ECS Fargate
- data sharing/privacy implications (memory, telemetry, credentials)
- benchmark against the built-in Hermes/our simple solution
- migration/rollback path and measurable benefit

**Decision:** prefer **reference-driven design** over multi-framework integration. No source code reuse is claimed.
