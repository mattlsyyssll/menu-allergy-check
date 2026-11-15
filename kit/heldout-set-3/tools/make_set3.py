#!/usr/bin/env python3
"""Build held-out set 3 (M33-M40) inputs inside heldout-set-3/: case-data.json, ANSWER-KEYS.md, menus/*.png.
Reuses the frozen set-1 generator (../../tools/make_kit.py) read-only; writes nothing outside heldout-set-3/.
Needs Pillow; run WITHOUT -I:  /usr/bin/python3 tools/make_set3.py   (from heldout-set-3/).
Then: keys.py write kit.json ; cases.py build kit.json ; freeze.py freeze kit.json (see README-SET3.md).
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SET3 = os.path.dirname(HERE)
KIT = os.path.dirname(SET3)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(KIT, 'tools'))
sys.path.insert(0, os.path.join(KIT, 'scripts', 'testkit'))
import menus_data3 as D2  # noqa: E402
import menus_data as M  # noqa: E402
import make_kit as MK  # noqa: E402
import common as C  # noqa: E402

UNI = MK.UNI
MK.LATIN['unicode'] = (UNI[0], 0, UNI[0], 0)   # Arial Unicode: Hangul, kana, kanji, won and yen signs

old = [d['name'] for m in M.MENUS for _, ds in m['sections'] for d in ds]
old_en = [d['en'] for m in M.MENUS for _, ds in m['sections'] for d in ds if d['en']]
old_titles = [m['title'] for m in M.MENUS]
_s2 = json.load(open(os.path.join(KIT, 'heldout-set-2', 'case-data.json'), encoding='utf-8'))['cases']
old += [d['printed_name'] for c in _s2 for d in c['dishes']]
old_en += [d['english_gloss'] for c in _s2 for d in c['dishes'] if d['english_gloss']]
old_titles += [c['title'].split(' (')[0] for c in _s2]
M.MENUS = D2.MENUS3   # make_kit.build() reads M.MENUS


def check_new():
    print('rule matches checked:', D2.check_rules())
    seen = [C.fold_name(x) for x in old + old_en]
    for m in D2.MENUS3:
        assert len(m['sections']) == 2, ('the renderer draws two columns only', m['id'])
        assert m['title'] not in old_titles, m['title']
        for _, ds in m['sections']:
            for d in ds:
                for x in (d['name'], d['en']):
                    if x:
                        assert C.fold_name(x) not in seen, ('dish name reused from M01-M24', m['id'], x)
                        for o in seen:
                            assert not (len(o) > 5 and C.name_ok(x, o)), ('dish name too close to M01-M24', m['id'], x, o)


RULE_TEXT = '''## Rule applied to every dish (new in set 3)

Each public-source list item is one rule, applied by code to every dish whose printed text (or its English translation) matches it. Examples: FARE_SES3 says baked goods, bread, buns and rolls may hold sesame, so every dish that is or includes bread, buns, rolls, toast, naan, pita, bagels, cake or pastry has "sesame Ask the kitchen" (unless a stricter fact applies); "sauces" give sesame, wheat, soy Ask; barbecue sauce gives fish and tree nut Ask; Worcestershire gives fish Ask; chili sauce gives peanut Ask; mayonnaise gives egg Ask; pasta gives egg Ask. A printed allergen word, or a basic ingredient of the named dish (flour, bread, pasta, bulgur, semolina), gives Avoid. Dish-specific Wikipedia (WP_*) facts are added by hand. Special and of-the-day dishes get Ask for all nine allergens. Rule tables: tools/menus_data3.py.

'''


def main():
    check_new()
    cases, ans, stats, per_allergen = MK.build()
    for c in cases:
        c['title'] = c['title'].replace('held out', 'held-out set 3')
    ans = [a.replace('HELD OUT', 'HELD OUT SET 3') for a in ans]
    ans[0] = '# Answer keys, held-out set 3 (M33-M40)'
    ans.insert(3, RULE_TEXT)
    os.makedirs(os.path.join(SET3, 'menus'), exist_ok=True)
    for m in D2.MENUS3:
        print(m['id'], MK.render_menu(m, os.path.join(SET3, 'menus', m['id'] + '.png')))
    C.write(os.path.join(SET3, 'case-data.json'), C.jdump({'cases': cases}))
    C.write(os.path.join(SET3, 'ANSWER-KEYS.md'), '\n'.join(ans) + '\n')
    print(json.dumps(stats), json.dumps({M.ALLERGENS[c]: n for c, n in per_allergen.items()}))


if __name__ == '__main__':
    main()
