"""Saved real Ethereum replay; mutations below are rejection fixtures only."""
import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch
import paired as p

FOLDER = Path('line-3/tools/paired-freshness')


def inputs():
    return (p.w.load_workspace_json(FOLDER/'paired-evidence.json'),
            p.w.load_workspace_json(FOLDER/'observed-policy.json'),
            p.w.load_workspace_json(FOLDER/'trial.json')['timeArguments'])


class PairedTests(unittest.TestCase):
    def evaluate(self, sample=None, **overrides):
        original, policy, args = inputs()
        args.update(overrides)
        return p.evaluate(original if sample is None else sample, policy, **args)

    def test_real_pair_and_immutable_inputs(self):
        sample, policy, args = inputs()
        before = copy.deepcopy((sample, policy, args))
        result = p.evaluate(sample, policy, **args)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['state'], 'corroborated_within_time_budget')
        self.assertEqual(len(result['providers']), 2)
        for provider in result['providers']:
            self.assertTrue(provider['accepted'])
            self.assertEqual(provider['payment']['transferEvidence']['netRaw'], policy['minimum_raw'])
        self.assertEqual((sample, policy, args), before)

    def test_both_stale_even_when_payment_passes(self):
        result = self.evaluate(as_of=inputs()[2]['as_of']+1201)
        self.assertFalse(result['accepted'])
        for index, item in enumerate(result['providers'], 1):
            self.assertTrue(item['payment']['accepted'])
            self.assertIn('provider_'+str(index)+':head_too_old', result['alerts'])
        self.assertEqual(p.exit_code(result), 1)

    def test_one_stale_provider_rejects_pair(self):
        # Move all of provider 2's timestamps backwards coherently. Never publish as real evidence.
        sample, _, args = inputs()
        for read in sample['providers'][1]['reads']:
            if read['method'] == 'eth_getBlockByNumber':
                read['result']['timestamp'] = hex(int(read['result']['timestamp'],16)-1201)
        result = self.evaluate(sample)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['providers'][0]['accepted'])
        self.assertIn('provider_2:head_too_old', result['alerts'])
        self.assertIn('shared_height_header_disagreement', result['alerts'])

    def test_timestamp_disagreement_even_when_both_fresh(self):
        sample, _, _ = inputs()
        for read in sample['providers'][1]['reads']:
            if read['method'] == 'eth_getBlockByNumber':
                read['result']['timestamp'] = hex(int(read['result']['timestamp'],16)+1)
        result = self.evaluate(sample)
        self.assertTrue(all(x['accepted'] for x in result['providers']))
        self.assertFalse(result['accepted'])
        self.assertEqual(result['alerts'], ['shared_height_header_disagreement'])

    def test_equal_amount_different_sender_rejected(self):
        sample, _, _ = inputs()
        second = sample['providers'][1]['reads']
        token = p.w.TOKENS['ZTO']
        recipient = sample['policy']['recipient']
        for read in second:
            if read['method'] == 'eth_getTransactionReceipt':
                for log in read['result']['logs']:
                    if log['address'].lower() == token and log['topics'][0].lower() == p.s.TRANSFER:
                        # Rejection-only mutation to the real ZTO contract address.
                        log['topics'][1] = '0x'+'0'*24+token[2:]
        result = self.evaluate(sample)
        self.assertFalse(result['accepted'])
        self.assertIn('transferEvidence', result['paymentDifferences'])

    def test_policy_shortfall_both_providers(self):
        sample, policy, args = inputs()
        policy['minimum_raw'] = str(int(policy['minimum_raw'])+1)
        sample['policy'] = copy.deepcopy(policy)
        result = p.evaluate(sample, policy, **args)
        self.assertFalse(result['accepted'])
        self.assertIn('payment_policy_not_met', result['alerts'])

    def test_single_provider_duplicate_swapped_or_wrong_sources(self):
        for kind in ('missing', 'duplicate', 'swapped', 'unknown'):
            sample, _, _ = inputs()
            if kind == 'missing': sample['providers'].pop()
            if kind == 'duplicate': sample['providers'][1]['source'] = sample['providers'][0]['source']
            if kind == 'swapped': sample['providers'].reverse()
            if kind == 'unknown': sample['providers'][1]['source'] = 'https://example.invalid'
            with self.subTest(kind=kind), self.assertRaises(p.w.Error): self.evaluate(sample)

    def test_exact_envelopes_request_types_and_consumption(self):
        for kind in ('version', 'extra', 'provider_extra', 'read_extra', 'request_type', 'unused'):
            sample, _, _ = inputs()
            if kind == 'version': sample['version'] = True
            if kind == 'extra': sample['accepted'] = True
            if kind == 'provider_extra': sample['providers'][0]['accepted'] = True
            read = sample['providers'][0]['reads'][1]
            if kind == 'read_extra': read['accepted'] = True
            if kind == 'request_type': read['params'][1] = 0
            if kind == 'unused': sample['providers'][0]['reads'].append(copy.deepcopy(read))
            with self.subTest(kind=kind), self.assertRaises(p.w.Error): self.evaluate(sample)

    def test_missing_timestamps_refused(self):
        sample, _, _ = inputs()
        del sample['providers'][1]['reads'][1]['result']['timestamp']
        with self.assertRaises(p.w.Error): self.evaluate(sample)

    def test_expected_policy_mismatch(self):
        sample, policy, args = inputs()
        policy['token'] = 'IMD'
        with self.assertRaises(p.w.Error): p.evaluate(sample, policy, **args)

    def test_invalid_time_and_unfinalized_policy_before_network(self):
        _, policy, args = inputs()
        for override in ({'as_of':None}, {'as_of':True}, {'max_head_age':0},
                         {'max_finalized_age':604801}, {'future_skew':3601}):
            with self.subTest(override=override), self.assertRaises(p.w.Error):
                p.collect(policy, **dict(args, **override), rpc_factory=lambda x:self.fail('network'))
        policy['finalized'] = False
        with self.assertRaises(p.w.Error):
            p.collect(policy, **args, rpc_factory=lambda x:self.fail('network'))

    def test_live_capture_replay_equivalence(self):
        sample, policy, args = inputs()
        def factory(source):
            return p.r.ExactReplay(sample['providers'][p.a.PROVIDERS.index(source)]['reads'])
        result = p.collect(policy, **args, rpc_factory=factory)
        self.assertTrue(result['accepted'])
        replay = p.evaluate(result['sample'], policy, **args)
        for key in ('accepted','state','alerts','providers','sampleSha256'):
            self.assertEqual(result[key], replay[key])

    def test_second_provider_failure_never_falls_back(self):
        sample, policy, args = inputs()
        calls = []
        def factory(source):
            calls.append(source)
            if len(calls) == 2: raise OSError('rejection fixture')
            return p.r.ExactReplay(sample['providers'][0]['reads'])
        result = p.collect(policy, **args, rpc_factory=factory)
        self.assertEqual(calls, list(p.a.PROVIDERS))
        self.assertEqual(result['state'], 'provider_error')
        self.assertFalse(result['accepted'])
        self.assertNotIn('sample', result)
        self.assertEqual(p.exit_code(result), 2)

    def test_demo_cli_and_missing_explicit_time(self):
        out = io.StringIO()
        with redirect_stdout(out): self.assertEqual(p.main(['--demo']), 0)
        self.assertTrue(json.loads(out.getvalue())['accepted'])
        for args in (['--demo','--as-of','1'], ['--live'],
                     ['--replay',str(FOLDER/'paired-evidence.json'),'--policy',str(FOLDER/'observed-policy.json')],
                     ['--live','--policy','../outside.json']):
            with self.subTest(args=args), redirect_stdout(io.StringIO()):
                self.assertEqual(p.main(args), 2)

    def test_fail_closed_output_limit(self):
        with self.assertRaises(p.w.Error), redirect_stdout(io.StringIO()):
            p.emit({'value':'x'*100000})

    def test_no_proxy_environment_discovery(self):
        with patch.object(p.s.urllib.request, 'getproxies', side_effect=AssertionError('environment')):
            for source in p.a.PROVIDERS: p.s.RPC(source)


if __name__ == '__main__': unittest.main()
