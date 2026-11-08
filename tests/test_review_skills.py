import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from hermes_orchestration.core import LocalStore, WorkflowError
from hermes_orchestration.day2 import review

class ReviewSkillsIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = LocalStore(self.temp.name)
        self.store.init("review-case", "Inspect demo change")
        self.store.record("review-case", "# Intent", role="pm-ba", mode="live")
        self.store.approve("review-case", actor="human:owner", decision="accept")
        self.store.advance("review-case")
        self.store.record("review-case", "# Spec", role="sa", mode="live")
        self.store.approve("review-case", actor="human:owner", decision="accept")
        self.store.advance("review-case")
        self.store.record("review-case", "# Plan", role="dev", mode="live",
                          evidence={"commit_sha": "a" * 40})
        self.store.advance("review-case")
        self.store.record("review-case", "# QA", role="qa", mode="live",
                          evidence={"test_passed": True})
        self.store.advance("review-case")

    def tearDown(self):
        self.temp.cleanup()

    @patch("hermes_orchestration.day2.invoke_role")
    @patch("hermes_orchestration.day2.subprocess.run")
    def test_two_axis_skill_loaded_and_review_capped(self, run, invoke):
        run.return_value.returncode = 0
        run.return_value.stdout = "diff --git a/demo_app/health.py b/demo_app/health.py\n+return 200"
        invoke.return_value = ("## Standards\nNo findings\n## Spec\nMeets intent", "reviewer-model")
        repo = Path(__file__).resolve().parents[1]
        self.assertEqual(len(review(self.store, "review-case", repo=repo)), 64)
        meta_path = self.store.item_dir("review-case") / "review-meta.json"
        meta = json.loads(meta_path.read_text())
        self.assertEqual(meta["skills"][0]["id"], "two-axis-review")
        self.assertEqual(meta["attempts"], 1)
        self.assertIn("two-axis-review", invoke.call_args.kwargs["role_instruction"])
        review(self.store, "review-case", repo=repo)
        self.assertEqual(json.loads(meta_path.read_text())["attempts"], 2)
        with self.assertRaisesRegex(WorkflowError, "budget exhausted"):
            review(self.store, "review-case", repo=repo)
        self.assertEqual(invoke.call_count, 2)


if __name__ == "__main__":
    unittest.main()
