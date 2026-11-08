# MVP Day 2: controlled Build, Test, Review, Deploy preparation and Maintain

> **Status: local/sandbox code + tests only.** Requires Day 1 branch (#10) and an explicitly accepted Plan and Design. Neither a real corporate LiteLLM review nor a protected GitHub merge or deployment was performed. The workflow is a partial vertical slice.

## Boundaries

- The command \`build\` records an existing, external code change + plan; it **does not autonomously create or verify a Git commit**. The SHA is syntactically checked only; source says \`external_git_commit_not_verified\`. Never treat it as immutable proof.
- \`test\` runs the repository's Python unittest suite as a subprocess with a timeout; the resulting exit code is independent test evidence. Failing QA prevents forward transition.
- \`review\` reads a bounded local Git diff and accepted \`spec.md\`; it calls a text-only model to produce separate **Standards** and **Spec** sections. It cannot edit or approve a PR. This review still requires a real model key and independent human validation.
- \`release\` checks QA evidence, review report hash, and a real-formatted GitHub PR URL; writes **release preparation only**, never merges or deploys. It does not verify GitHub PR identity remotely or parse model findings into a hard block; human gate remains mandatory.
- \`maintain\` records user-supplied observations. No live monitoring, auto-incident ingestion or skill promotion runs.
- All role instructions, evidence and metadata are **local mutable files**. A user able to edit them can forge state or model evidence. This is **not** a security boundary or production gate. Protected merges and releases must be managed by GitHub/IAM/CI outside this MVP.

## Commands

From repo root with Python 3.11+:

\`\`\`sh
export PYTHONPATH=src
python -m unittest discover -s tests -v

# After Day 1 has reached BUILD on demo-002:
python -m hermes_orchestration.day2 --root workitems build \
  --id demo-002 --plan-file plan.md --commit-sha YOUR_REAL_40_CHAR_COMMIT_SHA
python -m hermes_orchestration --root workitems advance --id demo-002

python -m hermes_orchestration.day2 --root workitems --repo . test --id demo-002
python -m hermes_orchestration --root workitems advance --id demo-002

# Model key and model alias must be configured as in Day 1. This is read-only.
python -m hermes_orchestration.day2 --root workitems --repo . review \
  --id demo-002 --base main

python -m hermes_orchestration.day2 --root workitems release --id demo-002 \
  --pr-url https://github.com/OWNER/REPO/pull/NUMBER

# Human must read review and release evidence before locally acknowledging approval.
python -m hermes_orchestration --root workitems approve --id demo-002 \
  --actor human:owner --decision accept
python -m hermes_orchestration --root workitems advance --id demo-002

python -m hermes_orchestration.day2 --root workitems maintain \
  --id demo-002 --observations "Record DEV feedback and next improvement"
\`\`\`

The \`plan.md\` file must be an accepted implementation plan prepared separately. This command sequence **does not** auto-write code or create a PR; those are external human/agent tasks. A broken QA run must return to BUILD via \`advance --target BUILD\`, then be retested on the next iteration. There is no unbounded retry loop. The reviewer report is read-only and should be followed by a named human reviewer and external code-owner approval.

## Evidence and limitations

- Unit tests exercise fake state artifacts to prove transition policy, not actual identity authentication or integration effectiveness.
- \`demo_app/health.py\` is only a small read-only function used by the test suite; it is not an HTTP server.
- The actual six-stage external integration run remains **BLOCKED** until corporate LiteLLM access, code PR verification, human approval and environment privileges are checked.
- Full phase adds durable state, authenticated external approvals, locked immutable evidence, real GitHub/OpenProject connectors, DevOps/SRE monitoring and safe deployment tools. See [Full roadmap](10-full-implementation-roadmap.md).


## Skills used by the Day 2 workflow

The Developer's `implementation-step` and `engineering-constraints` skills are explicitly resolved and their versions recorded as **recommended** on an existing commit, not claimed to have generated that commit. The independent Reviewer actually loads `two-axis-review` (reviewed local Markdown with SHA-256 provenance) into its model prompt; it cannot run arbitrary scripts or approve the PR. Review retries stop after two invocations (initial + one re-review). A remaining important finding is escalated for human decision.
