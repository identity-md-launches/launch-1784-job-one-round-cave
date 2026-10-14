#!/usr/bin/env python3
"""Revisit one saved hash-pinned ZTO observation with public Ethereum reads."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys

P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                       'hash-pinned-zto' / 'pinned.py'))
SAFE = P['SAFE']
B = P['B']
SCHEMA = 'line1-zto-revisit-v1'
MAX_BYTES = 100000


class RevisitError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise RevisitError(message)


def load_original(path):
    raw = SAFE['read_bytes'](path, MAX_BYTES)
    bundle = B['parse_json'](raw)
    info = P['validate_bundle'](bundle)
    return bundle, info, hashlib.sha256(raw).hexdigest()


def check(bundle, info, original_file_sha256, revisit):
    """Verify a second transcript against the exact saved original, offline."""
    require(isinstance(revisit, dict) and set(revisit) == {
        'schema', 'rpc_url', 'captured_at_utc', 'original_content_sha256',
        'original_file_sha256', 'reads', 'reads_sha256'},
        'revisit fields differ from schema')
    require(revisit['schema'] == SCHEMA and revisit['rpc_url'] == P['SOURCE'],
            'unexpected revisit schema or source')
    require(revisit['original_content_sha256'] == P['digest'](bundle) and
            revisit['original_file_sha256'] == original_file_sha256,
            'revisit is not bound to these original bytes and content')
    stamp = revisit['captured_at_utc']
    require(isinstance(stamp, str) and len(stamp) <= 64,
            'invalid revisit timestamp')
    try:
        moment = datetime.fromisoformat(stamp)
    except ValueError as exc:
        raise RevisitError('invalid revisit timestamp') from exc
    require(moment.utcoffset() is not None and
            moment.utcoffset().total_seconds() == 0,
            'revisit timestamp must be UTC')
    reads = revisit['reads']
    require(isinstance(reads, list) and len(reads) == 4,
            'expected four ordered revisit reads')
    results = [P['validate_read'](read) for read in reads]
    require(revisit['reads_sha256'] == P['digest'](reads),
            'revisit request/response checksum mismatch')
    number = hex(info['block_number'])
    block_hash = info['block_hash']
    for index in (0, 3):
        require(reads[index]['method'] == 'eth_getBlockByNumber' and
                reads[index]['params'] == [number, False] and
                P['block_identity'](results[index]) == (number, block_hash),
                'saved block is not canonical at the revisit read')
    pin = {'blockHash': block_hash, 'requireCanonical': True}
    for index, selector in ((1, '0x18160ddd'), (2, '0x313ce567')):
        require(reads[index]['method'] == 'eth_call' and
                reads[index]['params'] == [
                    {'to': P['ZTO'], 'data': selector}, pin],
                'revisit state read does not use the saved canonical block')
        require(isinstance(results[index], str) and
                P['HASH'].fullmatch(results[index]),
                'revisit state result must be one ABI word')
    require(int(results[1], 16) == int(info['total_supply_raw']) and
            int(results[2], 16) == info['decimals'],
            'ZTO state at saved block differs from original observation')
    return {
        'status': 'saved_block_reobserved',
        'block_number': info['block_number'],
        'block_hash': block_hash,
        'zto_address': P['ZTO'],
        'total_supply_raw': info['total_supply_raw'],
        'decimals': info['decimals'],
        'total_supply_tokens': info['total_supply_tokens'],
        'original_content_sha256': revisit['original_content_sha256'],
        'original_file_sha256': original_file_sha256,
        'revisit_reads_sha256': revisit['reads_sha256'],
        'captured_at_utc': stamp,
        'evidence': 'Provider observations, not a state or consensus proof',
    }


def capture(bundle, info, original_file_sha256, timeout=15, read=None):
    """Read one saved block twice around two EIP-1898 state calls."""
    require(type(timeout) in (int, float) and 0 < timeout <= 60,
            'timeout must be within (0, 60] seconds')
    read = P['rpc_read'] if read is None else read
    number = hex(info['block_number'])
    pin = {'blockHash': info['block_hash'], 'requireCanonical': True}
    calls = [
        ('eth_getBlockByNumber', [number, False]),
        ('eth_call', [{'to': P['ZTO'], 'data': '0x18160ddd'}, pin]),
        ('eth_call', [{'to': P['ZTO'], 'data': '0x313ce567'}, pin]),
        ('eth_getBlockByNumber', [number, False]),
    ]
    reads = [read(method, params, timeout) for method, params in calls]
    revisit = {
        'schema': SCHEMA,
        'rpc_url': P['SOURCE'],
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'original_content_sha256': P['digest'](bundle),
        'original_file_sha256': original_file_sha256,
        'reads': reads,
        'reads_sha256': P['digest'](reads),
    }
    return revisit, check(bundle, info, original_file_sha256, revisit)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--capture', metavar='ORIGINAL')
    action.add_argument('--verify', nargs=2, metavar=('ORIGINAL', 'REVISIT'))
    parser.add_argument('--output', help='new visible workspace path for capture')
    parser.add_argument('--timeout', type=float, default=15)
    args = parser.parse_args(argv)
    try:
        require((args.capture is None) == (args.output is None),
                '--capture requires --output; --verify forbids it')
        if args.capture:
            SAFE['parts'](args.output)
            bundle, info, raw_hash = load_original(args.capture)
            revisit, result = capture(bundle, info, raw_hash, args.timeout)
            raw = (json.dumps(revisit, sort_keys=True, indent=2,
                              allow_nan=False) + '\n').encode()
            SAFE['write_bytes'](args.output, raw, MAX_BYTES)
        else:
            bundle, info, raw_hash = load_original(args.verify[0])
            raw = SAFE['read_bytes'](args.verify[1], MAX_BYTES)
            result = check(bundle, info, raw_hash, B['parse_json'](raw))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (RevisitError, P['PinnedError'], B['SnapshotError'],
            OSError, ValueError, RecursionError) as exc:
        print('revisit-zto-snapshot: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
