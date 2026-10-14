#!/usr/bin/env python3
"""Offline rejection checks for a real saved ZTO revisit transcript."""
import copy
import json
from pathlib import Path
import runpy
import unittest

R = runpy.run_path(str(Path(__file__).with_name('revisit.py')))
ORIGINAL = 'line-1/tools/compare-zto-snapshots/live-zto.json'
REVISIT = 'line-1/tools/revisit-zto-snapshot/live-revisit.json'


class RevisitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, cls.info, cls.raw_hash = R['load_original'](ORIGINAL)
        cls.evidence = R['B']['parse_json'](R['SAFE']['read_bytes'](REVISIT, 100000))

    def check(self, evidence):
        return R['check'](self.bundle, self.info, self.raw_hash, evidence)

    def reseal(self, evidence, index):
        evidence['reads'][index]['response_sha256'] = R['P']['digest'](
            evidence['reads'][index]['response'])
        evidence['reads_sha256'] = R['P']['digest'](evidence['reads'])

    def test_real_public_revisit(self):
        result = self.check(self.evidence)
        self.assertEqual(result['status'], 'saved_block_reobserved')
        self.assertEqual(result['block_number'], 26192611)

    def test_original_bytes_are_bound(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['original_file_sha256'] = '0' * 64
        with self.assertRaisesRegex(R['RevisitError'], 'bound'):
            self.check(evidence)

    def test_resealed_block_reorganization_is_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['reads'][3]['response']['result']['hash'] = '0x' + '1' * 64
        self.reseal(evidence, 3)
        with self.assertRaisesRegex(R['RevisitError'], 'canonical'):
            self.check(evidence)

    def test_resealed_state_disagreement_is_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['reads'][1]['response']['result'] = '0x' + '0' * 64
        self.reseal(evidence, 1)
        with self.assertRaisesRegex(R['RevisitError'], 'differs'):
            self.check(evidence)

    def test_downgraded_state_selector_is_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['reads'][1]['params'][1] = 'latest'
        evidence['reads_sha256'] = R['P']['digest'](evidence['reads'])
        with self.assertRaises(R['P']['PinnedError']):
            self.check(evidence)

    def test_block_reread_swap_is_observationally_indistinguishable(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['reads'][0], evidence['reads'][3] = evidence['reads'][3], evidence['reads'][0]
        evidence['reads_sha256'] = R['P']['digest'](evidence['reads'])
        # Both block reads have the same request and identity, so swapping them
        # deliberately remains valid: the transcript cannot certify actual order.
        self.assertEqual(self.check(evidence)['status'], 'saved_block_reobserved')

    def test_reordered_state_reads_are_rejected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence['reads'][1], evidence['reads'][2] = evidence['reads'][2], evidence['reads'][1]
        evidence['reads_sha256'] = R['P']['digest'](evidence['reads'])
        with self.assertRaisesRegex(R['RevisitError'], 'saved canonical block'):
            self.check(evidence)

    def test_wrong_original_bundle_is_rejected(self):
        other = 'line-1/tools/hash-pinned-zto/live-zto.json'
        bundle, info, raw_hash = R['load_original'](other)
        with self.assertRaisesRegex(R['RevisitError'], 'bound'):
            R['check'](bundle, info, raw_hash, self.evidence)

    def test_live_read_sequence_can_be_replayed(self):
        supplied = iter(self.evidence['reads'])
        def read(method, params, timeout):
            answer = next(supplied)
            self.assertEqual((answer['method'], answer['params']), (method, params))
            return answer
        bundle, result = R['capture'](self.bundle, self.info, self.raw_hash,
                                      read=read)
        self.assertEqual(result['status'], 'saved_block_reobserved')
        self.assertEqual(bundle['reads_sha256'], self.evidence['reads_sha256'])


if __name__ == '__main__':
    unittest.main()
