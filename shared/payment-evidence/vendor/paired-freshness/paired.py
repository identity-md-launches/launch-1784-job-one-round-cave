#!/usr/bin/env python3
"""Require two timestamp-bearing Ethereum payment observations to agree."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location(
    'paired_freshness', Path(__file__).resolve().parent.parent / 'settlement-freshness' / 'freshness.py')
f = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f)
a, r, w, s = f.a, f.r, f.w, f.s
LIMIT = ('Two URL-labelled provider observations and caller time are trusted inputs, not '
         'consensus, independent operators, source authentication or receipt proofs. '
         'Offline results apply only at the explicitly supplied historical time.')


def evaluate(sample, expected_policy, as_of, max_head_age, max_finalized_age, future_skew=0):
    policy, bounds = f.validate(expected_policy, as_of, max_head_age, max_finalized_age, future_skew)
    if (not isinstance(sample, dict) or set(sample) != {'version', 'policy', 'providers'}
            or type(sample['version']) is not int or sample['version'] != 1
            or a.validate_policy(sample['policy']) != policy):
        raise w.Error('invalid paired envelope or policy mismatch')
    providers = sample['providers']
    if not isinstance(providers, list) or len(providers) != 2:
        raise w.Error('exactly two timestamp-bearing transcripts required')
    reports, timed, headers = [], [], []
    for source, item in zip(a.PROVIDERS, providers):
        if (not isinstance(item, dict) or set(item) != {'source', 'reads'}
                or item['source'] != source):
            raise w.Error('distinct documented sources required in order')
        single = {'version': 1, 'policy': policy, 'reads': item['reads']}
        timed.append(f.evaluate(single, policy, as_of, max_head_age, max_finalized_age, future_skew))
        reports.append(r.replay(single)[1])
        headers.append(f.headers(single))
    agreement = a.compare(reports, policy)
    conflicts = sorted(n for n in headers[0].keys() & headers[1].keys()
                       if headers[0][n] != headers[1][n])
    alerts = []
    if not agreement['accepted']:
        alerts.append('payment_' + agreement['state'])
    if conflicts:
        alerts.append('shared_height_header_disagreement')
    for index, result in enumerate(timed):
        alerts.extend('provider_' + str(index + 1) + ':' + alert for alert in result['alerts'])
    return {'accepted': not alerts,
            'state': 'corroborated_within_time_budget' if not alerts else 'review_required',
            'alerts': alerts, 'policy': policy, 'timePolicy': bounds,
            'paymentDifferences': agreement.get('differences', []),
            'conflictingBlockNumbers': conflicts,
            'providers': [dict(source=source, **result) for source, result in zip(a.PROVIDERS, timed)],
            'sampleSha256': r.digest(sample),
            'evidenceMode': 'offline historical paired evaluation at explicit time',
            'evidenceLimit': LIMIT}


def collect(expected_policy, as_of, max_head_age, max_finalized_age, future_skew=0,
            rpc_factory=s.RPC):
    policy, _ = f.validate(expected_policy, as_of, max_head_age, max_finalized_age, future_skew)
    providers = []
    for source in a.PROVIDERS:
        observation = f.collect(policy, as_of, max_head_age, max_finalized_age, future_skew,
                                source=source, rpc_factory=rpc_factory)
        if 'sample' not in observation:
            return {'accepted': False, 'state': 'provider_error', 'source': source,
                    'reason': 'Both providers must supply complete timestamp-bearing evidence; no fallback.',
                    'evidenceLimit': LIMIT}
        providers.append({'source': source, 'reads': observation['sample']['reads']})
    sample = {'version': 1, 'policy': policy, 'providers': providers}
    result = evaluate(sample, policy, as_of, max_head_age, max_finalized_age, future_skew)
    result.update(sample=sample, evidenceMode='live sequential read-only paired observation at explicit time')
    return result


def exit_code(result):
    return 0 if result['accepted'] else 2 if result['state'] in ('input_error', 'provider_error') else 1


def emit(result):
    encoded = json.dumps(result, indent=2, allow_nan=False)
    if len(encoded.encode()) > 100000:
        raise w.Error('output exceeds 100 KB')
    print(encoded)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--demo', action='store_true')
    mode.add_argument('--replay', help='workspace-relative paired timestamp-bearing transcript')
    mode.add_argument('--live', action='store_true')
    parser.add_argument('--policy', help='workspace-relative independently chosen payment policy')
    parser.add_argument('--as-of', type=int)
    parser.add_argument('--max-head-age', type=int)
    parser.add_argument('--max-finalized-age', type=int)
    parser.add_argument('--future-skew', type=int)
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if any(value is not None for value in (args.policy, args.as_of, args.max_head_age,
                                                   args.max_finalized_age, args.future_skew)):
                raise w.Error('demo refuses overrides')
            folder = Path(__file__).resolve().parent.relative_to(Path.cwd())
            policy = w.load_workspace_json(folder / 'observed-policy.json')
            trial = w.load_workspace_json(folder / 'trial.json')
            sample = w.load_workspace_json(folder / 'paired-evidence.json')
            result = evaluate(sample, policy, **trial['timeArguments'])
            result['demoNote'] = 'Real historical ZTO trial; observed recipient/amount, not an independent invoice or current freshness.'
        else:
            if args.policy is None:
                raise w.Error('supply independent expected policy')
            policy = w.load_workspace_json(args.policy)
            inputs = (policy, args.as_of, args.max_head_age, args.max_finalized_age,
                      args.future_skew if args.future_skew is not None else 0)
            f.validate(*inputs)
            result = collect(*inputs) if args.live else evaluate(w.load_workspace_json(args.replay), *inputs)
        emit(result)
        return exit_code(result)
    except (w.Error, ValueError, TypeError, KeyError, OSError, RecursionError):
        emit({'accepted': False, 'state': 'input_error',
              'reason': 'Invalid policy/time input, malformed paired transcript or output limit exceeded'})
        return 2


if __name__ == '__main__':
    sys.exit(main())
