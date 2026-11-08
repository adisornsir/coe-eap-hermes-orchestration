"""Deterministic local workflow; no model or skill may authorize transitions."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STAGES = ("PLAN", "DESIGN", "BUILD", "TEST", "DEPLOY", "MAINTAIN")
ROLES = {
    "PLAN": "pm-ba", "DESIGN": "sa", "BUILD": "dev",
    "TEST": "qa", "DEPLOY": "devops-sre", "MAINTAIN": "devops-sre",
}
ARTIFACTS = {
    "PLAN": "intent.md", "DESIGN": "spec.md", "BUILD": "plan.md",
    "TEST": "test-report.md", "DEPLOY": "release-record.md",
    "MAINTAIN": "incident-or-lessons.md",
}
NEXT = dict(zip(STAGES, STAGES[1:]))
REWORK = {"DESIGN": "PLAN", "BUILD": "DESIGN", "TEST": "BUILD", "DEPLOY": "BUILD", "MAINTAIN": "PLAN"}
HUMAN_APPROVAL = {"PLAN", "DESIGN", "DEPLOY"}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class WorkflowError(ValueError):
    """An operation does not satisfy the configured workflow."""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=2, sort_keys=True)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class LocalStore:
    """Single-process DEV store; NOT safe for concurrent writers/production."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def item_dir(self, item_id: str) -> Path:
        if not ID_RE.fullmatch(item_id):
            raise WorkflowError("Invalid work item ID")
        return self.root / item_id

    def _state_path(self, item_id: str) -> Path:
        return self.item_dir(item_id) / "state.json"

    def _event(self, item_id: str, event: dict) -> None:
        line = {"at": utcnow(), "work_item_id": item_id, **event}
        with (self.item_dir(item_id) / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, sort_keys=True) + "\n")

    def init(self, item_id: str, objective: str) -> dict:
        if not objective.strip():
            raise WorkflowError("Objective is required")
        directory = self.item_dir(item_id)
        directory.mkdir(parents=True, exist_ok=True)
        if self._state_path(item_id).exists():
            raise WorkflowError("Work item already exists")
        state = {"work_item_id": item_id, "objective": objective.strip(), "stage": "PLAN",
                 "status": "QUEUED", "artifacts": {}, "approvals": [], "history": []}
        _atomic_json(self._state_path(item_id), state)
        self._event(item_id, {"event": "init", "stage": "PLAN"})
        return state

    def load(self, item_id: str) -> dict:
        try:
            return json.loads(self._state_path(item_id).read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise WorkflowError(f"Unknown work item: {item_id}") from exc

    def record(self, item_id: str, text: str, *, role: str, mode: str, model: str = "", evidence: dict | None = None) -> dict:
        """Store a stage output; a mock result is never a successful stage artifact."""
        state = self.load(item_id)
        stage = state["stage"]
        if role != ROLES[stage]:
            raise WorkflowError(f"Role {role} not allowed to deliver {stage}")
        if state["status"] not in {"QUEUED", "BLOCKED"}:
            raise WorkflowError("Stage already recorded; advance or return to rework first")
        if not text.strip():
            raise WorkflowError("Empty artifact")
        if mode not in {"live", "mock"}:
            raise WorkflowError("mode must be live or mock")
        artifact = ARTIFACTS[stage]
        path = self.item_dir(item_id) / artifact
        path.write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        state["artifacts"][stage] = {"path": artifact, "sha256": digest, "mode": mode,
                                       "role": role, "model": model, "evidence": evidence or {}}
        state["status"] = "REVIEW_READY" if mode == "live" else "MOCK_ONLY"
        _atomic_json(self._state_path(item_id), state)
        self._event(item_id, {"event": "record", "stage": stage, "role": role,
                              "mode": mode, "sha256": digest})
        return state

    def approve(self, item_id: str, *, actor: str, decision: str) -> dict:
        """Local manual acknowledgement only; does NOT authenticate the actor."""
        state = self.load(item_id)
        if state["stage"] not in HUMAN_APPROVAL:
            raise WorkflowError("This stage has no human approval gate")
        if state["status"] != "REVIEW_READY":
            raise WorkflowError("A non-mock artifact is required before approval")
        if not actor.startswith("human:") or len(actor) < len("human:") + 2:
            raise WorkflowError("Actor must identify a human approver")
        if decision not in {"accept", "reject"}:
            raise WorkflowError("Decision must be accept or reject")
        artifact_sha = state["artifacts"][state["stage"]]["sha256"]
        record = {"stage": state["stage"], "actor": actor, "decision": decision,
                  "artifact_sha256": artifact_sha, "at": utcnow(), "verified_identity": False}
        state["approvals"].append(record)
        if decision == "reject":
            state["status"] = "BLOCKED"
        _atomic_json(self._state_path(item_id), state)
        self._event(item_id, {"event": "decision", **record})
        return state

    def advance(self, item_id: str, *, target: str | None = None) -> dict:
        state = self.load(item_id)
        stage = state["stage"]
        target = target or NEXT.get(stage)
        if target is None:
            raise WorkflowError("MAINTAIN is terminal; create the next intent as a new work item")
        if target == REWORK.get(stage):
            if stage == "MAINTAIN" and state["status"] != "REVIEW_READY":
                raise WorkflowError("Maintenance feedback required")
            state["history"].append({"from": stage, "to": target, "kind": "rework", "at": utcnow()})
            state["stage"], state["status"] = target, "QUEUED"
            state["artifacts"].pop(target, None)
            _atomic_json(self._state_path(item_id), state)
            self._event(item_id, {"event": "rework", "from": stage, "to": target})
            return state
        if target != NEXT.get(stage):
            raise WorkflowError(f"Invalid transition: {stage} -> {target}")
        if state["status"] != "REVIEW_READY":
            raise WorkflowError("A real completed artifact is required")
        artifact = state["artifacts"].get(stage)
        if not artifact or artifact["mode"] != "live":
            raise WorkflowError("Mock output cannot advance workflow")
        if stage == "BUILD" and not artifact.get("evidence", {}).get("commit_sha"):
            raise WorkflowError("BUILD requires actual code commit evidence")
        if stage == "TEST" and artifact.get("evidence", {}).get("test_passed") is not True:
            raise WorkflowError("QA tests failed or are missing")
        if stage == "DEPLOY":
            if not artifact.get("evidence", {}).get("review_sha256") or not artifact.get("evidence", {}).get("pr_url"):
                raise WorkflowError("Independent review and PR required before deploy readiness")
        if stage in HUMAN_APPROVAL:
            decisions = [x for x in state["approvals"] if x["stage"] == stage and x["artifact_sha256"] == artifact["sha256"]]
            if not decisions or decisions[-1]["decision"] != "accept":
                raise WorkflowError("Explicit human acceptance of current artifact required")
        state["history"].append({"from": stage, "to": target, "kind": "advance", "at": utcnow()})
        state["stage"], state["status"] = target, "QUEUED"
        _atomic_json(self._state_path(item_id), state)
        self._event(item_id, {"event": "advance", "from": stage, "to": target})
        return state
