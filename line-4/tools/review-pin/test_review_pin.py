import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from review_pin import commitment, main, review, verify_pin, PREFIX
from typed_digest import TypedDataError, loads_bounded

ROOT = Path(__file__).parent
DEMO = json.loads((ROOT / 'zto-set.json').read_text())


def alter(value, operation):
    request = value['requests'][0]['request']
    data = json.loads(request['params'][1])
    operation(data)
    request['params'][1] = json.dumps(data)


class PinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin = commitment(DEMO)

    def setUp(self):
        self.changed = copy.deepcopy(DEMO)

    def test_historical_zto_and_pinned_fixture(self):
        result = review(DEMO, DEMO, self.pin)
        self.assertTrue(result['accepted'])
        self.assertEqual(self.pin, (ROOT / 'zto.pin').read_text().strip())
        self.assertEqual(result['comparison']['items'][0]['client']['digest'],
                         '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774')

    def test_substitution_of_both_inputs_rejected(self):
        alter(self.changed, lambda d: d['message'].update(minimumRaw='1'))
        result = review(self.changed, self.changed, self.pin)
        self.assertFalse(result['pinMatches'])
        self.assertFalse(result['accepted'])
        self.assertNotIn('comparison', result)

    def test_client_alteration_rejected_with_correct_pin(self):
        alter(self.changed, lambda d: d['message'].update(minimumRaw='1'))
        result = review(DEMO, self.changed, self.pin)
        self.assertTrue(result['pinMatches'])
        self.assertFalse(result['accepted'])

    def test_public_account_bound_separately(self):
        self.changed['requests'][0]['request']['params'][0] = '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'
        self.assertNotEqual(commitment(self.changed), self.pin)

    def test_label_membership_order_bound(self):
        self.changed['requests'][0]['reviewId'] = 'new-label'
        self.assertNotEqual(commitment(self.changed), self.pin)
        entry = copy.deepcopy(DEMO['requests'][0]); entry['reviewId'] = 'second'
        pair = {'requests': [DEMO['requests'][0], entry]}
        self.assertNotEqual(commitment(pair), self.pin)
        self.assertNotEqual(commitment(pair), commitment({'requests': list(reversed(pair['requests']))}))

    def test_transport_format_case_and_integer_equivalence(self):
        req = self.changed['requests'][0]['request']
        req.update(jsonrpc='2.0', id='ignored')
        req['params'][0] = '0x' + req['params'][0][2:].upper()
        alter(self.changed, lambda d: d['message'].update(minimumRaw=hex(int(d['message']['minimumRaw']))))
        self.assertEqual(commitment(self.changed), self.pin)
        self.assertTrue(review(DEMO, self.changed, self.pin)['accepted'])

    def test_unused_valid_type_not_signed_or_pinned(self):
        alter(self.changed, lambda d: d['types'].update(Unused=[]))
        self.assertEqual(commitment(self.changed), self.pin)

    def test_invalid_unused_type_still_rejected(self):
        alter(self.changed, lambda d: d['types'].update(Unused=[{'name': 'bad', 'type': 'uint7'}]))
        with self.assertRaises(TypedDataError):
            commitment(self.changed)

    def test_domain_and_field_order_change_pin(self):
        alter(self.changed, lambda d: d['domain'].update(chainId=2))
        self.assertNotEqual(commitment(self.changed), self.pin)
        self.changed = copy.deepcopy(DEMO)
        def reverse(d):
            d['types'][d['primaryType']].reverse()
        alter(self.changed, reverse)
        self.assertNotEqual(commitment(self.changed), self.pin)

    def test_dynamic_preimage_not_only_digest(self):
        # Deliberately fake equal trace words/digests to prove raw dynamic
        # preimages are independently part of the outer SHA-256 commitment.
        def fake(text):
            return {'primaryType': 'Message', 'digest': 'same', 'nodes': [
                {'path': '/message/body', 'type': 'string', 'kind': 'dynamic',
                 'word': 'same', 'preimage': text}]}
        with patch('review_pin.explain', return_value=fake('0x61')):
            a = commitment(DEMO)
        with patch('review_pin.explain', return_value=fake('0x62')):
            self.assertNotEqual(commitment(DEMO), a)

    def test_canonical_protocol_bytes(self):
        fake = {'primaryType': 'M', 'digest': 'digest', 'nodes': [
            {'path': '/message', 'type': 'M', 'kind': 'struct', 'word': 'word',
             'typeEncoding': 'M()', 'preimage': '0x'}]}
        expected = [{'reviewId': 'zto-receipt-review',
                     'account': DEMO['requests'][0]['request']['params'][0].lower(),
                     'primaryType': 'M', 'digest': 'digest', 'nodes': {'/message': {
                         'type': 'M', 'kind': 'struct', 'word': 'word',
                         'typeEncoding': 'M()', 'preimage': '0x'}}}]
        raw = json.dumps(expected, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('ascii')
        self.assertEqual(PREFIX, b'eip712-request-review-pin:v1\n')
        with patch('review_pin.explain', return_value=fake):
            self.assertEqual(commitment(DEMO), hashlib.sha256(PREFIX + raw).hexdigest())

    def test_bad_pin_syntax(self):
        for pin in ('', 'f'*63, 'g'*64, 'A'*64, '0x'+'f'*64, 'f'*64+'\n', None, True):
            with self.subTest(pin=pin), self.assertRaises(TypedDataError):
                verify_pin(DEMO, pin)

    def test_invalid_empty_duplicate_or_method(self):
        for value in ({'requests': []}, {'requests': DEMO['requests']*2}, {'extra': []}):
            with self.assertRaises(TypedDataError):
                commitment(value)
        self.changed['requests'][0]['request']['method'] = 'eth_sendTransaction'
        with self.assertRaises(TypedDataError):
            commitment(self.changed)

    def test_size_bound_and_immutable(self):
        before = copy.deepcopy(DEMO)
        commitment(DEMO)
        self.assertEqual(before, DEMO)
        with patch('review_pin.MAX_COMMITMENT_BYTES', 10), self.assertRaises(TypedDataError):
            commitment(DEMO)

    def test_strict_json(self):
        for raw in (b'{"requests":[],"requests":[]}', b'{"requests":NaN}', b'{"requests":1.0}', b' '*65537):
            with self.assertRaises(ValueError):
                loads_bounded(raw)

    def test_cli_pin_accept_missing(self):
        fixture = str(ROOT / 'zto-set.json')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(['pin', fixture]), 0)
        self.assertEqual(out.getvalue(), self.pin+'\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['check', fixture, fixture, '--expect', self.pin]), 0)
            self.assertEqual(main(['check', fixture, str(ROOT / 'missing-set.json'), '--expect', self.pin]), 1)

    def test_wrong_pin_never_opens_client(self):
        with patch('review_pin.load_workspace_json', return_value=DEMO) as read:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['check', 'intended.json', 'not-opened.json', '--expect', 'f'*64]), 1)
            read.assert_called_once_with('intended.json')

    def test_summary_cannot_bypass_parent_report_limit(self):
        with patch('request_set_check.MAX_REPORT_BYTES', 1), self.assertRaises(TypedDataError):
            review(DEMO, DEMO, self.pin)

    def test_cli_outside_hidden_and_malformed_pin(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['pin', '../outside']), 2)
            self.assertEqual(main(['pin', '.hidden']), 2)
            self.assertEqual(main(['check', str(ROOT / 'zto-set.json'), 'unused', '--expect', 'bad']), 2)


if __name__ == '__main__':
    unittest.main()
