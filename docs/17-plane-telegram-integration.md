# 17 — Plane work management + Telegram entrypoint + Hermes Kanban execution

> **Architecture update / NOT DEPLOYED (2026-11-11).** Builds on [16 — Hermes-native deployment](16-hermes-native-deployment.md) and [15 — logical responsibility boundaries](15-logical-boundary-architecture.md). This is the accepted **target design** for the Hermes AI Software Company, not proof of a live Plane/Hermes/Telegram integration. No change to the six AI roles or the six Plan/Design/Build/Test/Deploy/Maintain processes.

## Architecture decision

**Use Plane as the only authoritative business work-management system. Keep native Hermes Kanban as an internal single-host execution board. Use Hermes Gateway's Telegram integration as the owner's conversational entrypoint and notification channel. Build one small Plane–Hermes Bridge containing SDLC policy validation and synchronization, rather than duplicating a worker scheduler.**

- **Plane** owns project, backlog, work item ID, business status, priority, owner, human-readable acceptance decisions and collaboration history.
- **Hermes native Kanban** owns internal profile assignment, dependencies, OS worker process/run state, heartbeat, local retry and per-board execution metadata; store a stable Plane reference for each execution.
- **Telegram** is a chat transport, command/intake surface and notification channel **only**. A Telegram reply or assistant message is not a trustworthy approval of privileged changes.
- **Thin Plane–Hermes Bridge + SDLC Policy Adapter** maps Plane work items to native Kanban cards, validates CI/QA/review and real approval evidence, handles synchronization/idempotency and guards the six SDLC stages. **It must not reimplement a distributed dispatcher.**
- **GitHub** remains the source of truth for code, PR/CI and protected merge. **LiteLLM** remains the approved LLM routing and spend gateway. **AgentMemory/SkillManager** remain logically separate from execution evidence.
- **OpenProject** is a previously proposed business-work adapter, now **superseded as default**. If existing work must be imported, plan a one-way migration; do **not** dual-write Plane and OpenProject. A separately governed alternative adapter can be retained for future portability.

## Component/deployment topology

~~~mermaid
flowchart TB
  OWNER["Human Owner / PM"] --> TG["Telegram bot (Hermes Gateway native adapter)<br/>chat requests and notifications"]
  OWNER --> PL["Plane UI<br/>project / backlog / status / collaboration"]
  subgraph AWS["Private AWS single Hermes host (EC2 + encrypted local EBS)"]
    TG --> G["One Hermes Gateway<br/>one bot token owned by one channel profile"]
    G --> INT["Constrained chat-intent adapter<br/>read status / create request / send notifications"]
    INT <--> BR["Thin Plane–Hermes Bridge + deterministic SDLC Policy Gates"]
    BR <--> K["Hermes native Kanban<br/>single-host SQLite, dependencies, dispatcher, worker runs"]
    K --> WORK["Six Hermes role profiles<br/>PM/BA · SA · Dev · QA · Reviewer · SRE"]
    K --> DB[("EBS: native Kanban DB / profile homes")]
  end
  PL <--> BR
  BR <--> GH["GitHub PR / CI / protected merge"]
  WORK --> LM["Gosoft LiteLLM model gateway"]
  BR --> NOTIF["Sanitized event notifications"]
  NOTIF --> TG
  DB -. "consistent backup, never shared live DB" .-> S3[("Private S3 backup / approved snapshots")]
~~~

**Plane → Bridge delivery** is conditional on network topology. Plane Webhook v2 requires an endpoint reachable from Plane. On a private EC2 with no approved inbound path, prefer **bounded outbound API reconciliation/polling** for the pilot, then adopt an authenticated/private webhook receiver when network policy permits. Never publish an unauthenticated Hermes dashboard or host just to receive Plane events.

### Source-of-truth and responsibility matrix

| Concern | Authoritative system | Mirrored as |
|---|---|---|
| Project/work item/backlog/priority/business status | **Plane** | Kanban card has immutable Plane UUID/reference; Telegram displays summary |
| Worker assignment, heartbeat, retry and task dependencies | **Hermes Kanban** | Plane gets only coarse `In Progress`, `Blocked`, `In Review`, `Done` after policy checks |
| Production or protected merge approval | **Authenticated external approval/SCM policy** | Audited decision reference linked in Plane; Telegram receives action-required link |
| Acceptance criteria/spec/QA and independent review | Versioned GitHub/CI/evidence refs with accepted Plane scope | Plane status, links and summary; Kanban internal card comments |
| Chat sender, notification destination | Hermes Telegram channel allowlist | Bound to approved user/Plane account by trusted identity registry |
| Model budgets/rate/spend | Approved LiteLLM admin | Redacted task usage and cost summary |
| Per-agent knowledge/skills | Hermes native profiles plus governed approved snapshot/skill registry | Pinned version/hash on task envelope, not a mutable workflow status |

