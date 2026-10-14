"""Contract change regressions; in-memory inputs and named workspace fixtures only."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import types
import unittest
from unittest.mock import patch

SCRIPT = Path('line-2/tools/contract-change/review.py')
review = types.ModuleType('contract_change_tests')
review.__file__ = str(SCRIPT.absolute())
exec(compile(SCRIPT.read_bytes(), str(SCRIPT), 'exec'), review.__dict__)
bounded, locations, engine, rules = review.dependencies()


def encoded(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


class MemoryReader:
    def __init__(self, inputs):
        self.inputs = inputs
        self.calls = []

    def read_bytes(self, name, limit=1_000_000):
        self.calls.append(name)
        value = self.inputs[name]
        if len(value) > limit:
            raise ValueError('input exceeds byte budget')
        return value


class ChangeTests(unittest.TestCase):
    def run_case(self, old, new, documents):
        reader = MemoryReader({'old.json': encoded(old), 'new.json': encoded(new),
                               **{k: encoded(v) for k, v in documents.items()}})
        return review.review(reader, locations, engine, rules,
                             'old.json', 'new.json', list(documents))

    def test_all_four_transitions_and_order(self):
        r = self.run_case({'type': 'integer', 'minimum': 2},
                          {'type': 'integer', 'maximum': 3},
                          {'keep': 2, 'reject': 4, 'accept': 1, 'bad': 'x'})
        self.assertFalse(r['valid'])
        self.assertFalse(r['no_observed_regressions'])
        self.assertEqual([d['transition'] for d in r['documents']],
                         ['still_accepted', 'newly_rejected', 'newly_accepted', 'still_rejected'])
        self.assertEqual(r['summary'], {'checked': 4, 'still_accepted': 1,
                         'newly_rejected': 1, 'newly_accepted': 1, 'still_rejected': 1})

    def test_no_regression_does_not_mean_valid(self):
        r = self.run_case({'type': 'integer'}, {'type': 'integer'}, {'bad': False})
        self.assertTrue(r['no_observed_regressions'])
        self.assertFalse(r['valid'])

    def test_newly_accepted_is_valid(self):
        r = self.run_case({'type': 'integer', 'minimum': 3}, {'type': 'integer'}, {'d': 1})
        self.assertTrue(r['valid'])
        self.assertEqual(r['summary']['newly_accepted'], 1)

    def test_real_record_contract_tightening(self):
        r = review.review(bounded, locations, engine, rules,
                          'line-2/tools/json-contract/record.contract.json',
                          'line-2/tools/ordered-deliverables/record.strict.contract.json',
                          ['dist/line-2/26.json', 'dist/line-2/27.json'])
        self.assertTrue(r['valid'])
        self.assertEqual(r['summary']['still_accepted'], 2)

    def test_real_saved_zto_policy_rejection_and_exact_spans(self):
        old = 'shared/payment-evidence/policy.contract.json'
        new = 'line-2/tools/contract-change/proposed-policy.contract.json'
        doc = 'shared/payment-evidence/example.policy.json'
        r = review.review(bounded, locations, engine, rules, old, new, [doc])
        self.assertEqual(r['summary']['newly_rejected'], 1)
        error = r['documents'][0]['after']['errors'][0]
        self.assertEqual(error['path'], '/confirmations')
        self.assertEqual(error['contract_path'], '/properties/confirmations/minimum')
        for name, field, token in [(doc, 'document_source', b'12'),
                                   (new, 'contract_source', b'13')]:
            span = error[field]['value']
            data = bounded.read_bytes(name)
            self.assertEqual(data[span['start']['byte_offset']:span['end']['byte_offset']], token)
        self.assertEqual(r['contracts']['after']['sha256'],
                         hashlib.sha256(bounded.read_bytes(new)).hexdigest())

    def test_missing_required_field_has_parent_anchor(self):
        old = {'type': 'object'}
        new = {'type': 'object', 'required': ['x'], 'properties': {'x': {'type': 'null'}}}
        r = self.run_case(old, new, {'d': {}})
        error = r['documents'][0]['after']['errors'][0]
        self.assertFalse(error['document_source']['present'])
        self.assertNotIn('value', error['document_source'])
        self.assertEqual(error['document_source']['anchor']['path'], '')

    def test_unicode_crlf_and_escaped_spelling_kept(self):
        key = 'é/~'
        reader = MemoryReader({'old': b'{"type":"object"}',
            'new': encoded({'type': 'object', 'properties': {key: {'type': 'integer'}}}),
            'd': '{\r\n "é/~": "\\u006e\\u006f"\r\n}'.encode('utf-8')})
        r = review.review(reader, locations, engine, rules, 'old', 'new', ['d'])
        error = r['documents'][0]['after']['errors'][0]
        self.assertEqual(error['path'], '/é~1~0')
        span = error['document_source']['value']
        self.assertEqual(reader.inputs['d'][span['start']['byte_offset']:span['end']['byte_offset']],
                         b'"\\u006e\\u006f"')
        self.assertEqual(span['start']['line'], 2)

    def test_captured_once_even_when_contract_is_document(self):
        reader = MemoryReader({'c': b'{"type":"object"}'})
        r = review.review(reader, locations, engine, rules, 'c', 'c', ['c'])
        self.assertTrue(r['valid'])
        self.assertEqual(reader.calls, ['c'])
        self.assertEqual(r['captured_bytes'], len(reader.inputs['c']))

    def test_contracts_checked_before_documents(self):
        for bad in ({'type': 'integer', 'minimun': 2}, {'type': 'object', 'required': ['x']}):
            reader = MemoryReader({'old': b'{"type":"integer"}', 'new': encoded(bad)})
            with self.assertRaises(ValueError):
                review.review(reader, locations, engine, rules, 'old', 'new', ['unread'])
            self.assertEqual(reader.calls, ['old', 'new'])

    def test_empty_duplicate_and_large_corpus_refused_before_read(self):
        for names in ([], ['d', 'd'], [str(i) for i in range(33)]):
            reader = MemoryReader({})
            with self.assertRaises(ValueError):
                review.review(reader, locations, engine, rules, 'old', 'new', names)
            self.assertEqual(reader.calls, [])

    def test_strict_inputs_fail_closed(self):
        for data in (b'{', b'{"x":1,"x":2}', b'NaN', b'1e9999', b'"\xff"'):
            reader = MemoryReader({'old': b'{"type":"object"}',
                                   'new': b'{"type":"object"}', 'd': data})
            with self.assertRaises(ValueError):
                review.review(reader, locations, engine, rules, 'old', 'new', ['d'])

    def test_total_input_budget(self):
        reader = MemoryReader({'c': b'{"type":"object"}',
            **{str(i): b' ' * 999_998 + b'{}' for i in range(4)}})
        with self.assertRaises(ValueError):
            review.review(reader, locations, engine, rules, 'c', 'c', [str(i) for i in range(4)])

    def test_output_budget_never_truncates_success(self):
        result = {'valid': True, 'large': ['é' * 1000] * 30}
        with self.assertRaises(ValueError):
            review.encode_report(result)
        small = {'valid': True}
        exact = len(json.dumps(small, indent=2).encode()) + 1
        self.assertEqual(json.loads(review.encode_report(small, exact)), small)
        with self.assertRaises(ValueError):
            review.encode_report(small, exact - 1)

    def test_cli_codes_and_unsafe_paths(self):
        old = 'shared/payment-evidence/policy.contract.json'
        new = 'line-2/tools/contract-change/proposed-policy.contract.json'
        doc = 'shared/payment-evidence/example.policy.json'
        for args, expected in [([old, old, doc], 0), ([old, new, doc], 1),
                               ([old, new, '/outside.json'], 2),
                               ([old, new, '../outside.json'], 2),
                               ([old, new, '.hidden.json'], 2),
                               ([old, new, doc, doc], 2)]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = review.main(args)
            self.assertEqual(code, expected)
            result = json.loads(out.getvalue())
            self.assertLess(len(out.getvalue().encode()), 100_001)
            if expected == 2:
                self.assertFalse(result['valid'])
                self.assertNotIn('documents', result)

    def test_cli_output_overflow_returns_only_error(self):
        old = 'shared/payment-evidence/policy.contract.json'
        with patch.object(review, 'encode_report', side_effect=ValueError('output limit')):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = review.main([old, old, 'shared/payment-evidence/example.policy.json'])
        self.assertEqual(code, 2)
        self.assertNotIn('documents', json.loads(out.getvalue()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
