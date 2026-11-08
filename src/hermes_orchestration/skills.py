"""Small read-only skills resolver for *reviewed local* Hermes skills only.

Skills guide model behavior. They NEVER grant tools, approve work, change policies,
or authorize a workflow transition. No remote URLs, scripts, or auto-install.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .core import ROLES, WorkflowError

# Explicit allowed stage + role pairings. The independent Reviewer consults a
# skill during DEPLOY but cannot perform the DevOps/SRE stage transition.
APPROVED = {
    ("PLAN", "pm-ba"): ("requirements-writing",),
    ("DESIGN", "sa"): ("requirements-writing", "engineering-constraints"),
    ("BUILD", "dev"): ("implementation-step", "engineering-constraints"),
    ("DEPLOY", "reviewer"): ("two-axis-review",),
}


@dataclass(frozen=True)
class Skill:
    id: str
    description: str
    sha256: str
    instructions: str

    @property
    def provenance(self) -> dict:
        return {"id": self.id, "sha256": self.sha256, "source": "reviewed-first-party-local"}


def load_approved(stage: str, role: str, *, root: Path | None = None) -> tuple[Skill, ...]:
    if stage not in ROLES:
        raise WorkflowError(f"Unknown stage: {stage}")
    if role != ROLES[stage] and (stage, role) != ("DEPLOY", "reviewer"):
        raise WorkflowError(f"Role {role} is not allowed to use stage {stage} skills")
    # Reject unknown skill mappings rather than scanning a directory.
    names = APPROVED.get((stage, role), ())
    root = (root or Path(__file__).resolve().parents[2]).resolve()
    out = []
    for name in names:
        path = root / "skills" / name / "SKILL.md"
        if not path.is_file() or path.is_symlink():
            raise WorkflowError(f"Missing or disallowed reviewed skill: {name}")
        data = path.read_bytes()
        if len(data) > 8192:
            raise WorkflowError(f"Skill exceeds review size limit: {name}")
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WorkflowError(f"Skill must be UTF-8: {name}") from exc
        lines = content.splitlines()
        if len(lines) < 5 or lines[0] != "---":
            raise WorkflowError(f"Missing skill frontmatter: {name}")
        try:
            close = lines.index("---", 1)
        except ValueError as exc:
            raise WorkflowError(f"Unterminated skill frontmatter: {name}") from exc
        fields = {}
        for line in lines[1:close]:
            if ":" not in line:
                raise WorkflowError(f"Invalid skill metadata: {name}")
            k, v = line.split(":", 1)
            k = k.strip()
            if k not in {"name", "description"} or k in fields:
                raise WorkflowError(f"Unexpected skill metadata: {name}")
            fields[k] = v.strip().strip('"')
        if fields.get("name") != name or not fields.get("description"):
            raise WorkflowError(f"Skill name/description mismatch: {name}")
        instructions = "\n".join(lines[close + 1:]).strip()
        if not instructions:
            raise WorkflowError(f"Empty skill instructions: {name}")
        out.append(Skill(name, fields["description"], hashlib.sha256(data).hexdigest(), instructions))
    return tuple(out)


def augment_role_instruction(instruction: str, stage: str, role: str, *, root: Path | None = None) -> tuple[str, list[dict]]:
    skills = load_approved(stage, role, root=root)
    if not skills:
        return instruction, []
    sections = [instruction, "\n## Versioned project procedures (guidance, never authorization)"]
    for skill in skills:
        sections.append(f"### {skill.id} [sha256:{skill.sha256}]\n{skill.instructions}")
    return "\n\n".join(sections), [skill.provenance for skill in skills]
