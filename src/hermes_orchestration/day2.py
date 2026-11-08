"""Day 2 evidence commands; intentionally no autonomous git merge or deployment."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from .core import LocalStore, WorkflowError
from .model import invoke_role, ModelConfigurationError
from .skills import augment_role_instruction, load_approved

PR_PATTERN = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+$")
SHA_PATTERN = re.compile(r"^[a-f0-9]{40}$")


def _require_stage(store: LocalStore, item_id: str, stage: str) -> dict:
    state = store.load(item_id)
    if state["stage"] != stage:
        raise WorkflowError(f"Expected {stage}, got {state['stage']}")
    return state


def build(store: LocalStore, item_id: str, *, plan: str, commit_sha: str) -> dict:
    """Record an existing code commit + accepted implementation plan, not generate code."""
    _require_stage(store, item_id, "BUILD")
    if not SHA_PATTERN.fullmatch(commit_sha):
        raise WorkflowError("A real full git commit SHA is required")
    # Build remains manual in the MVP: these recipes are recommended and pinned,
    # but are NOT claimed to have executed automatically.
    suggested = [s.provenance for s in load_approved("BUILD", "dev")]
    return store.record(item_id, plan, role="dev", mode="live",
                        evidence={"commit_sha": commit_sha,
                                  "source": "external_git_commit_not_verified",
                                  "recommended_skills": suggested})


def qa_tests(store: LocalStore, item_id: str, *, repo: Path, timeout: int = 120) -> dict:
    """Execute real local Python tests; never let a model supply the pass boolean."""
    _require_stage(store, item_id, "TEST")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo / "src")
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    try:
        result = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=timeout, check=False)
        passed, output = result.returncode == 0, (result.stdout + "\n" + result.stderr)[-16000:]
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        passed, output, exit_code = False, "Test command timed out", 124
    report = "# QA test report\n\nCommand: `python -m unittest discover -s tests -v`\n\nResult: " + ("PASS" if passed else "FAIL") + f" (exit {exit_code})\n\n```text\n{output}\n```\n"
    return store.record(item_id, report, role="qa", mode="live", evidence={"test_passed": passed, "exit_code": exit_code, "source": "subprocess"})


def review(store: LocalStore, item_id: str, *, repo: Path, base: str = "main") -> str:
    """Read-only independent AI report; never edits or approves source."""
    state = _require_stage(store, item_id, "DEPLOY")
    review_meta = store.item_dir(item_id) / "review-meta.json"
    previous = json.loads(review_meta.read_text(encoding="utf-8")) if review_meta.is_file() else {}
    attempts = int(previous.get("attempts", 0))
    if attempts >= 2:
        raise WorkflowError("Review budget exhausted: initial review + one re-review only")
    if not re.fullmatch(r"[A-Za-z0-9_./-]{1,100}", base) or base.startswith("-"):
        raise WorkflowError("Unsafe base ref")
    cmd = ["git", "diff", f"{base}...HEAD", "--", "src", "tests", "demo_app"]
    result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=15, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise WorkflowError("Cannot review an empty or invalid git diff")
    if len(result.stdout) > 48000:
        raise WorkflowError("Diff too large for MVP review; require human review")
    profile = (repo / "roles/reviewer/SOUL.md").read_text(encoding="utf-8")
    spec = (store.item_dir(item_id) / "spec.md").read_text(encoding="utf-8")
    instruction, selected_skills = augment_role_instruction(profile, "DEPLOY", "reviewer")
    instruction += "\nOutput sections ## Standards and ## Spec. Identify blockers explicitly."
    report, model = invoke_role(role_instruction=instruction, objective=state["objective"], input_text="SPEC:\n" + spec + "\nDIFF:\n" + result.stdout)
    if "## Standards" not in report or "## Spec" not in report:
        raise WorkflowError("Reviewer omitted required separate Standards/Spec sections")
    path = store.item_dir(item_id) / "review-report.md"
    path.write_text(report, encoding="utf-8")
    digest = hashlib.sha256(report.encode()).hexdigest()
    review_meta.write_text(json.dumps({"sha256": digest, "model": model,
                                       "source": "model_only", "base": base,
                                       "attempts": attempts + 1,
                                       "skills": selected_skills}), encoding="utf-8")
    return digest


def prepare_release(store: LocalStore, item_id: str, *, pr_url: str) -> dict:
    """DEV-only release *preparation*. Never deploy or merge from this function."""
    state = _require_stage(store, item_id, "DEPLOY")
    if not PR_PATTERN.fullmatch(pr_url):
        raise WorkflowError("A GitHub PR URL is required")
    qa = state["artifacts"].get("TEST", {})
    if qa.get("evidence", {}).get("test_passed") is not True:
        raise WorkflowError("Independent real QA tests must pass")
    folder = store.item_dir(item_id)
    try:
        report = (folder / "review-report.md").read_text(encoding="utf-8")
        meta = json.loads((folder / "review-meta.json").read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError("Independent Reviewer report missing") from exc
    if hashlib.sha256(report.encode()).hexdigest() != meta.get("sha256"):
        raise WorkflowError("Reviewer report changed after review")
    if "## Standards" not in report or "## Spec" not in report:
        raise WorkflowError("Two-axis review report is incomplete")
    # Reviewer findings need human judgment. We do not auto-approve even when clear.
    text = "# DEV release preparation (NOT DEPLOYED)\n\nPR: " + pr_url + "\nQA: passed\nReviewer: " + meta["sha256"] + "\nProduction: forbidden\nRollback: revert PR/commit after human review\n"
    return store.record(item_id, text, role="devops-sre", mode="live", evidence={"pr_url": pr_url, "review_sha256": meta["sha256"], "review_pending_human": True})


def maintain(store: LocalStore, item_id: str, *, observations: str) -> dict:
    _require_stage(store, item_id, "MAINTAIN")
    if not observations.strip():
        raise WorkflowError("Observations are required")
    return store.record(item_id, "# Maintenance observations (manual)\n\n" + observations, role="devops-sre", mode="live", evidence={"source": "human_notes", "auto_monitoring": False})


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Hermes Day 2 evidence tools, local sandbox only")
    p.add_argument("--root", default="workitems")
    p.add_argument("--repo", type=Path, default=Path.cwd())
    s = p.add_subparsers(dest="action", required=True)
    for name in ("build", "test", "review", "release", "maintain"):
        sp = s.add_parser(name)
        sp.add_argument("--id", required=True)
        if name == "build":
            sp.add_argument("--plan-file", type=Path, required=True)
            sp.add_argument("--commit-sha", required=True)
        if name == "review":
            sp.add_argument("--base", default="main")
        if name == "release":
            sp.add_argument("--pr-url", required=True)
        if name == "maintain":
            sp.add_argument("--observations", required=True)
    args = p.parse_args(argv)
    store = LocalStore(args.root)
    try:
        if args.action == "build":
            state = build(store, args.id, plan=args.plan_file.read_text(encoding="utf-8"), commit_sha=args.commit_sha)
        elif args.action == "test":
            state = qa_tests(store, args.id, repo=args.repo.resolve())
        elif args.action == "review":
            print("Reviewer SHA-256: " + review(store, args.id, repo=args.repo.resolve(), base=args.base))
            return 0
        elif args.action == "release":
            state = prepare_release(store, args.id, pr_url=args.pr_url)
        else:
            state = maintain(store, args.id, observations=args.observations)
        print(json.dumps({"id": state["work_item_id"], "stage": state["stage"], "status": state["status"]}))
        return 0
    except (WorkflowError, ModelConfigurationError, FileNotFoundError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("Day 2 BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
