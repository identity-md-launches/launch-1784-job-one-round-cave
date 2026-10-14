# JSON contract change reviewer

Check a proposed JSON structural contract against the exact same saved documents
as the previous contract, offline. Each document is classified as still accepted,
newly rejected, newly accepted, or still rejected. Both versions retain every
violation, its JSON Pointer, and exact document and rule source ranges. This helps
a worker review changes to an API response, manifest, build report or payment
policy before adopting them.

Python 3.10+, standard library only, POSIX. From the repository root, one command
shows it working on actual inherited deliverables:

```sh
python3 -B line-2/tools/contract-change/review.py line-2/tools/json-contract/record.contract.json line-2/tools/ordered-deliverables/record.strict.contract.json dist/line-2/26.json dist/line-2/27.json
```

Observed exit **0**: both documents remain accepted under the stricter ordered
contract. Exact contract/document hashes are in `records.result.json`. This
tests these documents only; it does not prove universal contract compatibility.

## A changed rule that rejects a saved real ZTO policy

```sh
python3 -B line-2/tools/contract-change/review.py shared/payment-evidence/policy.contract.json line-2/tools/contract-change/proposed-policy.contract.json shared/payment-evidence/example.policy.json
```

This intentionally exits **1**. The supplied candidate is a **hypothetical**
structural rule change from 1 to 13 minimum confirmations; it is not an approved
payment policy. Everything else in that candidate is copied from the inherited
policy contract, including ZTO and IMD support. The saved actual ZTO policy asks
for 12 confirmations: it passed the old contract but fails the candidate at
`/confirmations`. The result locates the original `12` token and the candidate's
`13` minimum rule. The exact output is `zto-policy.result.json`.
No transaction is sent, and this structural review does not establish current
chain state, settlement, ownership, policy approval or truth of the document.

## Output and exit codes

- `valid` means **every supplied document passes the candidate contract**.
  Exit **0** requires this; exit **1** means at least one is rejected.
- `no_observed_regressions` means none of these documents changed from accepted
  to rejected. It can be true while `valid` is false if a document remains invalid.
  There is no exit-code option that silently accepts such a result.
- `summary` counts all four transitions. Rows retain input order; both `before`
  and `after` contain complete source-locator diagnostics and exact input hashes.
  This compares acceptance, not individual violation identity or semantic meaning.
- Exit **2** means invalid contract, malformed/unreadable input, duplicate paths,
  exceeded bounds, or a source-location error. It prints only a bounded error,
  not a partially successful corpus report. Both contracts are checked before
  reading any document. A failure in any input invalidates the complete review.

Each distinct named file is captured once per run, even if both contract paths
are equal or a document names a contract file. Hashes, parsing, validation and
source locations all refer to those captured UTF-8 bytes. LF/CRLF and escaped
spelling are retained; offsets are zero-based, end-exclusive, with one-based
Unicode code-point lines/columns. Missing properties have a containing-object
anchor, not a fictitious value range. Locations become obsolete after editing;
compare the exact hash before using them.

Inputs: 1–32 distinct document paths, visible relative workspace regular files,
no symlinks/hidden/parent/absolute paths; 1,000,000 bytes per file and 4,000,000
captured bytes across all unique contracts/documents. Full serialized stdout is
at most 100,000 bytes including its newline. An oversized result fails closed;
it never truncates diagnostics. Review a smaller corpus if necessary, and keep
all batches when making a decision.

## Tests and dependencies

```sh
python3 -B line-2/tools/contract-change/test_review.py
```

All **15 new tests passed**, including all four transitions, unchanged rejection,
actual record tightening, saved ZTO policy rejection with byte slices, missing
fields, Unicode/CRLF/escapes, one capture per path, invalid contracts before
document reads, input/output budgets, strict parsing and fail-closed CLI codes.
The inherited source locator's **16 tests passed** separately. Actual commands,
exit codes and output checksums are saved in `validation.json`.

Keep this folder beside `source-locator/`, `rule-locator/`, `bounded-contract/`
and `json-contract/`. They are ordinary repository Python sources; no downloads
or packages are required. The trusted no-follow bootstrap is copied unchanged
from source-locator. The tool writes only stdout and uses no network, environment,
secret, wallet, signature, payment or transaction. No coin is needed for the
checker; its real payment-policy example uses ZTO first, with IMD also supported.

Supported rules are the existing explicit contract subset, not full JSON Schema.
Contracts, regexes and sibling Python code must be trusted. Regex runtime,
uniqueness comparisons, indexing and intermediate diagnostics are not separately
CPU/memory-bounded; the output limit constrains emitted bytes, not execution time.
Checksums identify bytes, not authenticated sources. Hardlink provenance and
hostile mutation during a read are not established.

## Mark

**Two Gates**, record 28: Pepe tries the same pebbles against two gates to see
which changed rule stops them. Generated charcoal rings and ochre/chalk pebbles
were added only to vacant lower-right stone. The ancestor's rock, cracks,
lighting, framing and all three Pepe figures remain exact outside that region.
See `../../WALL-28.md` and `../../wall-review-28.json` for the full prompt,
dimensions, preservation check and visual review.
