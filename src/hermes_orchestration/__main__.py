"""Minimal local CLI. Explicitly not an identity/security boundary."""
import argparse
import json
import sys
from pathlib import Path
from .core import LocalStore, WorkflowError, ROLES
from .model import invoke_role, ModelConfigurationError
from .skills import augment_role_instruction


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Hermes MVP controller (sandbox only)")
    p.add_argument("--root", default="workitems", help="Local work item directory")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--id", required=True)
    init.add_argument("--objective", required=True)
    for command in ("status", "run", "approve", "advance"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--id", required=True)
        if command == "run":
            cmd.add_argument("--dry-run", action="store_true", help="MOCK ONLY: not evidence")
        if command == "approve":
            cmd.add_argument("--actor", required=True, help="human:<name>; locally asserted, not authenticated")
            cmd.add_argument("--decision", required=True, choices=["accept", "reject"])
        if command == "advance":
            cmd.add_argument("--target", help="Explicit rework target (normally omitted)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = LocalStore(args.root)
    try:
        if args.command == "init":
            result = store.init(args.id, args.objective)
        elif args.command == "status":
            result = store.load(args.id)
        elif args.command == "approve":
            result = store.approve(args.id, actor=args.actor, decision=args.decision)
        elif args.command == "advance":
            result = store.advance(args.id, target=args.target)
        elif args.command == "run":
            state = store.load(args.id)
            stage = state["stage"]
            if stage not in {"PLAN", "DESIGN"}:
                raise WorkflowError("Day 1 runner supports PLAN and DESIGN only; later stages belong to Day 2")
            role = ROLES[stage]
            role_path = Path(__file__).resolve().parents[2] / "roles" / role / "SOUL.md"
            if not role_path.is_file():
                raise WorkflowError("Missing reviewed role profile: " + role)
            previous = (store.item_dir(args.id) / "intent.md").read_text(encoding="utf-8") if stage == "DESIGN" else ""
            instruction, versions = augment_role_instruction(
                role_path.read_text(encoding="utf-8"), stage, role
            )
            if args.dry_run:
                text, model, mode = "# MOCK ONLY: not real evidence\n\n" + state["objective"], "none", "mock"
            else:
                text, model = invoke_role(role_instruction=instruction,
                                          objective=state["objective"], input_text=previous)
                mode = "live"
            result = store.record(args.id, text, role=role, mode=mode, model=model,
                                  evidence={"skills": versions})
        else:
            raise WorkflowError("Unknown command")
        print(json.dumps({"id": result["work_item_id"], "stage": result["stage"],
                          "status": result["status"], "artifacts": result["artifacts"],
                          "approvals": result["approvals"]}, indent=2))
        return 0
    except (WorkflowError, ModelConfigurationError, OSError, ValueError, KeyError) as exc:
        print("Hermes MVP blocked: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
