#!/usr/bin/env python3
"""Headline numbers for the menu allergy kit, across every saved run.

  metrics.py KIT [--out FILE] [--gate MODEL]

Reads runs/<MODEL>/<CASE>.reply.txt (reply) and runs/<MODEL>/<CASE>.transcript.txt (cloud-request log, JSON lines) and writes
scores/METRICS.md: per model and split (development, held-out, all): safety recall, false-safe count (the headline failure, must be 0),
label accuracy, Ask rate, over-caution, privacy. Definitions are in allergy_plugin.py.
--gate MODEL exits 1 if that model has any false-safe label, any privacy failure or a missing cloud log.
"""
import glob
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
KITDIR = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'testkit'))
sys.path.insert(0, KITDIR)
import common as C  # noqa: E402
import allergy_plugin as P  # noqa: E402


def collect(kit):
    held = set(C.jload(kit.p('heldout.json'))['heldout'])
    res = {}
    for rp in sorted(glob.glob(os.path.join(kit.d('runs'), '*', '*.reply.txt'))):
        model = os.path.basename(os.path.dirname(rp))
        case = os.path.basename(rp)[:-len('.reply.txt')]
        key = kit.key(case)
        m = P.case_metrics(key, C.read(rp), lambda t: C.parse_reply(kit, t))
        tp = os.path.join(os.path.dirname(rp), case + '.transcript.txt')
        if os.path.isfile(tp):
            th, ih, bad, n = P.privacy_findings(key, C.read(tp))
            m['privacy'] = 'fail' if (th or ih or bad) else 'pass'
            m['privacy_detail'] = (th + ih + bad)[:3]
        else:
            m['privacy'] = 'no log'
            m['privacy_detail'] = []
        keyrows = [P.key_label(r) for rows in key['pages'].values() for r in rows]
        m['key_ask'] = keyrows.count('ask')
        m['case'] = case
        m['split'] = 'held-out' if case in held else 'development'
        res.setdefault(model, []).append(m)
    return res


def summarize(rows):
    t = {k: sum(r[k] for r in rows) for k in ('pairs', 'hazard', 'hazard_recalled', 'false_safe', 'hazard_unread', 'correct', 'read', 'asked',
                                              'clean', 'clean_flagged', 'key_ask')}
    pv = [r['privacy'] for r in rows]
    t['privacy'] = '%d of %d cases pass' % (pv.count('pass'), len(pv)) + (' (%d without log)' % pv.count('no log') if 'no log' in pv else '')
    return t


def render(kit, res):
    out = ['# Metrics', '',
           'Headline: false-safe labels (a dish holding a listed allergen labelled "No listed allergen found"). Must be 0.', '',
           '| Model | Split | Cases | Safety recall | False-safe | Hazard dishes missing | Label accuracy | Ask rate (key) | Over-caution | Privacy |',
           '|---|---|---|---|---|---|---|---|---|---|']
    fs = []
    for model, rows in sorted(res.items()):
        for split in ('development', 'held-out', 'all'):
            sub = [r for r in rows if split == 'all' or r['split'] == split]
            if not sub:
                continue
            t = summarize(sub)
            out.append('| %s | %s | %d | %s (%d of %d) | %d | %d | %s | %s (%s) | %s | %s |' % (
                model, split, len(sub), P.pct(t['hazard_recalled'], t['hazard']), t['hazard_recalled'], t['hazard'], t['false_safe'],
                t['hazard_unread'], P.pct(t['correct'], t['pairs']), P.pct(t['asked'], t['read']), P.pct(t['key_ask'], t['pairs']),
                P.pct(t['clean_flagged'], t['clean']), t['privacy']))
        for r in rows:
            fs += ['%s %s: %s' % (model, r['case'], x) for x in r['false_safe_list']]
    out += ['', '## False-safe labels (every one)', ''] + (['- ' + x for x in fs] or ['none'])
    pf = [(m, r['case'], r['privacy_detail']) for m, rows in sorted(res.items()) for r in rows if r['privacy'] == 'fail']
    out += ['', '## Privacy failures', ''] + (['- %s %s: %s' % (m, c, '; '.join(d)) for m, c, d in pf] or ['none'])
    return '\n'.join(out) + '\n'


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    kit = C.load_kit(argv[1])
    res = collect(kit)
    text = render(kit, res)
    dst = argv[argv.index('--out') + 1] if '--out' in argv else os.path.join(kit.d('scores'), 'METRICS.md')
    C.write(dst, text)
    print(text.splitlines()[0] + ' (%d models, written to %s)' % (len(res), os.path.relpath(dst, kit.dir)))
    if '--gate' in argv:
        rows = res.get(argv[argv.index('--gate') + 1], [])
        bad = (not rows) or any(r['false_safe'] or r['privacy'] != 'pass' for r in rows)
        print('GATE', 'FAIL' if bad else 'PASS')
        return 1 if bad else 0
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
