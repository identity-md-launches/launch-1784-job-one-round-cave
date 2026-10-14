"""Retain only the installed image tool's new pebble pigment on ancestor rock."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

BASE = Path('artifacts/line-1/wall.png')
TARGET = Path('artifacts/line-1/wall-v8.png')
ANCESTOR = 'f9c5d45898b050679bd36711c33833a632e42224a570c4c47f8ad3e0d5f9a11d'


def main():
    original = BASE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == ANCESTOR
    w, h, old = read_png(original)
    draft = TARGET.read_bytes()
    gw, gh, generated = read_png(draft)
    assert (w, h) == (1254, 1254) and (gw, gh) == (1024, 1024)
    final = bytearray(old)
    # The generated draft reinterpreted older paintings. Restrict it to the
    # irregular three-pebble silhouette and put that on previously empty rock.
    sx0, sy0, sw, sh = 235, 144, 72, 211
    x0, y0, width, height = 312, 196, 72, 174
    centers = ((276, 174, 31), (270, 248, 34), (265, 324, 29))
    changed = 0
    bounds = [w, h, 0, 0]
    for dy in range(height):
        for dx in range(width):
            x, y = x0 + dx, y0 + dy
            sx, sy = sx0 + dx * sw // width, sy0 + dy * sh // height
            in_pebble = any((sx-cx)**2 + (sy-cy)**2 <= radius**2
                            for cx, cy, radius in centers)
            in_join = 259 <= sx <= 282 and (194 <= sy <= 229 or 277 <= sy <= 310)
            if not (in_pebble or in_join):
                continue
            j = (sy*gw+sx)*3
            r, g, b = generated[j:j+3]
            if not (r < 86 and g < 77 and b < 69):
                continue
            i = (y*w+x)*3
            rock = old[i:i+3]
            if max(rock) < 84:
                continue
            # Preserve all original stone relief by blending flat earth pigment.
            pigment = (142, 62, 30) if sy < 211 or sy > 290 else (48, 34, 25)
            alpha = .57 if in_pebble else .37
            for channel in range(3):
                final[i+channel] = round(rock[channel]*(1-alpha) +
                                         pigment[channel]*alpha)
            if final[i:i+3] != old[i:i+3]:
                changed += 1
                bounds = [min(bounds[0], x), min(bounds[1], y),
                          max(bounds[2], x), max(bounds[3], y)]
    assert changed > 1500
    encoded = png(w, h, final)
    BASE.write_bytes(encoded)
    TARGET.write_bytes(encoded)
    preview = jpeg(512, 512, resize(w, h, final), 52)
    assert len(preview) < 100000
    Path('dist/line-1/28.jpg').write_bytes(preview)
    review = {
        'ancestor_sha256': ANCESTOR,
        'wall_sha256': hashlib.sha256(encoded).hexdigest(),
        'format': 'PNG', 'width': w, 'height': h, 'mode': 'RGB',
        'output_paths': [str(BASE), str(TARGET)],
        'changed_pixels': changed,
        'unchanged_pixels': w*h-changed,
        'changed_bounds_inclusive': bounds,
        'outside_addition_identical': True,
        'preview': {'path': 'dist/line-1/28.jpg', 'format': 'JPEG',
                    'width': 512, 'height': 512, 'bytes': len(preview)},
        'generation': {'tool': 'mcp__image__create_models_predictions',
                       'model': 'black-forest-labs/flux-kontext-pro',
                       'prediction_id': 'r0etp7qaz1rmr0d17gvsy5ctr4',
                       'draft_sha256': hashlib.sha256(draft).hexdigest(),
                       'draft_dimensions': [gw, gh], 'draft_retained': False,
                       'postprocess': 'Only new pebble pigment retained; ancestor pixels elsewhere restored exactly.'},
        'visual_review': {'status': 'awaiting final inspection',
                          'unmet_visual_requirements': []},
    }
    Path('line-1/wall-review-28.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
