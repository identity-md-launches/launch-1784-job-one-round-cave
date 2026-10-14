#!/usr/bin/env python3
"""Pin reviewed EIP-712 request encodings before comparing captured requests."""
import argparse
import hashlib
import hmac
import json
import re
import sys

from request_compare import encoding_node
from request_set_check import collection, compare_set
from rpc_request_check import unpack
from typed_digest import TypedDataError, load_workspace_json
from typed_trace import explain

PREFIX = b'eip712-request-review-pin:v1\n'
MAX_COMMITMENT_BYTES = 1_048_576
PIN = re.compile(r'[0-9a-f]{64}\Z')


def commitment(intended):
    """Commit order, labels, accounts and all reachable encoding inputs.

    This uses the same equivalence rules as the inherited request comparison:
    JSON formatting, RPC IDs, wrapper and normalized atomic spelling do not
    change the pin. Dynamic preimages and type encodings do change it.
    """
    ids, requests = collection(intended, intended=True)
    entries = []
    for key in ids:
        account, data, _ = unpack(requests[key])
        trace = explain(data)
        nodes = {node['path']: encoding_node(node) for node in trace['nodes']}
        entries.append({'reviewId': key, 'account': account,
                        'primaryType': trace['primaryType'],
                        'digest': trace['digest'], 'nodes': nodes})
        # Bound aggregation as each item is added; never emit the preimages.
        raw = json.dumps(entries, sort_keys=True, ensure_ascii=True,
                         separators=(',', ':')).encode('ascii')
        if len(PREFIX) + len(raw) > MAX_COMMITMENT_BYTES:
            raise TypedDataError('review commitment exceeds 1048576-byte limit')
    return hashlib.sha256(PREFIX + raw).hexdigest()


def verify_pin(intended, expected):
    if type(expected) is not str or not PIN.fullmatch(expected):
        raise TypedDataError('expected pin must be exactly 64 lowercase SHA-256 hex digits')
    actual = commitment(intended)
    return {'version': 1, 'pinMatches': hmac.compare_digest(actual, expected),
            'expectedPin': expected, 'actualPin': actual,
            'pinScheme': 'eip712-request-review-pin:v1',
            'pinTrust': 'expected pin must be independently retained after review; not a signature'}


def review(intended, client, expected):
    report = verify_pin(intended, expected)
    return finish_review(report, intended, client)


def finish_review(report, intended, client):
    report['accepted'] = False
    if report['pinMatches']:
        comparison = compare_set(intended, client)
        for item in comparison['items']:
            item.pop('differences')
        report['comparison'] = comparison
        report['accepted'] = comparison['accepted']
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    pin = sub.add_parser('pin', help='print a pin only after independently reviewing the collection')
    pin.add_argument('intended')
    check = sub.add_parser('check', help='require a separately retained pin before loading client input')
    check.add_argument('intended')
    check.add_argument('client')
    check.add_argument('--expect', required=True, help='previously retained lowercase SHA-256 pin')
    args = parser.parse_args(argv)
    try:
        intended = load_workspace_json(args.intended)
        if args.command == 'pin':
            print(commitment(intended))
            return 0
        # Fail before opening client data if the intended collection changed.
        report = verify_pin(intended, args.expect)
        if not report['pinMatches']:
            report['accepted'] = False
        else:
            report = finish_review(report, intended, load_workspace_json(args.client))
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report['accepted'] else 1
    except (ValueError, OSError, RecursionError) as exc:
        print('review-pin: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
