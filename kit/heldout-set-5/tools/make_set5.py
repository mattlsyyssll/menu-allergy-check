#!/usr/bin/env python3
"""Build held-out set 5 (M49-M56) inputs inside heldout-set-5/: case-data.json, ANSWER-KEYS.md, menus/*.png.
Reuses the frozen set-1 generator (../../tools/make_kit.py) read-only; writes nothing outside heldout-set-5/.
Needs Pillow; run WITHOUT -I:  /usr/bin/python3 tools/make_set5.py   (from heldout-set-5/).
Then: keys.py write kit.json ; cases.py build kit.json ; freeze.py freeze kit.json (see README-SET5.md).
"""
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SET5 = os.path.dirname(HERE)
KIT = os.path.dirname(SET5)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(KIT, 'tools'))
sys.path.insert(0, os.path.join(KIT, 'scripts', 'testkit'))
import menus_data5 as D2  # noqa: E402
import menus_data as M  # noqa: E402
import make_kit as MK  # noqa: E402
import common as C  # noqa: E402

UNI = MK.UNI
MK.LATIN['unicode'] = (UNI[0], 0, UNI[0], 0)   # Arial Unicode: Hangul, kana, kanji, won and yen signs

old = [d['name'] for m in M.MENUS for _, ds in m['sections'] for d in ds]
old_en = [d['en'] for m in M.MENUS for _, ds in m['sections'] for d in ds if d['en']]
old_titles = [m['title'] for m in M.MENUS]
_p = json.load(open(os.path.join(KIT, 'case-data.json'), encoding='utf-8'))['cases']
old += [d['printed_name'] for c in _p for d in c['dishes']]
old_en += [d['english_gloss'] for c in _p for d in c['dishes'] if d['english_gloss']]
for _n in ('heldout-set-2', 'heldout-set-3', 'heldout-set-4'):
    _s2 = json.load(open(os.path.join(KIT, _n, 'case-data.json'), encoding='utf-8'))['cases']
    old += [d['printed_name'] for c in _s2 for d in c['dishes']]
    old_en += [d['english_gloss'] for c in _s2 for d in c['dishes'] if d['english_gloss']]
    old_titles += [c['title'].split(' (')[0] for c in _s2]
M.MENUS = D2.MENUS5   # make_kit.build() reads M.MENUS
from make_render5 import render_menu5  # noqa: E402


def check_new():
    print('rule matches checked:', D2.check_rules())
    seen = [C.fold_name(x) for x in old + old_en]
    for m in D2.MENUS5:
        assert sum(m['colsplit']) == len(m['sections']) and len(m['colsplit']) <= 2, ('colsplit', m['id'])
        assert m['title'] not in old_titles, m['title']
        for _, ds in m['sections']:
            for d in ds:
                for x in (d['name'], d['en']):
                    if x:
                        assert C.fold_name(x) not in seen, ('dish name reused from M01-M40', m['id'], x)
                        for o in seen:
                            assert not (len(o) > 5 and C.name_ok(x, o)), ('dish name too close to M01-M40', m['id'], x, o)


RULE_TEXT = '''## Rule applied to every dish (set 5: named foods only)

Each named food from a fetched public list is one rule, applied by code to every dish whose printed text (or English translation) contains that food. Examples: bread, buns, rolls, bagels, breadsticks, bread crumbs, hummus, crackers, pretzels, sausages, shish kebabs, rice cakes give "sesame Ask the kitchen"; chili sauce, hot sauce, pesto, gravy, chocolate, ice cream, pudding, pies, cookies give peanut Ask; barbecue sauce, Caesar, Worcestershire, dashi give fish Ask; fish sauce gives shellfish Ask; mayonnaise, tartar sauce, pasta, bread give egg Ask; soy sauce, batter, breaded food, beer, marinara, sausages give wheat Ask. A printed allergen word, or a basic ingredient (flour, bread, pasta, dough, dumplings, ramen noodles), gives Avoid. Broad category, cuisine and cross-contact lines that name no food ("baked goods", "sauces, dressings, gravies and marinades", "soups", "stews", "stir fry", "Asian cuisine", "shellfish sometimes dipped in milk") are NOT applied. Special and of-the-day dishes get Ask for all nine allergens. Rule tables: tools/menus_data5.py (RULES_A, RULES_Q). Set 5 adds one named-food rule from a fetched page: achar (WP_MOMO) gives peanut, sesame and soy Ask.

'''


def main():
    check_new()
    cases, ans, stats, per_allergen = MK.build()
    for c in cases:
        c['title'] = c['title'].replace('held out', 'held-out set 5')
    ans = [a.replace('HELD OUT', 'HELD OUT SET 5') for a in ans]
    ans[0] = '# Answer keys, held-out set 5 (M49-M56)'
    ans.insert(3, RULE_TEXT)
    os.makedirs(os.path.join(SET5, 'menus'), exist_ok=True)
    for m in D2.MENUS5:
        print(m['id'], render_menu5(m, os.path.join(SET5, 'menus', m['id'] + '.png')))
    C.write(os.path.join(SET5, 'case-data.json'), C.jdump({'cases': cases}))
    C.write(os.path.join(SET5, 'ANSWER-KEYS.md'), '\n'.join(ans) + '\n')
    print(json.dumps(stats), json.dumps({M.ALLERGENS[c]: n for c, n in per_allergen.items()}))


if __name__ == '__main__':
    main()
