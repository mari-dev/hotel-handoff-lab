import concurrent.futures
from pathlib import Path
import tempfile
import unittest
from invoice_store import Store, Conflict

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name)/'test.db')
        self.key = self.store.create('Rossi', '', 'In person', '', 'A')

    def test_two_operators_cannot_claim_same_request(self):
        def claim(actor):
            try:
                self.store.act(self.key, 'claim', actor)
                return True
            except Conflict:
                return False
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            self.assertEqual(sum(pool.map(claim, ['A', 'B'])), 1)

    def test_only_owner_can_release(self):
        self.store.act(self.key, 'claim', 'A')
        with self.assertRaises(Conflict):
            self.store.act(self.key, 'release', 'B')

    def test_direct_simulated_completion_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.act(self.key,'demo_email','A')

    def test_details_can_be_added_before_pdf(self):
        self.store.details(self.key,'12-15 Sept','Address missing','A')
        self.assertEqual(self.store.list()[0]['stay'],'12-15 Sept')

    def test_same_name_can_represent_different_stays(self):
        other=self.store.create('Rossi', 'other dates', 'In person', '', 'A', True)
        self.assertNotEqual(other, self.key)
        self.assertEqual(len(self.store.list()), 2)
