#!/usr/bin/env python3
"""Integration tests for paired evidence, exact binding and prior review pin."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import paired_pinned_review as tool

HERE = Path(__file__).resolve().parent
PIN = (HERE / 'paired-pinned.pin').read_text().strip()


def fixture(name):
    return json.loads((HERE / name).read_text())


class PairedPinnedReviewTests(unittest.TestCase):
    def setUp(self):
        self.sample = fixture('paired-pinned-evidence.json')
        self.policy = fixture('paired-pinned-policy.json')
        self.intended = fixture('paired-pinned-intended.json')
        self.client = copy.deepcopy(self.intended)

    def decide(self, **changes):
        values = dict(sample=self.sample, policy=self.policy,
                      intended=self.intended, client=self.client,
                      expected_pin=PIN, as_of=1792012453,
                      max_head_age=120, max_finalized_age=1200, future_skew=60)
        values.update(changes)
        return tool.review(**values)

    def test_real_historical_pair_and_exact_request(self):
        result = self.decide()
        self.assertTrue(result['accepted'])
        self.assertEqual(result['sampleSha256'], '003b451e06c2fd8a135c06278833fb9e6b4d825e77330bce9c16e06545fe3731')
        self.assertEqual(result['intendedDigest'], result['requestComparison']['items'][0]['client']['digest'])

    def test_stale_pair_rejects_even_with_matching_request(self):
        result = self.decide(as_of=1792013654)
        self.assertFalse(result['accepted'])
        self.assertFalse(result['pairedAccepted'])
        self.assertTrue(result['capturedRequestMatchesPinnedIntended'])

    def test_changed_evidence_rejects_intended_binding(self):
        sample = copy.deepcopy(self.sample)
        for provider in sample['providers']:
            for read in provider['reads']:
                if read['method'] == 'eth_getTransactionReceipt':
                    read['result']['cumulativeGasUsed'] = '0x1653c5d'
        result = self.decide(sample=sample)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['pairedAccepted'])
        self.assertFalse(result['intendedBindsExactSampleAndPolicy'])

    def test_changed_client_account_rejects(self):
        self.client['requests'][0]['request']['params'][0] = '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'
        result = self.decide()
        self.assertFalse(result['accepted'])
        self.assertTrue(result['pairedAccepted'])
        self.assertFalse(result['capturedRequestMatchesPinnedIntended'])

    def test_pin_mismatch_precedes_missing_client_or_evidence(self):
        root = HERE.parent.parent
        command = [sys.executable, '-B', str(HERE / 'paired_pinned_review.py'),
                   'missing-evidence.json', 'missing-policy.json',
                   'shared/payment-evidence/paired-pinned-intended.json', 'missing-client.json',
                   '--expect-pin', '0' * 64, '--as-of', '1792012453',
                   '--max-head-age', '120', '--max-finalized-age', '1200']
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['state'], 'pin_mismatch')


if __name__ == '__main__':
    unittest.main()
