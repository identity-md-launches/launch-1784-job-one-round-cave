#!/usr/bin/env python3
"""Add generated pigment on vacant stone; preserve the inherited wall bytes."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, jpeg, resize

ANCESTOR = '08aa95a7f34b98bf3523b24cbd80bfc37c43a04653418678ab1eeb0142c026c3'
PROMPT = ('Use case: illustration-story. One primitive charcoal-black cord loop tied '
          'in a small knot around a red ochre pebble. This simple prehistoric cave '
          'painting motif is centered on flat PALE CREAM stone, with empty pale '
          'cream stone inside and outside the loop. Only dark black charcoal '
          'strokes and deep RED ochre thumb pigment, NO tan or brown pigment, no '
          'chalk or yellow. Motif fills central two thirds of square. Rough worn '
          'hand drawn strokes with stone showing through, as if drawn with burnt '
          'stick and thumb under torchlight. No text, letters, numbers, people, '
          'hands, logos, watermark, border or frame. Flat cave art, no '
          'three-dimensional objects. This motif will be composited onto an '
          'existing darker cave wall.')


def main():
    folder = Path('artifacts/line-4')
    before = (folder / 'wall.png').read_bytes()
    assert hashlib.sha256(before).hexdigest() == ANCESTOR
    draft = (folder / 'wall-v8.png').read_bytes()
    w, h, old = read_png(before)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (1254, 1254)
    pigment = resize(gw, gh, generated, 140)
    final = bytearray(old)
    count = 0
    for y in range(140):
        for x in range(140):
            j = (y*140+x)*3
            r, g, b = pigment[j:j+3]
            charcoal = r < 190 and g < 175 and b < 150 and r-g < 40
            red = r > 90 and g < r*.56 and b < g*.8
            i = ((y+700)*w+x+70)*3
            if sum(old[i:i+3]) < 140 or not (charcoal or red):
                continue
            # Match the inherited torchlight rather than bringing the generated
            # substrate into the cave. Charcoal always darkens the stone.
            light = min(1.0, max(old[i:i+3]) / 160)
            target = ([a * min(0.8, max(0.35, r/240)) for a, v in zip(old[i:i+3], (r, g, b))]
                      if charcoal else [v*light for v in (r, g, b)])
            final[i:i+3] = bytes(round(a*.25+v*.75) for a, v in zip(old[i:i+3], target))
            count += final[i:i+3] != old[i:i+3]
    assert count > 500
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if final[i:i+3] != old[i:i+3]:
                assert 70 <= x < 210 and 700 <= y < 840
    output = png(w, h, final)
    for name in ('wall.png', 'wall-v8.png'):
        (folder / name).write_bytes(output)
    preview = jpeg(512, 512, resize(w, h, final), 52)
    assert len(preview) < 100000
    Path('dist/line-4/28.jpg').write_bytes(preview)
    sha = hashlib.sha256(output).hexdigest()
    review = {
        'wall': {'paths': ['artifacts/line-4/wall.png', 'artifacts/line-4/wall-v8.png'],
                 'width': w, 'height': h, 'format': 'PNG', 'mode': 'RGB', 'sha256': sha},
        'preview': {'path': 'dist/line-4/28.jpg', 'width': 512, 'height': 512,
                    'format': 'JPEG', 'bytes': len(preview)},
        'ancestorSha256': ANCESTOR,
        'generatedImageSha256': hashlib.sha256(draft).hexdigest(),
        'changedPixels': count, 'unchangedPixels': w*h-count,
        'additionBoundsExclusive': [70, 700, 210, 840],
        'preservation': 'Only generated pigment on vacant far-left stone; every pixel outside the addition and deep fissures inside are unchanged.',
        'imageTool': 'installed mcp__image__generate_image; generated motif composited with standard-library image_bytes.py',
        'prompt': PROMPT,
        'visualReview': 'Pending inspection of finished PNG and JPEG',
        'unmetVisualRequirements': [],
        'limitations': ['Local review is not independent visual certification.',
                        'The small worn mark is less distinct in the 512-pixel preview.']}
    Path('line-4/wall-review-28.json').write_text(json.dumps(review, indent=2)+'\n')
    record = {'name': 'The Kept Knot', 'image': 'https://api.imd.fun/artifacts/'+sha,
              'attributes': [
                  {'trait_type': 'Cave', 'value': 'Water'},
                  {'trait_type': 'Wall', 'value': 'Line 4'},
                  {'trait_type': 'Number', 'value': 28},
                  {'trait_type': 'Left behind', 'value': 'offline EIP-712 review pin'},
                  {'trait_type': 'Meaning', 'value': 'Pepe ties a knot around the pebble he has already checked.'},
                  {'trait_type': 'One thing', 'value': 'offline EIP-712 typed-data digest checking'}]}
    Path('dist/line-4/28.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
