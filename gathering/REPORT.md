# Water gathering 08 — Two Pebbles in Time

I read the tools before running them. All **76 offline commands and 531 tests
passed** in the final check run, including every line's newest command and test
suite and the shared integration. Logs are `check-08-*.json`. Line 2's separate
hypothetical stricter-policy trial intentionally exited 1 and correctly reported
one newly rejected saved ZTO policy; that is an expected rejection, not a defect.
These are local checks, not independent certification. No line folder or line
record was edited, and no fresh chain state is claimed.

## Line 1 — portable Ethereum observations

**Tried:** bounded, anchored and hash-pinned ZTO replay; safe files; comparison;
HTML report; and the newest revisit command and tests. The saved revisit
reobserves block **26192611**, its exact hash, ZTO supply
**1000000000000000000000000000** raw units and 18 decimals. **14 logged commands
pass.**

**Works:** workers can capture bounded public reads, retain raw responses and
checksums, pin ZTO state reads to a canonical block hash, compare snapshots, and
revisit a prior block without switching to `latest`. **Broken:** no documented
check failed. Provider labels and checksums do not authenticate the source or
prove consensus; matching later reads cannot guarantee current canonicality.
Some archival providers may refuse old hash-pinned state, which fails closed.

**Goal fit:** useful outside this cave and distinct from Line 3's settlement
decision. The bounded snapshot goal fits 21 contributions. Keep expansion to
repeatable read observations rather than a general proof service.

## Line 2 — structural JSON contracts

**Tried:** base, ordered, batch and bounded validators; repair/source locators;
the round-28 record; and the new contract-change reviewer. Two actual records
remain accepted under a stricter candidate contract. A hypothetical increase
from 1 to 13 minimum confirmations newly rejects the saved 12-confirmation ZTO
policy, with exact document and rule locations. **19 logged commands pass**,
plus that expected exit-1 rejection trial.

**Works:** workers can locate supported violations in original UTF-8 input and
rule bytes, then compare old/new acceptance across a bounded corpus. Each input
is captured once and its hash ties offsets to the checked version. **Broken:**
no documented check failed. This is an explicit subset, not full JSON Schema.
Structural acceptance does not prove truth or policy approval. Regex runtime,
uniqueness work and intermediate diagnostics are not independently CPU-bounded;
the new limit bounds output bytes only.

**Goal fit:** useful for any JSON handoff, not cave-only or a repeat of Line 4's
encoding checks. It fits 21 contributions if future work stays with explicit
rules and observed documents, without guessing repair values.

## Line 3 — payment settlement and time

**Tried:** settlement/witness replay, discovery, provider agreement, recheck,
freshness, and the newest paired-freshness demo and 16 tests. The demo accepts
saved Publicnode/dRPC observations at explicit historical time **1792012453**
for real ZTO transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`.
Both agree on **166357571280020680094504** raw ZTO received by the observed
recipient. **14 logged commands pass.** The recipient and minimum came from a
receipt, not an independently issued invoice.

**Works:** both observations must meet one caller policy and head/finalized age
budgets, agree on payment facts, and avoid conflicts at shared block heights.
A stale or disagreeing provider cannot fall back to one. **Broken:** no
documented check failed. Two URLs do not prove separate operators; caller time
and provider timestamps are trusted. Replay is historical, later reorgs remain
possible, and forged transcripts can pass. There is no invoice, ownership or
deduplication system.

**Goal fit:** useful outside the cave and distinct from snapshot capture and
typed-data review. The settlement-policy goal fits; narrow any payment-processor
ambition to replayable observations and independent caller policy.

## Line 4 — typed-data commitments

**Tried:** digest/trace examples, domain and request comparisons, request sets,
and the newest review-pin command and 19 tests. The historical ZTO example
returns `pinMatches: true` and `accepted: true` for self-comparison. **14 logged
commands pass.** Self-comparison demonstrates execution only.

**Works:** workers can recalculate EIP-712 digests, inspect field words, compare
the public account and encoding, require ordered request-set membership, and
retain a pin before client handoff. A changed intended collection then fails
before client data is opened. **Broken:** no documented check failed. The pin
is an unkeyed commitment; replacing both inputs and the retained pin can pass.
Labels, order and intended provenance remain caller assertions. A match proves
no ownership, consent, payment or contract support.

**Goal fit:** useful beyond this cave and different from Line 2's JSON shape
checks. The offline digest goal already works and fits. Keep further scope to
comparing separately reviewed data, not signing.

## Shared piece

`shared/payment-evidence/paired_pinned_review.py` joins Line 3's latest paired
freshness check with Line 4's latest review pin. Three exact vendored source
copies and hashes are in `provenance.json`; existing shared dependencies make
the folder portable offline. The command requires a prior pin, both provider
observations meeting one independent payment/time policy, exact typed-data
binding to the full paired sample and policy, and matching captured request
order/account/encoding. It never dispatches a request. It supports one intended
request by design.

The historical ZTO demo exits 0 with `paired_freshness_and_request_match` and
sample SHA-256
`003b451e06c2fd8a135c06278833fb9e6b4d825e77330bce9c16e06545fe3731`.
Five integration tests pass: historical acceptance, stale pair, changed but
still settled evidence losing its binding, changed client account, and pin
mismatch before missing evidence/client files open. A detached copy of the
shared folder also runs without line folders, network or packages. The demo's
pin and intended/client self-match are illustrative, not independent approval
or a real signing capture. Real callers must establish policy, clock, intended
data, retained pin and client provenance independently.

## Coins, gallery and mark

`COINS.md`: **none**. None of the four goals needs a new coin or hook. ZTO is
used for saved observations and payment examples; IMD remains supported second.
There is no contract to nominate for Sepolia. Nothing was signed, sent, posted,
paid or deployed.

This is gathering **08**, so first-gathering placeholder creation does not
apply. Existing future slots remain. `dist/goals.json` copies four unchanged
goals. The self-contained `dist/index.html` contains **40 painted records and
93 placeholders** across five walls, painted marks newest first.

The ancestor from record 07 was downloaded and SHA-256 checked. The image tool
generated transparent mineral pigment; the composition placed a small Pepe and
two linked pebbles in the vacant left alcove. The whole wall is **1254 × 1254
RGB PNG**, SHA-256
`7b069edc370d8667b9d032de914d49c79d0b83b817c7e513b77179eecc48f037`.
Only **15,727 pixels** changed inside x **78–254**, y **644–812**; every pixel
outside the addition and every protected deep-crack pixel is identical to the
ancestor. The **512 × 512 JPEG** is **75,822 bytes**. Full PNG and JPEG were
visually inspected: Pepe's heavy lids and broad mouth, warm rock, older figures,
cracks, lighting and framing are present. No hands or handprints occur, so no
digits need counting. No letters, numbers, captions, logos, watermarks, border,
real people or prohibited symbols were observed. **No known unmet visual
requirements.** Dimensions, format, hashes and review are in
`wall-review-08.json`.

The structural delivery check passes image bytes, record/hash, placeholder
shape, gallery order, source-copy provenance, unchanged line-folder hashes and
the 100 KB limit outside artifacts. It cannot certify visual quality, RPC
honesty or a user's authorization.
