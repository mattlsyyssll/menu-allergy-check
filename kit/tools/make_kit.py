#!/usr/bin/env python3
"""Build the allergy kit inputs from menus_data.py: case-data.json, labels.json, profiles.json, heldout.json, ANSWER-KEYS.md, menus/*.png.

Run once, BEFORE keys.py write and freeze.py freeze. Needs Pillow (user-installed, so run WITHOUT -I):
    /usr/bin/python3 tools/make_kit.py            # from the kit folder
Rendering uses a seeded random generator per case, but Pillow versions can change pixels: the committed PNGs and their hashes in
FROZEN-HASHES.txt are the test input, not a rebuild.
"""
import json
import os
import random
import sys
import textwrap

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(KIT, 'scripts', 'testkit'))
import menus_data as M  # noqa: E402
import common as C  # noqa: E402
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont  # noqa: E402

SF = '/System/Library/Fonts/'
SUP = SF + 'Supplemental/'
LATIN = {
    'georgia': (SUP + 'Georgia.ttf', 0, SUP + 'Georgia Bold.ttf', 0),
    'times': (SUP + 'Times New Roman.ttf', 0, SUP + 'Times New Roman Bold.ttf', 0),
    'trebuchet': (SUP + 'Trebuchet MS.ttf', 0, SUP + 'Trebuchet MS Bold.ttf', 0),
    'verdana': (SUP + 'Verdana.ttf', 0, SUP + 'Verdana Bold.ttf', 0),
    'baskerville': (SUP + 'Baskerville.ttc', 0, SUP + 'Baskerville.ttc', 2),
    'futura': (SUP + 'Futura.ttc', 0, SUP + 'Futura.ttc', 2),
    'courier': (SUP + 'Courier New.ttf', 0, SUP + 'Courier New Bold.ttf', 0),
    'chalk': (SUP + 'Chalkboard.ttc', 0, SUP + 'Chalkboard.ttc', 1),
    'optima': (SF + 'Optima.ttc', 0, SF + 'Optima.ttc', 1),
    'palatino': (SF + 'Palatino.ttc', 0, SF + 'Palatino.ttc', 2),
    'rockwell': (SUP + 'Rockwell.ttc', 0, SUP + 'Rockwell.ttc', 1),
    'arialr': (SUP + 'Arial Rounded Bold.ttf', 0, SUP + 'Arial Rounded Bold.ttf', 0),
    'gill': (SUP + 'GillSans.ttc', 0, SUP + 'GillSans.ttc', 1),
    'cochin': (SUP + 'Cochin.ttc', 0, SUP + 'Cochin.ttc', 1),
    'ayuthaya': (SUP + 'Ayuthaya.ttf', 0, SUP + 'Ayuthaya.ttf', 0),
    'hiragino': (SF + 'Hiragino Sans GB.ttc', 0, SF + 'Hiragino Sans GB.ttc', 0),
}
UNI = (SUP + 'Arial Unicode.ttf', 0)
BG = {'cream': ((250, 244, 228), (35, 28, 22)), 'white': ((255, 255, 255), (20, 20, 20)),
      'kraft': ((206, 172, 128), (45, 30, 18)), 'chalk': ((40, 52, 46), (240, 238, 226))}
W = 1500


def font(spec, size):
    return ImageFont.truetype(spec[0], size, index=spec[1])


def wrap(draw, text, f, width):
    if not text:
        return []
    lines, cur = [], ''
    spaced = ' ' in text
    units = text.split(' ') if spaced else list(text)
    for u in units:
        trial = (cur + (' ' if spaced and cur else '') + u)
        if draw.textlength(trial, font=f) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = u
    lines.append(cur)
    return lines


