import json
from pathlib import Path
import unittest
from workflow import build_handoff
from demo import render

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parents[1]/"fixtures/shift.json").read_text())

    def test_invoice_missing_details_and_conflict_are_preserved(self):
        tasks = build_handoff(self.data["observations"], self.data["sources"])
        attention = {t["task_key"]: t["attention"] for t in tasks}
        self.assertEqual(attention, {"stay-12/invoice": "information_needed",
                         "stay-18/heating": "conflicting_reports", "stay-24/taxi": "open_work"})
        self.assertTrue(all(t["status"] == "needs_human_review" for t in tasks))

    def test_no_request_is_not_an_invoice_task(self):
        self.assertEqual(build_handoff([], {"n1": "Guest checked in."}), [])

    def test_unknown_state_fails(self):
        self.data["observations"][0]["state"] = "invented"
        with self.assertRaises(ValueError):
            build_handoff(self.data["observations"], self.data["sources"])

    def test_report_escapes_untrusted_text(self):
        tasks = build_handoff(self.data["observations"], self.data["sources"])
        tasks[0]["task_key"] = "<script>alert(1)</script>"
        rendered = render({"mode": "test", "tasks": tasks})
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_replay_is_visibly_distinguished_from_live_execution(self):
        replay = render({"mode": "Fixture replay — no AI model used", "tasks": []})
        live = render({"mode": "Live Strands extraction", "tasks": []})
        self.assertIn("Fixture replay", replay)
        self.assertNotIn("Live Strands extraction", replay)
        self.assertIn("Live Strands extraction", live)
        self.assertNotIn("Fixture replay", live)
