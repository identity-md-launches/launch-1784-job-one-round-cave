# Paired settlement freshness

Require **both** public Ethereum observations to meet the same independently
chosen ZTO (or IMD) payment policy and the same explicit head/finalized time
budgets. Compare inclusion, execution and the complete selected-token Transfer
set. Also reject conflicting hashes or timestamps at every block height shared
by the two transcripts. Different advancing head heights are allowed; each
provider must independently meet the time and settlement policy.

One working command from the repository root, requiring only Python's standard
library and no network:

```sh
python3 -B line-3/tools/paired-freshness/paired.py --demo
```

This replays actual saved reads from Publicnode and dRPC at the trial's explicit
historical clock. It returned `corroborated_within_time_budget`, exit 0, for the
real ZTO transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`.
Both observations decoded a net receipt amount of
`166357571280020680094504` raw ZTO to
`0x2d30e495a15f2657d57c3e2caa08b06415c26cbf`.
The recipient/minimum come from the earlier observed payment, **not an issued
invoice**. `trial.json` records actual collection times and chosen time budgets;
`paired-evidence.json` contains complete timestamp-bearing replay reads;
`live-check.json` records the live decision. The demo establishes historical
behavior and does not claim freshness today.

For a decision on your own evidence, independently review all six policy fields
in `observed-policy.json` (or supply your own policy file), and supply your own
trusted Unix clock and budgets:

```sh
python3 -B line-3/tools/paired-freshness/paired.py --replay line-3/tools/paired-freshness/paired-evidence.json --policy line-3/tools/paired-freshness/observed-policy.json --as-of 1792012453 --max-head-age 120 --max-finalized-age 1200 --future-skew 60
```

The explicit time above is the saved trial's historical decision clock.
To collect fresh evidence, replace
`--replay ...` with `--live` and choose an actual trusted decision time. No
implicit saved clock or current clock is used by the tool. No polling or fallback
occurs; both documented URLs are mandatory, in order, with timestamps required.

The input envelope is exactly `version` (integer 1), `policy`, `providers`.
Each of the two provider items is exactly `source`, `reads`, using Publicnode
then dRPC. Reads use the ancestor witness's exact method/parameters/results
format. Policy must exactly match the separately supplied expected policy and
require finality. Inputs are bounded, visible workspace-relative regular files
(up to 90 KB); symlinks, parent/hidden paths, duplicate JSON keys, nonfinite JSON,
extra envelope fields, unused reads and JSON request type mismatches are refused.
Output is bounded to 100 KB. CLI writes no files. Exit 0 means acceptance; exit 1
means review required; exit 2 means invalid input or unavailable provider.

Checks:

```sh
python3 -B -m unittest discover -s line-3/tools/paired-freshness -p 'test_*.py' -v
```

All 16 tests pass: actual immutable replay, stale pairs, one stale provider,
shared timestamp conflicts despite two otherwise fresh payments, changed sender
with unchanged net amount, policy shortfall, source requirements, exact transcript
consumption/types, missing timestamps, expected policy mismatch, invalid time
before transport, capture/replay agreement, failed second provider, CLI and
output boundaries, and disabled proxy/environment discovery. Test mutations are
labelled rejection fixtures; none is saved as real-chain evidence. The first test
run found a malformed address-topic fixture; correcting it to the real ZTO
contract address fixed the fixture without weakening validation.

This combines `settlement-freshness`, `payment-recheck`, `provider-agreement`,
`payment-witness`, and `settlement-check` without changing their files. Copy those
sibling folders along with this one for use elsewhere. Python 3.9+ and POSIX safe
file-open support are required. No third-party dependency or installation.

Two source labels do not authenticate responses or prove independent operators.
Consistently forged observations can pass. Caller time and provider timestamps
are trusted inputs, later reorgs remain possible, and replay is historical.
Shared-height checks do not establish ancestry between different-height anchors.
This does not provide consensus/receipt proofs, recipient ownership, invoice
provenance, balance checks, deduplication or a payment ledger. Public reads use
an explicit User-Agent, disabled proxy discovery and no redirects. No key,
wallet, environment lookup, signature, transaction submission, payment, posting,
deployment or new coin is involved.
