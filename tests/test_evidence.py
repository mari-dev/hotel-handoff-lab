import unittest
from handoff import validate_claim

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.sources = {"note-1": "Zimmer 12: Rechnung angefragt. Firmenadresse fehlt."}
        self.claim = {"text": "Billing address needs confirmation", "evidence": [
            {"source_id": "note-1", "quote": "Firmenadresse fehlt."}]}

    def test_exact_quote_still_requires_human_review(self):
        self.assertEqual(validate_claim(self.claim, self.sources)["status"], "needs_human_review")

    def test_fabricated_quote_is_rejected(self):
        self.claim["evidence"][0]["quote"] = "Rechnung erledigt."
        with self.assertRaises(ValueError):
            validate_claim(self.claim, self.sources)

    def test_unknown_source_is_rejected(self):
        self.claim["evidence"][0]["source_id"] = "invented"
        with self.assertRaises(ValueError):
            validate_claim(self.claim, self.sources)

    def test_empty_evidence_is_rejected(self):
        self.claim["evidence"] = []
        with self.assertRaises(ValueError):
            validate_claim(self.claim, self.sources)

    def test_blank_quote_is_rejected(self):
        self.claim["evidence"][0]["quote"] = " "
        with self.assertRaises(ValueError):
            validate_claim(self.claim, self.sources)

    def test_untrusted_status_cannot_mark_work_complete(self):
        self.claim["status"] = "completed"
        self.assertEqual(validate_claim(self.claim, self.sources)["status"], "needs_human_review")

    def test_malformed_citation_is_rejected(self):
        self.claim["evidence"] = [None]
        with self.assertRaises(ValueError):
            validate_claim(self.claim, self.sources)
