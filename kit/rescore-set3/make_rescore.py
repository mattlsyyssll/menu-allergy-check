#!/usr/bin/env python3
"""Rebuild the documented set-3 re-score and check it equals the saved files.

Usage (from kit/): python3 -I rescore-set3/make_rescore.py
1. Re-labels every set-3 key answer from its own facts in heldout-set-3/case-data.json with the broad-line facts removed
   (BROAD below), the strictest remaining fact winning, and compares with rescore-set3/keys/.
2. Runs the frozen scorer (scripts/metrics.py) on a temporary copy of the kit with those keys and compares the result
   with rescore-set3/METRICS-rescore.md.
Prints "rescore check ok" and exits 0 when both match. Frozen files are never written.
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(KIT, 'rescore-set3')
BROAD = re.compile(r"baked goods|dressings, gravies, marinades and sauces|lists (soup|sauce|marinated|skewers|stir-fried|herb|stew|broth|fried|curry|noodle|rice)\b|dipped in milk|\(or flavored rice|\(sauces", re.I)
LISTS = {'PROFILE-A': ['peanut'], 'PROFILE-B': ['tree nut', 'sesame'], 'PROFILE-C': ['milk', 'egg', 'wheat/gluten', 'soy'], 'PROFILE-D': ['fish', 'shellfish']}

def relabel():
    cd = {c['id']: c for c in json.load(open(os.path.join(KIT, 'heldout-set-3', 'case-data.json'), encoding='utf-8'))['cases']}
    out = {}
    for f in sorted(glob.glob(os.path.join(KIT, 'heldout-set-3', 'keys', 'M*-key.json'))):
        k = json.load(open(f, encoding='utf-8'))
        dishes = {d['printed_name']: d for d in cd[k['case']]['dishes']}
        for p, rows in k['pages'].items():
            for r in rows:
                d = dishes[r['Dish']['value'].split(' | ')[0]]
                lv = {x['level'] for x in d['facts'] if x['allergen'] in LISTS[p] and not BROAD.search(x['reason'])}
                r['Label']['value'] = 'Avoid' if 'Avoid' in lv else 'Ask the kitchen' if 'Ask' in lv else 'No listed allergen found'
        out[os.path.basename(f)] = k
    return out

def main():
    bad = 0
    for name, k in relabel().items():
        saved = json.load(open(os.path.join(HERE, 'keys', name), encoding='utf-8'))
        if saved != k:
            print('DIFFERS', name); bad += 1
    tmp = tempfile.mkdtemp()
    try:
        copy = os.path.join(tmp, 'kit')
        shutil.copytree(KIT, copy, ignore=shutil.ignore_patterns('.git', 'runs'))
        shutil.copytree(os.path.join(KIT, 'heldout-set-3', 'runs'), os.path.join(copy, 'heldout-set-3', 'runs'), dirs_exist_ok=True)
        for f in glob.glob(os.path.join(HERE, 'keys', '*.json')):
            shutil.copy(f, os.path.join(copy, 'heldout-set-3', 'keys', os.path.basename(f)))
        out = os.path.join(tmp, 'm.md')
        subprocess.run([sys.executable, '-I', os.path.join(copy, 'scripts', 'metrics.py'), 'kit.json', '--out', out], cwd=os.path.join(copy, 'heldout-set-3'), check=True, stdout=subprocess.DEVNULL)
        if open(out, encoding='utf-8').read() != open(os.path.join(HERE, 'METRICS-rescore.md'), encoding='utf-8').read():
            print('DIFFERS METRICS-rescore.md'); bad += 1
    finally:
        shutil.rmtree(tmp)
    if bad:
        sys.exit('rescore check FAILED')
    print('rescore check ok')

if __name__ == '__main__':
    main()
