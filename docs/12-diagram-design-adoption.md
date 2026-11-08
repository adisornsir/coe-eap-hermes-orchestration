# 12 — Diagram Design adoption for Hermes AI-native SDLC

> **Decision (2026-11-08): ADOPT SELECTIVELY as a diagram authoring skill.** This is documentation and a checked-in static sample, **not** an installed Hermes runtime integration. It does **not** add a seventh role, change the six stages, authorize actions, or expand the two-day / 16-hour MVP. Read with [08 roles and stages](08-six-stage-role-target.md), [09 two-day MVP](09-mvp-two-day-execution.md), [10 Full roadmap](10-full-implementation-roadmap.md) and [11 procedure skills](11-vtno-skills-adoption.md).

## Source, license, provenance

- Upstream: [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design) (MIT); reviewed at Git commit [`e57eda6102a19444538ebd611d39534fad65b663`](https://github.com/cathrynlavery/diagram-design/tree/e57eda6102a19444538ebd611d39534fad65b663).
- Entry point: [`skills/diagram-design/SKILL.md`](https://github.com/cathrynlavery/diagram-design/blob/e57eda6102a19444538ebd611d39534fad65b663/skills/diagram-design/SKILL.md). Upstream documents **45 visual types**, SVG inside self-contained HTML, and optional Mermaid/draw.io/Excalidraw import.
- **Adoption method:** reference its layout/style/quality patterns and optionally install the vetted Agent Skill on an operator machine. **No repository scripts or upstream code have been vendored or executed** in this PR. The checked-in [six-stage HTML example](../examples/diagrams/ai-native-sdlc-six-stage.html) is an original, offline-safe SVG adaptation of the design principles; it is **not evidence of a working plugin installation or verified upstream exporter**.
- Before a Full rollout, re-review the specific upstream commit, license/third-party notices, privacy statement, scripts, dependencies, and version; pin the exact reviewed revision in the approved skill registry. Never auto-update production workers.

## Why this helps the six processes

| SDLC stage | Accountable agent | When a diagram earns its cost | Preferred visual type | Authoritative input |
|---|---|---|---|---|
| **PLAN** | PM/BA | Clarify customer path, scope and priorities | User journey / story map / quadrant | Owner-approved `intent.md`, acceptance criteria |
| **DESIGN** | Solution Architect | Explain topology, trust boundaries, data and control flow | Architecture / sequence / ER / data flow | `spec.md`, ADR, interfaces |
| **BUILD** | Developer | Make a complex dependency or changed boundary clear | Dependency graph / UML class / architecture delta | `plan.md`, source diff |
| **TEST** | QA/Tester | Show a non-trivial test journey or failure transition | State machine / flowchart | Locked acceptance criteria, test evidence |
| **DEPLOY** | DevOps/SRE + Independent Reviewer | Make release paths, approval gates and rollback explicit | Deployment / secure paved road / architecture delta | Release plan, reviewed diff, approval and CI evidence |
| **MAINTAIN** | DevOps/SRE | Explain incident causes, current-vs-target state and feedback | Fishbone / timeline / architecture delta | Incident record, observability and `lessons.md` |

**Skill versus authority:** any role may request the bounded diagram capability, but the deterministic controller decides when, what files may be read, whether the output may be written, and what approvals are needed. A generated image never certifies architecture, policy, CI, test results or human authorization. Reviewer must validate material claims against the original documents.

## MVP: keep the two-day clock unchanged

- **P0:** none. The six-stage demo, state machine, test evidence, independent review, secure approvals and PR remain mandatory; visuals must never displace them.
- **P1, only with slack:** use the included [six-stage overview](../examples/diagrams/ai-native-sdlc-six-stage.html) as a read-only artifact during the demo. Optionally ask an installed diagram skill to regenerate a single **Design** architecture view from approved `spec.md`, but installation/render/export troubleshooting is **not** on the critical path.
- No new agent, web UI, always-on renderer, Python/Playwright dependency, automatic download or upstream script execution is required for the MVP. Record a blocked/omitted optional diagram honestly.

## Full: governed integration, not another service

1. **F0:** review the upstream revision, privacy, fonts and script permissions; pin an approved version and a local/project brand profile. Prefer local approved fonts or system fallbacks for confidential diagrams.
2. **F2:** add a task-scoped `diagram-design` capability for PM/BA, SA and DevOps/SRE, with QA/Reviewer read-only inspection. Inputs must be referenced by work-item ID plus source commit/SHA; write derived diagrams to a versioned technical artifact path.
3. **F3:** enforce scoped read/write paths, extension and SVG safety checks, dependency allowlists, offline/no-external-network rendering, redaction, and independent review for diagrams describing security or release boundaries. Disable unchecked HTML scripting or browser network fetches. Generated diagrams cannot bypass human gates.
4. **F4:** evaluate fidelity, legibility and drift against `spec.md`/architecture decisions. Keep a diagram manifest with `work_item_id`, `source_sha`, `skill_sha`, `profile_version`, output hash, reviewer and approval status. Regenerate on source changes where justified; don't make diagrams the source of truth.

**Compatibility caveat:** the upstream `npx skills add` command targets compatible Agent Skills hosts (such as supported coding CLIs). Hermes loading/execution compatibility must be proven separately with the actual chosen runner and must not be assumed from that list.

## Operator usage (opt-in, on a reviewed local workstation)

```bash
# Inspect/pin an approved upstream revision first. This command is upstream's
# interactive installer and may fetch code; DO NOT run from a production worker.
npx skills add cathrynlavery/diagram-design
```

For a supported host, ask: *“Use the diagram-design skill to create an offline, self-contained HTML+SVG architecture diagram for the approved Hermes six-stage SDLC. Read docs/08 and the approved spec. Preserve the independent Reviewer and human Owner release gates. Match our approved project palette, do not load Google Fonts or external assets, and attach source commit references. Keep under nine primary nodes; split overview/detail if needed.”*

Generate from the **approved technical source**, not from speculation. Explicitly review any imported Mermaid/draw.io/Excalidraw content for accidental secrets and sensitive internal topology. Export PNG/SVG only after inspecting the HTML/SVG.

## Diagram acceptance checks

- [ ] Stage labels remain exactly **PLAN, DESIGN, BUILD, TEST, DEPLOY, MAINTAIN**; the maintenance feedback path returns to Plan.
- [ ] Six roles remain **PM/BA, SA, Developer, QA/Tester, Independent Reviewer, DevOps/SRE**; Reviewer is not silently merged into QA, and Owner is human.
- [ ] Visuals do not imply autonomous protected merges or production releases. Highlight human scope and release gates where relevant.
- [ ] Source file/commit and diagram revision are traceable, and Reviewer can compare the drawing to the design.
- [ ] SVG labels are legible; no misleading crossing/overlap, no hidden steps or contradictory flows. Prefer a table where it communicates better.
- [ ] Confidential outputs contain no PII, secrets or network-loaded external assets/fonts/scripts. Test the exported file offline.
- [ ] Generated diagram is supplemental and cannot count as test/approval evidence by itself.

## Privacy / operational note

The upstream [privacy policy](https://github.com/cathrynlavery/diagram-design/blob/e57eda6102a19444538ebd611d39534fad65b663/PRIVACY.md) says the tool itself has no telemetry server, but its default HTML templates **can load Google Fonts** and any AI host used processes the supplied files under its own provider controls. For enterprise use, explicitly remove external font imports, review other outgoing requests, and prefer sanitized/test diagrams unless data handling is approved. The committed example uses only local/system fonts, CSS and inline SVG, with no JavaScript or network links.