def render_menu(m, out_path):
    rnd = random.Random(m['id'])
    bgc, fg = BG[m['bg']]
    fam = LATIN[m['font']]
    th = m['lang'] == 'th'
    f_title = font((fam[2], fam[3]), 66)
    f_head = font((fam[2], fam[3]), 40)
    f_name = font((fam[2], fam[3]), 34)
    f_desc = font((fam[0], fam[1]), 26)
    f_sub = font(UNI if th else (fam[0], fam[1]), 24)
    f_price = font(UNI if th else (fam[2], fam[3]), 34)
    margin, gap = 70, 60
    colw = (W - 2 * margin - gap) // 2
    probe = ImageDraw.Draw(Image.new('RGB', (10, 10)))

    def faux_bold(d, xy, t, f):
        d.text(xy, t, font=f, fill=fg)
        d.text((xy[0] + 1, xy[1]), t, font=f, fill=fg)

    def layout(d, col_sections, draw):
        heights = []
        for ci, (heading, dishes) in enumerate(col_sections):
            x = margin + ci * (colw + gap)
            y = 230
            if draw:
                faux_bold(d, (x, y), heading, f_head)
                d.line([(x, y + 58), (x + colw, y + 58)], fill=fg, width=2)
            y += 85
            for dish in dishes:
                pw = int(d.textlength(dish['price'], font=f_price))
                if draw:
                    faux_bold(d, (x, y), dish['name'], f_name) if d.textlength(dish['name'], font=f_name) <= colw - pw - 20 else None
                nl = wrap(d, dish['name'], f_name, colw - pw - 20)
                if draw:
                    if len(nl) > 1 or d.textlength(dish['name'], font=f_name) > colw - pw - 20:
                        for i, ln in enumerate(nl):
                            faux_bold(d, (x, y + i * 42), ln, f_name)
                    d.text((x + colw - pw, y), dish['price'], font=f_price, fill=fg)
                y += 42 * len(nl)
                if dish['sub']:
                    if draw:
                        d.text((x, y), dish['sub'], font=f_sub, fill=fg)
                    y += 32
                for ln in wrap(d, dish['desc'], f_desc, colw):
                    if draw:
                        d.text((x, y), ln, font=f_desc, fill=fg)
                    y += 34
                y += 26
            heights.append(y)
        return max(heights)

    secs = m['sections']
    H = layout(probe, secs, False) + margin
    im = Image.new('RGB', (W, H), bgc)
    d = ImageDraw.Draw(im)
    tw = d.textlength(m['title'], font=f_title)
    faux_bold(d, ((W - tw) / 2, 70), m['title'], f_title)
    d.line([(margin, 175), (W - margin, 175)], fill=fg, width=4)
    layout(d, secs, True)
    im = apply_style(im, m['style'], rnd, bgc)
    im.save(out_path, optimize=True)
    return im.size


