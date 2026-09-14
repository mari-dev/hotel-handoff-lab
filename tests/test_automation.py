import tempfile
from pathlib import Path
import unittest
from invoice_store import Store
from evidence_monitor import Monitor
from sample_documents import simple_pdf,sent_email
from invoice_intake import validate_proposal

class AutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'db.sqlite')
        self.key=self.store.create('Anna Keller','September 12–15','Booking','','A',True)
        self.monitor=Monitor(self.store,self.root/'inbox')
        self.pdf=simple_pdf('Anna Keller','September 12–15')
    def pdf_file(self): (self.root/'inbox/pdfs/invoice.pdf').write_bytes(self.pdf)
    def email_file(self,pdf=None): (self.root/'inbox/sent/sent.eml').write_bytes(sent_email(pdf or self.pdf))
    def status(self): return self.store.list()[0]['status']
    def test_actual_pdf_then_email_closes_once(self):
        self.pdf_file();self.monitor.scan();self.assertEqual(self.status(),'prepared')
        self.email_file();self.monitor.scan();self.assertEqual(self.status(),'sent')
        events=len(self.store.list()[0]['events'])
        self.monitor.scan();self.assertEqual(len(self.store.list()[0]['events']),events)
    def test_email_before_pdf_reconciles_later(self):
        self.email_file();self.monitor.scan();self.assertEqual(self.status(),'working')
        self.pdf_file();self.monitor.scan();self.assertEqual(self.status(),'sent')
    def test_same_name_different_stay_does_not_match(self):
        self.pdf=simple_pdf('Anna Keller','other dates');self.pdf_file();self.monitor.scan()
        self.assertEqual(self.status(),'working')
        self.assertEqual(self.monitor.records()[0]['state'],'pending')
    def test_ambiguous_requests_do_not_auto_match(self):
        self.store.create('Anna Keller','September 12–15','In person','','B')
        self.pdf_file();self.monitor.scan()
        self.assertFalse(any(r['status']=='prepared' for r in self.store.list()))
    def test_different_attachment_does_not_mark_sent(self):
        self.pdf_file();self.email_file(simple_pdf('Different guest','other dates'));self.monitor.scan()
        self.assertEqual(self.status(),'prepared')
    def test_bad_pdf_requires_review(self):
        self.pdf=b'not a PDF';self.pdf_file();self.monitor.scan()
        self.assertEqual(self.status(),'working')
        self.assertEqual(self.monitor.records()[0]['state'],'review')
    def test_fabricated_model_field_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_proposal({'invoice_requested':False,'guest':{'value':'Someone','quote':'Anna'}},'Anna')
    def test_missing_invoice_demand_is_not_created(self):
        self.assertFalse(validate_proposal({'invoice_requested':False},'Checking in tomorrow')['invoice_requested'])
