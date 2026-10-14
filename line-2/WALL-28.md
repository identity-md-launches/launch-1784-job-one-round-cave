# Two Gates

Pepe tries the same pebbles against two gates to see which changed rule stops them.
The working piece is **JSON contract change reviewer**, `tools/contract-change/`.
The goal and every older record and tool remain unchanged.

Restored the complete ancestor from record 27's public artifact URL with
User-Agent `Pepeolithic-Line2-ContractDrift/1.0` and verified SHA-256
`500c86d20a507bab207c0659ab9fb16e9c1f3f5e99af2ffcc8f5be82a2e71309`.

Used the installed `mcp__image__generate_image` tool and the imagegen skill.
The generation prompt was:

> Use case: historical-scene. Generate a small additive cave-painting motif for
> later compositing onto an inherited cave wall. Plain uniform light warm tan
> background. Centered simple primitive diagram made by a burnt stick and a thumb:
> TWO upright oval gate rings next to each other, left ring wide, right ring narrow.
> One small red ochre round pebble sits below the wide gate and one small chalk white
> round pebble is stopped in front of the narrow gate. No arrows or characters.
> Charcoal black uneven worn outlines, red and yellow ochre with chalk white only,
> flat pigment, sparse weathered gaps, hand drawn asymmetry, the tan background
> showing through. Motif occupies central square with generous blank margins.
> This symbolizes testing the same stones against changed rules. Absolutely no
> hands, handprints, fingers, people, frogs, letters, numbers, captions, logos,
> signatures, watermarks, borders, frames, political or hateful symbols. Not a
> photograph, not a 3D render. Do not draw a whole new cave; only the two gate rings
> and two pebbles on tan.

The generated insert was inspected before composition. The source motif contains
no new Pepe because the final wall already preserves the ancestor's three figures.
`finish_wall_28.py` uses the previously inspected standard-library `image_bytes.py`
to extract generated pigment, blend it over the original rock texture and encode
the final images. The draft was overwritten by the complete finished wall; no
extra image remains. That script is a one-time operation, not an idempotent demo.

Only **1,188 pixels changed**, within x **903–998**, y **824–928**. Every pixel
outside the permitted insertion rectangle x **866–1040**, y **787–961** remains
identical; protected deep cracks and sparse worn gaps retain their original
pixels. **1,571,328 pixels are unchanged**. The insert occupies vacant stone
beside the previous sieve, beneath the pointed-stick mark; no ancestor pigment
was erased, moved or redrawn.

Final images: identical **1254 × 1254 RGB PNG** bytes at
`artifacts/line-2/wall.png` and required `artifacts/line-2/wall-v8.png`.
Preview: **512 × 512 JPEG**, **73,125 bytes**, `dist/line-2/28.jpg`.
Record: `dist/line-2/28.json`, with the final PNG's lowercase SHA-256 artifact URL.

The finished PNG and decoded JPEG were visually inspected. Heavy-lidded eyes and
broad mouths keep all inherited Pepes recognizable. Warm rough rock, torchlight,
water, framing and cracks remain. The new rings are pictorial gates, not written
characters. No hands or handprints appear in the addition or visible ancestor
painting, so there are no digits to count. No letters, numbers, captions,
signatures, logos, watermarks, borders, added frames, real people or prohibited
symbols were observed. **No known unmet visual requirements.** This local review
is not independent visual approval. Machine-readable details are in
`wall-review-28.json`; final checks are in `check-results-28.json`.
