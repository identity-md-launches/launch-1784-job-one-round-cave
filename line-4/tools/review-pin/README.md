# Offline EIP-712 review pin

Retain a SHA-256 commitment after reviewing an intended collection, then require
that pin when comparing separately captured `eth_signTypedData_v4` requests.
This catches a handoff that silently replaces **both** input collections with
matching altered requests. Python standard library only; copy this whole folder
to run it offline. It reads JSON and prints results; it never dispatches requests.

One command from the repository root:

```sh
python3 -B line-4/tools/review-pin/review_pin.py check line-4/tools/review-pin/zto-set.json line-4/tools/review-pin/zto-set.json --expect c1f7a3ff0b7cf878d16be782f567b2bf89f88e9b962ed64210eeaeb2cf6d7023
```

Tried: exit **0**, `pinMatches: true`, `accepted: true`; historical real-ZTO
digest `0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`.
Self-comparison is an execution example, not independent review or approval.
The fixture and illustrative public account are inherited historical evidence;
no ownership, consent, live signing workflow or fresh chain observation is claimed.
Replace the second filename with `line-4/tools/review-pin/missing-set.json`:
exit **1**, matching pin but rejected missing request.

For your own work, independently review the intended collection, including its
accounts, labels, order and full typed data. Then run:

```sh
python3 -B line-4/tools/review-pin/review_pin.py pin line-4/tools/review-pin/zto-set.json
```

That prints one lowercase 64-character pin. Retain it separately from the files
being handed off, and pass that earlier value to `check --expect`. Do not compute
a new pin from incoming files and treat it as prior approval. A party who can
replace both the inputs **and** the expected pin can still pass. This is an
unkeyed integrity commitment, not a signature or source authentication.

The collection format is exactly `{"requests": [{"reviewId": "label", "request":
{"method": "eth_signTypedData_v4", "params": ["public account", "typed-data JSON string"]}}]}`.
Complete JSON-RPC 2.0 envelopes with `jsonrpc` and `id` are also supported. Each
label is unique, 1–64 ASCII letters/digits/`._-`, beginning with a letter/digit.
Intended collections contain 1–16 entries; captured collections allow 0–16.

The pin binds list order, review labels, normalized public accounts, primary
types, digests and every reachable encoding node's path, type, kind, word,
type encoding and raw preimage, using the ancestor comparator's equivalence
rules. Address case, equivalent integer notation, JSON whitespace/key order,
JSON-RPC IDs and provider-versus-JSON-RPC wrapping do not change it. Unreachable
valid type declarations are not encoded or pinned, but are still validated.
Labels and accounts are bound by this outer pin; they are not added to the
EIP-712 signed digest. No network, key, wallet or environment access occurs.

Protocol v1 is SHA-256 of ASCII bytes `eip712-request-review-pin:v1` followed by
one LF byte and canonical ASCII JSON of an ordered entry array. JSON uses
`sort_keys=True`, `ensure_ascii=True`, `separators=(',', ':')`. Each entry has
`reviewId`, `account`, `primaryType`, `digest`, `nodes`; `nodes` maps JSON Pointer
paths to the ancestor's `encoding_node` projection. The command does not print
the raw encoding preimages. This pin is distinct from an exact-file checksum
and from the Ethereum Keccak EIP-712 digest.

Exit **0**: pin produced or full match. Exit **1**: valid pin or collection
mismatch. Exit **2**: invalid input, bad pin syntax, unsafe path or exceeded
bound. A mismatching intended pin is rejected **before the client file is read**.
Files are strict UTF-8 JSON, max 65,536 bytes each, regular no-follow files beneath
cwd; hidden paths, parent traversal and symlinks are refused. POSIX directory
descriptors are required. Inherited bounds include depth 48, 8,192 nodes,
64 types, 256 fields, eight array dimensions, 1 MiB traces and comparisons.
The aggregate canonical pin preimage including prefix is also capped at 1 MiB.
Comparison reports are bounded before detailed differences are removed.

```sh
python3 -B -m unittest discover -s line-4/tools/review-pin -v
```

Tried: **19 tests pass**, including substituted inputs, changed account/domain/
field order, dynamic preimages with simulated equal digests, canonical protocol
bytes, transport equivalence, strict JSON, bounds, CLI exits and no client read
on pin mismatch. Acceptance and missing-request CLI trials pass; a detached copy
works without sibling tools or installed packages. Source copies and the ZTO
fixture are unchanged; `provenance.json` records exact source and copy hashes.

This reuses the ancestor encoder and comparator, so it is not an independent
cryptographic implementation. Matching establishes neither account ownership,
consent, payment, replay protection nor contract support. Establish the intended
source and preserve capture order independently. The mark represents a knot
around the pebble already checked.
