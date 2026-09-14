import unittest
from pydantic import ValidationError
from invoice_intake import GroundedProposal, _validation_context


class GroundedOutputTests(unittest.TestCase):
    def test_known_guest_cannot_be_omitted(self):
        with self.assertRaisesRegex(ValidationError, 'literal guest name'):
            GroundedProposal(**{**self.data, 'guest': ''})

    def setUp(self):
        self.message = 'Anna Keller requests an invoice. Address will follow.'
        self.calls = [{'name': 'read_request_message'},
                      {'name': 'find_existing_requests', 'guest': 'Anna Keller'}]
        self.token = _validation_context.set((self.message, self.calls))
        self.addCleanup(_validation_context.reset, self.token)
        self.data = dict(invoice_requested=True, request_quote='requests an invoice',
                         guest='Anna Keller', stay='', company='', address='')

    def test_empty_optional_fields_remain_null_in_public_proposal(self):
        p = GroundedProposal(**self.data).as_proposal()
        self.assertIsNone(p['address'])
        self.assertIsNone(p['stay'])
        self.assertEqual(p['guest'], {'value':'Anna Keller', 'quote':'Anna Keller'})

    def test_fabrication_is_rejected_inside_structured_output(self):
        with self.assertRaisesRegex(ValidationError, 'address'):
            GroundedProposal(**{**self.data, 'address':'Invented Street 1'})

    def test_wrong_guest_lookup_cannot_satisfy_tool_requirement(self):
        self.calls[1]['guest'] = 'Another Guest'
        with self.assertRaisesRegex(ValidationError, 'find_existing_requests'):
            GroundedProposal(**self.data)

    def test_no_source_read_is_rejected(self):
        self.calls.pop(0)
        with self.assertRaisesRegex(ValidationError, 'read_request_message'):
            GroundedProposal(**self.data)

    def test_literal_unrelated_quote_does_not_establish_invoice_demand(self):
        self.message='Breakfast starts at 7.'
        token=_validation_context.set((self.message,self.calls))
        try:
            with self.assertRaisesRegex(ValidationError, 'explicit invoice request'):
                GroundedProposal(**{**self.data,'request_quote':self.message,'guest':''})
        finally:
            _validation_context.reset(token)

    def test_negated_invoice_quote_is_rejected(self):
        token=_validation_context.set(('No invoice is requested.',self.calls))
        try:
            with self.assertRaisesRegex(ValidationError, 'explicit invoice request'):
                GroundedProposal(**{**self.data,'request_quote':'No invoice is requested.','guest':''})
        finally:
            _validation_context.reset(token)

    def test_no_context_is_rejected(self):
        token = _validation_context.set(None)
        try:
            with self.assertRaisesRegex(ValidationError, 'context'):
                GroundedProposal(**self.data)
        finally:
            _validation_context.reset(token)
