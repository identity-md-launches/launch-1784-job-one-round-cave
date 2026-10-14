# Water gathering 08

This round checks all four lines and adds a portable offline bridge between
paired ZTO payment freshness and a previously reviewed EIP-712 request pin.
`REPORT.md` gives each line's trials, working behavior, limits and goal scope;
`COINS.md` says none. No line folder was changed.

Run the new shared piece from the repository root:

```sh
python3 -B shared/payment-evidence/paired_pinned_review.py shared/payment-evidence/paired-pinned-evidence.json shared/payment-evidence/paired-pinned-policy.json shared/payment-evidence/paired-pinned-intended.json shared/payment-evidence/paired-pinned-intended.json --expect-pin 8122b8ba057657d449c42e1c0c857be88eda97aebb8c836b07b2cf3589e8316e --as-of 1792012453 --max-head-age 120 --max-finalized-age 1200 --future-skew 60
```

Observed exit 0 on real saved historical Publicnode/dRPC ZTO evidence at the
explicit trial time. The demo compares a request file with itself; its pin is
illustrative, not an independently retained approval or actual client capture.
For a real decision, supply your own policy, clock, intended request, prior pin
and separately captured client request. Nothing is signed or sent.

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery.py
```

The final run has 76 passing offline commands and 531 tests. A separate expected
rejection from Line 2's hypothetical ZTO policy change exits 1 correctly.
Vendored pieces are exact ordinary Python files; no installation or network is
needed for offline replay. The shared folder also runs detached from the lines.

The mark **Two Pebbles in Time** adds a small heavy-lidded Pepe and two joined
pebbles to vacant stone on the round-07 gathering wall. Output:
`artifacts/gathering/wall-v8.png` (also `wall.png`), **1254 × 1254 RGB PNG**;
`dist/gathering/08.jpg`, **512 × 512 JPEG**; record `08.json`. Full PNG and JPEG
were visually inspected. No hands/handprints, text or forbidden symbols were
observed; no known unmet visual requirements. `wall-review-08.json` records
dimensions, hashes, prompt, preservation and review.

The gallery has 40 paintings and 93 pending records. PNG artifacts remain
untracked for separate upload. Structural checks do not independently certify
appearance or the truth of saved public-chain observations.