## Plane ↔ Hermes bridge contract

**One Plane work item can produce multiple Kanban execution cards across the six stages.** Do not copy every internal worker status into Plane. Use this stable mapping:

~~~json
{
  "plane_workspace": "workspace-slug",
  "plane_project_id": "uuid-from-plane",
  "plane_work_item_id": "uuid-from-plane",
  "plane_identifier": "ENG-101",
  "hermes_host_id": "pilot-host-1",
  "hermes_board": "project-eng",
  "hermes_cards": {
    "PLAN": ["kanban-task-id"],
    "DESIGN": [],
    "BUILD": [],
    "TEST": [],
    "DEPLOY_REVIEW": [],
    "DEPLOY_PREP": [],
    "MAINTAIN": []
  },
  "policy_version": "approved-policy-version",
  "last_accepted_plane_event_id": null
}
~~~

The identifiers and example host are **schema illustrations**, not a working integration or literal IDs from the user's Plane workspace.

**Plane → Hermes** (create/change/approve): verify origin and authorization; fetch canonical current work item state from Plane API; accept only approved project/type and allowed stage; perform dedup check; create or unblock bounded Kanban card with reference; record bridge mapping and correlation ID. Do **not** interpret arbitrary comments or descriptions as commands to bypass stage gates.

**Hermes → Plane** (result): accept only result from the assigned role/task, reconcile actual GitHub CI/PR/evidence, evaluate severity and acceptance policy, then update only business-level Plane state/comment/evidence refs. Include a stable `origin=hermes-bridge` correlation marker and suppress reflected webhook echoes. A successful worker exit cannot set Plane `Done` without gate evidence.

**Plane Webhook v2:** validate `X-Plane-Signature` against raw request bytes using HMAC-SHA256 and a constant-time comparison; check workspace/project allowlists; deduplicate using **`event_id` (stable across retries), not `delivery_id`**; persist event handling/idempotency status, acknowledge only after durable record, periodically reconcile missed events through Plane API, and alert when webhook delivery is disabled. Use `X-Api-Key` over TLS for API calls with least permissions. Exact webhook availability and scopes in self-hosted Plane CE must be verified before coding.

**Failure modes:** stale Plane event -> refetch canonical state; duplicate webhook -> no duplicate Kanban card; post-PR model timeout -> query GitHub before retry; Hermes host restart -> restore local Kanban state and resume only safe work; Plane unavailable -> pause business updates and retry/reconcile, never silently mark `Done`.

### Business statuses (illustrative mapping)

| Plane UI status | Entry gate | Hermes internal state |
|---|---|---|
| Backlog | Owner captures intent, not yet authorized | No card or Kanban `triage` |
| Ready | Approved work is eligible to start | Native `todo/ready` |
| In Progress | One bounded role stage is executing | Native `running` |
| Blocked / Waiting Approval | Missing review, scope, credential or human decision | Native `blocked`, or downstream cards withheld |
| In Review | QA and independent Reviewer evidence pending | Native `review` or separate reviewer card |
| Done | All required stage gates, CI and required human decisions passed | Underlying accepted work recorded in native `done` |

Plane status names and availability vary by project and installation; configure per-project state IDs, never hardcode a string-to-ID assumption. The SDLC Stage is maintained in bridge mapping/evidence, **not inferred from Plane status labels**.

## Telegram interaction design

Use the **native Hermes Telegram adapter** and **one approved owner-facing Telegram bot token on a single ingress/channel profile** (typically the default Gateway profile). Kanban dispatches the six worker profiles internally. Do **not** duplicate the same Telegram token in each worker profile: multiplexed profiles cannot concurrently poll one credential.

**User intents** (design examples, not built-in Telegram slash commands or implemented actions):

| Owner message / intent | Read/write boundary | Expected behavior |
|---|---|---|
| “สร้างงาน API สุขภาพระบบ” | Plane create via Bridge only after identity, project/scope and policy checks | Show resulting Plane work-item ID; ask human to confirm scope if needed |
| “สถานะ ENG-101” | Plane read + authorized internal Kanban summary | Return coarse stage, blockers and links; no sensitive files in Telegram |
| “งานที่รออนุมัติ” | Trusted pending approvals view | Show scope/change/PR summary with **authenticated approval link** |
| “เริ่ม ENG-101” | Plane authorized command → Bridge | Verify eligibility, budget and Owner permission; request/start bounded Kanban task once |
| “สรุปงานวันนี้” | Plane reports + Bridge aggregate | Summarize accepted, blocked, cost and next action |
| “ยกเลิก ENG-101” | Restricted action | Require explicit identity/authorization; cancel safely; do not treat free-text as privileged command |

