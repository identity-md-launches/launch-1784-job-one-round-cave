"""One-time additive composition; generated pigment only, exact ancestor elsewhere."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

ANCESTOR = '500c86d20a507bab207c0659ab9fb16e9c1f3f5e99af2ffcc8f5be82a2e71309'
BASE = Path('artifacts/line-2/wall.png')
TARGET = Path('artifacts/line-2/wall-v8.png')


def main():
    old_bytes, draft = BASE.read_bytes(), TARGET.read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == ANCESTOR
    w, h, old = read_png(old_bytes)
    dw, dh, generated = read_png(draft)
    assert (w, h) == (1254, 1254) and dw == dh
    edge = 175
    small = resize(dw, dh, generated, edge)
    x0, y0 = 866, 787
    final = bytearray(old)
    colors = {'charcoal': (43, 29, 18), 'ochre': (146, 58, 24), 'chalk': (212, 190, 150)}
    counts = dict.fromkeys(colors, 0)
    for y in range(edge):
        for x in range(edge):
            r, g, b = small[(y*edge+x)*3:(y*edge+x)*3+3]
            ox, oy = x0+x, y0+y
            i = (oy*w+ox)*3
            rock = old[i:i+3]
            if max(rock) < 85 or (ox*19+oy*31) % 13 == 0:
                continue
            kind = None
            if max(r, g, b) < 130:
                kind = 'charcoal'
            elif r > 90 and g < .65*r and b < .45*r:
                kind = 'ochre'
            elif ((x/edge-.669)**2 + (y/edge-.756)**2 < .047**2
                  and r > 210 and g > 185 and b > 145):
                kind = 'chalk'
            if kind:
                light = min(1.15, max(.65, sum(rock)/(3*140)))
                alpha = .70 if kind != 'chalk' else .64
                for c in range(3):
                    final[i+c] = round(rock[c]*(1-alpha) + colors[kind][c]*light*alpha)
                counts[kind] += 1
    changed = 0
    bounds = [w, h, 0, 0]
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            if final[i:i+3] != old[i:i+3]:
                assert x0 <= x < x0+edge and y0 <= y < y0+edge
                assert max(old[i:i+3]) >= 85
                changed += 1
                bounds = [min(bounds[0], x), min(bounds[1], y), max(bounds[2], x), max(bounds[3], y)]
    assert changed > 500 and all(counts.values())
    encoded = png(w, h, final)
    BASE.write_bytes(encoded)
    TARGET.write_bytes(encoded)
    preview = jpeg(512, 512, resize(w, h, final), 52)
    assert len(preview) <= 100_000
    Path('dist/line-2/28.jpg').write_bytes(preview)
    review = {
        'name': 'Two Gates', 'number': 28,
        'ancestor_sha256': ANCESTOR, 'sha256': hashlib.sha256(encoded).hexdigest(),
        'full_wall': {'format': 'PNG', 'mode': 'RGB', 'width': w, 'height': h},
        'wall_paths': [str(BASE), str(TARGET)],
        'addition_region': {'x': x0, 'y': y0, 'width': edge, 'height': edge},
        'changed_pixels': changed, 'unchanged_pixels': w*h-changed,
        'changed_bounds_inclusive': bounds, 'pigment_pixels': counts,
        'outside_region_pixel_identical': True, 'deep_cracks_preserved': True,
        'preview': {'path': 'dist/line-2/28.jpg', 'format': 'JPEG', 'width': 512,
                    'height': 512, 'bytes': len(preview)},
        'generation': {'tool': 'mcp__image__generate_image',
                       'draft_sha256': hashlib.sha256(draft).hexdigest(),
                       'draft_dimensions': [dw, dh], 'draft_retained': False,
                       'prompt_file': 'line-2/WALL-28.md'},
        'method': 'Retained generated pigment only on vacant lower-right stone; original rock texture remains beneath the pigment. Every pixel outside the addition is exact.',
        'visual_review': 'Awaiting final PNG and JPEG inspection',
        'unmet_visual_requirements': []}
    Path('line-2/wall-review-28.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
