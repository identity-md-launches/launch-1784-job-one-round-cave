#!/usr/bin/env python3
"""Review a proposed structural contract against an exact offline JSON corpus."""
import argparse
import json
from pathlib import Path
import sys
import types

MAX_DOCUMENTS = 32
MAX_TOTAL_BYTES = 4_000_000
MAX_OUTPUT_BYTES = 100_000

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module



def dependencies():
    bounded = bounded_module()
    source = Path(__file__).absolute().parent.parent / 'source-locator' / 'locate.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    locations = types.ModuleType('change_source_locator')
    locations.__file__ = str(source)
    exec(compile(bounded.read_bytes(relative), str(source), 'exec'), locations.__dict__)
    _, engine, rules = locations.dependencies()
    return bounded, locations, engine, rules


def review(bounded, locations, engine, rules, old_name, new_name, names):
    if not 1 <= len(names) <= MAX_DOCUMENTS:
        raise ValueError('provide 1 to 32 documents')
    if len(set(names)) != len(names):
        raise ValueError('duplicate document paths are refused')
    cache = {}
    total = 0

    def capture(name):
        nonlocal total
        if name not in cache:
            # The remaining aggregate budget also constrains each actual read.
            remaining = min(1_000_000, MAX_TOTAL_BYTES - total)
            data = bounded.read_bytes(name, limit=remaining)
            total += len(data)
            cache[name] = locations.Source(data, name)
        return cache[name]

    old, new = capture(old_name), capture(new_name)
    engine.prepare(old.value)
    engine.prepare(new.value)
    rows = []
    counts = dict.fromkeys(('still_accepted', 'newly_rejected',
                            'newly_accepted', 'still_rejected'), 0)
    for name in names:
        document = capture(name)
        before = locations.locate(engine, rules, old, document)
        after = locations.locate(engine, rules, new, document)
        transition = {(True, True): 'still_accepted',
                      (True, False): 'newly_rejected',
                      (False, True): 'newly_accepted',
                      (False, False): 'still_rejected'}[before['valid'], after['valid']]
        counts[transition] += 1
        rows.append({'file': name, 'transition': transition,
                     'before': before, 'after': after})
    return {'valid': not (counts['newly_rejected'] or counts['still_rejected']),
            'scope': 'only the supplied documents; not universal contract compatibility',
            'no_observed_regressions': counts['newly_rejected'] == 0,
            'summary': {'checked': len(rows), **counts},
            'contracts': {'before': old.identity(), 'after': new.identity()},
            'captured_bytes': total, 'documents': rows}


def encode_report(result, limit=MAX_OUTPUT_BYTES):
    # Never truncate diagnostics or print a partial successful report.
    chunks, size = [], 0
    encoder = json.JSONEncoder(ensure_ascii=True, allow_nan=False, indent=2)
    for chunk in encoder.iterencode(result):
        size += len(chunk.encode('ascii'))
        if size + 1 > limit:
            raise ValueError('complete report exceeds 100000-byte output limit; use a smaller corpus')
        chunks.append(chunk)
    return ''.join(chunks)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before_contract', help='trusted existing contract')
    parser.add_argument('after_contract', help='trusted proposed contract')
    parser.add_argument('documents', nargs='+', help='relative workspace JSON paths')
    args = parser.parse_args(argv)
    try:
        result = review(*dependencies(), args.before_contract,
                        args.after_contract, args.documents)
        output = encode_report(result)
        print(output)
        return 0 if result['valid'] else 1
    except (ValueError, OSError, RecursionError, KeyError, IndexError, AttributeError) as exc:
        # A bounded generic error avoids echoing huge attacker-controlled names.
        message = str(exc)
        print(json.dumps({'valid': False, 'error': message[:400],
                          'error_truncated': len(message) > 400}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    sys.exit(main())
