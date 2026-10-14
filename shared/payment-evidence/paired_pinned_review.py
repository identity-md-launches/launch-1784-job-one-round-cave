#!/usr/bin/env python3
"""Require fresh paired payment evidence and a pinned captured EIP-712 request."""
import argparse
import json
from pathlib import Path
import sys

from check import commitment, load, module

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'vendor'))
import review_pin
import rpc_request_check

paired = module('shared_paired_freshness', 'vendor/paired-freshness/paired.py')
MAX_OUTPUT = 100000


def review(sample, policy, intended, client, expected_pin, as_of,
           max_head_age, max_finalized_age, future_skew=0):
    """Evaluate content and time; caller supplies policy, clock and prior pin."""
    pin = review_pin.verify_pin(intended, expected_pin)
    if not pin['pinMatches']:
        return {'accepted': False, 'state': 'pin_mismatch', 'pin': pin}
    result = paired.evaluate(sample, policy, as_of, max_head_age,
                             max_finalized_age, future_skew)
    expected_data, expected_digest = commitment(sample, policy)
    if expected_data['message']['transcriptHash'] != '0x' + result['sampleSha256']:
        raise ValueError('paired transcript commitment disagreement')
    ids, requests = review_pin.collection(intended, intended=True)
    if len(ids) != 1:
        raise ValueError('this review requires exactly one intended request')
    _, actual_data, _ = rpc_request_check.unpack(requests[ids[0]])
    binding = actual_data == expected_data
    comparison = review_pin.finish_review(pin, intended, client)
    accepted = result['accepted'] and binding and comparison['accepted']
    return {
        'accepted': accepted,
        'state': 'paired_freshness_and_request_match' if accepted else 'review_required',
        'pinMatches': pin['pinMatches'],
        'pairedAccepted': result['accepted'],
        'pairedState': result['state'],
        'pairedAlerts': result['alerts'],
        'sampleSha256': result['sampleSha256'],
        'paymentPolicy': result['policy'],
        'timePolicy': result['timePolicy'],
        'intendedBindsExactSampleAndPolicy': binding,
        'intendedDigest': expected_digest['digest'],
        'capturedRequestMatchesPinnedIntended': comparison['accepted'],
        'requestComparison': comparison['comparison'],
        'limits': ('Saved provider responses, caller clock and independently retained pin are trust inputs; '
                   'no signature, account ownership, invoice, current chain truth or independent operators proven.')}


def render(value):
    raw = json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
    if len(raw.encode()) > MAX_OUTPUT:
        raise ValueError('review output exceeds 100000 bytes')
    return raw


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paired', help='saved paired timestamp-bearing transcript')
    parser.add_argument('policy', help='independently selected payment policy')
    parser.add_argument('intended', help='independently reviewed request collection')
    parser.add_argument('client', help='separately captured request collection')
    parser.add_argument('--expect-pin', required=True, help='pin retained before handoff')
    parser.add_argument('--as-of', type=int, required=True)
    parser.add_argument('--max-head-age', type=int, required=True)
    parser.add_argument('--max-finalized-age', type=int, required=True)
    parser.add_argument('--future-skew', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        intended = load(args.intended)
        pin = review_pin.verify_pin(intended, args.expect_pin)
        if not pin['pinMatches']:
            print(render({'accepted': False, 'state': 'pin_mismatch', 'pin': pin}), end='')
            return 1
        # A changed intended file fails before opening the client or paired evidence.
        result = review(load(args.paired), load(args.policy), intended,
                        load(args.client), args.expect_pin, args.as_of,
                        args.max_head_age, args.max_finalized_age, args.future_skew)
        print(render(result), end='')
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, TypeError, KeyError, IndexError, RecursionError):
        print(render({'accepted': False, 'state': 'input_error',
                      'reason': 'Invalid pin, policy, time, evidence, request or output bound.'}), end='')
        return 2


if __name__ == '__main__':
    sys.exit(main())
