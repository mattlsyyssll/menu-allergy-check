#!/usr/bin/env python3
"""Build held-out set 2 (M25-M32) inputs inside heldout-set-2/: case-data.json, ANSWER-KEYS.md, menus/*.png.
Reuses the frozen set-1 generator (../../tools/make_kit.py) read-only; writes nothing outside heldout-set-2/.
Needs Pillow; run WITHOUT -I:  /usr/bin/python3 tools/make_set2.py   (from heldout-set-2/).
Then: keys.py write kit.json ; cases.py build kit.json ; freeze.py freeze kit.json (see README-SET2.md).
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SET2 = os.path.dirname(HERE)
KIT = os.path.dirname(SET2)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(KIT, 'tools'))
sys.path.insert(0, os.path.join(KIT, 'scripts', 'testkit'))
import menus_data2 as D2  # noqa: E402
import menus_data as M  # noqa: E402
import make_kit as MK  # noqa: E402
import common as C  # noqa: E402

UNI = MK.UNI
MK.LATIN['unicode'] = (UNI[0], 0, UNI[0], 0)   # Arial Unicode: Hangul, kana, kanji, won and yen signs

old = [d['name'] for m in M.MENUS for _, ds in m['sections'] for d in ds]
old_en = [d['en'] for m in M.MENUS for _, ds in m['sections'] for d in ds if d['en']]
old_titles = [m['title'] for m in M.MENUS]
M.MENUS = D2.MENUS2   # make_kit.build() reads M.MENUS


def check_new():
    seen = [C.fold_name(x) for x in old + old_en]
    for m in D2.MENUS2:
        assert len(m['sections']) == 2, ('the renderer draws two columns only', m['id'])
        assert m['title'] not in old_titles, m['title']
        for _, ds in m['sections']:
            for d in ds:
                for x in (d['name'], d['en']):
                    if x:
                        assert C.fold_name(x) not in seen, ('dish name reused from M01-M24', m['id'], x)
                        for o in seen:
                            assert not (len(o) > 5 and C.name_ok(x, o)), ('dish name too close to M01-M24', m['id'], x, o)


def main():
    check_new()
    cases, ans, stats, per_allergen = MK.build()
    for c in cases:
        c['title'] = c['title'].replace('held out', 'held-out set 2')
    ans = [a.replace('HELD OUT', 'HELD OUT SET 2') for a in ans]
    ans[0] = '# Answer keys, held-out set 2 (M25-M32)'
    os.makedirs(os.path.join(SET2, 'menus'), exist_ok=True)
    for m in D2.MENUS2:
        print(m['id'], MK.render_menu(m, os.path.join(SET2, 'menus', m['id'] + '.png')))
    C.write(os.path.join(SET2, 'case-data.json'), C.jdump({'cases': cases}))
    C.write(os.path.join(SET2, 'ANSWER-KEYS.md'), '\n'.join(ans) + '\n')
    print(json.dumps(stats), json.dumps({M.ALLERGENS[c]: n for c, n in per_allergen.items()}))


if __name__ == '__main__':
    main()
