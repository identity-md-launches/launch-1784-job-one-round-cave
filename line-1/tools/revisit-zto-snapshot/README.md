# Revisit a saved ZTO snapshot

This piece takes an earlier hash-pinned ZTO snapshot and asks a public Ethereum
RPC provider about that **same block** again. It stores four public responses:
the block at its height, `totalSupply()` and `decimals()` pinned to its hash
with `requireCanonical: true`, then the block at its height once more. It
compares the hash and exact token values with the original. The new transcript
binds both the original file bytes and its canonical JSON content by SHA-256.
No account, wallet, secret, transaction or payment is used.

One command from the repository root shows the saved **real-chain** result
working offline:

```sh
python3 -B line-1/tools/revisit-zto-snapshot/revisit.py --verify line-1/tools/compare-zto-snapshots/live-zto.json line-1/tools/revisit-zto-snapshot/live-revisit.json
```

I ran `--capture` on 2026-10-14 against the included earlier observation at
Ethereum block **26192611**, then ran that offline verification. Both exited 0.
The provider returned the saved block hash
`0x07dc4edf7c6e1360ce388ee676eb3c17a8b272b4caa6101a94f5541282db5b32`,
ZTO supply `1000000000000000000000000000` raw units and 18 decimals again. The
result is `saved_block_reobserved`. The included transcript is 47,888 bytes.
Nine offline tests passed, including resealed changed-block and changed-state
rejections. The trial uses the real ZTO contract and public read methods.

To make a new revisit transcript, choose a **new** visible workspace path:

```sh
python3 -B line-1/tools/revisit-zto-snapshot/revisit.py --capture line-1/tools/compare-zto-snapshots/live-zto.json --output test/scratch/my-revisit.json
```

The tool uses the sibling `hash-pinned-zto`, `bounded-rpc-snapshot` and
`safe-snapshot-files` Python files, all ordinary repository files. Capture
needs reachable public Ethereum RPC; verification is offline. Input and output
are capped at 100,000 bytes. File reads refuse symlinks and non-regular files;
output is created atomically without replacing an existing file. The transport
sets its own User-Agent, rejects redirects, and disables environment proxy
discovery.

The timestamps and provider URL are claims in saved data. A matching later
provider observation is **not** a cryptographic state proof, independently
authenticated provider evidence, or a guarantee against a later reorganization.
A forged and consistently resealed transcript can pass. Two block reads cannot
prove their wall-clock order, nor prove that the provider did not change state
between them. An archival provider may refuse old hash-pinned state reads; the
tool fails rather than falling back to a block number or `latest`.
