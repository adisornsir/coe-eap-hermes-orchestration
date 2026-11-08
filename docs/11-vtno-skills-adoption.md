# 11 — Adopt useful patterns from vtno/skills without changing the Hermes architecture

> **Decision (2026-11-08): ADOPT SELECTIVELY as process guidance, not as a runtime framework. Documentation/design only; nothing installed or executed.** Read with [08 six-stage roles](08-six-stage-role-target.md), [09 two-day MVP](09-mvp-two-day-execution.md) and [10 Full roadmap](10-full-implementation-roadmap.md).

## Source studied and scope

- [vtno/skills](https://github.com/vtno/skills), examined at commit [`98f8583d33bd53b7a7c12339b682aaad2dad6fc5`](https://github.com/vtno/skills/tree/98f8583d33bd53b7a7c12339b682aaad2dad6fc5).
- Five packages: `implement`, `code-review`, `engineering-rules`, `technical-writing`, and `unslop`.
- The `implement` and `engineering-rules` packages are locally authored in the source repository; its `VENDORED.md` documents MIT-licensed upstream sources for `code-review` (mattpocock/skills) and `technical-writing` + `unslop` (cursor/plugins, pstack). **No blanket license for the two local packages was verified**. Use their architectural ideas; do not copy source code, full instructions, or install scripts into Hermes without checking permissions. If vendoring later, keep upstream attribution and applicable full license notices.

**Decision:** Hermes keeps **six logical core roles and six SDLC processes**. Skills describe *how* a role performs an assigned job. A role is not a skill, and a skill cannot authorize access or advance workflow state.

| Concern | Owner | Enforcement |
|---|---|---|
| **Who** performs work? | Six role profiles + specialist pool | Controller role registry; isolated task identity |
| **When** does work start/advance? | Hermes six-stage state machine | Deterministic transition rules and approval records |
| **How** should work be done? | Versioned, task-scoped Skill recipes | Explicit resolver/loader or reviewed prompt excerpts; quality evaluated by tests |
| **What can it do?** | Policy, IAM, sandbox, MCP/tool allowlist | Deterministic external gate, never `SKILL.md` alone |

## Source-to-Hermes decisions

| Observed source skill | Source behavior | Adaptation for Hermes | MVP / Full |
|---|---|---|---|
| [implement](https://github.com/vtno/skills/blob/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/implement/SKILL.md) | One plan step → author PR → separate report-only reviewer → revise until hard findings disappear; user merges | Adopt **one work-item / one PR / independent reviewer**. Add Hermes ceilings: MVP maximum **two review iterations total** (initial review + one re-review), bounded model calls and explicit BLOCKED/escalation on remaining important findings. No self-merge. | MVP P0 bounded, Full expanded with budget policy |
| [code-review](https://github.com/vtno/skills/blob/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/code-review/SKILL.md) | Two independent axes: **Standards** vs **Spec**, fixed merge-base diff, independent reports; cosmetic smells advisory | Reviewer produces two distinct sections, names issue/spec and pinned diff, severity and evidence. Use **separate contexts** in Full; MVP can invoke a single Reviewer session with two explicit passes because independent model contexts are an optimization, not a security boundary. **Human code owner still approves protected merge.** | MVP P0 two-axis report; Full parallel reviewers and CI severity checks |
| [engineering-rules](https://github.com/vtno/skills/blob/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/engineering-rules/SKILL.md) | Inner layer first; caller-defined interfaces; hand-written fakes; deterministic tests; formatter, warnings-as-errors, three test runs including serial | Adopt small vertical slice, caller-driven interfaces and reproducible tests. Keep `make test` (or equivalent) and one failure-path test mandatory. Source's three repeated full-suite runs and different seeds are **Full / flaky-test diagnostic** guidance, not unconditional two-day MVP requirements. | MVP P0 lean checks; Full targeted stronger checks |
| [technical-writing](https://github.com/vtno/skills/blob/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/technical-writing/SKILL.md) | Diátaxis tutorial/how-to/reference/explanation; concise, direct docs | Apply to `intent.md`, `spec.md`, runbooks and change notes. Use a short reviewed template rather than injecting the entire writing standard into every run. The source marks it `disable-model-invocation: true`; activation must be tested for the chosen loader. | MVP P1 or manual template; Full governed reusable skill |
| [unslop](https://github.com/vtno/skills/blob/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/unslop/SKILL.md) | Edit text to remove AI filler, vague attributions and jargon | Optional doc-cleanup pass after correctness checks; **never** allow stylistic cleanup to change intent, acceptance criteria, policy or evidence. | MVP omit unless time remains; Full document quality check |

These are **design adaptations**, not claims that this source repo's five skills run unchanged in Hermes.

## Map skills to six stages and the six role contracts

| Stage | Lead | Skills used or analogous internal recipes | Artifact/gate |
|---|---|---|---|
| PLAN | PM/BA | `technical-writing` ideas for crisp structured problem statements | `intent.md` accepted by Owner |
| DESIGN | Solution Architect | `engineering-rules` layering + writing conventions | `spec.md` + decisions/risk approvals |
| BUILD | Developer | `implement` one planned PR; `engineering-rules` bounded checks | `plan.md` + code/branch/tests |
| TEST | QA/Tester | Deterministic tests/fakes; independently inspect original acceptance criteria | `test-report.md`; false -> BUILD |
| DEPLOY | Independent Reviewer + DevOps/SRE | `code-review` Standards and Spec passes; `implement` review/rework loop | `review-report.md`, release record, human merge/release authorization |
| MAINTAIN | DevOps/SRE | Structured incident summary, regression report, reviewed writing | Incident/lessons -> new `intent.md` |

**Important:** The two review axes belong to the independent **Reviewer** role. They **do not replace QA**, whose tests establish actual observed behavior. A Reviewer running in a new model context is *less coupled* to the author but still not a human, a security sandbox, or a source of authorization.

## Skills boundary for Hermes

### Minimal MVP — no new daemon or mass installer

1. Store **one to three short first-party, project-owned** task-specific `SKILL.md` recipes, written from scratch and reviewed: `implementation-step`, `two-axis-review`, and optionally `engineering-constraints`. Suggested location: `skills/<name>/SKILL.md` for the Hermes internal resolver. If the target client natively supports `.agents/skills/` or `.github/skills/`, use an approved install/export convention **after verifying behavior**; do not assume Hermes has native Agent Skills discovery.
2. Day 1 controller loads a chosen recipe *explicitly*, validates its `name`, `description`, reference path, version and allowed stage/role, and records `skill_id` + `skill_version` or Git SHA in the task envelope and audit evidence.
3. Day 2 Developer executes **one step**; Reviewer writes **Standards** and **Spec** sections, then Developer gets **at most one fix attempt**. QA reruns tests. If important findings remain, mark `BLOCKED`; do not auto-merge.
4. Do not execute arbitrary bundled `scripts/`, network install commands, auto-downloaded skills or third-party tools during task execution. Use pre-reviewed local files with Git pinning; command execution is controlled by an external tool allowlist.
5. Keep P0 demo within the existing **16 engineer-hours**. This integration **replaces** part of the already-planned role instructions and review logic; it adds no separate day or runtime infrastructure. If tasks overrun, implement two-axis review as output contract without building a generic skill registry.
6. Tests: independent QA/CI evidence, negative transition/approval test, and proof that a Reviewer cannot write code or approve the protected PR.

**Minimal planned layout** (not currently implemented):

```text
skills/
  implementation-step/SKILL.md
  two-axis-review/SKILL.md
  engineering-constraints/SKILL.md     # optional in the two-day MVP
src/hermes_orchestration/
  skill_loader.py                      # read-only first-party file resolver
  controller.py                        # authoritative state/policy/approvals
  runner.py                            # model/tool invocation
tests/test_skill_loading.py
tests/test_review_gate.py
```

All files must be authored for Hermes. Do **not** copy local `vtno/skills/implement` or `engineering-rules` without verifying permission.

### Full — governed skill library

- **Skill registry** contains `skill_id`, version/commit SHA, source URL, author/license, owning policy lead, supported roles/stages, input/output contract, approved scripts, content hash, security review, eval results and promotion state.
- **Skill selection** uses explicit role/stage/task allowlists and user intent; load just the matching instructions. File content is treated as lower-trust procedure, not overriding role policy or Owner decisions.
- **Skill lifecycle:** propose → static/schema scan and license check → test in sandbox/eval → named human approve → publish versioned immutable snapshot → monitor regressions → revoke/rollback. A skill can propose another skill but **cannot approve or grant itself permissions**.
- **Review execution:** use source-inspired parallel Standards/Spec reviewers when cost and benefit justify it; keep outputs separate, with deterministic severity thresholds and human code-owner approval.
- **Evaluation:** trigger on role, model or skill version change; measure correct skill selection, test pass, spec compliance, security policy, cost/task, false-positive review noise and review iterations. Add incident cases to regression set.
- **Portability:** adapt an approved Agent Skills-style `SKILL.md` metadata format. Keep loader adapters separate for Hermes CLI, Copilot, Claude and future clients. Verify each client; no guaranteed cross-client equivalence.
- **Supply chain:** pin upstream commit, review diffs before upgrading, preserve applicable copyright/license notices, static scan scripts, disable auto-fetch at runtime and sanitize any external content.

## Risks and decisions

1. **Trust:** Imported instructions can be prompt-injection carriers; `SKILL.md` never changes hard tool permissions, approval gates or policy version. Prompt behavior can still be compromised, so high-impact actions must be externally blocked.
2. **Budget/loop:** The original `implement` repeats review until findings disappear with no explicit loop budget. Hermes adds attempts/timeout/token/USD limits; `BLOCKED` and human escalation are valid results.
3. **License:** `VENDORED.md` identifies MIT upstream copies, but the two local skills do not have an explicit license in the reviewed root metadata. Prefer original project-owned skill wording for design MVP.
4. **Testing:** Re-running full tests three times may be expensive or irrelevant to tiny MVPs; use a deterministic minimum, then expand for flaky/concurrent issues.
5. **Security vs quality:** A second LLM reviewer improves checks but does not establish independence comparable to human approval or platform permission separation.
6. **Docs:** Writing cleanup cannot silently mutate requirements or test evidence.

## Decision and implementation ownership

- **Keep** existing Issues #2 and #3 as the two-day MVP backlog. Add focused checklist items without increasing the timebox: first-party `SKILL.md` + explicit loader; bounded review loop; two-axis output and failure-path test.
- **Full F0/F2/F3/F4:** schema and licensing baseline; two-axis review and governed skill registry; enforcement outside prompts; skill eval and lifecycle. Full scope is not reduced.
- **No vendor submodule and no direct dependency** on `vtno/skills` at runtime. Record the upstream commit as a design reference, not a package lockfile.
- **No runtime changes in this PR**. The PR remains a design proposal until approved.

## Sources

- [vtno/skills README](https://github.com/vtno/skills/blob/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/README.md), [implement](https://github.com/vtno/skills/tree/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/implement), [code-review](https://github.com/vtno/skills/tree/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/code-review), [engineering-rules](https://github.com/vtno/skills/tree/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/engineering-rules), [technical-writing](https://github.com/vtno/skills/tree/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/technical-writing), [unslop](https://github.com/vtno/skills/tree/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/unslop), [upstream license manifest](https://github.com/vtno/skills/blob/98f8583d33bd53b7a7c12339b682aaad2dad6fc5/VENDORED.md).
- [Agent Skills specification](https://agentskills.io/specification) and [GitHub Copilot skill directory guidance](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).
