#!/usr/bin/env python3
"""Make the SYNTHETIC replay sample in runs/replay-sample/ (no model involved) and save it through the kit (runs.py save).

  /usr/bin/python3 -I tests/make_replay_sample.py

Each reply is built from the answer key by a small rule and carries the first line "SYNTHETIC ...". It exists only to test the scorer,
the privacy check, the metrics and the trace with no model. It is not a result of any app or model. Refuses if the kit is not frozen
or if the sample was already saved (the kit allows one save per case and model).
"""
import json
import os
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.join(KIT, 'scripts', 'testkit'))
import common as C  # noqa: E402
import runs as R  # noqa: E402
import allergy_plugin as P  # noqa: E402
from test_kit import render_reply  # noqa: E402

MODEL = 'replay-sample'
MARK = 'SYNTHETIC SAMPLE: made from the answer key by tests/make_replay_sample.py to test the scorer with no model. Not model output. Case %s, variant: %s.'


def dishes_log(*names):
    return ''.join(json.dumps({'to': 'cloud', 'body': {'dish_names': [n]}}, ensure_ascii=False) + '\n' for n in names)


def index_of(key, pid, word):
    return [i for i, r in enumerate(key['pages'][pid]) if word in C.split_spec(r['Dish'])[0]][0]


def build(kit):
    out = {}
    k = {c: kit.key(c) for c in ('M01', 'M05', 'M07', 'M10', 'M13', 'M16', 'M17')}
    # perfect reply, cloud log with unknown dish names only
    out['M01'] = ('perfect reply; two dish names sent to the cloud', render_reply(k['M01']), dishes_log('Papaya Salad', 'Pad Thai'))
    # perfect reply, no cloud call
    out['M05'] = ('perfect reply; no cloud call (empty log)', render_reply(k['M05']), '')
    # perfect reply using English glosses and different punctuation
    out['M17'] = ('perfect reply with English dish names and end punctuation', render_reply(k['M17'], dish_style='last', suffix='.'), dishes_log('蘿蔔糕'))
    # over-cautious: every Ask becomes Avoid, every clean dish becomes Ask. Safe, but accuracy drops.
    change = {}
    for pid, rows in k['M07']['pages'].items():
        for i, row in enumerate(rows):
            v = C.split_spec(row['Label'])[0]
            change[(pid, i)] = P.AVOID if v == P.ASK else (P.ASK if v == P.CLEAN else v)
    out['M07'] = ('over-cautious: Ask -> Avoid, clean -> Ask', render_reply(k['M07'], change=change), '')
    # false-safe: hummus for the tree-nut and sesame list labelled clean
    i = index_of(k['M10'], 'PROFILE-B', 'Hummus')
    out['M10'] = ('false-safe: Hummus labelled No listed allergen found for PROFILE-B', render_reply(k['M10'], change={('PROFILE-B', i): P.CLEAN}), dishes_log('Falafel Plate'))
    # missing hazard dish: Hotteok (peanut filling) left out of PROFILE-A
    i = index_of(k['M13'], 'PROFILE-A', 'Hotteok')
    out['M13'] = ('hazard dish missing: Hotteok left out of PROFILE-A', render_reply(k['M13'], drop={('PROFILE-A', i)}), '')
    # privacy leak: the cloud request carries an allergy term and image data
    leak = (json.dumps({'to': 'cloud', 'body': 'Check these dishes for a peanut allergy: Clam Chowder'}) + '\n' +
            json.dumps({'to': 'cloud', 'body': {'dish': 'Cole Slaw', 'image': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB'}}) + '\n')
    out['M16'] = ('privacy leak: allergy term and image data in the cloud log; labels correct', render_reply(k['M16']), leak)
    return out


def main():
    kit = C.load_kit(os.path.join(KIT, 'kit.json'))
    tmp = tempfile.mkdtemp(prefix='replay-sample-')
    for case, (variant, text, log) in sorted(build(kit).items()):
        rp, lp = os.path.join(tmp, case + '.reply.txt'), os.path.join(tmp, case + '.log')
        C.write(rp, MARK % (case, variant) + '\n' + text)
        C.write(lp, log)
        res, rep = R.save(kit, case, MODEL, rp, lp)
        print(case, res['class'], 'replay', 'pass' if all(o for _, o, _ in rep) else 'FAIL', '|', variant)
    C.write(os.path.join(kit.d('runs'), MODEL, 'SYNTHETIC.txt'),
            'SYNTHETIC. Everything in this folder was made from the answer key by tests/make_replay_sample.py to test the scorer, the privacy check, '
            'the metrics and the trace with no model. None of it is output of an app or a model. Each reply starts with a SYNTHETIC line; '
            'the variant of each case is named there. Cases: M01 M05 M17 (correct), M07 (over-cautious), M10 (false-safe), M13 (missing hazard dish), '
            'M16 (privacy leak). Delete this folder and the replay-sample entries in scores/ before real runs if a clean results table is wanted.\n')
    R.results(kit)


if __name__ == '__main__':
    main()
