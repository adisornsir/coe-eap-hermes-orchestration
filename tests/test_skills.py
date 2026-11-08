"""Reviewed first-party skills must be loaded only for approved role/stage."""
import tempfile
import unittest
from pathlib import Path

from hermes_orchestration.core import WorkflowError
from hermes_orchestration.skills import load_approved, augment_role_instruction


class SkillTests(unittest.TestCase):
    def test_plan_and_design_resolve(self):
        plan = load_approved("PLAN", "pm-ba")
        self.assertEqual([s.id for s in plan], ["requirements-writing"])
        design = load_approved("DESIGN", "sa")
        self.assertEqual([s.id for s in design],
                         ["requirements-writing", "engineering-constraints"])
        self.assertTrue(all(len(s.sha256) == 64 for s in design))

    def test_build_and_review_separated(self):
        self.assertEqual([s.id for s in load_approved("BUILD", "dev")],
                         ["implementation-step", "engineering-constraints"])
        self.assertEqual([s.id for s in load_approved("DEPLOY", "reviewer")],
                         ["two-axis-review"])

    def test_wrong_role_rejected(self):
        with self.assertRaises(WorkflowError):
            load_approved("PLAN", "dev")
        with self.assertRaises(WorkflowError):
            load_approved("DEPLOY", "dev")
        with self.assertRaises(WorkflowError):
            load_approved("UNKNOWN", "sa")

    def test_instruction_has_versioned_evidence(self):
        message, versions = augment_role_instruction("SA profile", "DESIGN", "sa")
        self.assertIn("engineering-constraints", message)
        self.assertIn("never authorization", message)
        self.assertEqual(len(versions), 2)
        self.assertTrue(all(x["source"] == "reviewed-first-party-local" for x in versions))

    def test_reject_unreviewed_corrupted_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "skills" / "requirements-writing"
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text("---\nname: something-else\ndescription: bad\n---\nAction")
            with self.assertRaises(WorkflowError):
                load_approved("PLAN", "pm-ba", root=root)


if __name__ == "__main__":
    unittest.main()
