# MVP Day 1: local controller and Plan/Design

**Status:** code scaffold and unit tests implemented; real LiteLLM access and actual owner identity **not verified** in CI. This is a local, single-user demo only. It does not execute production changes, GitHub pushes or environment tools. Do not use the CLI \`--actor\` flag as a real authorization mechanism.

## Requirements

Python 3.11+. From the repository root:

\`\`\`sh
export PYTHONPATH=src
python -m unittest discover -s tests -v
python -m hermes_orchestration --root workitems init --id demo-001 --objective "Read-only health endpoint with unit tests"
python -m hermes_orchestration --root workitems run --id demo-001 --dry-run
python -m hermes_orchestration --root workitems status --id demo-001
\`\`\`

A dry run writes \`MOCK_ONLY\` and cannot pass the Plan approval gate. For a real text-only OpenAI-compatible LiteLLM invocation, connect using environment variables (do **not** commit or echo key values):

\`\`\`sh
export HERMES_LITELLM_BASE_URL="https://agent-gateway.gosoft.co.th"
export HERMES_LITELLM_API_KEY="<set in local secrets manager, not shell history>"
export HERMES_MODEL_ALIAS="<approved text-capable model alias>"
# Start a fresh work item; mock artifacts cannot be marked live
python -m hermes_orchestration --root workitems init --id demo-002 --objective "Describe a read-only health endpoint"
python -m hermes_orchestration --root workitems run --id demo-002
# Human checks workitems/demo-002/intent.md, then records a *local attestation*
python -m hermes_orchestration --root workitems approve --id demo-002 --actor human:owner --decision accept
python -m hermes_orchestration --root workitems advance --id demo-002
python -m hermes_orchestration --root workitems run --id demo-002
# Human checks spec.md before accepting
python -m hermes_orchestration --root workitems approve --id demo-002 --actor human:owner --decision accept
python -m hermes_orchestration --root workitems advance --id demo-002
\`\`\`

Provider route: by default the adapter posts to \`<base>/v1/chat/completions\` (or \`<base>/chat/completions\` if the base already ends with \`/v1\`). Test compatibility with the gateway before claiming live integration.

## Verified behavior vs blocked integration

- Local state is persisted in \`workitems/<id>/state.json\`; events in \`events.jsonl\`. Those files are excluded from Git and **not immutable or multi-writer safe**.
- Every artifact is SHA-256 hashed and linked to the role and model mode.
- The controller forbids stage skipping, wrong role, mock advancement and absence of human acceptance for Plan/Design.
- \`approve --actor human:...\` is an **unauthenticated local self-declaration**. Do not expose the CLI over a network or treat it as production approval. Full phase must use authenticated external gate.
- A model request has a 45-second timeout, no tools, a bounded prompt and a maximum output tokens field. Daily or monthly USD spend is **not guaranteed capped** by this code. Use LiteLLM budget controls separately.
- Day 1 implementation covers Plan/Design only; BUILD/TEST/DEPLOY/MAINTAIN execution belongs to Day 2. The presence of stage names is not full SDLC delivery.
- Missing credentials cannot be substituted silently with \`--dry-run\`. Report real integration as BLOCKED if needed.

**Next:** [Issue #3](https://github.com/adisornsir/coe-eap-hermes-orchestration/issues/3) introduces Build/Test/Review/DEV-release/Maintain evidence and negative tests.


## Reviewed Skills integration (no upstream install)

This PR now includes a **read-only, stage/role allowlisted** loader in `src/hermes_orchestration/skills.py`. It selects original local instructions modelled on ideas from `vtno/skills`, checks metadata, records SHA-256 provenance, and appends the selected instructions to the **PLAN/DESIGN** prompt. A missing or corrupted required skill blocks execution. No third-party skill source, script or installer is run.

PLAN uses `requirements-writing`; DESIGN uses `requirements-writing` and `engineering-constraints`. BUILD and independent DEPLOY review are mapped for the stacked Day 2 PR. These instructions do not enforce permissions or human approval; the state machine and external policy remain authoritative. Run `PYTHONPATH=src python -m unittest discover -s tests -v` to verify loader failure cases.
