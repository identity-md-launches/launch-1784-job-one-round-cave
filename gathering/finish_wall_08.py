#!/usr/bin/env python3
"""One-time additive pigment composition for gathering 08; stdlib only."""
import hashlib
import json
from pathlib import Path

from finish_wall_07 import read_rgba
from image_bytes import jpeg, png, read_png, resize

ROOT = Path(__file__).resolve().parent.parent
ANCESTOR_SHA = 'ea108b04ea0e22b3070f3919b8f88b58c4e3e24d0fb6df5062e16c30b973a2fc'
PROMPT = ('Transparent prehistoric mineral-pigment mark: recognizable heavy-lidded, '
          'wide-mouthed Pepe head above two linked pebbles, charcoal and worn ochre, '
          'no hands, text, frames, logos, modern shading or other figures. Imagegen draft '
          'composited only on vacant ancestral stone.')


def main():
    source = ROOT / 'test/scratch/gathering07.png'
    draft = ROOT / 'test/scratch/mark08.png'
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ANCESTOR_SHA:
        raise ValueError('wrong ancestor')
    w, h, old = read_png(raw)
    gw, gh, generated = read_rgba(draft.read_bytes())
    if (w, h) != (1254, 1254):
        raise ValueError('wrong wall size')
    opaque = [(x, y) for y in range(gh) for x in range(gw)
              if generated[(y*gw+x)*4+3] > 128]
    sx0, sy0 = min(x for x, y in opaque), min(y for x, y in opaque)
    sx1, sy1 = max(x for x, y in opaque)+1, max(y for x, y in opaque)+1
    # The dark left alcove is empty of ancestor drawings. Keep the deep cracks.
    x0, y0, width, height = 78, 644, 177, 169
    final = bytearray(old)
    changed = 0
    bounds = [w, h, 0, 0]
    for dy in range(height):
        for dx in range(width):
            x, y = x0+dx, y0+dy
            i = (y*w+x)*3
            rock = old[i:i+3]
            if max(rock) < 75:
                continue
            xa, xb = sx0+dx*(sx1-sx0)//width, sx0+(dx+1)*(sx1-sx0)//width
            ya, yb = sy0+dy*(sy1-sy0)//height, sy0+(dy+1)*(sy1-sy0)//height
            totals, weight = [0., 0., 0.], 0.
            for gy in range(ya, yb):
                for gx in range(xa, xb):
                    r, g, b, a = generated[(gy*gw+gx)*4:(gy*gw+gx)*4+4]
                    if a < 45:
                        continue
                    if r > 175 and g < 65 and b < 65:
                        continue  # rare generated red fringe is not earth pigment
                    charcoal = max(r, g, b) < 105
                    red_ochre = r > g*1.28 and g > b*1.2
                    color = (42, 34, 25) if charcoal else (155, 81, 43) if red_ochre else (177, 139, 93)
                    strength = a/255
                    weight += strength
                    for c in range(3):
                        totals[c] += color[c]*strength
            if not weight:
                continue
            alpha = min(.76, .84*weight/((xb-xa)*(yb-ya)))
            for c in range(3):
                final[i+c] = round(rock[c]*(1-alpha)+(totals[c]/weight)*alpha)
            if final[i:i+3] != rock:
                changed += 1
                bounds = [min(bounds[0], x), min(bounds[1], y), max(bounds[2], x), max(bounds[3], y)]
    if changed < 2000:
        raise ValueError('insufficient pigment')
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if not (x0 <= x < x0+width and y0 <= y < y0+height) or max(old[i:i+3]) < 75:
                assert final[i:i+3] == old[i:i+3]
    encoded = png(w, h, final)
    out = ROOT / 'artifacts/gathering'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'wall-v8.png').write_bytes(encoded)
    (out / 'wall.png').write_bytes(encoded)
    thumbnail = resize(w, h, final)
    quality = 52
    preview = jpeg(512, 512, thumbnail, quality)
    while len(preview) > 100000 and quality > 10:
        quality -= 5
        preview = jpeg(512, 512, thumbnail, quality)
    if len(preview) > 100000:
        raise ValueError('preview too large')
    (ROOT / 'dist/gathering/08.jpg').write_bytes(preview)
    review = {
        'ancestorSha256': ANCESTOR_SHA, 'ancestorSize': [w, h],
        'wallSize': [w, h], 'wallFormat': 'PNG', 'wallMode': 'RGB',
        'wallSha256': hashlib.sha256(encoded).hexdigest(),
        'generatedDraftSha256': hashlib.sha256(draft.read_bytes()).hexdigest(),
        'generatedDraftSize': [gw, gh], 'generatedDraftRetained': False,
        'changedPixels': changed, 'unchangedPixels': w*h-changed,
        'changedPixelBounds': bounds, 'additionRectangle': [x0, y0, width, height],
        'allPixelsOutsideAdditionUnchanged': True, 'deepCracksProtected': True,
        'previewSize': [512, 512], 'previewFormat': 'JPEG',
        'previewBytes': len(preview), 'previewQuality': quality,
        'imageTool': 'image_gen__imagegen', 'prompt': PROMPT,
        'reviewStatus': 'requires final visual inspection', 'unmetVisualRequirements': []}
    (ROOT / 'gathering/wall-review-08.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps({k: v for k, v in review.items() if k != 'prompt'}, indent=2))


if __name__ == '__main__':
    main()
