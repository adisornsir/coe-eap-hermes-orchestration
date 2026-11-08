import json
import tempfile
import unittest
from hermes_orchestration.core import LocalStore, WorkflowError
from hermes_orchestration.day2 import build, prepare_release, maintain

class Day2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = LocalStore(self.tmp.name)
        self.store.init('case1', 'health check')
        self.store.record('case1', '# Intent', role='pm-ba', mode='live')
        self.store.approve('case1', actor='human:owner', decision='accept')
        self.store.advance('case1')
        self.store.record('case1', '# Spec', role='sa', mode='live')
        self.store.approve('case1', actor='human:owner', decision='accept')
        self.store.advance('case1')
    def tearDown(self):
        self.tmp.cleanup()

    def test_build_requires_commit(self):
        with self.assertRaises(WorkflowError):
            build(self.store, 'case1', plan='plan', commit_sha='fake')
        with self.assertRaises(WorkflowError):
            self.store.advance('case1')

    def test_test_stage_fails_closed(self):
        self.store.record('case1', '# Plan', role='dev', mode='live', evidence={'commit_sha': 'a'*40})
        self.store.advance('case1')
        self.store.record('case1', '# fail', role='qa', mode='live', evidence={'test_passed': False})
        with self.assertRaises(WorkflowError):
            self.store.advance('case1')
        self.assertEqual(self.store.advance('case1', target='BUILD')['stage'], 'BUILD')

    def test_release_requires_independent_report_and_human_gate(self):
        self.store.record('case1', '# Plan', role='dev', mode='live', evidence={'commit_sha': 'a'*40})
        self.store.advance('case1')
        self.store.record('case1', '# QA', role='qa', mode='live', evidence={'test_passed': True})
        self.store.advance('case1')
        with self.assertRaises(WorkflowError):
            prepare_release(self.store, 'case1', pr_url='https://github.com/x/y/pull/10')
        folder=self.store.item_dir('case1')
        (folder/'review-report.md').write_text('## Standards\nNone\n## Spec\nNone')
        import hashlib
        digest=hashlib.sha256((folder/'review-report.md').read_bytes()).hexdigest()
        (folder/'review-meta.json').write_text(json.dumps({'sha256': digest}))
        prepare_release(self.store, 'case1', pr_url='https://github.com/x/y/pull/10')
        with self.assertRaises(WorkflowError):
            self.store.advance('case1')
        self.store.approve('case1', actor='human:owner', decision='accept')
        self.assertEqual(self.store.advance('case1')['stage'], 'MAINTAIN')
        maintain(self.store, 'case1', observations='No incidents in manual demo')
        self.assertEqual(self.store.advance('case1', target='PLAN')['stage'], 'PLAN')

if __name__=='__main__':
    unittest.main()