**Security principle:** Telegram user/chat allowlist prevents random access, but does not prove enterprise account, role or authorization. Link **Telegram numeric user ID → verified enterprise identity → approved Plane permissions** in a trusted registry. Avoid using an unverified name in a chat as approval evidence.

- **Pilot:** private one-to-one DM, allowlisted Telegram user IDs, read-only status + sanitized notifications; creating work is opt-in only when Plane identity binding and bridge authorization are verified.
- **High-impact changes:** Telegram message or button is *request/intent*, not final approval. Send a short-lived, authenticated SSO/SCM/Plane link for actual human Code Owner/Release Manager approval; verify server-side policy after callback.
- **Groups:** disable by default. If enabled later, require mention, restrict **sender IDs** not entire-chat allowlisting, avoid broad `TELEGRAM_GROUP_ALLOWED_CHATS`, and redact sensitive project data.
- **Credentials:** inject `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USERS` via protected secret/configuration, never Git; host egress to Telegram Bot API must be permitted. Do not set `TELEGRAM_ALLOW_ALL_USERS=true`.
- **Transport:** default **long polling** (outbound only) suits a permanently running private EC2. For future ingress webhook, explicitly configure `TELEGRAM_WEBHOOK_URL` + `TELEGRAM_WEBHOOK_SECRET` with TLS and secret verification; no webhook for the first pilot.
- **Operations:** one gateway/bot poller per credential; monitor bot connectivity, message retries, notification dedup and message delivery failures. Do not echo confidential task bodies, customer data, tokens or full source code into Telegram.

Recommended initial Gateway config overlay: [examples/hermes-native/config.telegram.example.yaml](../examples/hermes-native/config.telegram.example.yaml). The file contains **no tokens or account IDs** and needs a live version-compatibility smoke test.

## Delivery phases and acceptance

| Phase | Minimal delivery | Success proof |
|---|---|---|
| Existing MVP 2 days | Keep six-stage real sandbox flow, QA/Review/Owner gates. **Telegram read-only status and/or Plane manual linking only if ready within timebox** | Actual Hermes Kanban + LiteLLM + GitHub evidence; partial if mocked |
| Full F1 (operations) | One private EC2/EBS Hermes Gateway with Telegram long-polling, named authorized bot/profile, secured logs and backups | Approved DM produces real read-only response; unauthorized sender blocked |
| Full F2 (work management) | Plane v2 API adapter, Bridge mapping, eligible task intake/status sync, replay protection, secure callback or polling reconciliation | One Plane item drives an actual six-stage Hermes execution, status and evidence sync |
| Full F3 (governance) | Real enterprise identity binding, policy/approval audit, GitHub protected merge checks | Forged webhook, unauthorized Telegram write and self-approval all blocked |
| Full F4 (growth) | Governed memory/skills improvement and evaluation | Experience does not silently become approved learning |
| Full F5 (scaling) | Independent Hermes hosts by project when measured | Plane routes to proper host; no shared live SQLite |

**Do not add a second business tracker:** Plane replaces OpenProject in new implementation. Keep existing OpenProject references in historical docs as background only. Any migration is a separately approved data operation.

### Pilot acceptance tests

- [ ] Private Telegram bot can connect using one token/one Gateway poller; unauthorized user and unexpected group are rejected.
- [ ] A Telegram status query is restricted to projects the verified user is authorized to see and does not disclose secret/PII.
- [ ] A duplicate Telegram request or Plane Webhook v2 `event_id` does not create duplicate Plane items or native Kanban cards.
- [ ] A Plane update does not dispatch an agent until a policy check and an authorized work-item scope permit it.
- [ ] A worker result changes Plane business status only when real CI, QA, reviewer findings and required human approvals are verified.
- [ ] Feedback status sync does not create an infinite Plane webhook echo loop.
- [ ] Gateway crash/restart and missed Plane webhook reconcile without duplicate PRs or false approvals.
- [ ] Privileged Telegram “approve” or “deploy” intent alone never bypasses enterprise approval.
- [ ] No public ingress is required on the Hermes EC2 host for Telegram polling; Plane webhook or polling transport independently reviewed.

## Official references

- [Hermes — Telegram](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram)
- [Hermes — multi-profile gateway](https://hermes-agent.nousresearch.com/docs/user-guide/multi-profile-gateways)
- [Hermes — Kanban](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban)
- [Plane — REST API authentication](https://developers.plane.so/api-reference/introduction)
- [Plane — work item create v2](https://developers.plane.so/api-reference/v2/work-items/create-work-item)
- [Plane — Webhooks v2](https://developers.plane.so/dev-tools/intro-webhooks)
