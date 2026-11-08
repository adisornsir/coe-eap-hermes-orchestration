"""Deterministic Day 1 negative-gate tests with no network or credentials."""
import tempfile
import unittest
from pathlib import Path
from hermes_orchestration.core import LocalStore, WorkflowError
from hermes_orchestration.__main__ import main


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = LocalStore(self.tmp.name)
        self.store.init("demo-1", "Add a read-only health endpoint")

    def tearDown(self):
        self.tmp.cleanup()

    def test_id_sanitized(self):
        with self.assertRaises(WorkflowError):
            self.store.init("../evil", "bad")

    def test_no_stage_skip(self):
        with self.assertRaises(WorkflowError):
            self.store.advance("demo-1", target="DEPLOY")

    def test_no_advance_without_artifact(self):
        with self.assertRaises(WorkflowError):
            self.store.advance("demo-1")

    def test_mock_never_advances(self):
        self.store.record("demo-1", "# Mock", role="pm-ba", mode="mock")
        with self.assertRaises(WorkflowError):
            self.store.approve("demo-1", actor="human:owner", decision="accept")
        with self.assertRaises(WorkflowError):
            self.store.advance("demo-1")

    def test_role_separation(self):
        with self.assertRaises(WorkflowError):
            self.store.record("demo-1", "Test", role="dev", mode="live")

    def test_human_gate_and_artifact_hash(self):
        self.store.record("demo-1", "# Intent", role="pm-ba", mode="live", model="fake-local")
        with self.assertRaises(WorkflowError):
            self.store.advance("demo-1")
        self.store.approve("demo-1", actor="human:owner", decision="accept")
        result = self.store.advance("demo-1")
        self.assertEqual(result["stage"], "DESIGN")
        self.assertTrue((Path(self.tmp.name) / "demo-1" / "events.jsonl").exists())
        self.assertEqual(len(result["history"]), 1)

    def test_reject_blocks(self):
        self.store.record("demo-1", "# Intent", role="pm-ba", mode="live")
        self.store.approve("demo-1", actor="human:owner", decision="reject")
        with self.assertRaises(WorkflowError):
            self.store.advance("demo-1")

    def test_plan_design(self):
        self.store.record("demo-1", "# Intent", role="pm-ba", mode="live")
        self.store.approve("demo-1", actor="human:owner", decision="accept")
        self.store.advance("demo-1")
        self.store.record("demo-1", "# Spec", role="sa", mode="live")
        self.store.approve("demo-1", actor="human:architect", decision="accept")
        self.assertEqual(self.store.advance("demo-1")["stage"], "BUILD")

    def test_model_required_for_real_run(self):
        # CLI mock path is explicitly labelled and cannot pass human gate.
        code = main(["--root", self.tmp.name, "run", "--id", "demo-1", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertEqual(self.store.load("demo-1")["status"], "MOCK_ONLY")


if __name__ == "__main__":
    unittest.main()