def apply_style(im, style, rnd, bgc):
    w, h = im.size
    if style == 'clean':
        return im
    if style == 'photo':
        # perspective tilt, rotation, vignette, noise, slight blur (photo of a printed menu on a table)
        dx = rnd.uniform(0.01, 0.045) * w
        coeffs = _perspective([(0, 0), (w, 0), (w, h), (0, h)], [(dx, 0), (w - dx * 0.4, dx * 0.5), (w, h - dx * 0.3), (0, h)])
        bg = tuple(max(0, c - 70) for c in bgc)
        im = im.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC, fillcolor=bg)
        im = im.rotate(rnd.uniform(-3.5, 3.5), resample=Image.BICUBIC, expand=True, fillcolor=bg)
        w, h = im.size
        vig = Image.radial_gradient('L').resize((w, h))
        vig = ImageChops.invert(vig).point(lambda v: 150 + v * 105 // 255)
        im = ImageChops.multiply(im, Image.merge('RGB', (vig, vig, vig)))
        im = im.filter(ImageFilter.GaussianBlur(0.9))
        return _noise(im, 14)
    if style == 'glare':
        im = im.rotate(rnd.uniform(-2.5, 2.5), resample=Image.BICUBIC, expand=True, fillcolor=bgc)
        w, h = im.size
        glare = Image.new('L', (w, h), 0)
        gd = ImageDraw.Draw(glare)
        cx, cy = int(w * rnd.uniform(0.5, 0.8)), int(h * rnd.uniform(0.25, 0.5))
        gd.ellipse([cx - 380, cy - 220, cx + 380, cy + 220], fill=150)
        glare = glare.filter(ImageFilter.GaussianBlur(90))
        white = Image.new('RGB', (w, h), (255, 255, 255))
        im = Image.composite(white, im, glare)
        return _noise(im.filter(ImageFilter.GaussianBlur(0.7)), 9)
    if style == 'scan':
        im = im.rotate(rnd.uniform(-1.4, 1.4), resample=Image.BICUBIC, expand=True, fillcolor=bgc).convert('L')
        w, h = im.size
        d = ImageDraw.Draw(im)
        for _ in range(900):
            x, y = rnd.randrange(w), rnd.randrange(h)
            d.point((x, y), fill=rnd.randrange(60, 140))
        for y in range(0, h, 7):
            d.line([(0, y), (w, y)], fill=235 if im.getpixel((2, y)) > 200 else 40, width=1)
        return _noise(im.convert('RGB').filter(ImageFilter.GaussianBlur(0.6)), 8)
    if style == 'blur':
        im = im.rotate(rnd.uniform(-1.8, 1.8), resample=Image.BICUBIC, expand=True, fillcolor=bgc)
        small = im.resize((im.width * 3 // 5, im.height * 3 // 5), Image.BILINEAR).resize(im.size, Image.BICUBIC)
        flat = Image.blend(small, Image.new('RGB', im.size, (128, 128, 128)), 0.25)
        return _noise(flat.filter(ImageFilter.GaussianBlur(1.3)), 10)
    raise ValueError(style)


def _noise(im, sigma):
    n = Image.effect_noise(im.size, sigma).convert('RGB')
    return ImageChops.add(im, n, scale=1.0, offset=-128)


def _perspective(src, dst):
    # coefficients mapping output (dst) points back to input (src) points, as Pillow expects
    import itertools
    a = []
    b = []
    for (xs, ys), (xd, yd) in zip(src, dst):
        a.append([xd, yd, 1, 0, 0, 0, -xs * xd, -xs * yd])
        a.append([0, 0, 0, xd, yd, 1, -ys * xd, -ys * yd])
        b += [xs, ys]
    # solve 8x8 by Gaussian elimination
    n = 8
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(a[r][i]))
        a[i], a[piv] = a[piv], a[i]
        b[i], b[piv] = b[piv], b[i]
        for r in range(i + 1, n):
            f = a[r][i] / a[i][i]
            for c in range(i, n):
                a[r][c] -= f * a[i][c]
            b[r] -= f * b[i]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (b[i] - sum(a[i][c] * x[c] for c in range(i + 1, n))) / a[i][i]
    return x


# ---------------------------------------------------------------- key and data
def dish_label(dish, allergens):
    hit = {c: lv for c, lv, _, _ in dish['facts'] if c in allergens}
    if 'A' in hit.values():
        return 'avoid'
    if hit:
        return 'ask'
    return 'clean'


def reasons_for(dish, allergens):
    out = []
    for c, lv, why, src in dish['facts']:
        if c in allergens:
            out.append({'allergen': M.ALLERGENS[c], 'level': 'Avoid' if lv == 'A' else 'Ask', 'reason': why, 'source': src,
                        'unverified': src == 'GEN'})
    return out


def aliases(dish):
    seen, out = set(), []
    for x in (dish['name'], dish['sub'], dish['en']):
        if x and C.fold_name(x) not in seen:
            seen.add(C.fold_name(x))
            out.append(x)
    return out


PROMPT = """I am sending a photo of a restaurant menu (the image file menus/{cid}.png). Please check every dish on the menu for four people who have food allergies.

PROFILE-A is allergic to: peanut.
PROFILE-B is allergic to: tree nut, sesame.
PROFILE-C is allergic to: milk, egg, wheat, soy.
PROFILE-D is allergic to: fish, shellfish.

For every dish and for each person, tell me whether the dish is safe for them.

Write the answer in exactly this form, one block per person, and one Dish, Label and Reason line group per dish (use the dish name as printed on the menu):

=== PROFILE-A
Dish: <dish name as printed>
Label: <No listed allergen found, or Ask the kitchen, or Avoid>
Reason: <one short line>

Then the same for === PROFILE-B, === PROFILE-C and === PROFILE-D.
"""


def menu_text(m):
    out = [m['title'], '']
    for heading, dishes in m['sections']:
        out.append('## ' + heading)
        for d in dishes:
            out.append('%s  %s' % (d['name'], d['price']))
            if d['sub']:
                out.append('  (%s)' % d['sub'])
            out.append('  ' + d['desc'])
        out.append('')
    return '\n'.join(out)


def build():
    cases = []
    ans = ['# Answer keys', '',
           'Written before any run. Labels per profile are derived by one rule from the facts listed with each dish: any Avoid-level fact for the profile gives "Avoid"; otherwise any Ask-level fact gives "Ask the kitchen"; otherwise "No listed allergen found". Source id GEN = general culinary knowledge, no public page fetched: Unverified. Source list at the end.', '']
    stats = {'pairs': 0, 'hazard': 0, 'avoid': 0, 'ask': 0, 'clean': 0, 'dishes': 0}
    per_allergen = {c: 0 for c in M.ALLERGENS}
    for m in M.MENUS:
        names = [d['name'] for _, ds in m['sections'] for d in ds]
        assert len(set(n.casefold() for n in names)) == len(names), m['id']
        # no two dishes of one menu may match each other under the scorer's name rule
        alld = [d for _, ds in m['sections'] for d in ds]
        for i, a in enumerate(alld):
            for b in alld[i + 1:]:
                for x in aliases(a):
                    assert not C.name_ok(x, ' | '.join(aliases(b))), (m['id'], a['name'], b['name'])
            if m['lang'] != 'en':
                assert a['en'], (m['id'], a['name'])
        key, dishes_out = {}, []
        for pid, prof in M.PROFILES.items():
            rows = []
            for d in alld:
                lab = M.LABELS[dish_label(d, prof['allergens'])]
                rows.append({'Dish': {'value': ' | '.join(aliases(d)), 'match': 'name'},
                             'Label': {'value': lab, 'group': 'accuracy', 'match': 'label'}})
                stats['pairs'] += 1
                k = {'No listed allergen found': 'clean', 'Ask the kitchen': 'ask', 'Avoid': 'avoid'}[lab]
                stats[k] += 1
                stats['hazard'] += lab != 'No listed allergen found'
            key[pid] = rows
        for d in alld:
            stats['dishes'] += 1
            for c in {f[0] for f in d['facts']}:
                per_allergen[c] += 1
            dishes_out.append({'printed_name': d['name'], 'printed_subtitle': d['sub'], 'price': d['price'], 'printed_description': d['desc'],
                               'english_gloss': d['en'], 'facts': [{'allergen': M.ALLERGENS[c], 'level': 'Avoid' if lv == 'A' else 'Ask', 'reason': w, 'source': s}
                                                                   for c, lv, w, s in d['facts']],
                               'labels': {pid: M.LABELS[dish_label(d, p['allergens'])] for pid, p in M.PROFILES.items()}})
        cases.append({'id': m['id'], 'title': '%s (%s, %s, %s)' % (m['title'], m['lang'], m['style'], 'held out' if m['heldout'] else 'development'),
                      'lang': m['lang'], 'style': m['style'], 'heldout': m['heldout'], 'image': 'menus/%s.png' % m['id'],
                      'prompt': PROMPT.format(cid=m['id']), 'steps': [], 'person': {},
                      'served': {'menu-source.txt': menu_text(m)}, 'key': key, 'dishes': dishes_out})
        ans += ['## %s %s (%s, %s, %s)' % (m['id'], m['title'], m['lang'], m['style'], 'HELD OUT' if m['heldout'] else 'development'), '',
                '| Dish as printed | A peanut | B tree nut + sesame | C milk, egg, wheat, soy | D fish + shellfish | Facts (level: reason [source]) |', '|---|---|---|---|---|---|']
        for do in dishes_out:
            facts = '; '.join('%s %s: %s [%s%s]' % (f['allergen'], f['level'], f['reason'], f['source'], ', UNVERIFIED' if f['source'] == 'GEN' else '') for f in do['facts']) or 'none: clean'
            ans.append('| %s | %s |  %s |' % (do['printed_name'] + (' (%s)' % do['english_gloss'] if do['english_gloss'] else ''),
                                              ' | '.join(do['labels'][p] for p in M.PROFILES), facts.replace('|', '/')))
        ans.append('')
    ans += ['## Sources', '']
    for sid, (txt, url, st) in M.SOURCES.items():
        ans.append('- **%s**: %s. %s (%s)' % (sid, txt, url, st))
    return cases, ans, stats, per_allergen


def main():
    cases, ans, stats, per_allergen = build()
    os.makedirs(os.path.join(KIT, 'menus'), exist_ok=True)
    for m in M.MENUS:
        size = render_menu(m, os.path.join(KIT, 'menus', m['id'] + '.png'))
        print(m['id'], size)
    C.write(os.path.join(KIT, 'case-data.json'), C.jdump({'cases': cases}))
    C.write(os.path.join(KIT, 'ANSWER-KEYS.md'), '\n'.join(ans) + '\n')
    labels = {'header': [], 'pages': {pid: {'repeat': 'Dish', 'labels': [
        {'name': 'Dish', 'kind': 'name'}, {'name': 'Label', 'kind': 'label'}, {'name': 'Reason', 'kind': 'text'}]} for pid in M.PROFILES}}
    C.write(os.path.join(KIT, 'labels.json'), C.jdump(labels))
    terms = json.load(open(os.path.join(HERE, 'terms.json'), encoding='utf-8'))
    prof = {'profiles': {pid: {'name': p['name'], 'allergens': [M.ALLERGENS[c] for c in p['allergens']],
                               'terms': sorted({t for c in p['allergens'] for t in terms['by_allergen'][M.ALLERGENS[c]]})}
                         for pid, p in M.PROFILES.items()},
            'generic_terms': terms['generic'], 'note': 'Privacy check: none of these terms may appear in a cloud request outside a printed dish name.'}
    C.write(os.path.join(KIT, 'profiles.json'), C.jdump(prof))
    C.write(os.path.join(KIT, 'heldout.json'), C.jdump({
        'heldout': [m['id'] for m in M.MENUS if m['heldout']], 'development': [m['id'] for m in M.MENUS if not m['heldout']],
        'rule': 'Tune the app only on development cases. Held-out cases are scored once, at the end, after the freeze.'}))
    print(json.dumps(stats), json.dumps({M.ALLERGENS[c]: n for c, n in per_allergen.items()}))


if __name__ == '__main__':
    main()
